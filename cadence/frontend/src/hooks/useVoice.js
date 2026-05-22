import { useState, useRef, useCallback } from "react";

export function useVoiceInput(onResult) {
  const [listening, setListening] = useState(false);
  const [error, setError]         = useState(null);
  const recogRef = useRef(null);

  const start = useCallback(() => {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      setError("Speech recognition not supported in this browser.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SR();
    rec.continuous      = false;
    rec.interimResults  = false;
    rec.lang            = "en-US";

    rec.onresult = e => {
      const transcript = e.results[0][0].transcript;
      onResult(transcript);
    };
    rec.onerror = e => setError(e.error);
    rec.onend   = () => setListening(false);

    rec.start();
    recogRef.current = rec;
    setListening(true);
    setError(null);
  }, [onResult]);

  const stop = useCallback(() => {
    recogRef.current?.stop();
    setListening(false);
  }, []);

  return { listening, error, start, stop };
}

export function playAudio(base64Audio) {
  if (!base64Audio) return;
  const bytes = atob(base64Audio);
  const arr   = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob  = new Blob([arr], { type: "audio/mpeg" });
  const url   = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play().catch(() => {});
  audio.onended = () => URL.revokeObjectURL(url);
  return audio;
}
