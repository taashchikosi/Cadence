from rag_service import retrieve_relevant_chunks, format_rag_context
from database import query


def _pct(v):
    return f"{round(v * 100)}%" if v is not None else "N/A"


def build_weekly_review_prompt(user_id, week_start_date, metrics, patterns, user_profile):
    fpi_tag   = (metrics.get("friction_pattern_index") or {}).get("tag", "")
    pat_names = " ".join(p["pattern_name"] for p in patterns) if patterns else ""
    role      = user_profile.get("role_type", "executive") if user_profile else "executive"

    rag_query = (
        f"{pat_names} {fpi_tag} {role} intervention strategy "
        f"priority execution deep work planning leadership"
    ).strip()

    chunks = retrieve_relevant_chunks(rag_query, top_k=8)
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

    dwf = metrics.get('deep_work_frequency')
    dwf_str = f"{dwf}h" if dwf is not None else "N/A"
    sections.append(f"""
## THIS WEEK'S METRICS
- Execution Score: {est.get('current_avg', 'N/A')}/10 (trend: {est.get('trend', 'N/A')}, delta: {est.get('delta', 'N/A')})
- Priority Completion Rate: {_pct(metrics.get('priority_completion_rate'))} (3 priorities)
- Planning Accuracy: {_pct(metrics.get('planning_accuracy'))} (tasks completed vs planned)
- Deferral Rate: {_pct(metrics.get('deferral_rate'))} (deferred tasks + priorities / total)
- Deep Work: {dwf_str}/week
- Reactive Work Ratio: {_pct(metrics.get('reactive_work_ratio'))}
- Primary Friction: {fpi.get('tag', 'N/A').replace('_', ' ')} ({fpi.get('frequency_pct', 'N/A')}% intensity)""")

    if monday:
        p = [monday.get(f"priority_{i}") for i in range(1, 4) if monday.get(f"priority_{i}")]
        sections.append(f"""
## MONDAY COMMITMENTS (3 priorities)
{chr(10).join(f"- P{i+1}: {desc}" for i, desc in enumerate(p))}
- Estimated deep work: {monday.get('estimated_deep_work_hours')}h""")

    if friday:
        p_outcomes = []
        for i in range(1, 4):
            desc = monday.get(f"priority_{i}") if monday else None
            status = friday.get(f"priority_{i}_status")
            if status:
                label = desc if desc else f"Priority {i}"
                p_outcomes.append(f"- {label} → {status}")
        sections.append(f"""
## FRIDAY OUTCOMES
{chr(10).join(p_outcomes) if p_outcomes else '- No priority outcomes recorded'}
- Deep work: {friday.get('deep_work_hours')}h | Meetings: {friday.get('meetings_hours')}h | Reactive: {friday.get('reactive_work_hours')}h | Admin: {friday.get('admin_hours')}h
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
[One concrete, specific action for next week — an implementation instruction, not a principle. You MUST ground this in a specific framework or principle from the KNOWLEDGE BASE above. Cite the author by name and the concept explicitly. Format: the action itself, then on a new line — "Grounded in [Author's] [concept/book]: [one sentence explaining why this principle applies here]."]

**MATURITY LABEL**
[Exactly one of: "Early signal, not confirmed pattern" / "Emerging pattern" / "Confirmed pattern"]

Be direct. Do not soften. Do not add motivational language.""")

    return "\n".join(sections)
