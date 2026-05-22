import os
import re
import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")


def generate_weekly_review(prompt):
    if not ANTHROPIC_API_KEY:
        return _mock_review()
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_review(msg.content[0].text)
    except Exception as e:
        return {**_mock_review(), "error": str(e)}


def parse_review(text):
    result = {"raw_response": text, "diagnosis": "", "evidence": "", "intervention": "", "maturity_label": ""}
    patterns = {
        "diagnosis":    r"\*\*DIAGNOSIS\*\*\s*(.*?)(?=\*\*EVIDENCE\*\*|\Z)",
        "evidence":     r"\*\*EVIDENCE\*\*\s*(.*?)(?=\*\*INTERVENTION\*\*|\Z)",
        "intervention": r"\*\*INTERVENTION\*\*\s*(.*?)(?=\*\*MATURITY LABEL\*\*|\Z)",
        "maturity_label": r"\*\*MATURITY LABEL\*\*\s*(.*?)(?=\*\*|\Z)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            result[key] = m.group(1).strip()
    return result


def _mock_review():
    return {
        "diagnosis": "Planning Inflation combined with Depth Deprivation is the dominant operational failure this week. Task volume exceeds execution capacity while protected deep work remains structurally absent.",
        "evidence": (
            "- Planning accuracy below 50%: fewer than half of planned tasks reached completion.\n"
            "- Deep work frequency under 1 block/day — insufficient for complex strategic deliverables. (Deep Work, Newport)\n"
            "- Deferral rate exceeding 35%: a structural pattern, not a one-off disruption.\n"
            "- Primary friction tag indicates a recurring systemic issue, not random variation.\n"
            "- All three stated priorities incomplete by Friday — the stated and operative priority lists have diverged. (Essentialism, McKeown)"
        ),
        "intervention": "Monday: reduce your daily task list to a hard ceiling of 3 items. Block two 90-minute deep work sessions before 11am on Monday and Wednesday. These are non-negotiable — no meetings scheduled against them.",
        "maturity_label": "Emerging pattern",
        "raw_response": "[Mock review — set ANTHROPIC_API_KEY to enable real reviews]",
    }
