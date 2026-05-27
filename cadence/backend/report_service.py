import os
from openai import OpenAI

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def generate_coach_report(profile, metrics, priorities, tasks, friday_data, kb_context, week_start):
    if not DEEPSEEK_API_KEY:
        return _mock_report()

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    def pct(v):
        return f"{round(v * 100)}%" if v is not None else "N/A"

    fpi = metrics.get("friction_pattern_index") or {}
    est = metrics.get("execution_score_trend") or {}

    done_p    = sum(1 for p in priorities if p.get("status") == "done")
    total_p   = len(priorities)
    done_t    = sum(1 for t in tasks if t.get("status") == "done")
    deferred_t = sum(1 for t in tasks if t.get("status") == "deferred")
    total_t   = len(tasks)

    priority_lines = "\n".join(
        f"  - {p.get('description', 'N/A')}: {p.get('status', '').upper()}"
        for p in priorities
    ) or "  No priority data"

    task_lines = "\n".join(
        f"  - {t.get('description', 'N/A')}: {t.get('status', '').upper()}"
        for t in tasks
    ) or "  No task data"

    prompt = f"""You are writing a 1-page executive coaching report for week of {week_start}.

CLIENT: {profile.get('role_type', 'Senior Executive')}
KNOWN FAILURE PATTERN: {profile.get('self_identified_failure_pattern', 'Not specified')}

WEEKLY DATA:
- Execution Score: {est.get('current_avg', 'N/A')}/10
- Priorities: {done_p}/{total_p} done
- Tasks: {done_t}/{total_t} done, {deferred_t} deferred
- Planning Accuracy: {pct(metrics.get('planning_accuracy'))}
- Deferral Rate: {pct(metrics.get('deferral_rate'))} (tasks + priorities combined)
- Deep Work: {friday_data.get('deep_work_hours', 'N/A')}h this week
- Primary Friction: {fpi.get('tag', 'N/A').replace('_', ' ')}
- Reflection: {friday_data.get('reflection_text') or 'None provided'}

PRIORITY OUTCOMES:
{priority_lines}

TASK OUTCOMES:
{task_lines}

{kb_context}

Write a 1-page executive coaching report. Use this exact structure with these exact section headers:

**WEEKLY ASSESSMENT**
[2-3 sentences. Name the dominant execution pattern this week. Be precise and direct — no softening, no praise, no motivational language. Reference specific numbers from the data.]

**WHAT THE DATA REVEALS**
[Exactly 4 bullet points. Each must cite a specific metric or data point. Connect the metrics to reveal the underlying operational pattern — not isolated observations but a coherent picture.]

**COACHING PERSPECTIVE**
[3 paragraphs. Each paragraph must be grounded in a specific framework from the KNOWLEDGE BASE above. Name the author and book/concept explicitly in each paragraph. Connect each framework directly to this person's specific week — not generic advice. Write with the authority and precision of an elite executive coach who has read the data carefully.]

**YOUR CHALLENGE FOR NEXT WEEK**
[One action. Specific, behavioural, implementable on Monday morning. Not a principle — an instruction. End with: "— Grounded in [Author]'s [concept]: [one sentence on why it applies here.]"]

TONE RULES:
- You are an elite executive coach — incisive, data-grounded, intellectually demanding
- Never soften. Never motivate. Never use HR language or startup platitudes
- Operate at the level of the person's actual performance reality
- Write as if this person is paying £10,000/month for your time
- Every sentence must earn its place"""

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Report generation failed: {str(e)}"


def _mock_report():
    return """**WEEKLY ASSESSMENT**

Your execution this week reflects a fractured attention architecture — strong individual output constrained by an inability to defend the conditions required for high-leverage work. An execution score of 7 with 30% priority completion is not a performance problem. It is a protection problem. The data shows you are working, but not on what matters most.

**WHAT THE DATA REVEALS**

- **Priority completion at 33%** against a 65% planning accuracy signals your task-level execution is solid, but your highest-leverage commitments are the ones collapsing — the pattern of losing the strategic to the operational.
- **Meetings as primary friction on 100% of days** means your calendar is other-directed, not self-directed. This is a structural inversion of how senior leadership should operate.
- **Deep work below 10 hours** for a role that requires strategic output represents a structural misalignment between the work that creates value and the work that fills your week.
- **15% deferral rate across tasks and priorities combined** understates the real attrition — the "partial" category is where execution quietly dies without anyone declaring a failure.

**COACHING PERSPECTIVE**

Cal Newport's concept of *deep work* is not a productivity technique — it is a professional asset that compounds. Your week shows this asset being depleted faster than it is being built. Newport's central argument is that the ability to perform cognitively demanding work without distraction is becoming rarer and more valuable simultaneously. Every hour lost to meetings this week was an hour borrowed against your future capacity. The asymmetry is not recoverable through effort — only through architecture.

Peter Drucker identified the core discipline of effective executives as *knowing where your time goes* — not how hard you work, but what the work is actually for. Your week shows the classic pattern Drucker warned against: time being allocated by inertia and demand rather than by deliberate intent. "Effective executives do not start with their tasks," Drucker wrote. "They start with their time." Your calendar this week was built by other people's priorities.

Greg McKeown's *Essentialism* frames the root cause precisely: the inability to distinguish the vital few from the trivial many results in a strategy of "everything matters," which functionally means nothing gets the protection it requires. Your deferral of the highest-leverage priority is not a time problem — it is a boundaries problem. McKeown's question — *"What is the most important thing I can do with my time and energy right now?"* — when applied honestly to your week, reveals that the answer and your actual calendar were misaligned for most of it.

**YOUR CHALLENGE FOR NEXT WEEK**

Before you open email or take any meeting on Monday morning, block Tuesday and Thursday 7–10am as non-negotiable deep work sessions in your calendar — label them "External Meeting" so they are treated as immovable. Use one session exclusively for your deferred priority. Report back on whether it was honoured. — Grounded in Newport's *Rhythmic Scheduling*: consistent, protected deep work blocks are the only reliable mechanism for reclaiming strategic execution time from a calendar that defaults to other people's demands."""
