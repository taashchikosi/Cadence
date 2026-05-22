import {
  ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";

const GOLD = "#C9A84C";
const GOLD_L = "#E5C47255";
const RED = "#ef4444";

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-elevated border border-dark-border rounded px-3 py-2 text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {typeof p.value === "number" ? p.value.toFixed ? p.value.toFixed(2) : p.value : p.value}</p>
      ))}
    </div>
  );
};

export default function ExecutionChart({ history = [] }) {
  if (!history.length) return (
    <div className="h-48 flex items-center justify-center text-gray-600 text-sm">
      No historical data yet
    </div>
  );

  const data = [...history].reverse().map(w => ({
    week: w.week_start_date ? w.week_start_date.slice(5) : "—",
    score: w.avg_execution_score,
    pcr:   w.priority_completion_rate != null ? Math.round(w.priority_completion_rate * 100) : null,
    deferral: w.deferral_rate != null ? Math.round(w.deferral_rate * 100) : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" />
        <XAxis dataKey="week" tick={{ fill: "#555", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#555", fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 100]} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={80} stroke="#C9A84C22" strokeDasharray="4 4" />
        <Bar dataKey="pcr" name="Priority Completion %" fill={GOLD_L} radius={[2,2,0,0]} />
        <Line dataKey="score" name="Execution Score" stroke={GOLD} dot={{ fill: GOLD, r: 3 }} strokeWidth={2} type="monotone" />
        <Line dataKey="deferral" name="Deferral %" stroke={RED} dot={false} strokeWidth={1.5} type="monotone" strokeDasharray="4 4" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
