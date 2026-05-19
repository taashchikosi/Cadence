import { useState, useEffect, useCallback } from "react";
import { api } from "./api/client";
import OnboardingForm from "./components/OnboardingForm";
import DailyInputForm from "./components/DailyInputForm";
import MondayWeeklyForm from "./components/MondayWeeklyForm";
import FridayWeeklyReviewForm from "./components/FridayWeeklyReviewForm";
import MetricsDashboard from "./components/MetricsDashboard";
import AIWeeklyReview from "./components/AIWeeklyReview";
import ReviewHistory from "./components/ReviewHistory";

export default function App() {
  const [view, setView] = useState("dashboard");
  const [onboarding, setOnboarding] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [latestReview, setLatestReview] = useState(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const data = await api.getDashboard();
      setDashboard(data);
    } catch (e) {
      console.error("Dashboard fetch failed", e);
    }
  }, []);

  const fetchReviews = useCallback(async () => {
    try {
      const data = await api.getReviews();
      setReviews(data);
    } catch (e) {
      console.error("Reviews fetch failed", e);
    }
  }, []);

  useEffect(() => {
    async function init() {
      try {
        const ob = await api.getOnboarding();
        setOnboarding(ob);
        await fetchDashboard();
        await fetchReviews();
      } catch (e) {
        console.error("Init failed", e);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [fetchDashboard, fetchReviews]);

  function handleReviewGenerated(review) {
    setLatestReview(review);
    fetchDashboard();
    fetchReviews();
    setView("dashboard");
  }

  function handleDataSaved() {
    fetchDashboard();
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-slate-500 text-sm">Loading…</p>
      </div>
    );
  }

  if (!onboarding) {
    return (
      <OnboardingForm
        onComplete={async () => {
          const ob = await api.getOnboarding();
          setOnboarding(ob);
          await fetchDashboard();
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-900">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-slate-100 tracking-tight">
              Operational Review
            </h1>
            <p className="text-xs text-slate-600 mt-0.5">{onboarding?.role_type}</p>
          </div>
          <nav className="flex gap-1">
            {[
              { id: "dashboard", label: "Dashboard" },
              { id: "daily", label: "Daily Log" },
              { id: "monday", label: "Monday" },
              { id: "friday", label: "Friday Review" },
              { id: "history", label: "History" },
            ].map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setView(id)}
                className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  view === id
                    ? "bg-slate-700 text-slate-100"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-800"
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {view === "dashboard" && (
          <DashboardView dashboard={dashboard} latestReview={latestReview} />
        )}
        {view === "daily" && (
          <Panel title="Daily Operational Log">
            <DailyInputForm onSaved={handleDataSaved} />
            <RecentLogs logs={dashboard?.recent_logs} />
          </Panel>
        )}
        {view === "monday" && (
          <Panel title="Monday — Weekly Commitments">
            <MondayWeeklyForm onSaved={handleDataSaved} />
          </Panel>
        )}
        {view === "friday" && (
          <Panel title="Friday — Weekly Review">
            <FridayWeeklyReviewForm
              onSaved={handleDataSaved}
              onReviewGenerated={handleReviewGenerated}
            />
          </Panel>
        )}
        {view === "history" && (
          <Panel title="Review History">
            <ReviewHistory reviews={reviews} />
          </Panel>
        )}
      </main>
    </div>
  );
}

function DashboardView({ dashboard, latestReview }) {
  const review = latestReview || dashboard?.latest_review;

  return (
    <div className="space-y-10">
      <div>
        <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-4">
          Current Week Metrics
        </h2>
        <MetricsDashboard metrics={dashboard?.metrics} />
      </div>

      {review && (
        <div>
          <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-4">
            Latest Review
          </h2>
          <AIWeeklyReview review={review} />
        </div>
      )}

      {dashboard?.recent_logs?.length > 0 && (
        <div>
          <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-4">
            Recent Daily Logs
          </h2>
          <RecentLogs logs={dashboard.recent_logs} compact />
        </div>
      )}
    </div>
  );
}

function RecentLogs({ logs, compact }) {
  if (!logs || logs.length === 0) return null;

  return (
    <div className={compact ? "" : "mt-8"}>
      {!compact && (
        <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">
          Recent logs
        </h3>
      )}
      <div className="space-y-2">
        {logs.slice(0, compact ? 5 : 10).map((log) => (
          <div key={log.id} className="border border-slate-800 rounded p-3 bg-slate-900">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-300">{log.date}</span>
              <div className="flex gap-3 text-xs text-slate-500">
                <span>Score: {log.execution_score}/10</span>
                <span>DW: {log.deep_work_blocks}</span>
                {log.friction_tag && (
                  <span className="text-slate-600">{log.friction_tag.replace(/_/g, " ")}</span>
                )}
              </div>
            </div>
            {log.tasks?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {log.tasks.map((t) => (
                  <span
                    key={t.id}
                    className={`text-xs px-2 py-0.5 rounded-full border ${taskBadge(t.status)}`}
                  >
                    {t.description}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="max-w-2xl">
      <h2 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-6">{title}</h2>
      {children}
    </div>
  );
}

function taskBadge(status) {
  switch (status) {
    case "done": return "bg-emerald-950 border-emerald-800 text-emerald-400";
    case "partial": return "bg-amber-950 border-amber-800 text-amber-400";
    case "deferred": return "bg-slate-800 border-slate-600 text-slate-400";
    case "dropped": return "bg-red-950 border-red-900 text-red-500";
    default: return "bg-slate-800 border-slate-700 text-slate-400";
  }
}
