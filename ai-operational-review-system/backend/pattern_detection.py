from database import get_db
from metrics import get_week_dates


MIN_DATA_POINTS = 3


def _label(confidence, data_points):
    if data_points < MIN_DATA_POINTS:
        return "early signal, not confirmed pattern"
    if confidence >= 0.7:
        return "confirmed pattern"
    if confidence >= 0.4:
        return "emerging pattern"
    return "early signal, not confirmed pattern"


def detect_planning_inflation(week_start_date, metrics):
    """Many tasks planned but completion rate is low."""
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"""SELECT t.status FROM tasks t
            JOIN daily_logs dl ON t.daily_log_id = dl.id
            WHERE dl.date IN ({placeholders}) AND t.is_planned = 1""",
        dates
    ).fetchall()
    conn.close()

    data_points = len(rows)
    if data_points == 0:
        return None

    pa = metrics.get("planning_accuracy")
    if pa is None:
        return None

    # High inflation: many planned tasks + low completion
    completed = sum(1 for r in rows if r["status"] == "done")
    not_done = data_points - completed

    if data_points >= 5 and pa < 0.5:
        confidence = round(1 - pa, 2)
        return {
            "pattern_name": "Planning Inflation",
            "confidence_score": confidence,
            "maturity": _label(confidence, data_points),
            "evidence": f"{data_points} tasks planned, {completed} completed ({round(pa*100)}% completion rate). {not_done} tasks did not reach done status.",
            "explanation": "You consistently plan more tasks than you execute. This inflates your planning surface and dilutes focus from the highest-leverage work."
        }
    return None


def detect_false_priority(week_start_date, metrics):
    """Stated top priority is repeatedly incomplete, deferred, or absent from time."""
    conn = get_db()
    friday = conn.execute(
        "SELECT priority_1_status, priority_2_status, priority_3_status, deep_work_hours FROM weekly_friday_reviews WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    monday = conn.execute(
        "SELECT priority_1, priority_2, priority_3 FROM weekly_monday_inputs WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    conn.close()

    if not friday or not monday:
        return None

    statuses = [friday["priority_1_status"], friday["priority_2_status"], friday["priority_3_status"]]
    statuses = [s for s in statuses if s]
    if not statuses:
        return None

    incomplete = sum(1 for s in statuses if s in ("partial", "deferred", "dropped"))
    data_points = len(statuses)

    pcr = metrics.get("priority_completion_rate") or 0
    deep_work = friday["deep_work_hours"] or 0

    if incomplete >= 2 and (pcr < 0.4 or deep_work < 3):
        confidence = round(incomplete / data_points * (1 - pcr / 2), 2)
        confidence = min(confidence, 1.0)
        return {
            "pattern_name": "False Priority",
            "confidence_score": confidence,
            "maturity": _label(confidence, data_points),
            "evidence": f"{incomplete} of {data_points} stated priorities were not completed. Priority completion rate: {round(pcr*100)}%. Deep work logged: {deep_work}h.",
            "explanation": "Your declared priorities are not reflected in how you actually spend your time or what gets completed. The stated and operative priority lists are diverging."
        }
    return None


def detect_reactive_capture(week_start_date, metrics):
    """Reactive work hours dominate; deep work and priority completion are low."""
    conn = get_db()
    friday = conn.execute(
        "SELECT reactive_work_hours, deep_work_hours FROM weekly_friday_reviews WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    conn.close()

    if not friday:
        return None

    reactive = friday["reactive_work_hours"] or 0
    deep = friday["deep_work_hours"] or 0
    pcr = metrics.get("priority_completion_rate") or 0

    if reactive > deep and reactive > 8 and pcr < 0.5:
        confidence = round(min((reactive / (deep + 1)) * 0.3, 1.0), 2)
        return {
            "pattern_name": "Reactive Capture",
            "confidence_score": confidence,
            "maturity": _label(confidence, 3),  # week-level data
            "evidence": f"Reactive work: {reactive}h vs deep work: {deep}h. Priority completion: {round(pcr*100)}%.",
            "explanation": "Your schedule is being captured by reactive demands. Incoming requests and interruptions are consuming the capacity that should be directed at your top priorities."
        }
    return None


def detect_decision_deferral(week_start_date, metrics):
    """Same or similar task names deferred repeatedly."""
    conn = get_db()
    rows = conn.execute(
        """SELECT t.description, t.status FROM tasks t
           JOIN daily_logs dl ON t.daily_log_id = dl.id
           WHERE t.status = 'deferred'
           ORDER BY dl.date DESC LIMIT 50"""
    ).fetchall()
    conn.close()

    if len(rows) < MIN_DATA_POINTS:
        return None

    from collections import Counter
    # Simple: look for repeated keywords in deferred task descriptions
    words = []
    for r in rows:
        words.extend(r["description"].lower().split())
    stopwords = {"a", "an", "the", "to", "for", "of", "and", "or", "in", "on", "with", "up"}
    words = [w for w in words if len(w) > 3 and w not in stopwords]

    if not words:
        return None

    counts = Counter(words)
    top = counts.most_common(3)
    repeated = [(w, c) for w, c in top if c >= 2]

    dr = metrics.get("deferral_rate") or 0

    if repeated and dr > 0.3:
        evidence_words = ", ".join(f'"{w}" (x{c})' for w, c in repeated)
        confidence = round(min(dr * 1.5, 1.0), 2)
        return {
            "pattern_name": "Decision Deferral",
            "confidence_score": confidence,
            "maturity": _label(confidence, len(rows)),
            "evidence": f"Deferral rate: {round(dr*100)}%. Repeated keywords in deferred tasks: {evidence_words}.",
            "explanation": "Specific recurring tasks are being deferred rather than completed or consciously dropped. This suggests avoidance of a decision or action rather than genuine re-prioritisation."
        }
    return None


def detect_leverage_leakage(week_start_date, metrics):
    """Low-leverage/admin work is high; deep work is low."""
    conn = get_db()
    friday = conn.execute(
        "SELECT low_leverage_hours, admin_hours, deep_work_hours FROM weekly_friday_reviews WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    conn.close()

    if not friday:
        return None

    low_leverage = (friday["low_leverage_hours"] or 0) + (friday["admin_hours"] or 0)
    deep = friday["deep_work_hours"] or 0

    if low_leverage > deep and low_leverage > 8:
        confidence = round(min(low_leverage / (deep + 1) * 0.25, 1.0), 2)
        return {
            "pattern_name": "Leverage Leakage",
            "confidence_score": confidence,
            "maturity": _label(confidence, 3),
            "evidence": f"Low-leverage + admin hours: {low_leverage}h. Deep work hours: {deep}h.",
            "explanation": "A disproportionate share of your work week is being consumed by low-leverage tasks. This crowds out the strategic and creative work that drives outsized outcomes."
        }
    return None


def detect_depth_deprivation(week_start_date, metrics):
    """Deep work blocks are consistently low."""
    dwf = metrics.get("deep_work_frequency")
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"SELECT deep_work_blocks FROM daily_logs WHERE date IN ({placeholders})",
        dates
    ).fetchall()
    conn.close()

    data_points = len(rows)
    if data_points < MIN_DATA_POINTS or dwf is None:
        return None

    if dwf < 1.0:
        confidence = round(1 - dwf, 2)
        confidence = min(confidence, 1.0)
        return {
            "pattern_name": "Depth Deprivation",
            "confidence_score": confidence,
            "maturity": _label(confidence, data_points),
            "evidence": f"Average deep work blocks per day: {dwf} across {data_points} logged days.",
            "explanation": "Your schedule is not protecting time for focused, uninterrupted work. Without consistent deep work blocks, high-complexity tasks cannot be executed to a high standard."
        }
    return None


def detect_all_patterns(week_start_date, metrics):
    detectors = [
        detect_planning_inflation,
        detect_false_priority,
        detect_reactive_capture,
        detect_decision_deferral,
        detect_leverage_leakage,
        detect_depth_deprivation,
    ]
    patterns = []
    for fn in detectors:
        result = fn(week_start_date, metrics)
        if result:
            patterns.append(result)

    # Sort by confidence descending
    patterns.sort(key=lambda p: p["confidence_score"], reverse=True)
    return patterns
