import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Use a temp DB for tests
@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    db_file = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_file
    import database
    database.DB_PATH = db_file
    database.init_db()
    yield db_file
    if os.path.exists(db_file):
        os.unlink(db_file)


def _insert_log(date, score, friction, blocks, tasks):
    import database
    import metrics as m_mod
    # Reload module to pick up new DB_PATH
    import importlib
    importlib.reload(database)
    importlib.reload(m_mod)
    conn = database.get_db()
    cursor = conn.execute(
        "INSERT INTO daily_logs (date, execution_score, friction_tag, deep_work_blocks) VALUES (?, ?, ?, ?)",
        (date, score, friction, blocks)
    )
    log_id = cursor.lastrowid
    for desc, status in tasks:
        conn.execute(
            "INSERT INTO tasks (daily_log_id, description, status, is_planned) VALUES (?, ?, ?, 1)",
            (log_id, desc, status)
        )
    conn.commit()
    conn.close()
    return log_id


def _insert_friday(week_start, p1, p2, p3, deep, admin, meetings, reactive, learning, low_lev, score):
    import database
    conn = database.get_db()
    conn.execute("""
        INSERT INTO weekly_friday_reviews
            (week_start_date, priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, admin_hours, meetings_hours, reactive_work_hours,
             learning_hours, low_leverage_hours, weekly_execution_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (week_start, p1, p2, p3, deep, admin, meetings, reactive, learning, low_lev, score))
    conn.commit()
    conn.close()


WEEK = "2026-05-04"
DATES = ["2026-05-04", "2026-05-05", "2026-05-06", "2026-05-07", "2026-05-08"]


class TestPriorityCompletionRate:
    def test_all_done(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        _insert_friday(WEEK, "done", "done", "done", 10, 2, 5, 3, 1, 1, 8)
        assert metrics.calculate_priority_completion_rate(WEEK) == 1.0

    def test_partial(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        _insert_friday(WEEK, "done", "partial", "dropped", 5, 3, 8, 5, 1, 2, 5)
        rate = metrics.calculate_priority_completion_rate(WEEK)
        assert rate == pytest.approx(1/3, abs=0.01)

    def test_no_data(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        assert metrics.calculate_priority_completion_rate(WEEK) is None


class TestDeepWorkFrequency:
    def test_average(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        for i, date in enumerate(DATES):
            blocks = ["0", "1", "2", "3+", "1"][i]
            _insert_log(date, 6, "distraction", blocks, [])
        freq = metrics.calculate_deep_work_frequency(WEEK)
        # (0 + 1 + 2 + 3 + 1) / 5 = 1.4
        assert freq == pytest.approx(1.4, abs=0.01)

    def test_no_data(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        assert metrics.calculate_deep_work_frequency(WEEK) is None


class TestFrictionPatternIndex:
    def test_most_common(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        for date, friction in zip(DATES, ["overplanning", "overplanning", "distraction", "overplanning", "low_energy"]):
            _insert_log(date, 6, friction, "1", [])
        result = metrics.calculate_friction_pattern_index(WEEK)
        assert result is not None
        assert result["tag"] == "overplanning"
        assert result["count"] == 3
        assert result["frequency_pct"] == pytest.approx(60.0, abs=0.1)

    def test_no_data(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        assert metrics.calculate_friction_pattern_index(WEEK) is None


class TestExecutionScoreTrend:
    def test_improving(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        from datetime import date, timedelta
        prev_week = "2026-04-27"
        prev_dates = [(date.fromisoformat(prev_week) + timedelta(days=i)).isoformat() for i in range(5)]
        for d in prev_dates:
            _insert_log(d, 5, "distraction", "1", [])
        for d in DATES:
            _insert_log(d, 8, "distraction", "1", [])
        result = metrics.calculate_execution_score_trend(WEEK)
        assert result["trend"] == "improving"
        assert result["delta"] > 0

    def test_declining(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        from datetime import date, timedelta
        prev_week = "2026-04-27"
        prev_dates = [(date.fromisoformat(prev_week) + timedelta(days=i)).isoformat() for i in range(5)]
        for d in prev_dates:
            _insert_log(d, 9, "distraction", "1", [])
        for d in DATES:
            _insert_log(d, 4, "distraction", "1", [])
        result = metrics.calculate_execution_score_trend(WEEK)
        assert result["trend"] == "declining"

    def test_no_previous_week(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        for d in DATES:
            _insert_log(d, 7, "distraction", "1", [])
        result = metrics.calculate_execution_score_trend(WEEK)
        assert result["trend"] == "insufficient_history"


class TestDeferralRate:
    def test_rate(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        _insert_log(DATES[0], 6, "distraction", "1", [
            ("Task A", "done"),
            ("Task B", "deferred"),
            ("Task C", "deferred"),
            ("Task D", "done"),
        ])
        rate = metrics.calculate_deferral_rate(WEEK)
        assert rate == pytest.approx(0.5, abs=0.01)

    def test_zero_deferral(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        _insert_log(DATES[0], 8, "distraction", "1", [
            ("Task A", "done"), ("Task B", "done"),
        ])
        assert metrics.calculate_deferral_rate(WEEK) == 0.0


class TestPlanningAccuracy:
    def test_accuracy(self, temp_db):
        import database, importlib
        importlib.reload(database)
        import metrics
        importlib.reload(metrics)
        _insert_log(DATES[0], 6, "distraction", "1", [
            ("Task A", "done"),
            ("Task B", "partial"),
            ("Task C", "done"),
            ("Task D", "dropped"),
        ])
        acc = metrics.calculate_planning_accuracy(WEEK)
        assert acc == pytest.approx(0.5, abs=0.01)
