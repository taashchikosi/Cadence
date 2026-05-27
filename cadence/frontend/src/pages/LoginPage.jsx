import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage({ onSwitch }) {
  const { signIn } = useAuth();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState(null);
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error: err } = await signIn(email, password);
    if (err) setError(err.message);
    setLoading(false);
  }

  return (
    <AuthLayout>
      <h2 className="text-2xl font-semibold text-white mb-1">Sign in</h2>
      <p className="text-gray-300 text-sm mb-8">Your operational review awaits.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label-xs block mb-1.5">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            required className="input-cadence" placeholder="you@example.com" />
        </div>
        <div>
          <label className="label-xs block mb-1.5">Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            required className="input-cadence" placeholder="••••••••" />
        </div>
        {error && <p className="text-red-400 text-xs">{error}</p>}
        <button type="submit" disabled={loading} className="btn-gold w-full mt-2">
          {loading ? "Signing in…" : "Sign In"}
        </button>
      </form>

      <p className="text-center text-sm text-gray-300 mt-6">
        No account?{" "}
        <button onClick={onSwitch} className="text-gold hover:text-gold-light transition-colors">
          Create one
        </button>
      </p>
    </AuthLayout>
  );
}

function AuthLayout({ children }) {
  return (
    <div className="min-h-screen bg-dark flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <span className="text-4xl font-bold text-gold tracking-wider">C</span>
          <h1 className="text-xl font-semibold text-white tracking-widest uppercase mt-1">Cadence</h1>
          <p className="text-xs text-gray-400 tracking-widest uppercase mt-1">Discipline Today. Destiny Tomorrow.</p>
        </div>
        <div className="card p-8">
          {children}
        </div>
      </div>
    </div>
  );
}

export { AuthLayout };
