"""
Conversational AI service.
Manages back-and-forth sessions for Monday planning and Friday review.
Coach persona is injected from voice profile (male/female).
"""
import os
import json
import anthropic
from rag_service import retrieve_relevant_chunks, format_rag_context

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

FEMALE_SYSTEM = """You are an elite chief of staff and operational strategist — calm, composed, intellectually precise. Your name is Cadence.

You speak with clarity and intentional pacing. You are deeply organized and strategically minded. You are slightly warm but never nurturing. You prioritize operational clarity over energy or motivation.

AVOID: therapist energy, soft/nurturing tone, corporate HR language, motivational coaching, excessive friendliness, high-energy startup language.

You make the user feel: understood operationally, mentally clearer, more structured, and more intentional."""

MALE_SYSTEM = """You are an elite executive advisor and strategic operator — calm, authoritative, analytically precise. Your name is Cadence.

You speak in concise, structured thoughts. You understand execution, leverage, and decision-making at a high level. You are slightly challenging when necessary. You never sound like a productivity influencer or motivational speaker.

AVOID: motivational speaker energy, aggressive authority, startup language, excessive enthusiasm, therapy-like warmth.

You make the user feel: calm, focused, strategically aware, and operationally capable."""

MONDAY_CONTEXT = """
You are conducting a structured Monday planning session. Your goal is to collect:
1. Top 3–5 priorities for the week (specific, outcome-oriented — not vague goals)
2. Estimated deep work hours available this week
3. Predicted main derailers (what might prevent completion)

Ask one thing at a time. Probe for specificity when priorities are vague. Once you have all information, summarize clearly and ask for confirmation. When the user confirms, output a JSON block EXACTLY like this on a new line:
EXTRACTED:{"priorities":["...","..."],"deep_work_hours":0,"derailers":["..."]}
"""

FRIDAY_CONTEXT = """
You are conducting a structured Friday review session. Your goal is to collect:
1. Outcome of each priority (done / partial / deferred / dropped) with brief explanation
2. Time allocation this week across: deep work, admin, meetings, reactive work, learning, low-leverage tasks (in hours)
3. Weekly execution score (1–10) — how well they executed, not how they feel about it
4. A brief honest reflection on what determined this week's outcome

Ask one area at a time. Be direct about what you observe. Do not soften. Once complete, summarize and ask for confirmation. When confirmed, output:
EXTRACTED:{"priority_outcomes":{"p1":"done","p2":"partial"},"time_allocation":{"deep_work":0,"admin":0,"meetings":0,"reactive":0,"learning":0,"low_leverage":0},"execution_score":0,"reflection":"..."}
"""


def get_system_prompt(voice, session_type, user_profile, rag_context=""):
    base = FEMALE_SYSTEM if voice == "female" else MALE_SYSTEM
    session_ctx = MONDAY_CONTEXT if session_type == "monday" else FRIDAY_CONTEXT

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
    if not ANTHROPIC_API_KEY:
        return _mock_response(session_type, len(messages))

    rag_chunks = retrieve_relevant_chunks(query_text or session_type, top_k=3)
    rag_context = format_rag_context(rag_chunks)

    system = get_system_prompt(voice, session_type, user_profile, rag_context)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=512,
            system=system,
            messages=messages,
        )
        return response.content[0].text
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
    name = user_profile.get("role_type", "")
    if not ANTHROPIC_API_KEY:
        if session_type == "monday":
            return "Good morning. Let's set your week. What are the top priorities you're committing to this week — specific outcomes, not activities?"
        return "Let's review your week. Walk me through each priority — what was the outcome and what drove it?"

    rag_chunks = retrieve_relevant_chunks(session_type, top_k=2)
    rag_context = format_rag_context(rag_chunks)
    system = get_system_prompt(voice, session_type, user_profile, rag_context)

    prompt = (
        f"Open this {session_type} session. Greet the user concisely. "
        f"{'Context from recent weeks: ' + recent_context if recent_context else ''}"
        "Then ask the first question. Keep it under 3 sentences total."
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    except Exception:
        if session_type == "monday":
            return "Good morning. Let's set your week. What are the top priorities you're committing to?"
        return "Let's close your week. Walk me through each priority — what was the outcome?"


def _mock_response(session_type, message_count):
    if session_type == "monday":
        responses = [
            "Let's set your week. What are the top 3–5 priorities you're committing to? Be specific about the outcome, not just the activity.",
            "Good. What's priority two?",
            "Understood. And your third?",
            "How many hours of deep, uninterrupted work do you realistically have available this week?",
            "What's the most likely thing that will prevent you from completing these priorities?",
            "To confirm: I have your priorities, your estimated deep work hours, and your predicted derailer. Shall I lock this in?\n\nEXTRACTED:{\"priorities\":[\"Complete Q3 report\"],\"deep_work_hours\":12,\"derailers\":[\"meetings\"]}",
        ]
    else:
        responses = [
            "Let's review your week. Walk me through priority one — what was the outcome?",
            "And priority two?",
            "How did you allocate your time this week? Give me hours across: deep work, meetings, admin, reactive work, learning, and low-leverage tasks.",
            "On a scale of 1–10, how effectively did you execute this week — not how you feel about it, but how well you operated?",
            "What single factor most determined this week's outcome?",
            "Here's what I have from this week's review. Shall I lock this in?\n\nEXTRACTED:{\"priority_outcomes\":{\"p1\":\"done\",\"p2\":\"partial\"},\"time_allocation\":{\"deep_work\":8,\"admin\":4,\"meetings\":10,\"reactive\":8,\"learning\":2,\"low_leverage\":3},\"execution_score\":6,\"reflection\":\"Meetings consumed the week.\"}",
        ]
    idx = min(message_count // 2, len(responses) - 1)
    return responses[idx]
