from rag_service import retrieve_relevant_chunks, format_rag_context
from database import query


def _pct(v):
    return f"{round(v * 100)}%" if v is not None else "N/A"


def build_weekly_review_prompt(user_id, week_start_date, metrics, patterns, user_profile):
    chunks = retrieve_relevant_chunks(
        f"executive performance weekly review operational failure patterns {week_start_date}",
        top_k=6
    )
    rag_context = format_rag_context(chunks)

    friday = query(
        "SELECT * FROM weekly_friday_reviews WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    monday = query(
        "SELECT * FROM weekly_monday_inputs WHERE user_id=%s AND week_start_date=%s",
        (user_id, week_start_date), one=True
    )
    prev_review = query(
        "SELECT diagnosis, intervention FROM ai_reviews WHERE user_id=%s "
        "ORDER BY created_at DESC LIMIT 1",
        (user_id,), one=True
    )

    est = metrics.get("execution_score_trend") or {}
    fpi = metrics.get("friction_pattern_index") or {}

    sections = [
        "You are a senior operational advisor generating a weekly diagnostic review. "
        "Be analytical, precise, and consulting-grade. Every claim must be traceable to data. "
        "Do not fabricate. Do not soften. Reference the knowledge base frameworks where directly applicable.",
        f"\n## WEEK: {week_start_date}",
    ]

    if user_profile:
        sections.append(f"""
## OPERATOR PROFILE
- Role: {user_profile.get('role_type', '?')}
- Known failure pattern: {user_profile.get('self_identified_failure_pattern', '?')}
- Active goals: {user_profile.get('top_3_active_goals', '?')}""")

    sections.append(f"""
## THIS WEEK'S METRICS
- Priority Completion Rate: {_pct(metrics.get('priority_completion_rate'))}
- Deep Work Frequency: {metrics.get('deep_work_frequency', 'N/A')} blocks/day
- Deferral Rate: {_pct(metrics.get('deferral_rate'))}
- Planning Accuracy: {_pct(metrics.get('planning_accuracy'))}
- Execution Score: {est.get('current_avg', 'N/A')}/10 (trend: {est.get('trend', 'N/A')})
- Reactive Work Ratio: {_pct(metrics.get('reactive_work_ratio'))}
- Primary Friction: {fpi.get('tag', 'N/A')} ({fpi.get('frequency_pct', 'N/A')}% of days)""")

    if monday:
        p = [monday.get(f"priority_{i}") for i in range(1, 6) if monday.get(f"priority_{i}")]
        sections.append(f"""
## MONDAY COMMITMENTS
- Priorities: {' | '.join(p)}
- Estimated deep work: {monday.get('estimated_deep_work_hours')}h
- Predicted derailer: {monday.get('predicted_main_derailer')}""")

    if friday:
        p_outcomes = []
        for i in range(1, 6):
            if monday and monday.get(f"priority_{i}") and friday.get(f"priority_{i}_status"):
                p_outcomes.append(f"{monday.get(f'priority_{i}')} → {friday.get(f'priority_{i}_status')}")
        sections.append(f"""
## FRIDAY OUTCOMES
{chr(10).join(p_outcomes)}
- Time: Deep {friday.get('deep_work_hours')}h | Admin {friday.get('admin_hours')}h | Meetings {friday.get('meetings_hours')}h | Reactive {friday.get('reactive_work_hours')}h | Learning {friday.get('learning_hours')}h | Low-leverage {friday.get('low_leverage_hours')}h
- Execution score: {friday.get('weekly_execution_score')}/10
- Reflection: {friday.get('reflection_text') or 'None'}""")

    if patterns:
        sections.append("\n## DETECTED FAILURE PATTERNS")
        for p in patterns:
            sections.append(
                f"### {p['pattern_name']} ({p['maturity']}, confidence {p['confidence_score']})\n"
                f"Evidence: {p['evidence']}"
            )

    if prev_review:
        sections.append(f"""
## PRIOR WEEK SUMMARY
Diagnosis: {prev_review['diagnosis']}
Intervention given: {prev_review['intervention']}""")

    if rag_context:
        sections.append(rag_context)

    sections.append("""
## OUTPUT FORMAT (use exactly)

**DIAGNOSIS**
[1–2 sentences. Name the dominant pattern. Reference specific metrics.]

**EVIDENCE**
[4–6 bullet points. Each must cite specific data from above. No generic statements. Where applicable, cite the relevant framework from the knowledge base in parentheses.]

**INTERVENTION**
[One concrete, specific action for next week. Not a principle — an implementation instruction.]

**MATURITY LABEL**
[Exactly one of: "Early signal, not confirmed pattern" / "Emerging pattern" / "Confirmed pattern"]

Be direct. Do not soften. Do not add motivational language.""")

    return "\n".join(sections)
