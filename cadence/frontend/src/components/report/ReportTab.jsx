import { useState } from "react";
import { api } from "../../api/client";

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

// Simple markdown renderer — handles **bold**, bullet lists, section headers
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }

    // Section header: **TITLE** on its own line
    if (/^\*\*[A-Z][A-Z\s]+\*\*$/.test(line.trim())) {
      const title = line.trim().replace(/\*\*/g, "");
      elements.push(
        <div key={i} className="mt-7 mb-3 first:mt-0">
          <span className="text-xs font-bold tracking-[0.2em] uppercase text-gold/80">{title}</span>
          <div className="h-px bg-gold/20 mt-1.5" />
        </div>
      );
      i++; continue;
    }

    // Bullet point
    if (line.trim().startsWith("- ") || line.trim().startsWith("• ")) {
      const content = line.trim().slice(2);
      elements.push(
        <div key={i} className="flex gap-3 mb-2.5">
          <span className="text-gold/60 mt-1 shrink-0">·</span>
          <p className="text-white text-sm leading-relaxed">{inlineMarkdown(content)}</p>
        </div>
      );
      i++; continue;
    }

    // Regular paragraph
    elements.push(
      <p key={i} className="text-white text-sm leading-relaxed mb-4">
        {inlineMarkdown(line.trim())}
      </p>
    );
    i++;
  }

  return elements;
}

function inlineMarkdown(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

const pct = v => v != null ? `${Math.round(v * 100)}%` : "—";
const num = (v, suffix = "") => v != null ? `${typeof v === "number" ? v.toFixed(1) : v}${suffix}` : "—";

const METRIC_COLORS = ["#F97316", "#D4A520", "#06B6D4", "#F43F5E", "#60A5FA", "#A855F7"];

export default function ReportTab() {
  const currentMonday = getCurrentMonday();
  const [weekStart,  setWeekStart]  = useState(currentMonday);
  const [report,     setReport]     = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  const isCurrentWeek = weekStart >= currentMonday;

  function handleDownload() {
    window.print();
  }

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await api.getCoachReport(weekStart);
      setReport(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto py-8 space-y-6">

      {/* Header + week nav */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Executive Coach Report</h2>
          <p className="text-xs text-gray-300 mt-0.5">
            Grounded in your weekly data and the knowledge base
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setWeekStart(s => shiftWeek(s, -7))}
            className="btn-ghost text-sm px-3 py-1.5 text-white hover:text-white">
            ← Prev
          </button>
          <span className="text-sm font-medium text-gold px-2 min-w-[10rem] text-center">
            {formatWeek(weekStart)}
          </span>
          <button onClick={() => !isCurrentWeek && setWeekStart(s => shiftWeek(s, 7))}
            disabled={isCurrentWeek}
            className="btn-ghost text-sm px-3 py-1.5 text-white hover:text-white disabled:opacity-30 disabled:cursor-not-allowed">
            Next →
          </button>
        </div>
      </div>

      {/* Generate button */}
      {!report && !loading && (
        <div className="card p-8 text-center space-y-4" style={{ background: "#000" }}>
          <div className="space-y-1">
            <p className="text-white font-medium">Week of {formatWeek(weekStart)}</p>
            <p className="text-xs text-gray-300 max-w-sm mx-auto leading-relaxed">
              Generates a 1-page executive coaching report grounded in principles from the
              knowledge base — citing specific authors and frameworks relevant to your week.
            </p>
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <button onClick={handleGenerate} className="btn-gold px-8">
            Generate Report
          </button>
        </div>
      )}

      {loading && (
        <div className="card p-16 flex flex-col items-center gap-4" style={{ background: "#000" }}>
          <div className="w-8 h-8 border-2 border-gold border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-300 text-sm">Generating your coaching report…</p>
        </div>
      )}

      {/* Rendered report */}
      {report && !loading && (
        <div id="printable-report" className="space-y-4">

          {/* Metrics summary bar */}
          {report.metrics && (
            <div className="card p-5 grid grid-cols-6 gap-3 text-center" style={{ background: "#000" }}>
              {[
                { label: "Execution", value: num(report.metrics.avg_execution_score, "/10") },
                { label: "Priorities", value: report.metrics.priority_completion_rate != null
                    ? `${Math.round(report.metrics.priority_completion_rate * 3)}/3` : "—" },
                { label: "Planning",  value: pct(report.metrics.planning_accuracy)  },
                { label: "Deferral",  value: pct(report.metrics.deferral_rate)      },
                { label: "Deep Work", value: num(report.metrics.deep_work_frequency, "h") },
                { label: "Friction",  value: (report.metrics.friction_pattern_index?.tag || "—")
                    .replace(/_/g, " ") },
              ].map(({ label, value }, idx) => (
                <div key={label} className="flex flex-col gap-1">
                  <span className="text-xs text-gray-300 uppercase tracking-wider">{label}</span>
                  <span className="text-sm font-semibold" style={{ color: METRIC_COLORS[idx] }}>{value}</span>
                </div>
              ))}
            </div>
          )}

          {/* Priority outcomes */}
          {report.priorities?.length > 0 && (
            <div className="card p-5" style={{ background: "#000" }}>
              <p className="text-xs font-semibold text-white uppercase tracking-widest mb-3">
                Priority Outcomes
              </p>
              <div className="space-y-2">
                {report.priorities.map((p, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-white truncate mr-4">{p.description}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${
                      p.status === "done"     ? "bg-emerald-900/40 text-emerald-300" :
                      p.status === "partial"  ? "bg-amber-900/40 text-amber-300"    :
                                                "bg-red-900/30 text-red-400"
                    }`}>
                      {p.status?.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Main report text */}
          <div className="card p-8" style={{ background: "#000" }}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <p className="text-xs font-semibold text-white uppercase tracking-widest">
                  Coaching Report
                </p>
                <p className="text-xs text-gray-300 mt-0.5">Week of {formatWeek(weekStart)}</p>
              </div>
              <img src="/Logo.png" alt="" className="w-8 h-8 object-contain opacity-60"
                onError={e => { e.target.style.display = "none"; }} />
            </div>
            <div className="border-t border-dark-border pt-6">
              {renderMarkdown(report.report)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-center gap-3 no-print">
            <button onClick={handleDownload} className="btn-gold text-xs px-5 py-2">
              ↓ Download PDF
            </button>
            <button onClick={handleGenerate} className="btn-ghost text-xs px-4 py-2">
              ↺ Regenerate
            </button>
            <button onClick={() => setReport(null)} className="btn-ghost text-xs px-4 py-2">
              ← Back
            </button>
          </div>

        </div>
      )}

    </div>
  );
}
