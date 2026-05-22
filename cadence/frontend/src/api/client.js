import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5001";

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function getToken() {
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token;
}

async function req(path, options = {}) {
  const token = await getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  getProfile:  () => req("/api/profile"),
  saveProfile: (d) => req("/api/profile", { method: "POST", body: JSON.stringify(d) }),

  getDashboard: (weekStart) =>
    req(`/api/dashboard${weekStart ? `?week_start_date=${weekStart}` : ""}`),

  getDailyLogs: () => req("/api/daily-logs"),
  postDailyLog: (d) => req("/api/daily-log", { method: "POST", body: JSON.stringify(d) }),

  startConversation: (d) => req("/api/conversation/start", { method: "POST", body: JSON.stringify(d) }),
  sendMessage:       (d) => req("/api/conversation/message", { method: "POST", body: JSON.stringify(d) }),

  generateReview: (d) => req("/api/reviews/generate", { method: "POST", body: JSON.stringify(d) }),
  getReviews:     () => req("/api/reviews"),

  tts: (text) => req("/api/tts", { method: "POST", body: JSON.stringify({ text }) }),

  health: () => req("/api/health"),

  async generateReport(weekStart) {
    const token = await getToken();
    const res = await fetch(`${API_BASE}/api/report/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ week_start_date: weekStart }),
    });
    if (!res.ok) throw new Error(`Report error ${res.status}`);
    return res.blob();
  },
};
