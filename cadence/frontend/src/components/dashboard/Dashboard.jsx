import { useState, useEffect, useCallback } from "react";
import { api } from "../../api/client";
import MetricCard from "./MetricCard";
import ExecutionChart from "./ExecutionChart";
import AIReviewPanel from "./AIReviewPanel";

const pct = v => v != null ? `${Math.round(v * 100)}%` : null;

export default function Dashboard({ weekStart }) {
  const [data, setData]           = useState(null);
  const [loading, setLoading]     = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError]         = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api.getDashboard(weekStart);
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

  const { metrics, metrics_history, recent_logs, latest_review } = data;
  const dots = metrics?.action_dots || {};
  const est  = metrics?.execution_score_trend || {};
  const fpi  = metrics?.friction_pattern_index || {};

  const buildSparkline = (key, histKey) =>
    (metrics_history || []).filter(w => w[histKey ?? key] != null)
      .map(w => ({ value: w[histKey ?? key] })).reverse();

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Week header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Week of {weekStart}</h2>
          <p className="text-xs text-gray-600 mt-0.5">Operational performance overview</p>
        </div>
        <button onClick={load} className="btn-ghost text-xs px-3 py-1.5">Refresh</button>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <MetricCard
          label="Priority Completion"
          value={pct(metrics?.priority_completion_rate)}
          sub="of weekly priorities done"
          dot={dots.priority_completion_rate}
          sparkData={buildSparkline("priority_completion_rate")}
        />
        <MetricCard
          label="Deep Work"
          value={metrics?.deep_work_frequency != null ? `${metrics.deep_work_frequency}` : null}
          sub="blocks / day average"
          dot={dots.deep_work_frequency}
          sparkData={buildSparkline("deep_work_frequency")}
        />
        <MetricCard
          label="Deferral Rate"
          value={pct(metrics?.deferral_rate)}
          sub="tasks deferred"
          dot={dots.deferral_rate}
          inverted
          sparkData={buildSparkline("deferral_rate")}
        />
        <MetricCard
          label="Planning Accuracy"
          value={pct(metrics?.planning_accuracy)}
          sub="planned tasks completed"
          dot={dots.planning_accuracy}
          sparkData={buildSparkline("planning_accuracy")}
        />
        <MetricCard
          label="Execution Score"
          value={est.current_avg ? `${est.current_avg}/10` : null}
          sub={est.trend ? `Trend: ${est.trend}` : "No prior week data"}
          dot={est.trend === "improving" ? "green" : est.trend === "declining" ? "red" : "amber"}
          sparkData={buildSparkline("avg_execution_score")}
        />
        <MetricCard
          label="Primary Friction"
          value={fpi.tag?.replace(/_/g, " ") || null}
          sub={fpi.frequency_pct ? `${fpi.frequency_pct}% of logged days` : "No friction logged"}
          dot={null}
        />
      </div>

      {/* Execution chart */}
      {metrics_history?.length > 0 && (
        <div className="card p-4">
          <p className="label-xs mb-4">8-Week Performance Trend</p>
          <ExecutionChart history={metrics_history} />
          <div className="flex gap-4 mt-3">
            {[
              { color: "#C9A84C", label: "Execution Score" },
              { color: "#C9A84C55", label: "Priority Completion %" },
              { color: "#ef4444", label: "Deferral %" },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-1.5">
                <span className="w-2.5 h-0.5 rounded" style={{ background: color }} />
                <span className="text-xs text-gray-600">{label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Review */}
      <div>
        <p className="label-xs mb-3">Diagnostic Review</p>
        <AIReviewPanel
          review={latest_review}
          onGenerate={handleGenerateReview}
          generating={generating}
        />
      </div>

      {/* Recent logs */}
      {recent_logs?.length > 0 && (
        <div>
          <p className="label-xs mb-3">Recent Daily Logs</p>
          <div className="space-y-2">
            {recent_logs.slice(0, 5).map(log => (
              <div key={log.id} className="card px-4 py-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-medium text-gray-300">{log.date}</span>
                  <div className="flex gap-3 text-xs text-gray-600">
                    <span>Score {log.execution_score}/10</span>
                    <span>DW: {log.deep_work_blocks}</span>
                    {log.friction_tag && <span>{log.friction_tag.replace(/_/g, " ")}</span>}
                  </div>
                </div>
                {log.tasks?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {log.tasks.slice(0, 6).map(t => (
                      <span key={t.id} className={`text-xs px-2 py-0.5 rounded-full border ${taskBadge(t.status)}`}>
                        {t.description}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="grid grid-cols-3 gap-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 bg-dark-elevated rounded-lg border border-dark-border" />
        ))}
      </div>
      <div className="h-48 bg-dark-elevated rounded-lg border border-dark-border" />
    </div>
  );
}

function taskBadge(status) {
  switch (status) {
    case "done":     return "bg-emerald-950 border-emerald-800 text-emerald-400";
    case "partial":  return "bg-amber-950 border-amber-800 text-amber-400";
    case "deferred": return "bg-dark-elevated border-dark-border text-gray-400";
    case "dropped":  return "bg-red-950 border-red-900 text-red-500";
    default:         return "bg-dark-elevated border-dark-border text-gray-500";
  }
}
