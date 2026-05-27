from datetime import date, timedelta
from database import query, execute


ACTION_DOT_THRESHOLDS = {
    "priority_completion_rate": {"green": 0.80, "amber": 0.60},
    "deep_work_frequency":      {"green": 2.0,  "amber": 1.0},
    "deferral_rate":            {"green": 0.20, "amber": 0.35, "inverted": True},
    "planning_accuracy":        {"green": 0.70, "amber": 0.50},
    "reactive_work_ratio":      {"green": 0.25, "amber": 0.40, "inverted": True},
}


def get_dot(metric, value):
    if value is None:
        return None
    t = ACTION_DOT_THRESHOLDS.get(metric)
    if not t:
        return "green"
    inverted = t.get("inverted", False)
    if not inverted:
        if value >= t["green"]:
            return "green"
        if value >= t["amber"]:
            return "amber"
        return "red"
    else:
        if value <= t["green"]:
            return "green"
        if value <= t["amber"]:
            return "amber"
        return "red"


def week_dates(week_start_date):
    start = date.fromisoformat(str(week_start_date))
    return [(start + timedelta(days=i)).isoformat() for i in range(7)]


def calculate_priority_completion_rate(user_id, week_start_date):
    row = query(
        "SELECT priority_1_status, priority_2_status, priority_3_status "
        "FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not row:
        return None
    statuses = [row[k] for k in
                ["priority_1_status", "priority_2_status", "priority_3_status"] if row[k]]
    if not statuses:
        return None
    return round(sum(1 for s in statuses if s == "done") / len(statuses), 3)


def calculate_deep_work_frequency(user_id, week_start_date):
    row = query(
        "SELECT deep_work_hours FROM weekly_friday_reviews "
        "WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not row or row["deep_work_hours"] is None:
        return None
    return float(row["deep_work_hours"])


def calculate_friction_pattern_index(user_id, week_start_date):
    dates = week_dates(week_start_date)
    rows = query(
        "SELECT friction_tag FROM daily_logs WHERE user_id=%s AND date = ANY(%s::date[]) "
        "AND friction_tag IS NOT NULL",
        (user_id, dates)
    )
    if not rows:
        return None
    from collections import Counter
    counts = Counter(r["friction_tag"] for r in rows)
    if not counts:
        return None
    top_tag, top_count = counts.most_common(1)[0]
    return {"tag": top_tag, "frequency_pct": round(top_count / len(rows) * 100, 1), "count": top_count}


def calculate_execution_score_trend(user_id, week_start_date):
    dates = week_dates(week_start_date)
    rows = query(
        "SELECT execution_score FROM daily_logs WHERE user_id=%s AND date = ANY(%s::date[])",
        (user_id, dates)
    )
    if not rows:
        return None
    current_avg = sum(r["execution_score"] for r in rows) / len(rows)

    prev_start = (date.fromisoformat(str(week_start_date)) - timedelta(days=7)).isoformat()
    prev_dates = week_dates(prev_start)
    prev_rows = query(
        "SELECT execution_score FROM daily_logs WHERE user_id=%s AND date = ANY(%s::date[])",
        (user_id, prev_dates)
    )
    if not prev_rows:
        return {"current_avg": round(current_avg, 2), "trend": "insufficient_history", "delta": None}

    prev_avg = sum(r["execution_score"] for r in prev_rows) / len(prev_rows)
    delta = current_avg - prev_avg
    trend = "improving" if delta > 0.5 else "declining" if delta < -0.5 else "stable"
    return {"current_avg": round(current_avg, 2), "previous_avg": round(prev_avg, 2),
            "delta": round(delta, 2), "trend": trend}


def calculate_deferral_rate(user_id, week_start_date):
    dates = week_dates(week_start_date)
    task_rows = query(
        "SELECT t.status FROM tasks t JOIN daily_logs dl ON t.daily_log_id=dl.id "
        "WHERE t.user_id=%s AND dl.date = ANY(%s::date[])",
        (user_id, dates)
    ) or []

    priority_row = query(
        "SELECT priority_1_status, priority_2_status, priority_3_status "
        "FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )

    total    = len(task_rows)
    deferred = sum(1 for r in task_rows if r["status"] == "deferred")

    if priority_row:
        p_statuses = [priority_row.get(f"priority_{i}_status") for i in range(1, 4)]
        p_statuses = [s for s in p_statuses if s]
        total    += len(p_statuses)
        deferred += sum(1 for s in p_statuses if s == "deferred")

    return round(deferred / total, 3) if total > 0 else None


def calculate_planning_accuracy(user_id, week_start_date):
    dates = week_dates(week_start_date)
    rows = query(
        "SELECT t.status FROM tasks t JOIN daily_logs dl ON t.daily_log_id=dl.id "
        "WHERE t.user_id=%s AND dl.date = ANY(%s::date[]) AND t.is_planned=TRUE",
        (user_id, dates)
    )
    if not rows:
        return None
    return round(sum(1 for r in rows if r["status"] == "done") / len(rows), 3)


def calculate_reactive_work_ratio(user_id, week_start_date):
    row = query(
        "SELECT reactive_work_hours, deep_work_hours, admin_hours, meetings_hours, "
        "learning_hours, low_leverage_hours FROM weekly_friday_reviews "
        "WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    if not row:
        return None
    reactive = row["reactive_work_hours"] or 0
    total = sum(row[k] or 0 for k in ["reactive_work_hours", "deep_work_hours",
                "admin_hours", "meetings_hours", "learning_hours", "low_leverage_hours"])
    return round(reactive / total, 3) if total > 0 else None


def get_sparkline_data(user_id, metric, weeks=8):
    rows = query(
        f"SELECT week_start_date, {metric} FROM weekly_metrics "
        "WHERE user_id=%s AND {metric} IS NOT NULL "
        "ORDER BY week_start_date DESC LIMIT %s",
        (user_id, weeks)
    )
    return [{"week": str(r["week_start_date"]), "value": r[metric]}
            for r in reversed(rows)] if rows else []


def calculate_all_metrics(user_id, week_start_date):
    pcr  = calculate_priority_completion_rate(user_id, week_start_date)
    dwf  = calculate_deep_work_frequency(user_id, week_start_date)
    fpi  = calculate_friction_pattern_index(user_id, week_start_date)
    est  = calculate_execution_score_trend(user_id, week_start_date)
    dr   = calculate_deferral_rate(user_id, week_start_date)
    pa   = calculate_planning_accuracy(user_id, week_start_date)
    rwr  = calculate_reactive_work_ratio(user_id, week_start_date)

    metrics = {
        "week_start_date": str(week_start_date),
        "priority_completion_rate": pcr,
        "deep_work_frequency": dwf,
        "friction_pattern_index": fpi,
        "execution_score_trend": est,
        "deferral_rate": dr,
        "planning_accuracy": pa,
        "reactive_work_ratio": rwr,
        "avg_execution_score": est["current_avg"] if est else None,
        "action_dots": {
            "priority_completion_rate": get_dot("priority_completion_rate", pcr),
            "deep_work_frequency":      get_dot("deep_work_frequency", dwf),
            "deferral_rate":            get_dot("deferral_rate", dr),
            "planning_accuracy":        get_dot("planning_accuracy", pa),
            "reactive_work_ratio":      get_dot("reactive_work_ratio", rwr),
        }
    }

    try:
        execute("""
            INSERT INTO weekly_metrics
                (user_id, week_start_date, priority_completion_rate, deep_work_frequency,
                 friction_pattern_index, execution_score_trend, deferral_rate,
                 planning_accuracy, avg_execution_score)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id, week_start_date) DO UPDATE SET
                priority_completion_rate=EXCLUDED.priority_completion_rate,
                deep_work_frequency=EXCLUDED.deep_work_frequency,
                friction_pattern_index=EXCLUDED.friction_pattern_index,
                execution_score_trend=EXCLUDED.execution_score_trend,
                deferral_rate=EXCLUDED.deferral_rate,
                planning_accuracy=EXCLUDED.planning_accuracy,
                avg_execution_score=EXCLUDED.avg_execution_score,
                calculated_at=NOW()
        """, (
            user_id, week_start_date, pcr, dwf,
            psycopg2_json(fpi), psycopg2_json(est),
            dr, pa, metrics["avg_execution_score"]
        ))
    except Exception:
        pass

    return metrics


def get_multi_week_metrics(user_id, weeks=8, from_date=None):
    if from_date:
        rows = query(
            "SELECT * FROM weekly_metrics WHERE user_id=%s AND week_start_date <= %s "
            "ORDER BY week_start_date DESC LIMIT %s",
            (user_id, from_date, weeks)
        )
    else:
        rows = query(
            "SELECT * FROM weekly_metrics WHERE user_id=%s "
            "ORDER BY week_start_date DESC LIMIT %s",
            (user_id, weeks)
        )
    return [dict(r) for r in rows] if rows else []


def psycopg2_json(val):
    import json
    return json.dumps(val) if val is not None else None
