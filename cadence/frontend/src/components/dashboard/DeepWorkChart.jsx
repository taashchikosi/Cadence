import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid,
} from "recharts";

const TEAL = "#06B6D4";

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#131629", border: "1px solid #1E2245" }}
      className="rounded-lg px-3 py-2.5 text-xs shadow-xl">
      <p className="text-gray-400 mb-1 font-medium">Week of {label}</p>
      {payload[0]?.value != null && (
        <p style={{ color: TEAL }} className="font-medium">{payload[0].value.toFixed(1)}h deep work</p>
      )}
    </div>
  );
}

export default function DeepWorkChart({ history = [] }) {
  if (!history.length) return (
    <div className="h-40 flex items-center justify-center text-gray-600 text-sm">
      No data yet
    </div>
  );

  const data = [...history].reverse().map(w => ({
    week:  w.week_start_date ? w.week_start_date.slice(5) : "—",
    hours: w.deep_work_hours != null ? +parseFloat(w.deep_work_hours).toFixed(1) : null,
  }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={TEAL} stopOpacity={0.95} />
            <stop offset="100%" stopColor={TEAL} stopOpacity={0.25} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#131629" vertical={false} />
        <XAxis dataKey="week" tick={{ fill: "#555", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#555", fontSize: 10 }} axisLine={false} tickLine={false}
          tickFormatter={v => `${v}h`} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="hours" name="Deep Work Hours" fill="url(#barGrad)" radius={[4, 4, 0, 0]} maxBarSize={40} />
      </BarChart>
    </ResponsiveContainer>
  );
}
