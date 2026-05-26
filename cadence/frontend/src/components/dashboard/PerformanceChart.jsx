import {
  ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine,
} from "recharts";

const GOLD      = "#D4A520";
const GOLD_AREA = "#D4A52022";
const GOLD_DIM  = "#D4A52066";
const RED       = "#ef4444";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-dark-elevated border border-dark-border rounded-lg px-3 py-2.5 text-xs shadow-xl">
      <p className="text-gray-400 mb-2 font-medium">Week of {label}</p>
      {payload.map((p, i) => p.value != null && (
        <div key={i} className="flex items-center gap-2 mb-1">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-400">{p.name}:</span>
          <span className="text-white font-medium">{typeof p.value === "number" ? p.value.toFixed(1) : p.value}</span>
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
    week:    w.week_start_date ? w.week_start_date.slice(5) : "—",
    score:   w.avg_execution_score != null ? +w.avg_execution_score.toFixed(2) : null,
    pcr:     w.priority_completion_rate != null ? +(w.priority_completion_rate * 10).toFixed(2) : null,
    deferral:w.deferral_rate != null ? +(w.deferral_rate * 10).toFixed(2) : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={GOLD} stopOpacity={0.15} />
            <stop offset="95%" stopColor={GOLD} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="pcrGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor={GOLD_DIM} stopOpacity={0.2} />
            <stop offset="95%" stopColor={GOLD_DIM} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false} />
        <XAxis dataKey="week" tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false}
          interval={data.length > 13 ? Math.floor(data.length / 8) : 0} />
        <YAxis tick={{ fill: "#444", fontSize: 10 }} axisLine={false} tickLine={false}
          domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={8} stroke={GOLD} strokeOpacity={0.12} strokeDasharray="4 4" />
        <ReferenceLine y={6} stroke="#555"  strokeOpacity={0.15} strokeDasharray="4 4" />

        <Area dataKey="pcr"     name="Priority Completion" fill="url(#pcrGrad)"   stroke={GOLD_DIM} strokeWidth={1.5} type="monotone" dot={false} />
        <Area dataKey="score"   name="Execution Score"     fill="url(#scoreGrad)" stroke={GOLD}     strokeWidth={2.5} type="monotone"
          dot={{ fill: GOLD, r: 3, strokeWidth: 0 }} activeDot={{ r: 5, fill: GOLD }} />
        <Line dataKey="deferral" name="Deferral Rate"      stroke={RED}     strokeWidth={1.5} type="monotone" dot={false} strokeDasharray="4 3" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
