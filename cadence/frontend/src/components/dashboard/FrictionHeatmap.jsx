const ALL_FRICTIONS = [
  { key: "meetings",           label: "Meetings" },
  { key: "context_switching",  label: "Context Switch" },
  { key: "admin",              label: "Admin Overhead" },
  { key: "overcommitment",     label: "Overcommitment" },
  { key: "decision_avoidance", label: "Decision Avoidance" },
  { key: "reactive_work",      label: "Reactive Work" },
  { key: "unclear_priorities", label: "Unclear Priorities" },
];

export default function FrictionHeatmap({ history = [] }) {
  if (!history.length) return (
    <div className="h-40 flex items-center justify-center text-gray-600 text-sm">
      No data yet
    </div>
  );

  const weeks = [...history].reverse();

  return (
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
                const freq = isPrimary ? (fpi.frequency_pct || 0) : 0;
                const opacity = isPrimary ? Math.max(0.35, freq / 100) : 0;

                return (
                  <td key={i} className="py-0.5">
                    <div
                      title={isPrimary ? `Primary friction — ${freq}% of days` : label}
                      style={{
                        width: 32,
                        height: 18,
                        borderRadius: 3,
                        margin: "0 auto",
                        background: isPrimary
                          ? `rgba(212,165,32,${opacity})`
                          : "#0d0d0d",
                        border: isPrimary
                          ? "1px solid rgba(212,165,32,0.4)"
                          : "1px solid #1a1a1a",
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
  );
}
