import os
import re

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def generate_review(prompt):
    if not ANTHROPIC_API_KEY:
        return _mock_review()

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text
        return parse_review(raw)
    except Exception as e:
        return {"error": str(e), **_mock_review()}


def parse_review(text):
    sections = {
        "diagnosis": "",
        "evidence": "",
        "intervention": "",
        "maturity_label": "",
        "raw_response": text
    }

    patterns = {
        "diagnosis": r"\*\*DIAGNOSIS\*\*\s*(.*?)(?=\*\*EVIDENCE\*\*|\Z)",
        "evidence": r"\*\*EVIDENCE\*\*\s*(.*?)(?=\*\*INTERVENTION\*\*|\Z)",
        "intervention": r"\*\*INTERVENTION\*\*\s*(.*?)(?=\*\*MATURITY LABEL\*\*|\Z)",
        "maturity_label": r"\*\*MATURITY LABEL\*\*\s*(.*?)(?=\*\*|\Z)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections


def _mock_review():
    return {
        "diagnosis": "Planning Inflation combined with Depth Deprivation is the dominant operational failure pattern this week. Task volume consistently exceeds execution capacity, while deep work blocks remain below the threshold required for complex work.",
        "evidence": (
            "- Planning accuracy is below 50%, indicating more tasks are planned than can realistically be completed.\n"
            "- Deep work frequency averages under 1 block per day, insufficient for sustained progress on strategic priorities.\n"
            "- Deferral rate exceeds 30%, with recurring tasks appearing across multiple days.\n"
            "- Execution scores are trending downward week-over-week.\n"
            "- Primary friction tag indicates a structural issue, not a one-off disruption."
        ),
        "intervention": "On Monday, cap your daily task list to 3 items maximum. Block two 90-minute deep work sessions before 12pm and treat them as non-negotiable. Do not schedule meetings before 11am.",
        "maturity_label": "Emerging pattern",
        "raw_response": "[Mock review — ANTHROPIC_API_KEY not set]"
    }
