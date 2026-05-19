export default function AIWeeklyReview({ review }) {
  if (!review) return null;

  const maturityClass =
    review.maturity_label?.toLowerCase().includes("confirmed")
      ? "text-red-400 bg-red-950 border-red-800"
      : review.maturity_label?.toLowerCase().includes("emerging")
      ? "text-amber-400 bg-amber-950 border-amber-800"
      : "text-slate-400 bg-slate-800 border-slate-700";

  return (
    <div className="border border-slate-700 rounded-lg overflow-hidden">
      <div className="bg-slate-800 px-5 py-3 border-b border-slate-700 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">
          AI Operational Review
        </h3>
        {review.week_start_date && (
          <span className="text-xs text-slate-500">Week of {review.week_start_date}</span>
        )}
      </div>

      <div className="p-5 space-y-5">
        {review.diagnosis && (
          <Section label="Diagnosis">
            <p className="text-slate-200 text-sm leading-relaxed">{review.diagnosis}</p>
          </Section>
        )}

        {review.evidence && (
          <Section label="Evidence">
            <div className="text-slate-300 text-sm leading-relaxed whitespace-pre-line">
              {review.evidence}
            </div>
          </Section>
        )}

        {review.intervention && (
          <Section label="Intervention">
            <div className="bg-slate-800 border border-slate-600 rounded p-3">
              <p className="text-slate-200 text-sm leading-relaxed">{review.intervention}</p>
            </div>
          </Section>
        )}

        {review.maturity_label && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Signal maturity:</span>
            <span className={`text-xs font-medium px-2 py-1 rounded border ${maturityClass}`}>
              {review.maturity_label}
            </span>
          </div>
        )}

        {review.patterns && review.patterns.length > 0 && (
          <Section label="Detected patterns">
            <div className="space-y-2">
              {review.patterns.map((p, i) => (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <div className="flex-1">
                    <span className="text-slate-300 font-medium">{p.pattern_name}</span>
                    <span className="text-slate-600 mx-2">·</span>
                    <span className="text-slate-500 text-xs">{p.maturity}</span>
                  </div>
                  <span className="text-slate-500 text-xs shrink-0">
                    {Math.round(p.confidence_score * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      {children}
    </div>
  );
}
