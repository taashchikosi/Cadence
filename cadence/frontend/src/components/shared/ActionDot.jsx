const COLORS = {
  green: "bg-emerald-500",
  amber: "bg-amber-400",
  red:   "bg-red-500 animate-pulse",
};

const LABELS = {
  green: "On track",
  amber: "Monitor",
  red:   "Action required",
};

export default function ActionDot({ status, showLabel = false }) {
  if (!status) return null;
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${COLORS[status]}`} />
      {showLabel && (
        <span className={`text-xs ${status === "red" ? "text-red-400" : status === "amber" ? "text-amber-400" : "text-emerald-400"}`}>
          {LABELS[status]}
        </span>
      )}
    </span>
  );
}
