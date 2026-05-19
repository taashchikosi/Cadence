from database import get_db


def get_week_dates(week_start_date):
    """Return all 7 dates for a week starting on week_start_date (YYYY-MM-DD)."""
    from datetime import date, timedelta
    start = date.fromisoformat(week_start_date)
    return [(start + timedelta(days=i)).isoformat() for i in range(7)]


def calculate_priority_completion_rate(week_start_date):
    """Completed weekly priorities / total weekly priorities."""
    conn = get_db()
    row = conn.execute(
        "SELECT priority_1_status, priority_2_status, priority_3_status "
        "FROM weekly_friday_reviews WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    statuses = [row["priority_1_status"], row["priority_2_status"], row["priority_3_status"]]
    statuses = [s for s in statuses if s]
    if not statuses:
        return None

    completed = sum(1 for s in statuses if s == "done")
    return round(completed / len(statuses), 2)


def calculate_deep_work_frequency(week_start_date):
    """Average daily deep work blocks across the week."""
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"SELECT deep_work_blocks FROM daily_logs WHERE date IN ({placeholders})",
        dates
    ).fetchall()
    conn.close()

    if not rows:
        return None

    def blocks_to_num(val):
        if val == "3+":
            return 3
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    total = sum(blocks_to_num(r["deep_work_blocks"]) for r in rows)
    return round(total / len(rows), 2)


def calculate_friction_pattern_index(week_start_date):
    """Most common friction tag and its frequency percentage."""
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"SELECT friction_tag FROM daily_logs WHERE date IN ({placeholders}) AND friction_tag IS NOT NULL",
        dates
    ).fetchall()
    conn.close()

    if not rows:
        return None

    from collections import Counter
    counts = Counter(r["friction_tag"] for r in rows if r["friction_tag"])
    if not counts:
        return None

    top_tag, top_count = counts.most_common(1)[0]
    pct = round(top_count / len(rows) * 100, 1)
    return {"tag": top_tag, "frequency_pct": pct, "count": top_count}


def calculate_execution_score_trend(week_start_date):
    """Compare current week avg execution score against previous week."""
    from datetime import date, timedelta
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"SELECT execution_score FROM daily_logs WHERE date IN ({placeholders})",
        dates
    ).fetchall()

    prev_start = (date.fromisoformat(week_start_date) - timedelta(days=7)).isoformat()
    prev_dates = get_week_dates(prev_start)
    prev_placeholders = ",".join("?" * len(prev_dates))
    prev_rows = conn.execute(
        f"SELECT execution_score FROM daily_logs WHERE date IN ({prev_placeholders})",
        prev_dates
    ).fetchall()
    conn.close()

    if not rows:
        return None

    current_avg = sum(r["execution_score"] for r in rows) / len(rows)

    if not prev_rows:
        return {"current_avg": round(current_avg, 2), "trend": "insufficient_history"}

    prev_avg = sum(r["execution_score"] for r in prev_rows) / len(prev_rows)
    delta = current_avg - prev_avg

    if delta > 0.5:
        trend = "improving"
    elif delta < -0.5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "current_avg": round(current_avg, 2),
        "previous_avg": round(prev_avg, 2),
        "delta": round(delta, 2),
        "trend": trend
    }


def calculate_deferral_rate(week_start_date):
    """Deferred tasks / total tracked tasks for the week."""
    conn = get_db()
    dates = get_week_dates(week_start_date)
    placeholders = ",".join("?" * len(dates))
    rows = conn.execute(
        f"""SELECT t.status FROM tasks t
            JOIN daily_logs dl ON t.daily_log_id = dl.id
            WHERE dl.date IN ({placeholders})""",
        dates
    ).fetchall()
    conn.close()

    if not rows:
        return None

    total = len(rows)
    deferred = sum(1 for r in rows if r["status"] == "deferred")
    return round(deferred / total, 2)


def calculate_planning_accuracy(week_start_date):
    """Completed planned tasks / total planned tasks for the week."""
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

    if not rows:
        return None

    total = len(rows)
    completed = sum(1 for r in rows if r["status"] == "done")
    return round(completed / total, 2)


def calculate_all_metrics(week_start_date):
    pcr = calculate_priority_completion_rate(week_start_date)
    dwf = calculate_deep_work_frequency(week_start_date)
    fpi = calculate_friction_pattern_index(week_start_date)
    est = calculate_execution_score_trend(week_start_date)
    dr = calculate_deferral_rate(week_start_date)
    pa = calculate_planning_accuracy(week_start_date)

    avg_exec = est["current_avg"] if est else None

    conn = get_db()
    conn.execute("""
        INSERT INTO weekly_metrics
            (week_start_date, priority_completion_rate, deep_work_frequency,
             friction_pattern_index, execution_score_trend, deferral_rate,
             planning_accuracy, avg_execution_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(week_start_date) DO UPDATE SET
            priority_completion_rate=excluded.priority_completion_rate,
            deep_work_frequency=excluded.deep_work_frequency,
            friction_pattern_index=excluded.friction_pattern_index,
            execution_score_trend=excluded.execution_score_trend,
            deferral_rate=excluded.deferral_rate,
            planning_accuracy=excluded.planning_accuracy,
            avg_execution_score=excluded.avg_execution_score,
            calculated_at=datetime('now')
    """, (
        week_start_date,
        pcr,
        dwf,
        str(fpi) if fpi else None,
        str(est) if est else None,
        dr,
        pa,
        avg_exec
    ))
    conn.commit()
    conn.close()

    return {
        "week_start_date": week_start_date,
        "priority_completion_rate": pcr,
        "deep_work_frequency": dwf,
        "friction_pattern_index": fpi,
        "execution_score_trend": est,
        "deferral_rate": dr,
        "planning_accuracy": pa,
    }
