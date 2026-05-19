import { useState } from "react";
import { api } from "../api/client";

const FAILURE_PATTERNS = [
  "Planning Inflation",
  "False Priority",
  "Reactive Capture",
  "Decision Deferral",
  "Leverage Leakage",
  "Depth Deprivation",
  "Not sure yet",
];

export default function OnboardingForm({ onComplete }) {
  const [form, setForm] = useState({
    role_type: "",
    self_identified_failure_pattern: "",
    typical_week_structure: "",
    top_3_active_goals: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.postOnboarding(form);
      onComplete();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto py-12 px-6">
      <h1 className="text-2xl font-semibold text-slate-100 mb-1">Operational Calibration</h1>
      <p className="text-slate-400 text-sm mb-8">
        This is a one-time setup. Your answers calibrate the AI diagnostic framework.
      </p>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Field label="Role / Function">
          <input
            type="text"
            value={form.role_type}
            onChange={set("role_type")}
            placeholder="e.g. Founder, Head of Product, Director of Engineering"
            required
            className="input-base"
          />
        </Field>

        <Field label="Self-identified failure pattern" hint="Which of these most often describes your execution breakdown?">
          <select
            value={form.self_identified_failure_pattern}
            onChange={set("self_identified_failure_pattern")}
            className="input-base"
          >
            <option value="">Select…</option>
            {FAILURE_PATTERNS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </Field>

        <Field label="Typical week structure" hint="How does your week normally flow? When do you do your best work?">
          <textarea
            value={form.typical_week_structure}
            onChange={set("typical_week_structure")}
            rows={3}
            placeholder="e.g. Mon–Fri. Heavy meetings Tuesday and Thursday. I do my best thinking in the morning before 10am."
            className="input-base"
          />
        </Field>

        <Field label="Top 3 active goals (this quarter)">
          <textarea
            value={form.top_3_active_goals}
            onChange={set("top_3_active_goals")}
            rows={3}
            placeholder="1. …&#10;2. …&#10;3. …"
            required
            className="input-base"
          />
        </Field>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={saving}
          className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded font-medium text-sm transition-colors disabled:opacity-50"
        >
          {saving ? "Saving…" : "Complete Setup"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-1">{label}</label>
      {hint && <p className="text-xs text-slate-500 mb-2">{hint}</p>}
      {children}
    </div>
  );
}
