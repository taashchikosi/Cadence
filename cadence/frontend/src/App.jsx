import { useState, useEffect } from "react";
import Dashboard from "./components/dashboard/Dashboard";
import ChatInterface from "./components/chat/ChatInterface";
import ReportTab from "./components/report/ReportTab";
import FridayReminder from "./components/shared/FridayReminder";
import SettingsPanel from "./components/shared/SettingsPanel";
import UserSwitcher from "./components/shared/UserSwitcher";
import IntroPage from "./components/shared/IntroPage";
import { api } from "./api/client";

const mondayOfWeek = () => {
  const d = new Date();
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d.toISOString().slice(0, 10);
};

const TABS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "weekly",    label: "Weekly Session" },
  { id: "report",    label: "Report" },
];

export default function App() {
  const [entered, setEntered] = useState(() => !!localStorage.getItem("cadence_entered"));
  const [tab, setTab]         = useState("dashboard");
  const [profile, setProfile] = useState(null);
  const weekStart = mondayOfWeek();

  useEffect(() => {
    if (entered) {
      api.getProfile().then(p => setProfile(p)).catch(() => {});
    }
  }, [entered]);

  function handleEnter() {
    localStorage.setItem("cadence_entered", "1");
    setEntered(true);
  }

  if (!entered) return <IntroPage onEnter={handleEnter} />;

  const responseMode = profile?.response_mode   || "text";
  const voicePref    = profile?.voice_preference || "female";

  return (
    <div className="min-h-screen bg-black flex flex-col">
      <header className="border-b border-dark-border bg-dark-surface sticky top-0 z-10"
        style={{ borderBottomColor: "#1E1E1E" }}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">

          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setEntered(false)}>
            <img src="/Logo.png" alt="" className="w-7 h-7 object-contain"
              onError={e => { e.target.style.display = "none"; }} />
            <span className="font-['Cinzel',serif] text-gold font-bold text-sm tracking-[0.2em] uppercase"
              style={{ background: "linear-gradient(135deg, #D4A520, #F0C040, #C46A1F)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Cadence
            </span>
          </div>

          <nav className="flex gap-1">
            {TABS.map(t => (
              <button key={t.id} onClick={() => setTab(t.id)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${
                  tab === t.id
                    ? "bg-dark-elevated text-gold border border-gold-muted"
                    : "text-gray-500 hover:text-gray-300 hover:bg-dark-elevated"
                }`}>
                {t.label}
                {t.id === "weekly" && <FridayDot />}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <UserSwitcher />
            <SettingsPanel profile={profile} onUpdate={setProfile} />
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {tab === "dashboard" && <Dashboard />}

        {tab === "weekly" && (
          <div className="card h-[calc(100vh-8rem)] flex flex-col overflow-hidden">
            <ChatInterface
              sessionType="weekly"
              weekStart={weekStart}
              responseMode={responseMode}
              voicePreference={voicePref}
              onComplete={() => setTab("report")}
            />
          </div>
        )}

        {tab === "report" && <ReportTab />}
      </main>

      <FridayReminder onStartSession={() => setTab("weekly")} />
    </div>
  );
}

function FridayDot() {
  const now = new Date();
  const isFriday = now.getDay() === 5 && now.getHours() >= 13 && now.getHours() < 19;
  if (!isFriday) return null;
  return <span className="ml-1.5 inline-block w-1.5 h-1.5 rounded-full bg-gold animate-pulse-gold" />;
}
