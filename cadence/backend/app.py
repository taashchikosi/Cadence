import os
import json
from datetime import date, timedelta
from flask import Flask, request, jsonify, g, send_file
from flask_cors import CORS

from auth import require_auth
from database import query, execute
from metrics import calculate_all_metrics, get_multi_week_metrics
from pattern_detection import detect_all_patterns
from prompt_builder import build_weekly_review_prompt
from llm_service import generate_weekly_review
from conversation_service import chat, extract_data, opening_message
from tts_service import synthesize
from pdf_service import generate_pdf
from rag_service import ingest_knowledge_base, has_knowledge_base, retrieve_relevant_chunks, format_rag_context
from report_service import generate_coach_report
from seed_demo import seed_all_users

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def current_week_start():
    today = date.today()
    return (today - timedelta(days=today.weekday())).isoformat()


def get_user_profile(user_id):
    return query("SELECT * FROM user_profiles WHERE id=%s", (user_id,), one=True)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "knowledge_base": has_knowledge_base()})


# ---------------------------------------------------------------------------
# User profile / onboarding
# ---------------------------------------------------------------------------

@app.route("/api/profile", methods=["GET"])
@require_auth
def get_profile():
    row = get_user_profile(g.user_id)
    return jsonify(dict(row) if row else None)


@app.route("/api/profile", methods=["POST"])
@require_auth
def upsert_profile():
    d = request.json
    execute("""
        INSERT INTO user_profiles (id, role_type, self_identified_failure_pattern,
            typical_week_structure, top_3_active_goals, voice_preference,
            response_mode, onboarding_complete)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO UPDATE SET
            role_type=EXCLUDED.role_type,
            self_identified_failure_pattern=EXCLUDED.self_identified_failure_pattern,
            typical_week_structure=EXCLUDED.typical_week_structure,
            top_3_active_goals=EXCLUDED.top_3_active_goals,
            voice_preference=EXCLUDED.voice_preference,
            response_mode=EXCLUDED.response_mode,
            onboarding_complete=EXCLUDED.onboarding_complete,
            updated_at=NOW()
    """, (
        g.user_id,
        d.get("role_type"),
        d.get("self_identified_failure_pattern"),
        d.get("typical_week_structure"),
        d.get("top_3_active_goals"),
        d.get("voice_preference", "female"),
        d.get("response_mode", "text"),
        d.get("onboarding_complete", False),
    ))
    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------------------
# Daily logs
# ---------------------------------------------------------------------------

@app.route("/api/daily-log", methods=["POST"])
@require_auth
def create_daily_log():
    d = request.json
    row = execute("""
        INSERT INTO daily_logs (user_id, date, execution_score, friction_tag,
            deep_work_blocks, free_text)
        VALUES (%s,%s,%s,%s,%s,%s) RETURNING id
    """, (g.user_id, d["date"], d.get("execution_score"), d.get("friction_tag"),
          d.get("deep_work_blocks", "0"), d.get("free_text")))
    log_id = row["id"]
    for task in d.get("tasks", []):
        if task.get("description", "").strip():
            execute(
                "INSERT INTO tasks (daily_log_id, user_id, description, status, is_planned) "
                "VALUES (%s,%s,%s,%s,%s)",
                (log_id, g.user_id, task["description"], task.get("status", "planned"), True)
            )
    return jsonify({"status": "ok", "id": str(log_id)}), 201


@app.route("/api/daily-logs", methods=["GET"])
@require_auth
def get_daily_logs():
    rows = query(
        "SELECT * FROM daily_logs WHERE user_id=%s ORDER BY date DESC LIMIT 30",
        (g.user_id,)
    )
    result = []
    for r in rows:
        log = dict(r)
        tasks = query("SELECT * FROM tasks WHERE daily_log_id=%s", (log["id"],))
        log["tasks"] = [dict(t) for t in tasks]
        log["id"] = str(log["id"])
        result.append(log)
    return jsonify(result)


# ---------------------------------------------------------------------------
# Conversations (Monday + Friday)
# ---------------------------------------------------------------------------

@app.route("/api/conversation/start", methods=["POST"])
@require_auth
def start_conversation():
    d = request.json
    session_type = d.get("type")  # "monday" or "friday"
    week_start = d.get("week_start_date", current_week_start())
    profile = get_user_profile(g.user_id)
    profile_dict = dict(profile) if profile else {}
    voice = profile_dict.get("voice_preference", "female")

    recent_ctx = ""
    prev_review = query(
        "SELECT diagnosis FROM ai_reviews WHERE user_id=%s ORDER BY created_at DESC LIMIT 1",
        (g.user_id,), one=True
    )
    if prev_review:
        recent_ctx = prev_review["diagnosis"]

    opener = opening_message(voice, session_type, profile_dict, recent_ctx)

    session_row = execute("""
        INSERT INTO conversation_sessions
            (user_id, session_type, week_start_date, messages, status)
        VALUES (%s,%s,%s,%s,'active') RETURNING id
    """, (g.user_id, session_type, week_start,
          json.dumps([{"role": "assistant", "content": opener}])))

    audio_b64 = None
    if profile_dict.get("response_mode") == "voice":
        audio_b64, _ = synthesize(opener, voice)

    return jsonify({
        "session_id": str(session_row["id"]),
        "message": opener,
        "audio": audio_b64,
    })


@app.route("/api/conversation/message", methods=["POST"])
@require_auth
def send_message():
    d = request.json
    session_id = d["session_id"]
    user_msg = d["message"]

    session = query(
        "SELECT * FROM conversation_sessions WHERE id=%s AND user_id=%s",
        (session_id, g.user_id), one=True
    )
    if not session:
        return jsonify({"error": "Session not found"}), 404

    messages = session["messages"] or []
    messages.append({"role": "user", "content": user_msg})

    profile = get_user_profile(g.user_id)
    profile_dict = dict(profile) if profile else {}
    voice = profile_dict.get("voice_preference", "female")
    session_type = session["session_type"]

    ai_reply = chat(messages, voice, session_type, profile_dict, query_text=user_msg)
    messages.append({"role": "assistant", "content": ai_reply})

    extracted = extract_data(ai_reply)
    status = "complete" if extracted else "active"

    execute("""
        UPDATE conversation_sessions
        SET messages=%s, extracted_data=%s, status=%s, updated_at=NOW()
        WHERE id=%s
    """, (json.dumps(messages), json.dumps(extracted or {}), status, session_id))

    if extracted and status == "complete":
        _save_extracted_data(g.user_id, session_type,
                             session["week_start_date"], extracted)

    audio_b64 = None
    reply_text = ai_reply.replace(f"EXTRACTED:{json.dumps(extracted)}", "").strip() if extracted else ai_reply
    if profile_dict.get("response_mode") == "voice":
        audio_b64, _ = synthesize(reply_text, voice)

    return jsonify({
        "message": reply_text,
        "audio": audio_b64,
        "complete": status == "complete",
        "extracted": extracted,
    })


def _save_extracted_data(user_id, session_type, week_start_date, data):
    review_data   = data.get("review", data)
    planning_data = data.get("planning", {})

    exec_score  = review_data.get("execution_score")
    friction    = review_data.get("friction_tag")
    deep_hours  = review_data.get("deep_work_hours") or 0
    reflection  = review_data.get("reflection", "")

    def hours_to_blocks(h):
        h = h or 0
        if h < 4:  return "0"
        if h < 8:  return "1"
        if h < 14: return "2"
        return "3+"

    # One weekly log entry per week (dated Monday)
    log_row = execute("""
        INSERT INTO daily_logs
            (user_id, date, execution_score, friction_tag, deep_work_blocks, free_text)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
    """, (user_id, week_start_date, exec_score, friction,
          hours_to_blocks(deep_hours), reflection))
    if not log_row:
        # Row already exists — update it then fetch the id
        execute("""
            UPDATE daily_logs SET
                execution_score  = %s,
                friction_tag     = %s,
                deep_work_blocks = %s,
                free_text        = %s
            WHERE user_id = %s AND date = %s
        """, (exec_score, friction, hours_to_blocks(deep_hours), reflection,
              user_id, week_start_date))
        log_row = execute(
            "SELECT id FROM daily_logs WHERE user_id=%s AND date=%s",
            (user_id, week_start_date)
        )
    log_id = log_row["id"]

    # Replace tasks for this weekly log
    execute("DELETE FROM tasks WHERE daily_log_id = %s", (log_id,))
    for task in review_data.get("tasks", []):
        desc = (task.get("description") or "").strip()
        if desc:
            execute("""
                INSERT INTO tasks (daily_log_id, user_id, description, status, is_planned)
                VALUES (%s, %s, %s, %s, TRUE)
            """, (log_id, user_id, desc[:200], task.get("status", "done")))

    # Save 3 priority outcomes + deep work hours
    priorities = review_data.get("priorities", [])
    p_statuses = [p.get("status") for p in priorities]
    p1, p2, p3 = (p_statuses + [None, None, None])[:3]

    execute("""
        INSERT INTO weekly_friday_reviews
            (user_id, week_start_date,
             priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, weekly_execution_score, reflection_text)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, week_start_date) DO UPDATE SET
            priority_1_status      = EXCLUDED.priority_1_status,
            priority_2_status      = EXCLUDED.priority_2_status,
            priority_3_status      = EXCLUDED.priority_3_status,
            deep_work_hours        = EXCLUDED.deep_work_hours,
            weekly_execution_score = EXCLUDED.weekly_execution_score,
            reflection_text        = EXCLUDED.reflection_text
    """, (user_id, week_start_date, p1, p2, p3, deep_hours, exec_score, reflection))

    # Save next week's planning
    if planning_data:
        next_week = (date.fromisoformat(str(week_start_date)) + timedelta(days=7)).isoformat()
        next_pri = planning_data.get("priorities", [])
        execute("""
            INSERT INTO weekly_monday_inputs
                (user_id, week_start_date, priority_1, priority_2, priority_3,
                 estimated_deep_work_hours)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, week_start_date) DO UPDATE SET
                priority_1                = EXCLUDED.priority_1,
                priority_2                = EXCLUDED.priority_2,
                priority_3                = EXCLUDED.priority_3,
                estimated_deep_work_hours = EXCLUDED.estimated_deep_work_hours
        """, (
            user_id, next_week,
            next_pri[0] if len(next_pri) > 0 else None,
            next_pri[1] if len(next_pri) > 1 else None,
            next_pri[2] if len(next_pri) > 2 else None,
            planning_data.get("deep_work_hours"),
        ))


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@app.route("/api/reviews/generate", methods=["POST"])
@require_auth
def generate_review():
    d = request.json or {}
    week_start = d.get("week_start_date", current_week_start())
    profile = get_user_profile(g.user_id)
    profile_dict = dict(profile) if profile else {}

    metrics = calculate_all_metrics(g.user_id, week_start)
    patterns = detect_all_patterns(g.user_id, week_start, metrics)
    prompt = build_weekly_review_prompt(g.user_id, week_start, metrics, patterns, profile_dict)
    review = generate_weekly_review(prompt)

    try:
        execute("""
            INSERT INTO ai_reviews
                (user_id, week_start_date, diagnosis, evidence, intervention,
                 maturity_label, raw_response, patterns_detected)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            g.user_id, week_start,
            review.get("diagnosis"), review.get("evidence"),
            review.get("intervention"), review.get("maturity_label"),
            review.get("raw_response"), json.dumps([p["pattern_name"] for p in patterns]),
        ))
    except Exception:
        pass

    return jsonify({**review, "week_start_date": week_start, "patterns": patterns})


@app.route("/api/reviews", methods=["GET"])
@require_auth
def get_reviews():
    rows = query(
        "SELECT * FROM ai_reviews WHERE user_id=%s ORDER BY created_at DESC LIMIT 20",
        (g.user_id,)
    )
    return jsonify([{**dict(r), "id": str(r["id"])} for r in rows])


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
@require_auth
def get_dashboard():
    week_start = request.args.get("week_start_date", current_week_start())
    weeks = min(int(request.args.get("weeks", 8)), 26)
    metrics = calculate_all_metrics(g.user_id, week_start)
    history = get_multi_week_metrics(g.user_id, weeks=weeks, from_date=week_start)

    # Enrich history with deep_work_hours from weekly_friday_reviews.
    # week_start_date in history is already ISO string (normalised in get_multi_week_metrics).
    if history:
        wsd_list = [r['week_start_date'] for r in history if r.get('week_start_date')]
        friday_rows = query(
            "SELECT week_start_date, deep_work_hours FROM weekly_friday_reviews "
            "WHERE user_id=%s AND week_start_date = ANY(%s::date[])",
            (g.user_id, wsd_list)
        ) or []
        # Normalise friday_map keys to ISO strings
        friday_map = {str(r['week_start_date'])[:10]: float(r['deep_work_hours'])
                      for r in friday_rows if r.get('deep_work_hours') is not None}
        for row in history:
            row['deep_work_hours'] = friday_map.get(row.get('week_start_date', ''))

    # Fetch the review for the specific week being viewed, falling back to the most recent
    latest_review = query(
        "SELECT * FROM ai_reviews WHERE user_id=%s AND week_start_date=%s "
        "ORDER BY created_at DESC LIMIT 1",
        (g.user_id, week_start), one=True
    )
    if not latest_review:
        latest_review = query(
            "SELECT * FROM ai_reviews WHERE user_id=%s ORDER BY created_at DESC LIMIT 1",
            (g.user_id,), one=True
        )

    profile = get_user_profile(g.user_id)

    def _serial(row):
        """Convert a DB row dict to JSON-safe: dates → ISO strings, UUIDs → str."""
        out = {}
        for k, v in row.items():
            if hasattr(v, 'isoformat'):
                out[k] = v.isoformat()[:10] if hasattr(v, 'year') and not hasattr(v, 'hour') \
                          else v.isoformat()
            else:
                out[k] = str(v) if hasattr(v, 'hex') else v  # UUID → str
        return out

    return jsonify({
        "metrics": metrics,
        "metrics_history": history,
        "latest_review": _serial(dict(latest_review)) if latest_review else None,
        "profile": dict(profile) if profile else None,
        "week_start_date": week_start,
    })


# ---------------------------------------------------------------------------
# PDF Report
# ---------------------------------------------------------------------------

@app.route("/api/report/generate", methods=["POST"])
@require_auth
def generate_report():
    d = request.json or {}
    week_start = d.get("week_start_date", current_week_start())
    profile = dict(get_user_profile(g.user_id) or {})
    metrics = calculate_all_metrics(g.user_id, week_start)
    patterns = detect_all_patterns(g.user_id, week_start, metrics)

    review = query(
        "SELECT * FROM ai_reviews WHERE user_id=%s AND week_start_date=%s "
        "ORDER BY created_at DESC LIMIT 1",
        (g.user_id, week_start), one=True
    )
    friday = query(
        "SELECT * FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (g.user_id, week_start), one=True
    )
    monday = query(
        "SELECT * FROM weekly_monday_inputs WHERE user_id=%s AND week_start_date=%s",
        (g.user_id, week_start), one=True
    )

    pdf_buffer = generate_pdf(
        profile, metrics, patterns,
        dict(review) if review else None,
        dict(friday) if friday else None,
        dict(monday) if monday else None,
        week_start,
    )

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"cadence-report-{week_start}.pdf",
    )


# ---------------------------------------------------------------------------
# Executive Coach Report
# ---------------------------------------------------------------------------

@app.route("/api/report/coach", methods=["POST"])
@require_auth
def coach_report():
    d = request.json or {}
    week_start = d.get("week_start_date", current_week_start())
    profile = dict(get_user_profile(g.user_id) or {})
    metrics = calculate_all_metrics(g.user_id, week_start)

    friday = query(
        "SELECT * FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (g.user_id, week_start), one=True
    )
    monday = query(
        "SELECT * FROM weekly_monday_inputs WHERE user_id=%s AND week_start_date=%s",
        (g.user_id, week_start), one=True
    )
    tasks = query(
        "SELECT t.description, t.status FROM tasks t "
        "JOIN daily_logs dl ON t.daily_log_id=dl.id "
        "WHERE t.user_id=%s AND dl.date=%s",
        (g.user_id, week_start)
    ) or []

    priorities = []
    if friday:
        for i in range(1, 4):
            status = friday.get(f"priority_{i}_status")
            desc = monday.get(f"priority_{i}") if monday else None
            if status:
                priorities.append({"description": desc or f"Priority {i}", "status": status})

    fpi = metrics.get("friction_pattern_index") or {}
    rag_query = (
        f"{fpi.get('tag', '')} {profile.get('role_type', 'executive')} "
        "execution deep work priorities intervention"
    ).strip()
    chunks = retrieve_relevant_chunks(rag_query, top_k=6)
    kb_context = format_rag_context(chunks)

    report_text = generate_coach_report(
        profile, metrics, priorities, tasks,
        dict(friday) if friday else {},
        kb_context, week_start
    )

    return jsonify({
        "report": report_text,
        "week_start_date": week_start,
        "metrics": metrics,
        "priorities": priorities,
    })


# ---------------------------------------------------------------------------
# Knowledge base ingestion
# ---------------------------------------------------------------------------

@app.route("/api/admin/seed-demo", methods=["POST"])
def seed_demo():
    result = seed_all_users()
    return jsonify(result)


@app.route("/api/admin/ingest", methods=["POST"])
@require_auth
def ingest():
    if not request.json or "content" not in request.json:
        return jsonify({"error": "No content provided"}), 400
    count = ingest_knowledge_base(request.json["content"])
    return jsonify({"status": "ok", "chunks_ingested": count})


@app.route("/api/admin/ingest-from-file", methods=["POST"])
@require_auth
def ingest_from_file():
    kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "books.md"))
    if not os.path.exists(kb_path):
        return jsonify({"error": f"Knowledge base file not found: {kb_path}"}), 404
    with open(kb_path, "r") as f:
        content = f.read()
    count = ingest_knowledge_base(content)
    return jsonify({"status": "ok", "chunks_ingested": count})


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

@app.route("/api/tts", methods=["POST"])
@require_auth
def tts():
    d = request.json
    text = d.get("text", "")
    profile = get_user_profile(g.user_id)
    voice = dict(profile).get("voice_preference", "female") if profile else "female"
    audio, error = synthesize(text, voice)
    if error and not audio:
        return jsonify({"error": error}), 500
    return jsonify({"audio": audio})


def _auto_ingest_kb():
    try:
        if has_knowledge_base():
            return
        kb_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "books.md"))
        if not os.path.exists(kb_path):
            return
        with open(kb_path, "r") as f:
            content = f.read()
        count = ingest_knowledge_base(content)
        print(f"[startup] Auto-ingested {count} knowledge base chunks.")
    except Exception as e:
        print(f"[startup] KB ingest skipped: {e}")


_auto_ingest_kb()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)
