import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

from database import init_db, get_db
from metrics import calculate_all_metrics
from pattern_detection import detect_all_patterns
from prompt_builder import build_review_prompt
from llm_service import generate_review

app = Flask(__name__)
CORS(app)

init_db()


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

@app.route("/api/onboarding", methods=["POST"])
def create_onboarding():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO onboarding_profile
            (role_type, self_identified_failure_pattern, typical_week_structure, top_3_active_goals)
        VALUES (?, ?, ?, ?)
    """, (
        data.get("role_type"),
        data.get("self_identified_failure_pattern"),
        data.get("typical_week_structure"),
        data.get("top_3_active_goals"),
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/onboarding", methods=["GET"])
def get_onboarding():
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM onboarding_profile ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if not row:
        return jsonify(None)
    return jsonify(dict(row))


# ---------------------------------------------------------------------------
# Daily logs
# ---------------------------------------------------------------------------

@app.route("/api/daily-log", methods=["POST"])
def create_daily_log():
    data = request.json
    conn = get_db()
    cursor = conn.execute("""
        INSERT INTO daily_logs (date, execution_score, friction_tag, deep_work_blocks, free_text)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("date"),
        data.get("execution_score"),
        data.get("friction_tag"),
        data.get("deep_work_blocks", "0"),
        data.get("free_text"),
    ))
    log_id = cursor.lastrowid

    tasks = data.get("tasks", [])
    for task in tasks:
        conn.execute("""
            INSERT INTO tasks (daily_log_id, description, status, is_planned)
            VALUES (?, ?, ?, ?)
        """, (log_id, task.get("description"), task.get("status", "planned"), 1))

    conn.commit()
    conn.close()
    return jsonify({"status": "ok", "id": log_id}), 201


@app.route("/api/daily-logs", methods=["GET"])
def get_daily_logs():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM daily_logs ORDER BY date DESC LIMIT 30"
    ).fetchall()
    result = []
    for row in rows:
        log = dict(row)
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE daily_log_id = ?", (log["id"],)
        ).fetchall()
        log["tasks"] = [dict(t) for t in tasks]
        result.append(log)
    conn.close()
    return jsonify(result)


# ---------------------------------------------------------------------------
# Weekly Monday Input
# ---------------------------------------------------------------------------

@app.route("/api/weekly/monday", methods=["POST"])
def create_monday_input():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO weekly_monday_inputs
            (week_start_date, priority_1, priority_2, priority_3,
             estimated_deep_work_hours, predicted_main_derailer)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data.get("week_start_date"),
        data.get("priority_1"),
        data.get("priority_2"),
        data.get("priority_3"),
        data.get("estimated_deep_work_hours"),
        data.get("predicted_main_derailer"),
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/weekly/monday", methods=["GET"])
def get_monday_inputs():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM weekly_monday_inputs ORDER BY week_start_date DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Weekly Friday Review
# ---------------------------------------------------------------------------

@app.route("/api/weekly/friday", methods=["POST"])
def create_friday_review():
    data = request.json
    conn = get_db()
    conn.execute("""
        INSERT INTO weekly_friday_reviews
            (week_start_date, priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, admin_hours, meetings_hours, reactive_work_hours,
             learning_hours, low_leverage_hours, weekly_execution_score, reflection_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("week_start_date"),
        data.get("priority_1_status"),
        data.get("priority_2_status"),
        data.get("priority_3_status"),
        data.get("deep_work_hours", 0),
        data.get("admin_hours", 0),
        data.get("meetings_hours", 0),
        data.get("reactive_work_hours", 0),
        data.get("learning_hours", 0),
        data.get("low_leverage_hours", 0),
        data.get("weekly_execution_score"),
        data.get("reflection_text"),
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201


@app.route("/api/weekly/friday", methods=["GET"])
def get_friday_reviews():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM weekly_friday_reviews ORDER BY week_start_date DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@app.route("/api/metrics/current-week", methods=["GET"])
def get_current_week_metrics():
    week_start = request.args.get("week_start_date")
    if not week_start:
        from datetime import date, timedelta
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()
    metrics = calculate_all_metrics(week_start)
    return jsonify(metrics)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    from datetime import date, timedelta
    today = date.today()
    week_start = (today - timedelta(days=today.weekday())).isoformat()

    metrics = calculate_all_metrics(week_start)

    conn = get_db()
    recent_logs = conn.execute(
        "SELECT * FROM daily_logs ORDER BY date DESC LIMIT 7"
    ).fetchall()
    logs_with_tasks = []
    for row in recent_logs:
        log = dict(row)
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE daily_log_id = ?", (log["id"],)
        ).fetchall()
        log["tasks"] = [dict(t) for t in tasks]
        logs_with_tasks.append(log)

    latest_review = conn.execute(
        "SELECT * FROM ai_reviews ORDER BY created_at DESC LIMIT 1"
    ).fetchone()

    onboarding = conn.execute(
        "SELECT * FROM onboarding_profile ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    return jsonify({
        "metrics": metrics,
        "recent_logs": logs_with_tasks,
        "latest_review": dict(latest_review) if latest_review else None,
        "onboarding": dict(onboarding) if onboarding else None,
        "week_start_date": week_start,
    })


# ---------------------------------------------------------------------------
# AI Review Generation
# ---------------------------------------------------------------------------

@app.route("/api/reviews/generate", methods=["POST"])
def generate_weekly_review():
    data = request.json or {}
    week_start = data.get("week_start_date")
    if not week_start:
        from datetime import date, timedelta
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()

    metrics = calculate_all_metrics(week_start)
    patterns = detect_all_patterns(week_start, metrics)

    conn = get_db()
    onboarding = conn.execute(
        "SELECT * FROM onboarding_profile ORDER BY id DESC LIMIT 1"
    ).fetchone()

    prev_review = conn.execute(
        "SELECT diagnosis, intervention FROM ai_reviews ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()

    prev_summary = None
    if prev_review:
        prev_summary = f"Prior diagnosis: {prev_review['diagnosis']}\nPrior intervention: {prev_review['intervention']}"

    prompt = build_review_prompt(
        week_start,
        metrics,
        patterns,
        dict(onboarding) if onboarding else {},
        prev_summary
    )

    review = generate_review(prompt)

    conn = get_db()
    conn.execute("""
        INSERT INTO ai_reviews
            (week_start_date, diagnosis, evidence, intervention, maturity_label, raw_response, patterns_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        week_start,
        review.get("diagnosis"),
        review.get("evidence"),
        review.get("intervention"),
        review.get("maturity_label"),
        review.get("raw_response"),
        json.dumps([p["pattern_name"] for p in patterns]),
    ))
    conn.commit()
    conn.close()

    return jsonify({**review, "week_start_date": week_start, "patterns": patterns})


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM ai_reviews ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
