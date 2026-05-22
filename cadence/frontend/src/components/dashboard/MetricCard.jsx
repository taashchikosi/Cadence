import ActionDot from "../shared/ActionDot";
import SparkLine from "../shared/SparkLine";

export default function MetricCard({ label, value, sub, dot, sparkData, inverted }) {
  return (
    <div className="card p-4 flex flex-col gap-2 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="label-xs">{label}</span>
        <ActionDot status={dot} />
      </div>
      <div className="flex items-end justify-between gap-2">
        <span className={`text-2xl font-semibold ${dotColor(dot)}`}>{value ?? "—"}</span>
        {sparkData && <SparkLine data={sparkData} inverted={inverted} />}
      </div>
      {sub && <span className="text-xs text-gray-600">{sub}</span>}
    </div>
  );
}

function dotColor(dot) {
  if (!dot) return "text-white";
  return dot === "green" ? "text-emerald-400" : dot === "amber" ? "text-amber-400" : "text-red-400";
}
