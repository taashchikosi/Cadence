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
You are conducting a combined Friday afternoon review and planning session. This is the most important operational conversation of the week.

You will run this in two parts — complete Part 1 fully before moving to Part 2.

PART 1 — WEEK REVIEW:
Collect the following, one area at a time:
1. Outcome of each stated priority this week (done / partial / deferred / dropped) with a brief honest explanation
2. Time allocation across: deep work, admin, meetings, reactive work, learning, low-leverage tasks (in hours)
3. Execution score (1–10) — operational execution quality, not how they feel about the week
4. A candid reflection: what single factor most determined this week's outcome?

PART 2 — NEXT WEEK PLANNING:
Transition naturally. Collect:
1. Top 3–5 priorities for next week — specific, outcome-oriented commitments (not activities)
2. Estimated deep work hours available
3. Predicted main derailers

Rules:
- Ask one thing at a time
- Probe for specificity when answers are vague or generic
- Do not soften findings or offer reassurance
- Once BOTH parts are complete, give a clean summary and ask for confirmation
- When the user confirms, output EXACTLY this on a new line:
EXTRACTED:{"review":{"priority_outcomes":{"p1":"done","p2":"partial","p3":"deferred"},"time_allocation":{"deep_work":0,"admin":0,"meetings":0,"reactive":0,"learning":0,"low_leverage":0},"execution_score":0,"reflection":"..."},"planning":{"priorities":["...","..."],"deep_work_hours":0,"derailers":["..."]}}
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
        "It's Friday. Let's close this week and set the next one. Walk me through priority one — what was the outcome and what drove it?",
        "Understood. And priority two?",
        "How did you allocate your time this week? Give me hours across: deep work, meetings, admin, reactive work, learning, and low-leverage tasks.",
        "Execution score for the week — 1 to 10. Operational quality, not how you feel about it.",
        "What single factor most determined this week's outcome?",
        "Good. Now next week. What are the 3–5 priorities you're committing to? Specific outcomes, not activities.",
        "What's priority two?",
        "How many hours of protected deep work do you realistically have available?",
        "What's most likely to derail completion?",
        "Here's what I have. Shall I lock in the review and next week's plan?\n\nEXTRACTED:{\"review\":{\"priority_outcomes\":{\"p1\":\"done\",\"p2\":\"partial\",\"p3\":\"deferred\"},\"time_allocation\":{\"deep_work\":8,\"admin\":4,\"meetings\":10,\"reactive\":8,\"learning\":2,\"low_leverage\":3},\"execution_score\":6,\"reflection\":\"Meetings consumed the week.\"},\"planning\":{\"priorities\":[\"Close Series A lead\",\"Finalise pricing model\",\"Hire VP Eng\"],\"deep_work_hours\":12,\"derailers\":[\"meetings\"]}}",
    ]
    idx = min(message_count // 2, len(responses) - 1)
    return responses[idx]
