import { useState } from "react";
import { api } from "../api/client";

const DERAILERS = [
  { value: "meetings", label: "Meetings" },
  { value: "distractions", label: "Distractions" },
  { value: "low_energy", label: "Low energy" },
  { value: "unclear_priorities", label: "Unclear priorities" },
  { value: "external_requests", label: "External requests" },
  { value: "avoidance", label: "Avoidance" },
  { value: "overcommitment", label: "Overcommitment" },
];

const mondayOfWeek = () => {
  const d = new Date();
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
};

export default function MondayWeeklyForm({ onSaved }) {
  const [form, setForm] = useState({
    week_start_date: mondayOfWeek(),
    priority_1: "",
    priority_2: "",
    priority_3: "",
    estimated_deep_work_hours: "",
    predicted_main_derailer: "",
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.postMondayInput({
        ...form,
        estimated_deep_work_hours: Number(form.estimated_deep_work_hours),
      });
      setSaved(true);
      setTimeout(() => { setSaved(false); if (onSaved) onSaved(); }, 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Field label="Week starting">
        <input
          type="date"
          value={form.week_start_date}
          onChange={set("week_start_date")}
          required
          className="input-base"
        />
      </Field>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Top 3 priorities this week</label>
        <p className="text-xs text-slate-500 mb-3">
          List only what you will be held accountable to completing. Not aspirations.
        </p>
        <div className="space-y-2">
          {[1, 2, 3].map((n) => (
            <div key={n} className="flex gap-2 items-center">
              <span className="text-slate-600 text-sm w-4">{n}.</span>
              <input
                type="text"
                value={form[`priority_${n}`]}
                onChange={set(`priority_${n}`)}
                placeholder={`Priority ${n}`}
                required={n === 1}
                className="input-base flex-1"
              />
            </div>
          ))}
        </div>
      </div>

      <Field label="Estimated deep work hours this week">
        <input
          type="number"
          min={0}
          max={60}
          step={0.5}
          value={form.estimated_deep_work_hours}
          onChange={set("estimated_deep_work_hours")}
          placeholder="e.g. 15"
          className="input-base w-32"
        />
      </Field>

      <Field label="Predicted main derailer" hint="What is most likely to prevent completion?">
        <select
          value={form.predicted_main_derailer}
          onChange={set("predicted_main_derailer")}
          className="input-base"
        >
          <option value="">Select…</option>
          {DERAILERS.map((d) => (
            <option key={d.value} value={d.value}>{d.label}</option>
          ))}
        </select>
      </Field>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={saving}
        className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded font-medium text-sm transition-colors disabled:opacity-50"
      >
        {saved ? "Saved" : saving ? "Saving…" : "Submit Monday Commitments"}
      </button>
    </form>
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
