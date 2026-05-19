import { useState } from "react";

export default function ReviewHistory({ reviews }) {
  const [expanded, setExpanded] = useState(null);

  if (!reviews || reviews.length === 0) {
    return <p className="text-slate-500 text-sm">No past reviews yet.</p>;
  }

  return (
    <div className="space-y-3">
      {reviews.map((r) => (
        <div key={r.id} className="border border-slate-700 rounded-lg overflow-hidden">
          <button
            type="button"
            onClick={() => setExpanded(expanded === r.id ? null : r.id)}
            className="w-full flex items-center justify-between px-4 py-3 bg-slate-800 hover:bg-slate-750 text-left transition-colors"
          >
            <div>
              <span className="text-sm font-medium text-slate-200">Week of {r.week_start_date}</span>
              {r.maturity_label && (
                <span className="ml-3 text-xs text-slate-500">{r.maturity_label}</span>
              )}
            </div>
            <span className="text-slate-600 text-sm">{expanded === r.id ? "▲" : "▼"}</span>
          </button>

          {expanded === r.id && (
            <div className="p-4 space-y-4 bg-slate-900">
              {r.diagnosis && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Diagnosis</p>
                  <p className="text-sm text-slate-300 leading-relaxed">{r.diagnosis}</p>
                </div>
              )}
              {r.evidence && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Evidence</p>
                  <div className="text-sm text-slate-400 whitespace-pre-line leading-relaxed">{r.evidence}</div>
                </div>
              )}
              {r.intervention && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Intervention</p>
                  <div className="bg-slate-800 border border-slate-700 rounded p-3">
                    <p className="text-sm text-slate-200">{r.intervention}</p>
                  </div>
                </div>
              )}
              <p className="text-xs text-slate-600">Generated {r.created_at}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
