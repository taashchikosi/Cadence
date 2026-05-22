import os
import re
from openai import OpenAI

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")


def _client():
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def generate_weekly_review(prompt):
    if not DEEPSEEK_API_KEY:
        return _mock_review()
    try:
        resp = _client().chat.completions.create(
            model="deepseek-chat",
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_review(resp.choices[0].message.content)
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
        "raw_response": "[Mock review — set DEEPSEEK_API_KEY to enable real reviews]",
    }
