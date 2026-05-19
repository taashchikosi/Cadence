import json
from database import get_db


def build_review_prompt(week_start_date, metrics, patterns, onboarding, prev_review=None):
    sections = []

    sections.append("You are a senior operational advisor conducting a weekly diagnostic review. "
                    "Your tone is analytical, precise, and consulting-grade — not motivational or encouraging. "
                    "Base every claim on the data provided. Do not fabricate or extrapolate.")

    sections.append(f"\n## WEEK UNDER REVIEW: {week_start_date}")

    if onboarding:
        sections.append(f"""
## OPERATOR CONTEXT
- Role: {onboarding.get('role_type', 'Not specified')}
- Self-identified failure pattern: {onboarding.get('self_identified_failure_pattern', 'Not specified')}
- Typical week structure: {onboarding.get('typical_week_structure', 'Not specified')}
- Active goals: {onboarding.get('top_3_active_goals', 'Not specified')}""")

    m = metrics
    est = m.get("execution_score_trend") or {}
    fpi = m.get("friction_pattern_index") or {}

    sections.append(f"""
## OPERATIONAL METRICS (THIS WEEK)
- Priority Completion Rate: {_pct(m.get('priority_completion_rate'))}
- Deep Work Frequency: {m.get('deep_work_frequency', 'N/A')} blocks/day avg
- Deferral Rate: {_pct(m.get('deferral_rate'))}
- Planning Accuracy: {_pct(m.get('planning_accuracy'))}
- Execution Score: {est.get('current_avg', 'N/A')} / 10 (trend: {est.get('trend', 'N/A')})
- Primary Friction Tag: {fpi.get('tag', 'N/A')} ({fpi.get('frequency_pct', 'N/A')}% of logged days)""")

    conn = get_db()
    friday = conn.execute(
        "SELECT * FROM weekly_friday_reviews WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    monday = conn.execute(
        "SELECT * FROM weekly_monday_inputs WHERE week_start_date = ?",
        (week_start_date,)
    ).fetchone()
    conn.close()

    if monday:
        sections.append(f"""
## MONDAY COMMITMENTS
- Priority 1: {monday['priority_1']}
- Priority 2: {monday['priority_2']}
- Priority 3: {monday['priority_3']}
- Estimated deep work hours: {monday['estimated_deep_work_hours']}h
- Predicted derailer: {monday['predicted_main_derailer']}""")

    if friday:
        sections.append(f"""
## FRIDAY OUTCOMES
- Priority 1: {monday['priority_1'] if monday else '?'} → {friday['priority_1_status']}
- Priority 2: {monday['priority_2'] if monday else '?'} → {friday['priority_2_status']}
- Priority 3: {monday['priority_3'] if monday else '?'} → {friday['priority_3_status']}
- Time allocation: Deep Work {friday['deep_work_hours']}h | Admin {friday['admin_hours']}h | Meetings {friday['meetings_hours']}h | Reactive {friday['reactive_work_hours']}h | Learning {friday['learning_hours']}h | Low-Leverage {friday['low_leverage_hours']}h
- Weekly execution score: {friday['weekly_execution_score']}/10
- Reflection: {friday['reflection_text'] or 'None provided'}""")

    if patterns:
        sections.append("\n## DETECTED FAILURE PATTERNS")
        for p in patterns:
            sections.append(f"""
### {p['pattern_name']} (confidence: {p['confidence_score']}, {p['maturity']})
Evidence: {p['evidence']}
Explanation: {p['explanation']}""")
    else:
        sections.append("\n## DETECTED FAILURE PATTERNS\nNo patterns detected above threshold this week.")

    if prev_review:
        sections.append(f"""
## PRIOR WEEK REVIEW SUMMARY
{prev_review}""")

    sections.append("""
## OUTPUT FORMAT
Produce a structured operational review using EXACTLY this format:

**DIAGNOSIS**
[1–2 sentences. Name the dominant operational failure pattern. Be specific. Reference the data.]

**EVIDENCE**
[3–5 bullet points. Each bullet must cite a specific metric, task, or behaviour from the data above. No generic statements.]

**INTERVENTION**
[1 specific, concrete behavioural or structural change to implement next week. Not a principle — an action.]

**MATURITY LABEL**
[State exactly one of: "Early signal, not confirmed pattern" / "Emerging pattern" / "Confirmed pattern"]

Be direct. Do not soften findings. Do not add motivational language.""")

    return "\n".join(sections)


def _pct(val):
    if val is None:
        return "N/A"
    return f"{round(val * 100)}%"
