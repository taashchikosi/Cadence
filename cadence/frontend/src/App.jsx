import { useState, useEffect } from "react";
import Dashboard from "./components/dashboard/Dashboard";
import ChatInterface from "./components/chat/ChatInterface";
import ReportTab from "./components/report/ReportTab";
import FridayReminder from "./components/shared/FridayReminder";
import SettingsPanel from "./components/shared/SettingsPanel";
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
  const [tab, setTab]         = useState("dashboard");
  const [profile, setProfile] = useState(null);
  const weekStart = mondayOfWeek();

  useEffect(() => {
    api.getProfile().then(p => setProfile(p)).catch(() => {});
  }, []);

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
                {t.id === "weekly" && <FridayDot />}
              </button>
            ))}
          </nav>

          <div className="w-24 flex justify-end">
            <SettingsPanel profile={profile} onUpdate={setProfile} />
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        {tab === "dashboard" && <Dashboard weekStart={weekStart} />}

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

        {tab === "report" && <ReportTab weekStart={weekStart} />}
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
