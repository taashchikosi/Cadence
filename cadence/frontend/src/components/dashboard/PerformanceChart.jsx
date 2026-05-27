import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";

const GOLD = "#D4A520";
const RED  = "#ef4444";
const TEAL = "#2dd4bf";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-elevated border border-dark-border rounded-lg px-3 py-2.5 text-xs shadow-xl">
      <p className="text-gray-400 mb-2 font-medium">Week of {label}</p>
      {payload.map((p, i) => p.value != null && (
        <div key={i} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-400">{p.name}:</span>
          <span className="text-white font-medium">{p.value.toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

export default function PerformanceChart({ history = [] }) {
  if (!history.length) return (
    <div className="h-56 flex items-center justify-center text-gray-600 text-sm">
      No historical data yet
    </div>
  );

  const data = [...history].reverse().map(w => ({
    week:     w.week_start_date ? w.week_start_date.slice(5) : "—",
    score:    w.avg_execution_score != null ? +(w.avg_execution_score    * 10).toFixed(1)  : null,
    planning: w.planning_accuracy  != null ? +(w.planning_accuracy      * 100).toFixed(1) : null,
    deferral: w.deferral_rate      != null ? +(w.deferral_rate          * 100).toFixed(1) : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false} />
        <XAxis dataKey="week" tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false}
          interval={data.length > 6 ? 1 : 0} />
        <YAxis tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false}
          domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tickFormatter={v => `${v}%`} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={80} stroke={GOLD} strokeOpacity={0.12} strokeDasharray="4 4" />
        <ReferenceLine y={50} stroke="#333"  strokeOpacity={0.3}  strokeDasharray="4 4" />

        <Line dataKey="score"    name="Execution Score"   stroke={GOLD} strokeWidth={2.5} type="monotone"
          dot={{ fill: GOLD, r: 3, strokeWidth: 0 }} activeDot={{ r: 5, fill: GOLD }} />
        <Line dataKey="planning" name="Planning Accuracy" stroke={TEAL} strokeWidth={1.5} type="monotone"
          dot={false} strokeDasharray="6 3" />
        <Line dataKey="deferral" name="Deferral Rate"     stroke={RED}  strokeWidth={1.5} type="monotone"
          dot={false} strokeDasharray="4 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}
