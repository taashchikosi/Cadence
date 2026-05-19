export default function MetricsDashboard({ metrics }) {
  if (!metrics) return <p className="text-slate-500 text-sm">No metrics available for this week.</p>;

  const {
    priority_completion_rate,
    deep_work_frequency,
    friction_pattern_index,
    execution_score_trend,
    deferral_rate,
    planning_accuracy,
  } = metrics;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <MetricCard
        label="Priority Completion"
        value={pct(priority_completion_rate)}
        sub="of weekly priorities done"
        color={rateColor(priority_completion_rate)}
      />
      <MetricCard
        label="Deep Work Frequency"
        value={deep_work_frequency != null ? `${deep_work_frequency}` : "—"}
        sub="blocks / day avg"
        color={dwColor(deep_work_frequency)}
      />
      <MetricCard
        label="Deferral Rate"
        value={pct(deferral_rate)}
        sub="tasks deferred"
        color={inverseColor(deferral_rate)}
      />
      <MetricCard
        label="Planning Accuracy"
        value={pct(planning_accuracy)}
        sub="planned tasks completed"
        color={rateColor(planning_accuracy)}
      />
      <MetricCard
        label="Execution Score"
        value={execution_score_trend ? `${execution_score_trend.current_avg}/10` : "—"}
        sub={execution_score_trend ? `Trend: ${execution_score_trend.trend}` : "No data"}
        color={trendColor(execution_score_trend?.trend)}
      />
      <MetricCard
        label="Primary Friction"
        value={friction_pattern_index ? friction_pattern_index.tag?.replace(/_/g, " ") : "—"}
        sub={friction_pattern_index ? `${friction_pattern_index.frequency_pct}% of days` : "No friction logged"}
        color="text-slate-300"
      />
    </div>
  );
}

function MetricCard({ label, value, sub, color }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>{value ?? "—"}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  );
}

function pct(val) {
  if (val == null) return "—";
  return `${Math.round(val * 100)}%`;
}

function rateColor(val) {
  if (val == null) return "text-slate-400";
  if (val >= 0.75) return "text-emerald-400";
  if (val >= 0.5) return "text-amber-400";
  return "text-red-400";
}

function inverseColor(val) {
  if (val == null) return "text-slate-400";
  if (val <= 0.2) return "text-emerald-400";
  if (val <= 0.4) return "text-amber-400";
  return "text-red-400";
}

function dwColor(val) {
  if (val == null) return "text-slate-400";
  if (val >= 2) return "text-emerald-400";
  if (val >= 1) return "text-amber-400";
  return "text-red-400";
}

function trendColor(trend) {
  if (!trend) return "text-slate-400";
  if (trend === "improving") return "text-emerald-400";
  if (trend === "declining") return "text-red-400";
  return "text-slate-300";
}
