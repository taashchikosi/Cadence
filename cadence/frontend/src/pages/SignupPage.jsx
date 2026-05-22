import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { AuthLayout } from "./LoginPage";

const FAILURE_PATTERNS = [
  "Planning Inflation", "False Priority", "Reactive Capture",
  "Decision Deferral", "Leverage Leakage", "Depth Deprivation", "Not sure yet",
];

export default function SignupPage({ onSwitch }) {
  const { signUp } = useAuth();
  const [step, setStep]         = useState(1);
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [profile, setProfile]   = useState({
    role_type: "", self_identified_failure_pattern: "",
    typical_week_structure: "", top_3_active_goals: "",
    voice_preference: "female", response_mode: "text",
  });
  const [error, setError]   = useState(null);
  const [loading, setLoading] = useState(false);

  const set = k => e => setProfile(p => ({ ...p, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    if (step === 1) { setStep(2); return; }
    setLoading(true);
    setError(null);
    const { error: err } = await signUp(email, password);
    if (err) { setError(err.message); setLoading(false); return; }
    setLoading(false);
  }

  return (
    <AuthLayout>
      {step === 1 ? (
        <>
          <h2 className="text-2xl font-semibold text-white mb-1">Create account</h2>
          <p className="text-gray-500 text-sm mb-8">Start your operational review.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-xs block mb-1.5">Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                required className="input-cadence" placeholder="you@example.com" />
            </div>
            <div>
              <label className="label-xs block mb-1.5">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                required minLength={8} className="input-cadence" placeholder="Minimum 8 characters" />
            </div>
            <button type="submit" className="btn-gold w-full mt-2">Continue</button>
          </form>
          <p className="text-center text-sm text-gray-600 mt-6">
            Have an account?{" "}
            <button onClick={onSwitch} className="text-gold hover:text-gold-light transition-colors">Sign in</button>
          </p>
        </>
      ) : (
        <>
          <h2 className="text-xl font-semibold text-white mb-1">Calibration</h2>
          <p className="text-gray-500 text-xs mb-6">This personalises your AI advisor from day one.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label-xs block mb-1.5">Role / Function</label>
              <input type="text" value={profile.role_type} onChange={set("role_type")}
                required className="input-cadence" placeholder="e.g. Founder, Head of Product" />
            </div>
            <div>
              <label className="label-xs block mb-1.5">Known failure pattern</label>
              <select value={profile.self_identified_failure_pattern}
                onChange={set("self_identified_failure_pattern")} className="input-cadence">
                <option value="">Select…</option>
                {FAILURE_PATTERNS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="label-xs block mb-1.5">Top 3 active goals (this quarter)</label>
              <textarea value={profile.top_3_active_goals} onChange={set("top_3_active_goals")}
                rows={3} required className="input-cadence"
                placeholder={"1. …\n2. …\n3. …"} />
            </div>
            <div>
              <label className="label-xs block mb-1.5">Advisor voice</label>
              <div className="flex gap-3">
                {["female", "male"].map(v => (
                  <button key={v} type="button"
                    onClick={() => setProfile(p => ({ ...p, voice_preference: v }))}
                    className={`flex-1 py-2 rounded text-sm border transition-colors ${
                      profile.voice_preference === v
                        ? "bg-dark-elevated border-gold text-gold"
                        : "bg-dark-elevated border-dark-border text-gray-500 hover:border-gray-600"
                    }`}>
                    {v === "female" ? "Operational Clarity" : "Strategic Operator"}
                  </button>
                ))}
              </div>
            </div>
            {error && <p className="text-red-400 text-xs">{error}</p>}
            <button type="submit" disabled={loading} className="btn-gold w-full">
              {loading ? "Creating account…" : "Complete Setup"}
            </button>
          </form>
        </>
      )}
    </AuthLayout>
  );
}
