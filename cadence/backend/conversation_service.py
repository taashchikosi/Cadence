"""
Conversational AI service.
Manages back-and-forth sessions for the combined Friday weekly review + planning session.
Coach persona is injected from voice profile (male/female).
"""
import os
import json
from openai import OpenAI
from rag_service import retrieve_relevant_chunks, format_rag_context

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def _client():
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


FEMALE_SYSTEM = """You are an elite chief of staff and operational strategist — calm, composed, intellectually precise. Your name is Cadence.

You speak with clarity and intentional pacing. You are deeply organized and strategically minded. You are slightly warm but never nurturing. You prioritize operational clarity over energy or motivation.

AVOID: therapist energy, soft/nurturing tone, corporate HR language, motivational coaching, excessive friendliness, high-energy startup language.

You make the user feel: understood operationally, mentally clearer, more structured, and more intentional."""

MALE_SYSTEM = """You are an elite executive advisor and strategic operator — calm, authoritative, analytically precise. Your name is Cadence.

You speak in concise, structured thoughts. You understand execution, leverage, and decision-making at a high level. You are slightly challenging when necessary. You never sound like a productivity influencer or motivational speaker.

AVOID: motivational speaker energy, aggressive authority, startup language, excessive enthusiasm, therapy-like warmth.

You make the user feel: calm, focused, strategically aware, and operationally capable."""

WEEKLY_CONTEXT = """
You are conducting a weekly operational review and planning session. This is the most important conversation of the week.

Complete PART 1 fully before moving to PART 2. Ask one question at a time. Press for specificity.

PART 1 — THIS WEEK'S REVIEW (collect in this order):
1. Their 3 top priorities this week — for each one: outcome (done / partial / deferred) and the honest reason why
2. Their 10 key tasks this week — ask them to list all tasks they worked on, then get a status for each (done / partial / deferred). Make sure you collect exactly 10 tasks with statuses.
3. Execution score 1–10: operational quality of the week, not how they feel about it
4. Deep work: how many hours of focused, uninterrupted work did they actually get this week?
5. Primary friction: what was the single biggest source of interruption or lost time?
   (Pin them to one of: meetings / context_switching / admin / overcommitment / decision_avoidance / reactive_work / unclear_priorities)
6. Reflection: what single factor most determined this week's outcome?

PART 2 — NEXT WEEK'S PLAN:
7. Top 3 priorities for next week — specific outcome-oriented commitments, not activities
8. How many hours of deep work can they realistically protect next week?

Rules:
- Do not soften. Do not reassure. Do not add motivational language.
- When BOTH parts are complete, give a 2-sentence summary and ask for confirmation.
- When confirmed, output EXACTLY this block (fill in all values, keep all 10 tasks):
EXTRACTED:{"review":{"execution_score":0,"priorities":[{"description":"...","status":"done"},{"description":"...","status":"partial"},{"description":"...","status":"deferred"}],"tasks":[{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"},{"description":"...","status":"done"}],"deep_work_hours":0,"friction_tag":"meetings","reflection":"..."},"planning":{"priorities":["...","...","..."],"deep_work_hours":0}}
"""


def get_system_prompt(voice, session_type, user_profile, rag_context=""):
    base = FEMALE_SYSTEM if voice == "female" else MALE_SYSTEM
    session_ctx = WEEKLY_CONTEXT

    profile_ctx = ""
    if user_profile:
        profile_ctx = f"""
## USER PROFILE
- Role: {user_profile.get('role_type', 'Not specified')}
- Known failure pattern: {user_profile.get('self_identified_failure_pattern', 'Not specified')}
- Goals: {user_profile.get('top_3_active_goals', 'Not specified')}
- Typical week: {user_profile.get('typical_week_structure', 'Not specified')}
"""

    return base + "\n\n" + session_ctx + profile_ctx + rag_context


def chat(messages, voice, session_type, user_profile, query_text=""):
    if not DEEPSEEK_API_KEY:
        return _mock_response(session_type, len(messages))

    rag_chunks = retrieve_relevant_chunks(query_text or session_type, top_k=3)
    rag_context = format_rag_context(rag_chunks)
    system = get_system_prompt(voice, session_type, user_profile, rag_context)

    try:
        resp = _client().chat.completions.create(
            model="deepseek-chat",
            max_tokens=512,
            messages=[{"role": "system", "content": system}] + messages,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"I encountered an issue: {str(e)}. Please try again."


def extract_data(response_text):
    """Parse the EXTRACTED JSON block from the AI response."""
    if "EXTRACTED:" not in response_text:
        return None
    try:
        json_str = response_text.split("EXTRACTED:")[1].strip().split("\n")[0]
        return json.loads(json_str)
    except Exception:
        return None


def opening_message(voice, session_type, user_profile, recent_context=""):
    """Generate the opening message for a new conversation session."""
    if not DEEPSEEK_API_KEY:
        return "It's Friday. Let's close this week and set the next one. Walk me through each of your priorities — what was the outcome, and what drove it?"

    rag_chunks = retrieve_relevant_chunks(session_type, top_k=2)
    rag_context = format_rag_context(rag_chunks)
    system = get_system_prompt(voice, session_type, user_profile, rag_context)

    prompt = (
        "It's Friday afternoon. Open the weekly review and planning session. "
        "Greet the user briefly — no more than 2 sentences. "
        f"{'Note from last week: ' + recent_context if recent_context else ''} "
        "Then ask about the first priority outcome. Keep it tight."
    )

    try:
        resp = _client().chat.completions.create(
            model="deepseek-chat",
            max_tokens=200,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content
    except Exception:
        return "It's Friday. Let's close this week and set the next one. Walk me through each of your priorities — what was the outcome, and what drove it?"


def _mock_response(session_type, message_count):
    responses = [
        "It's Friday. Let's close this week properly. Walk me through priority one — what was the outcome and what drove it?",
        "Got it. Priority two?",
        "And priority three?",
        "Now let's go through your tasks. List the 10 key things you worked on this week — I'll take a status on each.",
        "Execution score for the week — 1 to 10. Operational quality, not how you feel about it.",
        "How many hours of focused, uninterrupted deep work did you actually get this week?",
        "What was the single biggest source of interruption or lost time — meetings, context switching, admin, overcommitment, decision avoidance, reactive work, or unclear priorities?",
        "What single factor most determined this week's outcome?",
        "Next week. Three priorities — specific, outcome-oriented commitments. What's first?",
        "How many hours of deep work can you realistically protect next week?",
        "Here's what I have. Two priorities done, one deferred. Eight tasks done, two deferred. Execution at 7. Deep work short at 8 hours. Meetings as the primary friction. Confirm?\n\nEXTRACTED:{\"review\":{\"execution_score\":7,\"priorities\":[{\"description\":\"Close Series A lead investor\",\"status\":\"done\"},{\"description\":\"Finalise product roadmap for Q3\",\"status\":\"done\"},{\"description\":\"Hire VP Engineering\",\"status\":\"deferred\"}],\"tasks\":[{\"description\":\"Investor deck revision\",\"status\":\"done\"},{\"description\":\"Partner intro calls x3\",\"status\":\"done\"},{\"description\":\"Q3 roadmap workshop\",\"status\":\"done\"},{\"description\":\"Engineering interviews\",\"status\":\"deferred\"},{\"description\":\"Board update memo\",\"status\":\"done\"},{\"description\":\"Pricing model review\",\"status\":\"done\"},{\"description\":\"GTM strategy draft\",\"status\":\"done\"},{\"description\":\"1:1s with direct reports\",\"status\":\"done\"},{\"description\":\"OKR calibration\",\"status\":\"partial\"},{\"description\":\"Competitor analysis\",\"status\":\"deferred\"}],\"deep_work_hours\":8,\"friction_tag\":\"meetings\",\"reflection\":\"Investor process consumed protected morning blocks.\"},\"planning\":{\"priorities\":[\"Close VP Eng hire\",\"Finalise Series A term sheet\",\"Ship roadmap to team\"],\"deep_work_hours\":12}}",
    ]
    idx = min(message_count // 2, len(responses) - 1)
    return responses[idx]
