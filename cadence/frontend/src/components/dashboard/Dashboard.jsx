import { useState, useEffect, useCallback } from "react";
import { api } from "../../api/client";
import PerformanceChart from "./PerformanceChart";
import DeepWorkChart from "./DeepWorkChart";
import FrictionHeatmap from "./FrictionHeatmap";
import AIReviewPanel from "./AIReviewPanel";

const pct = v => v != null ? `${Math.round(v * 100)}%` : "—";

const FRICTION_LABELS = {
  meetings:           "Meetings",
  reactive_work:      "Reactive Work",
  context_switching:  "Context Switching",
  decision_avoidance: "Decision Avoidance",
  overcommitment:     "Overcommitment",
  admin:              "Admin Overhead",
  unclear_priorities: "Unclear Priorities",
};

function getCurrentMonday() {
  const d = new Date();
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
}

function shiftWeek(dateStr, days) {
  const d = new Date(dateStr + "T12:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function formatWeek(dateStr) {
  const d = new Date(dateStr + "T12:00:00");
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export default function Dashboard() {
  const [weekStart,  setWeekStart]  = useState(getCurrentMonday);
  const [data,       setData]       = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error,      setError]      = useState(null);

  const currentMonday = getCurrentMonday();
  const isCurrentWeek = weekStart >= currentMonday;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await api.getDashboard(weekStart, 8);
      setData(d);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [weekStart]);

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

  const m       = data.metrics || {};
  const history = data.metrics_history || [];
  const fpi     = m.friction_pattern_index || {};
  const dots    = m.action_dots || {};

  const priorityCount = m.priority_completion_rate != null
    ? `${Math.round(m.priority_completion_rate * 3)}/3`
    : "—";

  return (
    <div className="space-y-6 animate-fade-in">

      {/* Week navigation header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Performance Review</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {history.length} week{history.length !== 1 ? "s" : ""} of history
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setWeekStart(s => shiftWeek(s, -7))}
            className="btn-ghost text-sm px-3 py-1.5 text-white hover:text-white">
            ← Prev
          </button>
          <span className="text-sm font-medium text-gold px-2 min-w-[11rem] text-center">
            {formatWeek(weekStart)}
          </span>
          <button onClick={() => !isCurrentWeek && setWeekStart(s => shiftWeek(s, 7))}
            disabled={isCurrentWeek}
            className="btn-ghost text-sm px-3 py-1.5 text-white hover:text-white disabled:opacity-30 disabled:cursor-not-allowed">
            Next →
          </button>
          <button onClick={load} className="btn-ghost text-xs px-2 py-1.5 ml-1 text-gray-300">↺</button>
        </div>
      </div>

      {/* 6 metric cards */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard
          label="Execution Score"
          value={m.avg_execution_score != null ? m.avg_execution_score.toFixed(1) : "—"}
          suffix="/10"
          dot={m.avg_execution_score >= 8 ? "green" : m.avg_execution_score >= 6 ? "amber" : m.avg_execution_score != null ? "red" : null}
          accent="orange"
        />
        <MetricCard
          label="Priority Completion"
          value={priorityCount}
          sub={m.priority_completion_rate != null ? pct(m.priority_completion_rate) + " complete" : "No review yet"}
          dot={dots.priority_completion_rate}
          accent="gold"
        />
        <MetricCard
          label="Planning Accuracy"
          value={pct(m.planning_accuracy)}
          dot={dots.planning_accuracy}
          accent="teal"
        />
        <MetricCard
          label="Deferral Rate"
          value={pct(m.deferral_rate)}
          dot={dots.deferral_rate}
          accent="pink"
        />
        <MetricCard
          label="Deep Work"
          value={m.deep_work_frequency != null ? m.deep_work_frequency.toFixed(1) : "—"}
          suffix=" hrs/wk"
          dot={dots.deep_work_frequency}
          accent="blue"
        />
        <MetricCard
          label="Primary Friction"
          value={fpi.tag ? (FRICTION_LABELS[fpi.tag] || fpi.tag.replace(/_/g, " ")) : "—"}
          sub={fpi.tag ? "primary this week" : null}
          accent="purple"
        />
      </div>

      {/* Performance trend — 3 lines as % */}
      <div className="card p-5" style={{ background: "#000" }}>
        <div className="flex items-center justify-between mb-4">
          <p className="text-xs font-semibold text-white uppercase tracking-widest">Performance Trend</p>
          <div className="flex gap-4">
            {[
              { color: "#F97316", label: "Execution Score",   dash: false },
              { color: "#06B6D4", label: "Planning Accuracy", dash: true  },
              { color: "#F43F5E", label: "Deferral Rate",     dash: true  },
            ].map(({ color, label, dash }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="w-5 h-0.5 rounded inline-block"
                  style={{ background: color, opacity: dash ? 0.8 : 1 }} />
                <span className="text-xs text-gray-300">{label}</span>
              </div>
            ))}
          </div>
        </div>
        <PerformanceChart history={history} />
      </div>

      {/* Deep Work + Friction Heatmap side-by-side */}
      <div className="grid grid-cols-2 gap-4">

        <div className="card p-5" style={{ background: "#000" }}>
          <p className="text-xs font-semibold text-white uppercase tracking-widest mb-4">
            Deep Work Hours / Week
          </p>
          <DeepWorkChart history={history} />
        </div>

        <div className="card p-5" style={{ background: "#000" }}>
          <p className="text-xs font-semibold text-white uppercase tracking-widest mb-4">
            Friction Heatmap
          </p>
          <FrictionHeatmap history={history} />
        </div>

      </div>

      {/* AI Diagnostic Review */}
      <div>
        <p className="text-xs font-semibold text-white uppercase tracking-widest mb-3">
          AI Diagnostic Review
        </p>
        <AIReviewPanel
          review={data.latest_review}
          onGenerate={handleGenerateReview}
          generating={generating}
        />
      </div>

    </div>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────

const ACCENT_PALETTE = {
  orange: { color: "#F97316", glow: "rgba(249,115,22,0.18)", border: "rgba(249,115,22,0.45)" },
  teal:   { color: "#06B6D4", glow: "rgba(6,182,212,0.18)",  border: "rgba(6,182,212,0.45)"  },
  pink:   { color: "#F43F5E", glow: "rgba(244,63,94,0.18)",  border: "rgba(244,63,94,0.45)"  },
  blue:   { color: "#60A5FA", glow: "rgba(96,165,250,0.18)", border: "rgba(96,165,250,0.45)" },
  purple: { color: "#A855F7", glow: "rgba(168,85,247,0.18)", border: "rgba(168,85,247,0.45)" },
  gold:   { color: "#D4A520", glow: "rgba(212,165,32,0.18)", border: "rgba(212,165,32,0.45)" },
};

function MetricCard({ label, value, suffix = "", sub, dot, accent }) {
  const dotColor = dot === "green" ? "#10b981"
    : dot === "amber" ? "#f59e0b"
    : dot === "red"   ? "#ef4444"
    : null;

  const ac = ACCENT_PALETTE[accent] || null;

  return (
    <div
      className="card p-5 flex flex-col gap-2 transition-all duration-300 hover:brightness-110"
      style={ac ? {
        borderTopColor: ac.border,
        borderTopWidth: 2,
        boxShadow: `0 0 28px ${ac.glow}, 0 1px 0 ${ac.border} inset`,
      } : {}}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-300 uppercase tracking-wider">{label}</span>
        {dotColor && <span className="w-2 h-2 rounded-full shrink-0" style={{ background: dotColor }} />}
      </div>
      <div className="flex items-end gap-1 mt-1">
        <span className="text-2xl font-semibold leading-none"
          style={{ color: ac ? ac.color : "white" }}>
          {value}
        </span>
        {suffix && <span className="text-sm text-gray-300 mb-0.5">{suffix}</span>}
      </div>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-8 w-48 bg-dark-elevated rounded" />
      <div className="grid grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 bg-dark-elevated rounded-lg border border-dark-border" />
        ))}
      </div>
      <div className="h-64 bg-dark-elevated rounded-lg border border-dark-border" />
      <div className="grid grid-cols-2 gap-4">
        <div className="h-48 bg-dark-elevated rounded-lg border border-dark-border" />
        <div className="h-48 bg-dark-elevated rounded-lg border border-dark-border" />
      </div>
    </div>
  );
}
