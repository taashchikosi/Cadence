import { useState } from "react";
import { api } from "../api/client";

const STATUSES = ["done", "partial", "deferred", "dropped"];

const mondayOfWeek = () => {
  const d = new Date();
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
};

export default function FridayWeeklyReviewForm({ onSaved, onReviewGenerated }) {
  const [form, setForm] = useState({
    week_start_date: mondayOfWeek(),
    priority_1_status: "",
    priority_2_status: "",
    priority_3_status: "",
    deep_work_hours: "",
    admin_hours: "",
    meetings_hours: "",
    reactive_work_hours: "",
    learning_hours: "",
    low_leverage_hours: "",
    weekly_execution_score: 5,
    reflection_text: "",
  });
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.postFridayReview({
        ...form,
        weekly_execution_score: Number(form.weekly_execution_score),
        deep_work_hours: Number(form.deep_work_hours) || 0,
        admin_hours: Number(form.admin_hours) || 0,
        meetings_hours: Number(form.meetings_hours) || 0,
        reactive_work_hours: Number(form.reactive_work_hours) || 0,
        learning_hours: Number(form.learning_hours) || 0,
        low_leverage_hours: Number(form.low_leverage_hours) || 0,
      });
      setSaved(true);

      // Auto-generate review
      setGenerating(true);
      const review = await api.generateReview({ week_start_date: form.week_start_date });
      if (onReviewGenerated) onReviewGenerated(review);
      if (onSaved) onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
      setGenerating(false);
    }
  }

  const timeFields = [
    { key: "deep_work_hours", label: "Deep work" },
    { key: "admin_hours", label: "Admin" },
    { key: "meetings_hours", label: "Meetings" },
    { key: "reactive_work_hours", label: "Reactive work" },
    { key: "learning_hours", label: "Learning" },
    { key: "low_leverage_hours", label: "Low-leverage" },
  ];

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
        <label className="block text-sm font-medium text-slate-300 mb-2">Priority outcomes</label>
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div key={n} className="flex gap-3 items-center">
              <span className="text-slate-500 text-sm w-24 shrink-0">Priority {n}</span>
              <div className="flex gap-2 flex-1">
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, [`priority_${n}_status`]: s }))}
                    className={`flex-1 py-1.5 rounded text-xs font-medium border transition-colors ${
                      form[`priority_${n}_status`] === s
                        ? statusColors(s)
                        : "bg-slate-800 border-slate-700 text-slate-500 hover:border-slate-500"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-2">Time allocation (hours)</label>
        <p className="text-xs text-slate-500 mb-3">Estimate how your working hours were distributed this week.</p>
        <div className="grid grid-cols-2 gap-3">
          {timeFields.map(({ key, label }) => (
            <div key={key}>
              <label className="text-xs text-slate-400 mb-1 block">{label}</label>
              <input
                type="number"
                min={0}
                max={80}
                step={0.5}
                value={form[key]}
                onChange={set(key)}
                placeholder="0"
                className="input-base"
              />
            </div>
          ))}
        </div>
      </div>

      <Field label={`Weekly execution score: ${form.weekly_execution_score}/10`}>
        <input
          type="range"
          min={1}
          max={10}
          value={form.weekly_execution_score}
          onChange={set("weekly_execution_score")}
          className="w-full accent-slate-400 mt-2"
        />
        <div className="flex justify-between text-xs text-slate-600 mt-1">
          <span>1 — Poor week</span><span>10 — Full execution</span>
        </div>
      </Field>

      <Field label="Weekly reflection (optional)" hint="What determined the outcome of this week?">
        <textarea
          value={form.reflection_text}
          onChange={set("reflection_text")}
          rows={3}
          placeholder="What actually drove this week's results…"
          className="input-base"
        />
      </Field>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={saving || generating}
        className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded font-medium text-sm transition-colors disabled:opacity-50"
      >
        {generating
          ? "Generating AI review…"
          : saved
          ? "Saved"
          : saving
          ? "Saving…"
          : "Submit & Generate Review"}
      </button>
    </form>
  );
}

function statusColors(status) {
  switch (status) {
    case "done": return "bg-emerald-900 border-emerald-700 text-emerald-300";
    case "partial": return "bg-amber-900 border-amber-700 text-amber-300";
    case "deferred": return "bg-slate-700 border-slate-500 text-slate-300";
    case "dropped": return "bg-red-900 border-red-800 text-red-400";
    default: return "";
  }
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
