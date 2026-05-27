import os
import json
import random
import psycopg2
import psycopg2.extras
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Fixed demo user definitions
# ---------------------------------------------------------------------------

DEMO_USERS = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "Ligia",
        "email": "ligia@cadence-demo.internal",
        "role_type": "Chief Operations Officer",
        "persona": "ligia",
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "Tifano",
        "email": "tifano@cadence-demo.internal",
        "role_type": "VP Marketing",
        "persona": "tifano",
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "Qasim",
        "email": "qasim@cadence-demo.internal",
        "role_type": "Head of Operations",
        "persona": "qasim",
    },
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "Dilorom",
        "email": "dilorom@cadence-demo.internal",
        "role_type": "Strategy Director",
        "persona": "dilorom",
    },
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "name": "Sherzod",
        "email": "sherzod@cadence-demo.internal",
        "role_type": "Founder & CEO",
        "persona": "sherzod",
    },
    {
        "id": "00000000-0000-0000-0000-000000000006",
        "name": "Taash",
        "email": "taash@cadence-demo.internal",
        "role_type": "Chief Executive Officer",
        "persona": "taash",
    },
]


# ---------------------------------------------------------------------------
# Persona-specific priority pools
# ---------------------------------------------------------------------------

PRIORITIES = {
    "ligia": [
        "Finalize Q3 operational efficiency report for board review",
        "Review and approve cross-functional team headcount plan",
        "Drive vendor contract renegotiation for logistics SLA",
        "Align engineering and ops on deployment process improvements",
        "Resolve escalated customer support backlog with CS lead",
        "Implement new incident response runbook across teams",
        "Close hiring loop on two senior ops manager roles",
        "Prepare ops dashboard KPIs for monthly leadership review",
        "Streamline inter-department handoff process for onboarding",
        "Lead post-mortem on last week's production incident",
        "Evaluate third-party tooling for process automation",
        "Define OKR targets for ops team Q4",
        "Conduct 1:1 performance check-ins with direct reports",
        "Audit current SOP documentation for accuracy",
        "Present capacity planning model to CFO",
    ],
    "tifano": [
        "Launch Q3 brand awareness campaign across paid channels",
        "Finalize agency creative brief for product relaunch",
        "Review and align on content calendar for next 8 weeks",
        "Analyze attribution data to optimize channel mix",
        "Coordinate with product on GTM messaging for new feature",
        "Build influencer partnership deck for exec approval",
        "Run NPS analysis and present findings to leadership",
        "Set up A/B test framework for email subject lines",
        "Consolidate marketing analytics into single reporting view",
        "Close partnership deal with two co-marketing brands",
        "Develop social media strategy for Q4 push",
        "Review PR agency performance against quarterly targets",
        "Brief agency on competitor positioning shift",
        "Audit marketing spend vs. pipeline contribution",
        "Finalize event sponsorship budget and ROI model",
    ],
    "qasim": [
        "Complete root cause analysis for recurring delivery delays",
        "Finalize process redesign for warehouse receiving workflow",
        "Implement Lean audit findings across three facility sites",
        "Present operations maturity scorecard to executive team",
        "Drive cross-site SOP standardization project to completion",
        "Negotiate revised SLA terms with two key 3PL providers",
        "Automate weekly ops reporting pipeline",
        "Close out compliance review action items before audit",
        "Build capacity model for Q4 peak season planning",
        "Evaluate new route optimization software vendor",
        "Mentor two high-potential operations analysts",
        "Resolve escalation backlog with customer success team",
        "Develop business case for additional warehouse investment",
        "Complete weekly operational performance review with leads",
        "Define metrics framework for new ops initiative",
    ],
    "dilorom": [
        "Draft strategic roadmap presentation for board offsite",
        "Complete competitive landscape analysis for new vertical",
        "Define success metrics for three strategic initiatives",
        "Facilitate cross-functional strategy alignment workshop",
        "Synthesize market research into strategic recommendations",
        "Build scenario planning model for three growth paths",
        "Review and refine mission and vision statements with CEO",
        "Lead OKR calibration session with department heads",
        "Identify partnership opportunities in adjacent markets",
        "Evaluate M&A target list against strategic fit criteria",
        "Prepare executive briefing on regulatory headwinds",
        "Complete strategic risk register and mitigation plans",
        "Develop investor narrative for upcoming fundraise",
        "Align product and go-to-market strategy for H2",
        "Drive resolution on deferred pricing strategy decision",
    ],
    "sherzod": [
        "Finalize fundraising narrative and update pitch deck",
        "Meet with three potential strategic partners this week",
        "Define product vision for next 18 months with CPO",
        "Align leadership team on company priorities for Q4",
        "Review board deck draft and add CEO commentary",
        "Host all-hands to share updated company direction",
        "Close negotiations on key commercial partnership",
        "Approve revised compensation philosophy for senior hires",
        "Clear backlog of investor intro meetings",
        "Evaluate go/no-go on new market expansion",
        "Review and sign off on annual budget with CFO",
        "Develop thought leadership angle for upcoming conference",
        "Clarify strategic ownership of three contested initiatives",
        "Set founder-level OKRs for next quarter",
        "Decide on org design for post-Series B structure",
    ],
    "taash": [
        "Align board on revised strategic priorities for H2",
        "Complete performance calibrations for all direct reports",
        "Finalize annual operating plan and present to board",
        "Lead executive team offsite planning session",
        "Review and approve company-wide OKR framework",
        "Drive resolution on key product-market fit questions",
        "Close critical senior executive hire",
        "Meet with top three enterprise customers this week",
        "Review investor update and quarterly metrics package",
        "Define CEO priorities for next quarter with COO",
        "Evaluate strategic options for international expansion",
        "Approve updated company values and culture rollout plan",
        "Prepare for upcoming board meeting with finance team",
        "Lead all-hands and set tone for Q4 sprint",
        "Sign off on revised go-to-market strategy",
    ],
}

FRICTION_TAGS = {
    "ligia": ["meetings", "meetings", "meetings", "meetings", "admin", "context_switching"],
    "tifano": ["context_switching", "context_switching", "context_switching", "meetings", "admin", "overcommitment"],
    "qasim": ["admin", "admin", "admin", "meetings", "context_switching"],
    "dilorom": ["decision_avoidance", "decision_avoidance", "decision_avoidance", "meetings", "admin", "context_switching"],
    "sherzod": ["overcommitment", "overcommitment", "overcommitment", "meetings", "context_switching", "admin"],
    "taash": ["context_switching", "meetings", "admin", "overcommitment", "decision_avoidance"],
}

FREE_TEXTS = {
    "ligia": [
        "Solid execution today — moved three blockers through the system.",
        "Too many meetings interrupted deep work windows again.",
        "Made good progress on the ops roadmap but got pulled into a vendor call.",
        "Cleared a significant backlog of approvals and escalations.",
        "Productive morning derailed by two unplanned crisis calls.",
        "Strong alignment session with engineering — decisions got made.",
        "Felt reactive most of the afternoon, but mornings were focused.",
        "Managed to carve out two hours of uninterrupted strategic thinking.",
        "Team issues consumed more bandwidth than expected today.",
        "Clear priorities drove a disciplined day — pleased with output.",
        "Back-to-back meetings left no time for deep work.",
        "Worked through the compliance review items methodically.",
        "Longer-than-expected leadership sync took the afternoon.",
        "Pushed one deliverable to tomorrow — needed more data.",
        "Good energy today; finished the capacity model draft.",
    ],
    "tifano": [
        "Started strong but lost focus after the agency call ran long.",
        "Context switching between four projects made it hard to go deep.",
        "Campaign analysis took longer than planned — data was messy.",
        "Strong creative session with the team this morning.",
        "Felt scattered all afternoon despite good morning intentions.",
        "Managed to ship the brief but quality felt rushed.",
        "Kept getting pulled into Slack threads instead of deep thinking.",
        "Missed two planned work blocks due to rescheduled calls.",
        "Better day — stayed in one project for three hours straight.",
        "A/B test results are promising, need to review more thoroughly.",
        "Too many priorities competing for attention this week.",
        "Finished the partnership deck but not at the quality I wanted.",
        "Jumped between tasks and lost context repeatedly.",
        "Made meaningful progress on channel attribution model.",
        "Felt more focused than usual — blocked calendar worked.",
    ],
    "qasim": [
        "Excellent focus session — solved the delivery delay root cause.",
        "Completed three major deliverables before noon.",
        "Methodical progress on the SOP standardization project.",
        "Deep work block on the capacity model was highly productive.",
        "Cleared all action items from last week's compliance review.",
        "Locked in three hours of uninterrupted process redesign work.",
        "Ahead of schedule on the warehouse audit findings implementation.",
        "Sharp, efficient day — stayed on plan throughout.",
        "Solid progress across all planned items with no major interruptions.",
        "Finished the performance scorecard ahead of Friday deadline.",
        "Admin tasks ate less time than expected — good outcome.",
        "Led a crisp, decision-driven team standup this morning.",
        "Resolved the 3PL escalation and documented the fix.",
        "Built the route optimization evaluation framework in one session.",
        "Delivered ahead of plan — strong execution day.",
    ],
    "dilorom": [
        "Stalled on the market analysis — struggled to make a call on framing.",
        "Made progress on the roadmap but deferred two key decisions again.",
        "Good research day but couldn't synthesize into clear recommendations.",
        "Workshop was productive but I avoided committing to a recommendation.",
        "Delayed sending the strategic brief — still not confident in it.",
        "Productive morning; afternoon got lost in over-analysis.",
        "Sent the board deck draft but it felt incomplete.",
        "Avoided a tough conversation with the CPO — need to schedule it.",
        "Better today — made two concrete decisions and moved forward.",
        "Spent too much time researching instead of deciding.",
        "Good momentum on the scenario planning model.",
        "Keep deferring the pricing decision — needs to be resolved this week.",
        "Made progress on the OKR calibration doc but second-guessed myself.",
        "Clearer thinking today — finished the risk register.",
        "Sat with ambiguity too long on the partnership evaluation.",
    ],
    "sherzod": [
        "Too many commitments on the calendar again — said yes to too much.",
        "Productive investor meetings but vision alignment session ran long.",
        "Great energy today — made two major decisions and moved them forward.",
        "Overbooked day left no space for reflection or deep thinking.",
        "Pitch session went well; need to follow up with three leads.",
        "Got pulled in four directions — none got my full attention.",
        "Cleared three strategic ambiguities that had been blocking the team.",
        "Committed to a new initiative mid-week — may have been premature.",
        "Strong all-hands; team felt energized and aligned.",
        "Spent too little time on the product vision this week.",
        "Meetings all day — no deep work blocks materialized.",
        "Made a bold call on the market expansion — feels right.",
        "Partnership conversation was promising; need to close this week.",
        "Day felt fragmented — need to restructure the weekly calendar.",
        "Focused morning session produced the clearest strategic thinking in weeks.",
    ],
    "taash": [
        "Still finding my rhythm — too much reactive work today.",
        "Managed to block two hours for deep thinking — noticing a difference.",
        "Less distracted than last month; execution is improving.",
        "Made real decisions today instead of deferring them.",
        "Focused morning led to breakthrough on the OKR framework.",
        "Cleaner day than usual — structure is helping.",
        "Strong execution across all priorities — best day in weeks.",
        "Blocked calendar made a measurable difference in output quality.",
        "Starting to see what high-performance weeks feel like.",
        "Finished everything on the plan — rarely happens, but it did today.",
        "Deep work block yielded the best strategic memo I've written.",
        "Discipline is compounding — more done in less time.",
        "Three hard decisions made and communicated clearly.",
        "Interrupted less than expected — proactive blocking is working.",
        "Consecutive focused days are producing real results.",
    ],
}

REFLECTIONS = {
    "ligia": [
        "Good week overall — execution stayed high despite heavy meeting load.",
        "Meetings continue to be the biggest drag on deep work. Need to cut Thursdays.",
        "Solid delivery on priorities. Ops team is performing well.",
        "Managed the vendor escalation well. Would have preferred more strategic time.",
        "Strong planning adherence this week. Felt in control of the agenda.",
        "Some reactive drift mid-week but recovered by Friday.",
        "Best week of the month — clear priorities led to clear outcomes.",
        "Would like to protect Wednesday mornings for strategic work going forward.",
    ],
    "tifano": [
        "Mixed week — good creative output but poor deep work discipline.",
        "Context switching is my biggest enemy. Need to batch similar work.",
        "Started the week overconfident on what I could deliver. Adjusted by Thursday.",
        "Campaign work suffered from too many interruptions. Will restructure next week.",
        "Better week than last. Still struggling to estimate task complexity.",
        "Good progress on partnership work but fell short on analytics.",
        "Starting to see improvement in focus when I block Slack notifications.",
        "Still overcommitting at the start of the week. Getting more realistic.",
        "Week felt scattered but outputs were reasonable — can do better.",
    ],
    "qasim": [
        "Strong week — delivered on all five priorities with time to spare.",
        "Execution was tight. Blocked calendar and minimal meetings made the difference.",
        "Completed everything planned. Team blockers resolved faster than expected.",
        "Very efficient week. Deep work sessions yielded high-quality outputs.",
        "All priorities completed. Ahead of pace on the quarterly roadmap.",
        "Sharp week — every hour had intent. Proud of the team's delivery.",
        "Hit everything on the plan. Starting to see the compound effect of focus.",
        "Good week for process improvement work. Quantifiable results.",
    ],
    "dilorom": [
        "Deferred too many decisions again — need to get more comfortable with ambiguity.",
        "Better than last week, but still stalled on the pricing strategy.",
        "Made one big call this week and it felt good. Need to do more of that.",
        "Over-researched two topics that needed a decision, not more data.",
        "Good progress on OKRs once I stopped second-guessing the framework.",
        "Starting to recognize my decision avoidance pattern more clearly.",
        "Committed to a strategic recommendation without waiting for perfect data — progress.",
        "Still too much deferral. Setting a 24-hour decision rule for next week.",
        "Improving, but the instinct to delay is still strong.",
    ],
    "sherzod": [
        "Overcommitted again — said yes to three things I should have declined.",
        "Great vision week but execution of tactical items fell short.",
        "Too many priorities — team is confused about what matters most.",
        "Need to ruthlessly cut agenda items. Focus is a strategic choice.",
        "Strong investor conversations but internal execution suffered.",
        "Spread too thin again. Committed to protecting two focus blocks next week.",
        "Good week for big-picture thinking. Poor week for follow-through.",
        "All-hands was strong. Operational delivery was inconsistent.",
        "The best weeks are when I say no more than I say yes.",
    ],
    "taash": [
        "Slow start to the six months — still operating reactively.",
        "Starting to protect mornings. Small wins adding up.",
        "Noticeable improvement in focus since restructuring the calendar.",
        "Best planning week yet — priorities matched actual time allocation.",
        "Execution score trending up. Consistency is the key.",
        "Seeing real results from deep work discipline. Should have started sooner.",
        "Strongest week to date — delivered on everything planned.",
        "The system is working. Momentum feels sustainable now.",
    ],
}


# ---------------------------------------------------------------------------
# Persona parameter generators
# ---------------------------------------------------------------------------

def persona_params(persona, week_index, total_weeks=8):
    """Return (exec_score, deep_work_hours, friction_tag, planning_accuracy, deferral_rate)
    for a given persona and week index (0 = earliest, total_weeks-1 = most recent)."""

    progress = week_index / max(total_weeks - 1, 1)  # 0.0 → 1.0

    if persona == "ligia":
        score      = round(random.gauss(7.2, 1.2))
        deep_h     = random.gauss(10.0, 2.0)          # ~10h, lots of meetings
        friction   = random.choice(FRICTION_TAGS["ligia"])
        plan_acc   = random.gauss(0.70, 0.08)
        defer_rate = random.gauss(0.18, 0.07)

    elif persona == "tifano":
        base_score = 6.1 + progress * 1.2
        score      = round(random.gauss(base_score, 1.5))
        deep_h     = random.gauss(7.0 + progress * 2.0, 1.5)   # improves over time
        friction   = random.choice(FRICTION_TAGS["tifano"])
        plan_acc   = random.gauss(0.55 + progress * 0.15, 0.10)
        defer_rate = random.gauss(0.32 - progress * 0.10, 0.08)

    elif persona == "qasim":
        score      = round(random.gauss(8.3, 0.7))
        deep_h     = random.gauss(17.0, 1.5)           # high deep work
        friction   = random.choice(FRICTION_TAGS["qasim"])
        plan_acc   = random.gauss(0.84, 0.06)
        defer_rate = random.gauss(0.08, 0.04)

    elif persona == "dilorom":
        base_score = 5.8 + progress * 1.8
        score      = round(random.gauss(base_score, 1.4))
        deep_h     = random.gauss(9.0 + progress * 2.0, 1.5)
        friction   = random.choice(FRICTION_TAGS["dilorom"])
        plan_acc   = random.gauss(0.58 + progress * 0.20, 0.10)
        defer_rate = random.gauss(0.42 - progress * 0.20, 0.08)

    elif persona == "sherzod":
        score      = round(random.gauss(7.0, 1.4))
        deep_h     = random.gauss(7.5, 2.0)            # always overcommitted
        friction   = random.choice(FRICTION_TAGS["sherzod"])
        plan_acc   = random.gauss(0.55, 0.12)
        defer_rate = random.gauss(0.28, 0.10)

    elif persona == "taash":
        # Clear arc: starts struggling, ends high-performing
        base_score = 5.5 + progress * 3.5
        score      = round(random.gauss(base_score, max(1.5 - progress, 0.5)))
        deep_h     = random.gauss(5.0 + progress * 12.0, max(2.0 - progress, 0.5))
        friction   = random.choice(FRICTION_TAGS["taash"])
        plan_acc   = random.gauss(0.45 + progress * 0.40, max(0.12 - progress * 0.08, 0.04))
        defer_rate = random.gauss(0.38 - progress * 0.25, 0.08)

    else:
        score      = round(random.gauss(7.0, 1.0))
        deep_h     = 10.0
        friction   = "meetings"
        plan_acc   = 0.70
        defer_rate = 0.20

    score      = max(1,   min(10,  score))
    deep_h     = max(1.0, min(25.0, deep_h))
    plan_acc   = max(0.1, min(1.0,  plan_acc))
    defer_rate = max(0.0, min(0.9,  defer_rate))

    return score, round(deep_h, 1), friction, plan_acc, defer_rate


def task_status(planned, defer_rate):
    """Return a task status based on planning accuracy and deferral rate."""
    r = random.random()
    if r < planned:
        return "done"
    elif r < planned + defer_rate * (1 - planned):
        return "deferred"
    else:
        return "partial"


def week_time_allocation(persona, exec_score):
    """Return (deep_work_h, meetings_h, admin_h, reactive_h, learning_h, low_leverage_h)."""
    total = 40.0
    if persona == "ligia":
        meetings = random.uniform(12, 18)
        deep = random.uniform(6, 12)
        admin = random.uniform(3, 6)
        reactive = random.uniform(3, 7)
    elif persona == "tifano":
        meetings = random.uniform(8, 14)
        deep = random.uniform(4, 8)
        admin = random.uniform(3, 6)
        reactive = random.uniform(5, 10)
    elif persona == "qasim":
        meetings = random.uniform(6, 10)
        deep = random.uniform(12, 18)
        admin = random.uniform(2, 5)
        reactive = random.uniform(2, 5)
    elif persona == "dilorom":
        meetings = random.uniform(10, 16)
        deep = random.uniform(5, 10)
        admin = random.uniform(3, 6)
        reactive = random.uniform(5, 9)
    elif persona == "sherzod":
        meetings = random.uniform(14, 20)
        deep = random.uniform(4, 9)
        admin = random.uniform(2, 5)
        reactive = random.uniform(5, 10)
    else:  # taash
        meetings = random.uniform(10, 16)
        deep = random.uniform(5, 14)
        admin = random.uniform(2, 5)
        reactive = random.uniform(3, 8)

    learning = random.uniform(1, 3)
    used = meetings + deep + admin + reactive + learning
    low_leverage = max(0, total - used)

    return (
        round(deep, 1),
        round(meetings, 1),
        round(admin, 1),
        round(reactive, 1),
        round(learning, 1),
        round(low_leverage, 1),
    )


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_all_users():
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url, sslmode="require")
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    try:
        # ------------------------------------------------------------------
        # 1. Upsert auth.users
        # ------------------------------------------------------------------
        auth_rows = [
            (
                u["id"],
                u["email"],
                "2024-01-01T00:00:00+00:00",
                "2024-01-01T00:00:00+00:00",
                '{"provider":"email","providers":["email"]}',
                '{}',
                False,
                "$2a$10$placeholder_password_hash_not_used",
            )
            for u in DEMO_USERS
        ]
        psycopg2.extras.execute_values(cur, """
            INSERT INTO auth.users
                (id, email, created_at, updated_at,
                 raw_app_meta_data, raw_user_meta_data,
                 is_super_admin, encrypted_password)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """, auth_rows, template="(%s::uuid,%s,%s::timestamptz,%s::timestamptz,%s::jsonb,%s::jsonb,%s,%s)")

        # ------------------------------------------------------------------
        # 2. Upsert user_profiles
        # ------------------------------------------------------------------
        profile_rows = [
            (u["id"], u["role_type"], "female", "text", True)
            for u in DEMO_USERS
        ]
        psycopg2.extras.execute_values(cur, """
            INSERT INTO user_profiles
                (id, role_type, voice_preference, response_mode, onboarding_complete)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
        """, profile_rows, template="(%s::uuid,%s,%s,%s,%s)")

        # ------------------------------------------------------------------
        # 3. Compute 4 Mondays going back from today
        # ------------------------------------------------------------------
        today = date.today()
        days_since_monday = today.weekday()
        current_monday = today - timedelta(days=days_since_monday)
        # 4 weeks (1 month), most recent week last
        mondays = [current_monday - timedelta(weeks=(7 - i)) for i in range(8)]

        total_weekly_logs = 0
        total_tasks       = 0
        total_metrics     = 0

        for user in DEMO_USERS:
            uid     = user["id"]
            persona = user["persona"]
            pool    = PRIORITIES[persona]
            reflection_pool = REFLECTIONS[persona]

            for week_index, monday in enumerate(mondays):
                if monday > today:
                    continue

                seed_key = uid + str(monday)
                random.seed(hash(seed_key) & 0xFFFFFFFF)

                exec_score, deep_hours, friction, plan_acc, defer_rate = persona_params(
                    persona, week_index, total_weeks=len(mondays)
                )

                # Shuffle priority pool and pick 3 priorities + 10 tasks
                shuffled = pool[:]
                random.shuffle(shuffled)
                p1_desc, p2_desc, p3_desc = shuffled[0], shuffled[1], shuffled[2]
                task_pool = shuffled[3:13] if len(shuffled) >= 13 else shuffled[3:]
                # pad to 10 if needed
                while len(task_pool) < 10:
                    task_pool.append(random.choice(pool))

                # ---- weekly_monday_inputs ----
                cur.execute("""
                    INSERT INTO weekly_monday_inputs
                        (user_id, week_start_date, priority_1, priority_2, priority_3,
                         estimated_deep_work_hours)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (user_id, week_start_date) DO NOTHING
                """, (uid, monday.isoformat(), p1_desc, p2_desc, p3_desc, round(deep_hours, 1)))

                # ---- ONE weekly log entry (dated Monday) ----
                reflection = random.choice(reflection_pool)
                def hours_to_blocks(h):
                    if h < 4:  return "0"
                    if h < 8:  return "1"
                    if h < 14: return "2"
                    return "3+"

                cur.execute("""
                    INSERT INTO daily_logs
                        (user_id, date, execution_score, friction_tag, deep_work_blocks, free_text)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (user_id, date) DO UPDATE SET
                        execution_score  = EXCLUDED.execution_score,
                        friction_tag     = EXCLUDED.friction_tag,
                        deep_work_blocks = EXCLUDED.deep_work_blocks,
                        free_text        = EXCLUDED.free_text
                    RETURNING id
                """, (uid, monday.isoformat(), exec_score, friction,
                      hours_to_blocks(deep_hours), reflection))
                log_row = cur.fetchone()
                if not log_row:
                    continue
                log_id = log_row["id"]
                total_weekly_logs += 1

                # ---- 10 tasks for this weekly log ----
                task_rows = []
                for task_desc in task_pool[:10]:
                    status = task_status(plan_acc, defer_rate)
                    task_rows.append((log_id, uid, task_desc[:200], status, True))

                if task_rows:
                    psycopg2.extras.execute_values(cur, """
                        INSERT INTO tasks (daily_log_id, user_id, description, status, is_planned)
                        VALUES %s
                        ON CONFLICT DO NOTHING
                    """, task_rows, template="(%s::uuid,%s::uuid,%s,%s,%s)")
                    total_tasks += len(task_rows)

                # ---- weekly_friday_reviews ----
                p1_s = task_status(plan_acc, defer_rate)
                p2_s = task_status(plan_acc, defer_rate)
                p3_s = task_status(plan_acc, defer_rate)
                deep_h, _, _, reactive_h, _, _ = week_time_allocation(persona, exec_score)

                cur.execute("""
                    INSERT INTO weekly_friday_reviews
                        (user_id, week_start_date,
                         priority_1_status, priority_2_status, priority_3_status,
                         deep_work_hours, reactive_work_hours,
                         weekly_execution_score, reflection_text)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (user_id, week_start_date) DO UPDATE SET
                        priority_1_status      = EXCLUDED.priority_1_status,
                        priority_2_status      = EXCLUDED.priority_2_status,
                        priority_3_status      = EXCLUDED.priority_3_status,
                        deep_work_hours        = EXCLUDED.deep_work_hours,
                        reactive_work_hours    = EXCLUDED.reactive_work_hours,
                        weekly_execution_score = EXCLUDED.weekly_execution_score,
                        reflection_text        = EXCLUDED.reflection_text
                """, (uid, monday.isoformat(),
                      p1_s, p2_s, p3_s,
                      round(deep_h, 1), round(reactive_h, 1),
                      exec_score, reflection))

                # ---- weekly_metrics ----
                total_t    = len(task_rows)
                deferred_t = sum(1 for t in task_rows if t[3] == "deferred")
                done_t     = sum(1 for t in task_rows if t[3] == "done")
                pa_val     = round(done_t / total_t, 3) if total_t > 0 else None

                # deferral: (deferred tasks + deferred priorities) / (10 + 3)
                p_deferred = sum(1 for s in [p1_s, p2_s, p3_s] if s == "deferred")
                dr_total   = total_t + 3
                dr_val     = round((deferred_t + p_deferred) / dr_total, 3) if dr_total > 0 else None

                done_p  = sum(1 for s in [p1_s, p2_s, p3_s] if s == "done")
                pcr_val = round(done_p / 3, 3)

                fpi_val = {"tag": friction, "frequency_pct": 100.0, "count": 1}
                est_val = {"current_avg": exec_score, "trend": "stable", "delta": None}

                cur.execute("""
                    INSERT INTO weekly_metrics
                        (user_id, week_start_date, priority_completion_rate,
                         deep_work_frequency, friction_pattern_index,
                         execution_score_trend, deferral_rate,
                         planning_accuracy, avg_execution_score)
                    VALUES (%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                    ON CONFLICT (user_id, week_start_date) DO UPDATE SET
                        priority_completion_rate = EXCLUDED.priority_completion_rate,
                        deep_work_frequency      = EXCLUDED.deep_work_frequency,
                        friction_pattern_index   = EXCLUDED.friction_pattern_index,
                        execution_score_trend    = EXCLUDED.execution_score_trend,
                        deferral_rate            = EXCLUDED.deferral_rate,
                        planning_accuracy        = EXCLUDED.planning_accuracy,
                        avg_execution_score      = EXCLUDED.avg_execution_score,
                        calculated_at            = NOW()
                """, (uid, monday.isoformat(),
                      pcr_val, round(deep_h, 2),
                      json.dumps(fpi_val), json.dumps(est_val),
                      dr_val, pa_val, exec_score))
                total_metrics += 1

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return {
        "users_seeded": len(DEMO_USERS),
        "weeks":        len(mondays),
        "weekly_logs":  total_weekly_logs,
        "tasks":        total_tasks,
        "metrics_rows": total_metrics,
    }
