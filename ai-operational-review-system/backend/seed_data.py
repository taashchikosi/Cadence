"""
Seed the database with 2 weeks of realistic test data.
Run: python seed_data.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DB_PATH", "operational_review.db")

from database import init_db, get_db

WEEK1 = "2026-05-04"  # Monday
WEEK2 = "2026-05-11"  # Monday


def seed():
    init_db()
    conn = get_db()

    # Onboarding
    conn.execute("DELETE FROM onboarding_profile")
    conn.execute("""
        INSERT INTO onboarding_profile
            (role_type, self_identified_failure_pattern, typical_week_structure, top_3_active_goals)
        VALUES (?, ?, ?, ?)
    """, (
        "Founder / CEO",
        "Planning Inflation — I consistently overplan and underdeliver on strategic work.",
        "Mon–Fri. Meetings heavy Tues/Wed. Prefer deep work mornings if protected.",
        "1. Launch new pricing model. 2. Close Series A lead investor. 3. Hire VP Engineering."
    ))

    # Monday inputs
    conn.execute("DELETE FROM weekly_monday_inputs")
    conn.execute("""
        INSERT INTO weekly_monday_inputs
            (week_start_date, priority_1, priority_2, priority_3,
             estimated_deep_work_hours, predicted_main_derailer)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (WEEK1, "Finalise investor deck", "Define pricing tiers", "Draft VP Eng JD", 15, "meetings"))
    conn.execute("""
        INSERT INTO weekly_monday_inputs
            (week_start_date, priority_1, priority_2, priority_3,
             estimated_deep_work_hours, predicted_main_derailer)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (WEEK2, "Send deck to 3 leads", "Pricing page live", "VP Eng interviews scheduled", 12, "unclear_priorities"))

    # Daily logs — Week 1 (Mon–Fri: 2026-05-04 to 2026-05-08)
    conn.execute("DELETE FROM daily_logs")
    conn.execute("DELETE FROM tasks")

    week1_logs = [
        ("2026-05-04", 7, "overplanning", "1",
         [("Investor deck v1 draft", "partial"), ("Review cap table", "done"), ("Call with lawyer re: term sheet", "deferred"), ("Update board slides", "deferred")]),
        ("2026-05-05", 5, "external_demands", "0",
         [("Investor deck v2", "deferred"), ("Pricing model spreadsheet", "partial"), ("3 candidate screening calls", "done"), ("Team all-hands prep", "done")]),
        ("2026-05-06", 6, "distraction", "1",
         [("Investor deck v2", "partial"), ("Pricing tier research", "done"), ("Reply to inbound partnership emails", "done"), ("Roadmap review", "deferred")]),
        ("2026-05-07", 4, "low_energy", "0",
         [("Investor deck v2 final", "deferred"), ("VP Eng JD draft", "partial"), ("Ops catch-up call", "done"), ("Expense review", "done"), ("Slack backlog", "done")]),
        ("2026-05-08", 6, "overplanning", "1",
         [("Investor deck send", "partial"), ("Pricing decision", "deferred"), ("VP Eng JD", "deferred"), ("Weekly review", "done")]),
    ]

    for date, score, friction, blocks, tasks in week1_logs:
        cursor = conn.execute("""
            INSERT INTO daily_logs (date, execution_score, friction_tag, deep_work_blocks, free_text)
            VALUES (?, ?, ?, ?, ?)
        """, (date, score, friction, blocks, None))
        log_id = cursor.lastrowid
        for desc, status in tasks:
            conn.execute("""
                INSERT INTO tasks (daily_log_id, description, status, is_planned)
                VALUES (?, ?, ?, 1)
            """, (log_id, desc, status))

    # Friday review — Week 1
    conn.execute("DELETE FROM weekly_friday_reviews")
    conn.execute("""
        INSERT INTO weekly_friday_reviews
            (week_start_date, priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, admin_hours, meetings_hours, reactive_work_hours,
             learning_hours, low_leverage_hours, weekly_execution_score, reflection_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (WEEK1, "partial", "partial", "dropped", 6, 5, 12, 10, 1, 6, 5,
          "Too many meetings this week. The deck never got a proper focused block."))

    # Daily logs — Week 2 (Mon–Fri: 2026-05-11 to 2026-05-15)
    week2_logs = [
        ("2026-05-11", 7, "overplanning", "2",
         [("Send investor deck to Sequoia", "done"), ("Send deck to Benchmark", "done"), ("Pricing page copy", "partial"), ("Interview prep", "deferred")]),
        ("2026-05-12", 8, "external_demands", "2",
         [("Investor follow-up emails", "done"), ("Pricing page copy final", "partial"), ("VP Eng phone screen #1", "done"), ("VP Eng phone screen #2", "done")]),
        ("2026-05-13", 6, "decision_uncertainty", "1",
         [("Pricing decision", "deferred"), ("Third investor outreach", "deferred"), ("Ops metrics review", "done"), ("Legal contract review", "done")]),
        ("2026-05-14", 7, "avoidance", "1",
         [("Pricing page live", "partial"), ("VP Eng onsite schedule", "done"), ("Team 1:1s", "done"), ("Pricing decision", "deferred")]),
        ("2026-05-15", 8, "overplanning", "2",
         [("Pricing live", "done"), ("Investor third outreach", "done"), ("Weekly review", "done"), ("VP Eng debrief", "done")]),
    ]

    for date, score, friction, blocks, tasks in week2_logs:
        cursor = conn.execute("""
            INSERT INTO daily_logs (date, execution_score, friction_tag, deep_work_blocks, free_text)
            VALUES (?, ?, ?, ?, ?)
        """, (date, score, friction, blocks, None))
        log_id = cursor.lastrowid
        for desc, status in tasks:
            conn.execute("""
                INSERT INTO tasks (daily_log_id, description, status, is_planned)
                VALUES (?, ?, ?, 1)
            """, (log_id, desc, status))

    conn.execute("""
        INSERT INTO weekly_friday_reviews
            (week_start_date, priority_1_status, priority_2_status, priority_3_status,
             deep_work_hours, admin_hours, meetings_hours, reactive_work_hours,
             learning_hours, low_leverage_hours, weekly_execution_score, reflection_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (WEEK2, "done", "partial", "partial", 10, 4, 9, 7, 2, 3, 7,
          "Better week. Pricing took longer than expected due to indecision on tiers."))

    # Seed a prior AI review for Week 1
    conn.execute("DELETE FROM ai_reviews")
    conn.execute("""
        INSERT INTO ai_reviews
            (week_start_date, diagnosis, evidence, intervention, maturity_label, raw_response, patterns_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        WEEK1,
        "Planning Inflation is the dominant operational failure pattern. Task load consistently exceeds execution capacity, with deep work blocks insufficient to support the complexity of the stated priorities.",
        "- Planning accuracy: 38% — fewer than 4 in 10 planned tasks reached done status.\n- Deep work frequency: 0.6 blocks/day — well below the threshold for complex deliverables.\n- Primary friction: overplanning (60% of logged days).\n- All three weekly priorities remained incomplete or dropped by Friday.\n- Deferral rate: 35% of all tracked tasks.",
        "On Monday, reduce your daily task list to a maximum of 3 items. Block two 90-minute deep work sessions before noon on Monday and Wednesday and mark them as non-negotiable in your calendar.",
        "Confirmed pattern",
        "[Seeded review]",
        '["Planning Inflation", "Depth Deprivation", "False Priority"]'
    ))

    conn.commit()
    conn.close()
    print("Seed data inserted successfully.")
    print(f"  Week 1: {WEEK1} | Week 2: {WEEK2}")


if __name__ == "__main__":
    seed()
