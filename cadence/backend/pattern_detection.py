from database import query
from metrics import week_dates

MIN_POINTS = 3


def _maturity(conf, n):
    if n < MIN_POINTS:
        return "early signal, not confirmed pattern"
    if conf >= 0.70:
        return "confirmed pattern"
    if conf >= 0.40:
        return "emerging pattern"
    return "early signal, not confirmed pattern"


def detect_planning_inflation(user_id, week_start_date, metrics):
    dates = week_dates(week_start_date)
    rows = query(
        "SELECT t.status FROM tasks t JOIN daily_logs dl ON t.daily_log_id=dl.id "
        "WHERE t.user_id=%s AND dl.date=ANY(%s) AND t.is_planned=TRUE",
        (user_id, dates)
    )
    n = len(rows)
    pa = metrics.get("planning_accuracy")
    if n < 5 or pa is None or pa >= 0.5:
        return None
    done = sum(1 for r in rows if r["status"] == "done")
    conf = round(1 - pa, 2)
    return {
        "pattern_name": "Planning Inflation",
        "confidence_score": conf,
        "maturity": _maturity(conf, n),
        "evidence": f"{n} tasks planned, {done} completed ({round(pa*100)}%). {n-done} tasks did not reach done status.",
        "explanation": "Task volume consistently exceeds execution capacity. Planning surface is inflated beyond what the week can absorb.",
    }


def detect_false_priority(user_id, week_start_date, metrics):
    friday = query(
        "SELECT priority_1_status,priority_2_status,priority_3_status,deep_work_hours "
        "FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not friday:
        return None
    statuses = [friday[f"priority_{i}_status"] for i in range(1, 4) if friday.get(f"priority_{i}_status")]
    if not statuses:
        return None
    incomplete = sum(1 for s in statuses if s in ("partial", "deferred", "dropped"))
    pcr = metrics.get("priority_completion_rate") or 0
    dw = friday.get("deep_work_hours") or 0
    if incomplete < 2 or (pcr >= 0.4 and dw >= 3):
        return None
    conf = round(min(incomplete / len(statuses) * (1 - pcr / 2), 1.0), 2)
    return {
        "pattern_name": "False Priority",
        "confidence_score": conf,
        "maturity": _maturity(conf, len(statuses)),
        "evidence": f"{incomplete}/{len(statuses)} stated priorities incomplete. PCR: {round(pcr*100)}%. Deep work: {dw}h.",
        "explanation": "Declared priorities are not reflected in actual time allocation or completion outcomes. Operative and stated priorities have diverged.",
    }


def detect_reactive_capture(user_id, week_start_date, metrics):
    friday = query(
        "SELECT reactive_work_hours, deep_work_hours FROM weekly_friday_reviews "
        "WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not friday:
        return None
    reactive = friday.get("reactive_work_hours") or 0
    deep = friday.get("deep_work_hours") or 0
    pcr = metrics.get("priority_completion_rate") or 0
    if not (reactive > deep and reactive > 8 and pcr < 0.5):
        return None
    conf = round(min(reactive / (deep + 1) * 0.3, 1.0), 2)
    return {
        "pattern_name": "Reactive Capture",
        "confidence_score": conf,
        "maturity": _maturity(conf, 3),
        "evidence": f"Reactive: {reactive}h vs deep work: {deep}h. PCR: {round(pcr*100)}%.",
        "explanation": "Schedule is being captured by reactive demands. Incoming requests consume the capacity reserved for priority execution.",
    }


def detect_decision_deferral(user_id, week_start_date, metrics):
    rows = query(
        "SELECT t.description FROM tasks t JOIN daily_logs dl ON t.daily_log_id=dl.id "
        "WHERE t.user_id=%s AND t.status='deferred' ORDER BY dl.date DESC LIMIT 60",
        (user_id,)
    )
    if len(rows) < MIN_POINTS:
        return None
    from collections import Counter
    stopwords = {"a","an","the","to","for","of","and","or","in","on","with","up","is","it"}
    words = [w for r in rows for w in r["description"].lower().split()
             if len(w) > 3 and w not in stopwords]
    if not words:
        return None
    counts = Counter(words)
    repeated = [(w, c) for w, c in counts.most_common(3) if c >= 2]
    dr = metrics.get("deferral_rate") or 0
    if not repeated or dr <= 0.3:
        return None
    evidence_words = ", ".join(f'"{w}" (×{c})' for w, c in repeated)
    conf = round(min(dr * 1.5, 1.0), 2)
    return {
        "pattern_name": "Decision Deferral",
        "confidence_score": conf,
        "maturity": _maturity(conf, len(rows)),
        "evidence": f"Deferral rate: {round(dr*100)}%. Recurring deferred keywords: {evidence_words}.",
        "explanation": "Specific tasks are being repeatedly deferred rather than completed or consciously dropped. Likely avoidance of a decision rather than genuine reprioritisation.",
    }


def detect_leverage_leakage(user_id, week_start_date, metrics):
    friday = query(
        "SELECT low_leverage_hours, admin_hours, deep_work_hours FROM weekly_friday_reviews "
        "WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not friday:
        return None
    low_lev = (friday.get("low_leverage_hours") or 0) + (friday.get("admin_hours") or 0)
    deep = friday.get("deep_work_hours") or 0
    if not (low_lev > deep and low_lev > 8):
        return None
    conf = round(min(low_lev / (deep + 1) * 0.25, 1.0), 2)
    return {
        "pattern_name": "Leverage Leakage",
        "confidence_score": conf,
        "maturity": _maturity(conf, 3),
        "evidence": f"Low-leverage + admin: {low_lev}h. Deep work: {deep}h.",
        "explanation": "Disproportionate time consumed by low-leverage tasks, crowding out strategic and creative work.",
    }


def detect_depth_deprivation(user_id, week_start_date, metrics):
    dwf = metrics.get("deep_work_frequency")
    dates = week_dates(week_start_date)
    rows = query(
        "SELECT deep_work_blocks FROM daily_logs WHERE user_id=%s AND date=ANY(%s)",
        (user_id, dates)
    )
    n = len(rows)
    if n < MIN_POINTS or dwf is None or dwf >= 1.0:
        return None
    conf = round(min(1 - dwf, 1.0), 2)
    return {
        "pattern_name": "Depth Deprivation",
        "confidence_score": conf,
        "maturity": _maturity(conf, n),
        "evidence": f"Average deep work blocks: {dwf}/day across {n} logged days.",
        "explanation": "Schedule is not protecting time for focused, uninterrupted work. Complex strategic tasks cannot be executed to standard without consistent depth.",
    }


def detect_all_patterns(user_id, week_start_date, metrics):
    fns = [
        detect_planning_inflation,
        detect_false_priority,
        detect_reactive_capture,
        detect_decision_deferral,
        detect_leverage_leakage,
        detect_depth_deprivation,
    ]
    patterns = [p for f in fns if (p := f(user_id, week_start_date, metrics)) is not None]
    return sorted(patterns, key=lambda x: x["confidence_score"], reverse=True)
