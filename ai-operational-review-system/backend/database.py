import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "operational_review.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS onboarding_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_type TEXT NOT NULL,
            self_identified_failure_pattern TEXT,
            typical_week_structure TEXT,
            top_3_active_goals TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            execution_score INTEGER NOT NULL,
            friction_tag TEXT,
            deep_work_blocks TEXT DEFAULT '0',
            free_text TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            daily_log_id INTEGER REFERENCES daily_logs(id),
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'planned',
            is_planned INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS weekly_monday_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            priority_1 TEXT,
            priority_2 TEXT,
            priority_3 TEXT,
            estimated_deep_work_hours REAL,
            predicted_main_derailer TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS weekly_friday_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            priority_1_status TEXT,
            priority_2_status TEXT,
            priority_3_status TEXT,
            deep_work_hours REAL DEFAULT 0,
            admin_hours REAL DEFAULT 0,
            meetings_hours REAL DEFAULT 0,
            reactive_work_hours REAL DEFAULT 0,
            learning_hours REAL DEFAULT 0,
            low_leverage_hours REAL DEFAULT 0,
            weekly_execution_score INTEGER,
            reflection_text TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS weekly_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL UNIQUE,
            priority_completion_rate REAL,
            deep_work_frequency REAL,
            friction_pattern_index TEXT,
            execution_score_trend TEXT,
            deferral_rate REAL,
            planning_accuracy REAL,
            avg_execution_score REAL,
            calculated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS ai_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            diagnosis TEXT,
            evidence TEXT,
            intervention TEXT,
            maturity_label TEXT,
            raw_response TEXT,
            patterns_detected TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()
