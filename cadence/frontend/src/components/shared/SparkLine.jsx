/**
 * Tufte-style sparkline — word-sized, no axes, no labels.
 * data: [{value}]
 * inverted: true if lower is better (e.g. deferral rate)
 */
export default function SparkLine({ data = [], inverted = false, width = 64, height = 20 }) {
  if (!data || data.length < 2) return <span className="text-gray-700 text-xs">—</span>;

  const values = data.map(d => d.value).filter(v => v != null);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - ((v - min) / range) * height * 0.8 - height * 0.1;
    return `${x},${y}`;
  });

  const lastVal = values[values.length - 1];
  const prevVal = values[values.length - 2];
  const trend = lastVal > prevVal ? "up" : lastVal < prevVal ? "down" : "flat";
  const positive = inverted ? trend === "down" : trend === "up";
  const color = trend === "flat" ? "#555" : positive ? "#10b981" : "#ef4444";

  const lastX = (((values.length - 1) / (values.length - 1)) * width);
  const lastY = height - ((lastVal - min) / range) * height * 0.8 - height * 0.1;

  return (
    <svg width={width} height={height} className="inline-block align-middle overflow-visible">
      <polyline
        points={pts.join(" ")}
        fill="none"
        stroke={color}
        strokeWidth="1.2"
        strokeLinejoin="round"
        strokeLinecap="round"
        opacity="0.8"
      />
      <circle cx={lastX} cy={lastY} r="2" fill={color} />
    </svg>
  );
}
