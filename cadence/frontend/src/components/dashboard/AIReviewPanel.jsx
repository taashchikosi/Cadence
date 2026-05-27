import { useState } from "react";

const MATURITY_STYLE = {
  "confirmed pattern":               "text-red-300 border-red-700 bg-red-950",
  "emerging pattern":                "text-amber-300 border-amber-700 bg-amber-950",
  "early signal, not confirmed pattern": "text-gray-200 border-dark-border bg-dark-elevated",
};

export default function AIReviewPanel({ review, onGenerate, generating }) {
  const [expanded, setExpanded] = useState(true);
  if (!review && !generating) {
    return (
      <div className="card p-5 flex flex-col items-center gap-3 text-center" style={{ background: "#000" }}>
        <p className="text-gray-300 text-sm">No review generated for this week yet.</p>
        <button onClick={onGenerate} className="btn-ghost text-xs">
          Generate Weekly Review
        </button>
      </div>
    );
  }

  if (generating) {
    return (
      <div className="card p-5 flex items-center gap-3" style={{ background: "#000" }}>
        <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse-gold" />
        <span className="text-white text-sm">Generating diagnostic review…</span>
      </div>
    );
  }

  const maturityKey = review.maturity_label?.toLowerCase();
  const maturityStyle = MATURITY_STYLE[maturityKey] || MATURITY_STYLE["early signal, not confirmed pattern"];

  return (
    <div className="card overflow-hidden animate-fade-in" style={{ background: "#000" }}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-dark-elevated transition-colors"
        style={{ background: "#0a0a0a" }}
      >
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-white uppercase tracking-widest">AI Diagnostic Review</span>
          {review.week_start_date && (
            <span className="text-xs text-gray-300">Week of {review.week_start_date}</span>
          )}
        </div>
        <span className="text-gray-300 text-xs">{expanded ? "▲" : "▼"}</span>
      </button>

      {expanded && (
        <div className="p-5 space-y-5">
          {review.diagnosis && (
            <Section label="Diagnosis">
              <p className="text-sm text-white leading-relaxed">{review.diagnosis}</p>
            </Section>
          )}
          {review.evidence && (
            <Section label="Evidence">
              <div className="text-sm text-gray-100 leading-relaxed space-y-1.5 whitespace-pre-line">
                {review.evidence}
              </div>
            </Section>
          )}
          {review.intervention && (
            <Section label="Intervention">
              <div className="border-l-2 pl-4" style={{ borderColor: "#06B6D4" }}>
                <p className="text-sm text-white leading-relaxed">{review.intervention}</p>
              </div>
            </Section>
          )}
          {review.maturity_label && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-300 uppercase tracking-widest">Signal maturity</span>
              <span className={`text-xs px-2 py-0.5 rounded border ${maturityStyle}`}>
                {review.maturity_label}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-medium text-gray-300 uppercase tracking-widest mb-2">{label}</p>
      {children}
    </div>
  );
}
