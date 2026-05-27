import { useState, useRef, useEffect } from "react";
import { api } from "../../api/client";

export default function SettingsPanel({ profile, onUpdate }) {
  const [open, setOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  async function save(patch) {
    setSaving(true);
    try {
      const updated = await api.saveProfile({ ...profile, ...patch });
      onUpdate({ ...profile, ...patch });
    } catch (e) {
      // silently fail
    } finally {
      setSaving(false);
    }
  }

  const mode  = profile?.response_mode   || "text";
  const voice = profile?.voice_preference || "female";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-8 h-8 flex items-center justify-center rounded text-gray-300 hover:text-white hover:bg-dark-elevated transition-colors"
        title="Settings"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="8" r="2.5" />
          <path d="M8 1v1.5M8 13.5V15M15 8h-1.5M2.5 8H1M12.95 3.05l-1.06 1.06M4.11 11.89l-1.06 1.06M12.95 12.95l-1.06-1.06M4.11 4.11l-1.06-1.06" />
        </svg>
      </button>

      {open && (
        <div className="absolute right-0 top-10 w-56 bg-dark-surface border border-dark-border rounded-lg shadow-xl z-50 p-4 space-y-4">
          <p className="text-xs font-semibold text-gold uppercase tracking-wider">Preferences</p>

          <div>
            <p className="text-xs text-gray-300 mb-2">Response mode</p>
            <div className="flex gap-2">
              {["text", "voice"].map(m => (
                <button
                  key={m}
                  onClick={() => save({ response_mode: m })}
                  className={`flex-1 py-1.5 rounded text-xs font-medium transition-colors capitalize ${
                    mode === m
                      ? "bg-gold text-black"
                      : "bg-dark-elevated text-gray-200 hover:text-white"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {mode === "voice" && (
            <div>
              <p className="text-xs text-gray-300 mb-2">Voice</p>
              <div className="flex gap-2">
                {["female", "male"].map(v => (
                  <button
                    key={v}
                    onClick={() => save({ voice_preference: v })}
                    className={`flex-1 py-1.5 rounded text-xs font-medium transition-colors capitalize ${
                      voice === v
                        ? "bg-gold text-black"
                        : "bg-dark-elevated text-gray-200 hover:text-white"
                    }`}
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>
          )}

          {saving && <p className="text-xs text-gray-300">Saving…</p>}
        </div>
      )}
    </div>
  );
}
