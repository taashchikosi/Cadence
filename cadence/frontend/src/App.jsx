import { useState, useEffect } from "react";
import { useAuth } from "./context/AuthContext";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import Dashboard from "./components/dashboard/Dashboard";
import ChatInterface from "./components/chat/ChatInterface";
import ReportTab from "./components/report/ReportTab";
import { api } from "./api/client";

const mondayOfWeek = () => {
  const d = new Date();
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
};

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "monday",    label: "Weekly Planning" },
  { id: "friday",    label: "Friday Review" },
  { id: "report",    label: "Report" },
];

export default function App() {
  const { user, loading: authLoading, signOut } = useAuth();
  const [authView, setAuthView] = useState("login");
  const [tab, setTab]           = useState("dashboard");
  const [profile, setProfile]   = useState(null);
  const weekStart = mondayOfWeek();

  useEffect(() => {
    if (user) {
      api.getProfile().then(p => setProfile(p)).catch(() => {});
    }
  }, [user]);

  if (authLoading) return <FullPageLoader />;

  if (!user) {
    return authView === "login"
      ? <LoginPage onSwitch={() => setAuthView("signup")} />
      : <SignupPage onSwitch={() => setAuthView("login")} />;
  }

  const responseMode = profile?.response_mode   || "text";
  const voicePref    = profile?.voice_preference || "female";

  return (
    <div className="min-h-screen bg-dark flex flex-col">
      <header className="border-b border-dark-border bg-dark-surface sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-gold font-bold text-lg tracking-wider">C</span>
            <span className="text-white font-semibold text-sm tracking-widest uppercase">Cadence</span>
          </div>
          <nav className="flex gap-1">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  tab === t.id
                    ? "bg-dark-elevated text-gold border border-gold-muted"
                    : "text-gray-500 hover:text-gray-300 hover:bg-dark-elevated"
                }`}>
                {t.label}
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-600 hidden md:block">{user.email}</span>
            <button onClick={signOut}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors">
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {tab === "dashboard" && <Dashboard weekStart={weekStart} />}

        {tab === "monday" && (
          <div className="card h-[calc(100vh-8rem)] flex flex-col overflow-hidden">
            <ChatInterface
              sessionType="monday"
              weekStart={weekStart}
              responseMode={responseMode}
              voicePreference={voicePref}
              onComplete={() => {}}
            />
          </div>
        )}

        {tab === "friday" && (
          <div className="card h-[calc(100vh-8rem)] flex flex-col overflow-hidden">
            <ChatInterface
              sessionType="friday"
              weekStart={weekStart}
              responseMode={responseMode}
              voicePreference={voicePref}
              onComplete={() => setTab("report")}
            />
          </div>
        )}

        {tab === "report" && <ReportTab weekStart={weekStart} />}
      </main>
    </div>
  );
}

function FullPageLoader() {
  return (
    <div className="min-h-screen bg-dark flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <span className="text-gold font-bold text-3xl tracking-widest">C</span>
        <span className="text-xs text-gray-600 tracking-widest uppercase animate-pulse">Loading</span>
      </div>
    </div>
  );
}
