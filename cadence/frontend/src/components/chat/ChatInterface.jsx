import { useState, useEffect, useRef } from "react";
import { api } from "../../api/client";
import { playAudio } from "../../hooks/useVoice";
import VoiceButton from "./VoiceButton";

export default function ChatInterface({ sessionType, weekStart, responseMode, voicePreference, onComplete }) {
  const [sessionId, setSessionId]   = useState(null);
  const [messages, setMessages]     = useState([]);
  const [input, setInput]           = useState("");
  const [loading, setLoading]       = useState(false);
  const [complete, setComplete]     = useState(false);
  const [extracted, setExtracted]   = useState(null);
  const [starting, setStarting]     = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    initSession();
  }, [sessionType]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function initSession() {
    setStarting(true);
    setMessages([]);
    setComplete(false);
    setExtracted(null);
    try {
      const res = await api.startConversation({ type: sessionType, week_start_date: weekStart });
      setSessionId(res.session_id);
      setMessages([{ role: "assistant", content: res.message }]);
      if (res.audio && responseMode === "voice") playAudio(res.audio);
    } catch (e) {
      setMessages([{ role: "assistant", content: "Unable to start session. Please try again." }]);
    } finally {
      setStarting(false);
    }
  }

  async function send(text) {
    if (!text.trim() || !sessionId || loading) return;
    const userMsg = text.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.sendMessage({ session_id: sessionId, message: userMsg });
      setMessages(m => [...m, { role: "assistant", content: res.message }]);
      if (res.audio && responseMode === "voice") playAudio(res.audio);
      if (res.complete) {
        setComplete(true);
        setExtracted(res.extracted);
        if (onComplete) onComplete(res.extracted);
      }
    } catch (e) {
      setMessages(m => [...m, { role: "assistant", content: "An error occurred. Please try again." }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  }

  const label = sessionType === "monday" ? "Weekly Planning" : "Friday Review";

  return (
    <div className="flex flex-col h-full" style={{ background: "#000" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-dark-border">
        <div>
          <h2 className="text-sm font-semibold text-white">{label}</h2>
          <p className="text-xs text-gray-300 mt-0.5">Week of {weekStart}</p>
        </div>
        {complete && (
          <span className="text-xs text-emerald-300 border border-emerald-700 bg-emerald-950 px-2 py-1 rounded">
            Session complete
          </span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {starting && (
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse-gold" />
            Cadence is preparing…
          </div>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} content={m.content} />
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-300 text-sm">
            <span className="flex gap-1">
              {[0,1,2].map(i => (
                <span key={i} className="w-1 h-1 rounded-full bg-gold-muted animate-pulse"
                  style={{ animationDelay: `${i * 150}ms` }} />
              ))}
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      {!complete && (
        <div className="px-5 py-4 border-t border-dark-border" style={{ background: "#000" }}>
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your response… (Enter to send)"
              rows={2}
              disabled={loading || starting}
              className="flex-1 resize-none rounded px-3 py-2.5 text-sm text-white placeholder-gray-600
                         focus:outline-none focus:border-gold-muted transition-colors border border-dark-border"
              style={{ background: "#000" }}
            />
            <VoiceButton onTranscript={t => { setInput(t); setTimeout(() => send(t), 100); }} disabled={loading || starting} />
            <button
              onClick={() => send(input)}
              disabled={!input.trim() || loading || starting}
              className="btn-gold px-4 py-2.5 self-end"
            >
              Send
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2">Shift+Enter for new line · Click mic to speak</p>
        </div>
      )}

      {complete && extracted && (
        <div className="px-5 py-4 border-t border-dark-border" style={{ background: "#0a0a0a" }}>
          <p className="text-xs text-emerald-300 mb-1">Saved successfully</p>
          <p className="text-xs text-gray-300">
            {sessionType === "monday"
              ? `${(extracted.priorities || []).length} priorities locked in for the week.`
              : "Week review captured. Head to the Report tab to generate your PDF."}
          </p>
        </div>
      )}
    </div>
  );
}

function ChatBubble({ role, content }) {
  const isAI = role === "assistant";
  return (
    <div className={`flex ${isAI ? "justify-start" : "justify-end"} animate-fade-in`}>
      <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm leading-relaxed ${
        isAI
          ? "border border-dark-border text-white"
          : "border border-gold-muted text-white"
      }`}
        style={{ background: isAI ? "#0d0d0d" : "#111" }}
      >
        {isAI && (
          <div className="flex items-center gap-1.5 mb-1.5">
            <span className="w-1 h-1 rounded-full bg-gold" />
            <span className="text-xs text-gold font-medium">Cadence</span>
          </div>
        )}
        <p className="whitespace-pre-wrap">{content.replace(/EXTRACTED:.*$/s, "").trim()}</p>
      </div>
    </div>
  );
}
