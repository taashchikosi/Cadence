const BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  getOnboarding: () => request("/api/onboarding"),
  postOnboarding: (data) => request("/api/onboarding", { method: "POST", body: JSON.stringify(data) }),

  getDailyLogs: () => request("/api/daily-logs"),
  postDailyLog: (data) => request("/api/daily-log", { method: "POST", body: JSON.stringify(data) }),

  getMondayInputs: () => request("/api/weekly/monday"),
  postMondayInput: (data) => request("/api/weekly/monday", { method: "POST", body: JSON.stringify(data) }),

  getFridayReviews: () => request("/api/weekly/friday"),
  postFridayReview: (data) => request("/api/weekly/friday", { method: "POST", body: JSON.stringify(data) }),

  getDashboard: () => request("/api/dashboard"),
  getCurrentWeekMetrics: (weekStart) =>
    request(`/api/metrics/current-week${weekStart ? `?week_start_date=${weekStart}` : ""}`),

  generateReview: (data) => request("/api/reviews/generate", { method: "POST", body: JSON.stringify(data) }),
  getReviews: () => request("/api/reviews"),
};
