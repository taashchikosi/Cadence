import { useState } from "react";
import { api } from "../api/client";

const FRICTION_TAGS = [
  { value: "lack_of_clarity", label: "Lack of clarity" },
  { value: "distraction", label: "Distraction" },
  { value: "low_energy", label: "Low energy" },
  { value: "external_demands", label: "External demands" },
  { value: "avoidance", label: "Avoidance" },
  { value: "overplanning", label: "Overplanning" },
  { value: "decision_uncertainty", label: "Decision uncertainty" },
  { value: "other", label: "Other" },
];

const DEEP_WORK_OPTIONS = ["0", "1", "2", "3+"];
const TASK_STATUSES = ["planned", "done", "partial", "deferred", "dropped"];

const today = () => new Date().toISOString().slice(0, 10);

export default function DailyInputForm({ onSaved }) {
  const [form, setForm] = useState({
    date: today(),
    execution_score: 5,
    friction_tag: "",
    deep_work_blocks: "1",
    free_text: "",
  });
  const [tasks, setTasks] = useState([{ description: "", status: "planned" }]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function setTask(i, field, value) {
    setTasks((prev) => prev.map((t, idx) => idx === i ? { ...t, [field]: value } : t));
  }

  function addTask() {
    setTasks((prev) => [...prev, { description: "", status: "planned" }]);
  }

  function removeTask(i) {
    setTasks((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.postDailyLog({
        ...form,
        execution_score: Number(form.execution_score),
        tasks: tasks.filter((t) => t.description.trim()),
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
      <div className="grid grid-cols-2 gap-4">
        <Field label="Date">
          <input type="date" value={form.date} onChange={set("date")} required className="input-base" />
        </Field>
        <Field label="Deep work blocks">
          <div className="flex gap-2 mt-1">
            {DEEP_WORK_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setForm((f) => ({ ...f, deep_work_blocks: opt }))}
                className={`flex-1 py-2 rounded text-sm font-medium border transition-colors ${
                  form.deep_work_blocks === opt
                    ? "bg-slate-600 border-slate-500 text-white"
                    : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        </Field>
      </div>

      <Field label={`Execution score: ${form.execution_score}/10`} hint="How effectively did you execute today?">
        <input
          type="range"
          min={1}
          max={10}
          value={form.execution_score}
          onChange={set("execution_score")}
          className="w-full accent-slate-400 mt-2"
        />
        <div className="flex justify-between text-xs text-slate-600 mt-1">
          <span>1 — Minimal</span><span>10 — Peak</span>
        </div>
      </Field>

      <Field label="Primary friction" hint="What most impeded execution today?">
        <select value={form.friction_tag} onChange={set("friction_tag")} className="input-base">
          <option value="">None / not applicable</option>
          {FRICTION_TAGS.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>
      </Field>

      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-slate-300">Tasks</label>
          <button type="button" onClick={addTask} className="text-xs text-slate-400 hover:text-slate-200 transition-colors">
            + Add task
          </button>
        </div>
        <div className="space-y-2">
          {tasks.map((task, i) => (
            <div key={i} className="flex gap-2">
              <input
                type="text"
                value={task.description}
                onChange={(e) => setTask(i, "description", e.target.value)}
                placeholder={`Task ${i + 1}`}
                className="input-base flex-1"
              />
              <select
                value={task.status}
                onChange={(e) => setTask(i, "status", e.target.value)}
                className="input-base w-36"
              >
                {TASK_STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              {tasks.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeTask(i)}
                  className="text-slate-600 hover:text-slate-400 px-1 text-lg leading-none"
                >
                  ×
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <Field label="Notes (optional)" hint="Observations about your day — not a journal entry.">
        <textarea
          value={form.free_text}
          onChange={set("free_text")}
          rows={2}
          placeholder="Any operational notes…"
          className="input-base"
        />
      </Field>

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <button
        type="submit"
        disabled={saving}
        className="w-full py-2.5 bg-slate-700 hover:bg-slate-600 text-slate-100 rounded font-medium text-sm transition-colors disabled:opacity-50"
      >
        {saved ? "Saved" : saving ? "Saving…" : "Log Day"}
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
