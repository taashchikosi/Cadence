import { useState } from "react";
import { api } from "../../api/client";

export default function ReportTab({ weekStart }) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [done, setDone]       = useState(false);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setDone(false);
    try {
      const blob = await api.generateReport(weekStart);
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `cadence-report-${weekStart}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setDone(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto py-12 px-6 text-center">
      <div className="mb-8">
        <h2 className="text-xl font-semibold text-white mb-2">Weekly Report</h2>
        <p className="text-gray-500 text-sm leading-relaxed">
          Generates a PDF diagnostic report for the week of{" "}
          <span className="text-gray-300">{weekStart}</span>. Includes metrics, priority outcomes,
          time allocation, detected patterns, and your AI review.
        </p>
      </div>

      <div className="card p-8 mb-6">
        <div className="space-y-3 text-left text-sm text-gray-400 mb-8">
          {[
            "Operational metrics with trend indicators",
            "Priority commitments vs outcomes",
            "Time allocation breakdown",
            "AI diagnostic review — Diagnosis · Evidence · Intervention",
            "Detected failure patterns with confidence scores",
            "Weekly reflection",
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="w-1 h-1 rounded-full bg-gold shrink-0" />
              <span>{item}</span>
            </div>
          ))}
        </div>

        {error && <p className="text-red-400 text-xs mb-4">{error}</p>}
        {done && <p className="text-emerald-400 text-xs mb-4">Report downloaded.</p>}

        <button onClick={handleGenerate} disabled={loading} className="btn-gold w-full">
          {loading ? "Generating report…" : "Download PDF Report"}
        </button>
      </div>

      <p className="text-xs text-gray-700">
        This report is for your eyes only. It is not shared or stored externally.
      </p>
    </div>
  );
}
