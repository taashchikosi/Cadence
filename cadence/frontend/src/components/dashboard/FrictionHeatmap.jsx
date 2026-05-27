const ALL_FRICTIONS = [
  { key: "meetings",           label: "Meetings" },
  { key: "context_switching",  label: "Context Switch" },
  { key: "admin",              label: "Admin Overhead" },
  { key: "overcommitment",     label: "Overcommitment" },
  { key: "decision_avoidance", label: "Decision Avoidance" },
  { key: "reactive_work",      label: "Reactive Work" },
  { key: "unclear_priorities", label: "Unclear Priorities" },
];

function heatStyle(isPrimary, freq) {
  if (!isPrimary) return { background: "#0C0F1E", border: "1px solid #1E2245" };
  const t = Math.max(0, Math.min(1, (freq || 50) / 100));
  // Interpolate purple → amber → orange → red based on intensity
  if (t < 0.4) {
    const a = 0.3 + t * 0.5;
    return { background: `rgba(168,85,247,${a})`, border: "1px solid rgba(168,85,247,0.5)" };
  }
  if (t < 0.7) {
    const a = 0.45 + (t - 0.4) * 0.8;
    return { background: `rgba(249,115,22,${a})`, border: "1px solid rgba(249,115,22,0.6)" };
  }
  const a = 0.6 + (t - 0.7) * 0.7;
  return { background: `rgba(239,68,68,${a})`, border: "1px solid rgba(239,68,68,0.65)" };
}

export default function FrictionHeatmap({ history = [] }) {
  if (!history.length) return (
    <div className="h-40 flex items-center justify-center text-gray-600 text-sm">
      No data yet
    </div>
  );

  const weeks = [...history].reverse();

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto">
        <table className="text-xs" style={{ borderSpacing: "3px", borderCollapse: "separate" }}>
          <thead>
            <tr>
              <th className="text-left text-gray-600 font-normal pr-4 pb-2 whitespace-nowrap w-36" />
              {weeks.map((w, i) => (
                <th key={i} className="text-center text-gray-600 font-normal pb-2 min-w-[2.5rem]">
                  {w.week_start_date ? w.week_start_date.slice(5) : "—"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ALL_FRICTIONS.map(({ key, label }) => (
              <tr key={key}>
                <td className="text-gray-500 pr-4 py-0.5 whitespace-nowrap">{label}</td>
                {weeks.map((w, i) => {
                  const fpi = w.friction_pattern_index || {};
                  const isPrimary = fpi.tag === key;
                  const freq = isPrimary ? (fpi.frequency_pct || 50) : 0;
                  const style = heatStyle(isPrimary, freq);

                  return (
                    <td key={i} className="py-0.5">
                      <div
                        title={isPrimary ? `Primary friction — ${freq}% of days` : label}
                        style={{
                          width: 32,
                          height: 18,
                          borderRadius: 3,
                          margin: "0 auto",
                          ...style,
                          transition: "all 0.2s",
                        }}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-2 pt-1">
        <span className="text-gray-600 text-[10px]">Low Impact</span>
        <div style={{
          flex: 1,
          height: 6,
          borderRadius: 3,
          background: "linear-gradient(to right, rgba(168,85,247,0.4), rgba(249,115,22,0.7), rgba(239,68,68,0.9))",
        }} />
        <span className="text-gray-600 text-[10px]">High Impact</span>
      </div>
    </div>
  );
}
