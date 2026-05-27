import { useVoiceInput } from "../../hooks/useVoice";

export default function VoiceButton({ onTranscript, disabled }) {
  const { listening, error, start, stop } = useVoiceInput(onTranscript);

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        onClick={listening ? stop : start}
        disabled={disabled}
        className={`w-10 h-10 rounded-full border flex items-center justify-center transition-all ${
          listening
            ? "border-gold bg-gold-muted text-gold animate-pulse-gold"
            : "border-dark-border bg-dark-elevated text-gray-300 hover:border-gold-muted hover:text-white"
        } disabled:opacity-30`}
        title={listening ? "Stop recording" : "Speak"}
      >
        <MicIcon listening={listening} />
      </button>
      {error && <span className="text-red-400 text-xs">{error}</span>}
    </div>
  );
}

function MicIcon({ listening }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}
