"""
ElevenLabs text-to-speech service.
Falls back silently if API key is not set.
"""
import os
import requests

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

VOICE_IDS = {
    "female": os.environ.get("ELEVENLABS_FEMALE_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),  # Rachel
    "male":   os.environ.get("ELEVENLABS_MALE_VOICE_ID",   "pNInz6obpgDQGcFmaJgB"),  # Adam
}

VOICE_SETTINGS = {
    "stability":        0.65,
    "similarity_boost": 0.80,
    "style":            0.20,
    "use_speaker_boost": True,
}


def synthesize(text, voice="female"):
    if not ELEVENLABS_API_KEY:
        return None, "ELEVENLABS_API_KEY not configured"

    voice_id = VOICE_IDS.get(voice, VOICE_IDS["female"])
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    try:
        resp = requests.post(
            url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": VOICE_SETTINGS,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            import base64
            audio_b64 = base64.b64encode(resp.content).decode("utf-8")
            return audio_b64, None
        return None, f"ElevenLabs error {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)
