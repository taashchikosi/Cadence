import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(autouse=True)
def temp_db(tmp_path):
    db_file = str(tmp_path / "test.db")
    os.environ["DB_PATH"] = db_file
    import database
    database.DB_PATH = db_file
    database.init_db()
    yield db_file


def _reload():
    import importlib
    import database
    importlib.reload(database)
    import metrics
    importlib.reload(metrics)
    import pattern_detection
    importlib.reload(pattern_detection)
    return pattern_detection


def _insert_log(date, score, friction, blocks, tasks):
    import database
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


def _insert_friday(week_start, **kwargs):
    import database
    conn = database.get_db()
    defaults = dict(
        priority_1_status="done", priority_2_status="done", priority_3_status="done",
        deep_work_hours=10, admin_hours=3, meetings_hours=5, reactive_work_hours=4,
        learning_hours=2, low_leverage_hours=2, weekly_execution_score=7, reflection_text=None
    )
    defaults.update(kwargs)
    conn.execute("""
        INSERT INTO weekly_friday_reviews
            (week_start_date, priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, admin_hours, meetings_hours, reactive_work_hours,
             learning_hours, low_leverage_hours, weekly_execution_score, reflection_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (week_start,
          defaults["priority_1_status"], defaults["priority_2_status"], defaults["priority_3_status"],
          defaults["deep_work_hours"], defaults["admin_hours"], defaults["meetings_hours"],
          defaults["reactive_work_hours"], defaults["learning_hours"], defaults["low_leverage_hours"],
          defaults["weekly_execution_score"], defaults["reflection_text"]))
    conn.commit()
    conn.close()


WEEK = "2026-05-04"
DATES = ["2026-05-04", "2026-05-05", "2026-05-06", "2026-05-07", "2026-05-08"]


class TestPlanningInflation:
    def test_detected_when_many_tasks_low_completion(self, temp_db):
        pd = _reload()
        for date in DATES:
            _insert_log(date, 5, "overplanning", "0", [
                ("Task 1", "deferred"), ("Task 2", "dropped"), ("Task 3", "done"),
            ])
        metrics = {"planning_accuracy": 0.33, "deferral_rate": 0.5}
        result = pd.detect_planning_inflation(WEEK, metrics)
        assert result is not None
        assert result["pattern_name"] == "Planning Inflation"
        assert result["confidence_score"] > 0.5

    def test_not_detected_when_high_completion(self, temp_db):
        pd = _reload()
        for date in DATES:
            _insert_log(date, 8, "distraction", "2", [
                ("Task 1", "done"), ("Task 2", "done"),
            ])
        metrics = {"planning_accuracy": 0.9, "deferral_rate": 0.1}
        result = pd.detect_planning_inflation(WEEK, metrics)
        assert result is None


class TestDepthDeprivation:
    def test_detected_when_low_blocks(self, temp_db):
        pd = _reload()
        for date in DATES:
            _insert_log(date, 5, "distraction", "0", [])
        metrics = {"deep_work_frequency": 0.0}
        result = pd.detect_depth_deprivation(WEEK, metrics)
        assert result is not None
        assert result["pattern_name"] == "Depth Deprivation"
        assert result["confidence_score"] == pytest.approx(1.0)

    def test_not_detected_when_sufficient_blocks(self, temp_db):
        pd = _reload()
        for date in DATES:
            _insert_log(date, 8, "distraction", "2", [])
        metrics = {"deep_work_frequency": 2.0}
        result = pd.detect_depth_deprivation(WEEK, metrics)
        assert result is None

    def test_not_detected_insufficient_data(self, temp_db):
        pd = _reload()
        _insert_log(DATES[0], 5, "distraction", "0", [])
        metrics = {"deep_work_frequency": 0.0}
        result = pd.detect_depth_deprivation(WEEK, metrics)
        # Only 1 data point — below MIN_DATA_POINTS
        assert result is None


class TestReactiveCapture:
    def test_detected_when_reactive_dominates(self, temp_db):
        pd = _reload()
        _insert_friday(WEEK, reactive_work_hours=15, deep_work_hours=3)
        metrics = {"priority_completion_rate": 0.33}
        result = pd.detect_reactive_capture(WEEK, metrics)
        assert result is not None
        assert result["pattern_name"] == "Reactive Capture"

    def test_not_detected_when_balanced(self, temp_db):
        pd = _reload()
        _insert_friday(WEEK, reactive_work_hours=5, deep_work_hours=12)
        metrics = {"priority_completion_rate": 0.8}
        result = pd.detect_reactive_capture(WEEK, metrics)
        assert result is None


class TestLeverageLeakage:
    def test_detected_when_admin_dominates(self, temp_db):
        pd = _reload()
        _insert_friday(WEEK, low_leverage_hours=8, admin_hours=5, deep_work_hours=3)
        metrics = {}
        result = pd.detect_leverage_leakage(WEEK, metrics)
        assert result is not None
        assert result["pattern_name"] == "Leverage Leakage"

    def test_not_detected_when_deep_work_high(self, temp_db):
        pd = _reload()
        _insert_friday(WEEK, low_leverage_hours=3, admin_hours=2, deep_work_hours=15)
        metrics = {}
        result = pd.detect_leverage_leakage(WEEK, metrics)
        assert result is None
