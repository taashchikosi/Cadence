import { useState, useEffect, useCallback } from "react";
import { api } from "../../api/client";
import PerformanceChart from "./PerformanceChart";
import AIReviewPanel from "./AIReviewPanel";

const PERIODS = [
  { label: "1 Month",  weeks: 4  },
  { label: "3 Months", weeks: 13 },
  { label: "6 Months", weeks: 26 },
];

const pct    = v  => v  != null ? `${Math.round(v * 100)}%` : "—";
const num    = v  => v  != null ? String(v) : "—";
const avg    = arr => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null;
const trend  = (arr) => {
  if (arr.length < 4) return null;
  const half = Math.floor(arr.length / 2);
  const early = avg(arr.slice(0, half));
  const late  = avg(arr.slice(half));
  if (early == null || late == null) return null;
  const delta = late - early;
  if (delta >  0.03) return "up";
  if (delta < -0.03) return "down";
  return "flat";
};

const FRICTION_LABELS = {
  meetings:          "Meetings",
  reactive_work:     "Reactive Work",
  context_switching: "Context Switching",
  decision_avoidance:"Decision Avoidance",
  overcommitment:    "Overcommitment",
  admin:             "Admin Overhead",
  unclear_priorities:"Unclear Priorities",
};

export default function Dashboard({ weekStart }) {
  const [period,     setPeriod]     = useState(PERIODS[1]);
  const [data,       setData]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error,      setError]      = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await api.getDashboard(weekStart, period.weeks);
      setData(d);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [weekStart, period]);

  useEffect(() => { load(); }, [load]);

  async function handleGenerateReview() {
    setGenerating(true);
    try {
      await api.generateReview({ week_start_date: weekStart });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error)   return <p className="text-red-400 text-sm p-6">{error}</p>;
  if (!data)   return null;

  const history      = data.metrics_history || [];
  const latestReview = data.latest_review;

  // Period aggregates
  const scores = history.map(w => w.avg_execution_score).filter(v => v != null);
  const pcrs   = history.map(w => w.priority_completion_rate).filter(v => v != null);
  const drs    = history.map(w => w.deferral_rate).filter(v => v != null);
  const pas    = history.map(w => w.planning_accuracy).filter(v => v != null);
  const dws    = history.map(w => w.deep_work_frequency).filter(v => v != null);

  const periodAvgScore = avg(scores);
  const periodAvgPCR   = avg(pcrs);
  const periodAvgDR    = avg(drs);
  const periodAvgPA    = avg(pas);
  const periodAvgDW    = avg(dws);

  const scoreTrend = trend(scores);
  const pcrTrend   = trend(pcrs);
  const dsTrend    = trend(drs.map(v => -v)); // lower is better

  // Friction frequency
  const frictionCounts = {};
  history.forEach(w => {
    const fpi = w.friction_pattern_index;
    if (fpi?.tag) frictionCounts[fpi.tag] = (frictionCounts[fpi.tag] || 0) + 1;
  });
  const topFrictions = Object.entries(frictionCounts)
    .sort((a, b) => b[1] - a[1]).slice(0, 3);
  const maxFriction = topFrictions[0]?.[1] || 1;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Performance Overview</h2>
          <p className="text-xs text-gray-600 mt-0.5">{history.length} weeks of data</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex rounded border border-dark-border overflow-hidden">
            {PERIODS.map(p => (
              <button key={p.weeks} onClick={() => setPeriod(p)}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  period.weeks === p.weeks
                    ? "bg-dark-elevated text-gold"
                    : "text-gray-500 hover:text-gray-300"
                }`}>
                {p.label}
              </button>
            ))}
          </div>
          <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">↺</button>
        </div>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-5 gap-3">
        <KPI label="Execution Score" value={periodAvgScore != null ? periodAvgScore.toFixed(1) : "—"} suffix="/10" trend={scoreTrend} color="gold" />
        <KPI label="Priority Completion" value={pct(periodAvgPCR)} trend={pcrTrend} color={pcrColor(periodAvgPCR)} />
        <KPI label="Planning Accuracy"   value={pct(periodAvgPA)}  color={pctColor(periodAvgPA, 0.7, 0.5)} />
        <KPI label="Deferral Rate"       value={pct(periodAvgDR)}  trend={dsTrend} color={drColor(periodAvgDR)} inverted />
        <KPI label="Deep Work"           value={periodAvgDW != null ? periodAvgDW.toFixed(1) : "—"} suffix=" blk/day" color="muted" />
      </div>

      {/* Main chart */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Performance Trend</p>
          <div className="flex gap-4">
            {[
              { color: "#D4A520", label: "Execution Score" },
              { color: "#D4A52055", label: "Priority Completion" },
              { color: "#ef4444", label: "Deferral Rate" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="w-5 h-0.5 rounded inline-block" style={{ background: color }} />
                <span className="text-xs text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        </div>
        <PerformanceChart history={history} />
      </div>

      {/* Bottom two-col */}
      <div className="grid grid-cols-3 gap-4">

        {/* Weekly heatmap */}
        <div className="col-span-2 card p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">Weekly Execution Heatmap</p>
          <WeeklyHeatmap history={history} />
        </div>

        {/* Friction breakdown */}
        <div className="card p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-4">Primary Friction</p>
          {topFrictions.length === 0
            ? <p className="text-xs text-gray-600">No friction data yet</p>
            : <div className="space-y-3">
                {topFrictions.map(([tag, count]) => (
                  <div key={tag}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs text-gray-300">{FRICTION_LABELS[tag] || tag.replace(/_/g, " ")}</span>
                      <span className="text-xs text-gray-600">{count}w</span>
                    </div>
                    <div className="h-1 rounded bg-dark-elevated overflow-hidden">
                      <div className="h-full rounded transition-all duration-500"
                        style={{ width: `${(count / maxFriction) * 100}%`, background: "linear-gradient(90deg, #8B6914, #D4A520)" }} />
                    </div>
                  </div>
                ))}
              </div>
          }

          {/* Metric dots legend */}
          <div className="mt-6 pt-4 border-t border-dark-border space-y-2">
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">Score Key</p>
            {[
              { color: "#10b981", label: "Strong (8–10)" },
              { color: "#D4A520", label: "Good (6–7)" },
              { color: "#f59e0b", label: "Moderate (4–5)" },
              { color: "#ef4444", label: "Weak (1–3)" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-sm shrink-0" style={{ background: color, opacity: 0.8 }} />
                <span className="text-xs text-gray-500">{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Review */}
      <div>
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">AI Diagnostic Review</p>
        <AIReviewPanel
          review={latestReview}
          onGenerate={handleGenerateReview}
          generating={generating}
        />
      </div>

    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

function KPI({ label, value, suffix = "", trend, color, inverted }) {
  const colorMap = {
    gold:    "text-gold",
    green:   "text-emerald-400",
    amber:   "text-amber-400",
    red:     "text-red-400",
    muted:   "text-gray-300",
  };
  const trendIcon = trend === "up" ? "↑" : trend === "down" ? "↓" : trend === "flat" ? "→" : "";
  const trendColor = trend === "up"
    ? (inverted ? "text-red-400" : "text-emerald-400")
    : trend === "down"
    ? (inverted ? "text-emerald-400" : "text-red-400")
    : "text-gray-600";

  return (
    <div className="card p-4 flex flex-col gap-1">
      <span className="text-xs text-gray-600 uppercase tracking-wider">{label}</span>
      <div className="flex items-end gap-1.5 mt-1">
        <span className={`text-2xl font-semibold ${colorMap[color] || "text-white"}`}>{value}{suffix}</span>
        {trendIcon && <span className={`text-sm mb-0.5 ${trendColor}`}>{trendIcon}</span>}
      </div>
    </div>
  );
}

function WeeklyHeatmap({ history }) {
  if (!history.length) return <p className="text-xs text-gray-600">No data yet</p>;

  const weeks = [...history].reverse();

  return (
    <div className="flex flex-wrap gap-1.5">
      {weeks.map((w, i) => {
        const score = w.avg_execution_score;
        const bg = score == null ? "#1a1a1a"
          : score >= 8  ? "#10b981cc"
          : score >= 6  ? "#D4A520bb"
          : score >= 4  ? "#f59e0baa"
          : "#ef444488";
        const date = w.week_start_date ? w.week_start_date.slice(5) : "—";
        return (
          <div key={i} title={`Week of ${date}\nScore: ${score?.toFixed(1) ?? "—"}`}
            className="relative group cursor-default"
            style={{ width: 28, height: 28, borderRadius: 4, background: bg, border: "1px solid #ffffff11" }}>
            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10 pointer-events-none">
              <div className="bg-dark-elevated border border-dark-border rounded px-2 py-1 text-xs whitespace-nowrap">
                <p className="text-gray-400">{date}</p>
                <p className="text-white font-medium">{score?.toFixed(1) ?? "—"}/10</p>
                {w.priority_completion_rate != null && (
                  <p className="text-gray-500">PCR {Math.round(w.priority_completion_rate * 100)}%</p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-5 gap-3">
        {[...Array(5)].map((_, i) => <div key={i} className="h-20 bg-dark-elevated rounded-lg border border-dark-border" />)}
      </div>
      <div className="h-64 bg-dark-elevated rounded-lg border border-dark-border" />
      <div className="grid grid-cols-3 gap-4">
        <div className="col-span-2 h-40 bg-dark-elevated rounded-lg border border-dark-border" />
        <div className="h-40 bg-dark-elevated rounded-lg border border-dark-border" />
      </div>
    </div>
  );
}

// Color helpers
function pctColor(v, greenThresh = 0.7, amberThresh = 0.5) {
  if (v == null) return "muted";
  return v >= greenThresh ? "green" : v >= amberThresh ? "amber" : "red";
}
function drColor(v) {
  if (v == null) return "muted";
  return v <= 0.2 ? "green" : v <= 0.35 ? "amber" : "red";
}
function pcrColor(v) { return pctColor(v, 0.7, 0.5); }
