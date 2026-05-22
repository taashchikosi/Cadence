import { useState, useEffect } from "react";

const REMINDER_HOUR_START = 13; // 1pm
const REMINDER_HOUR_END   = 19; // 7pm
const STORAGE_KEY = "cadence_friday_reminder_dismissed";

function isFridayAfternoon() {
  const now = new Date();
  return now.getDay() === 5 &&
    now.getHours() >= REMINDER_HOUR_START &&
    now.getHours() < REMINDER_HOUR_END;
}

function wasDismissedToday() {
  const dismissed = localStorage.getItem(STORAGE_KEY);
  if (!dismissed) return false;
  return new Date(dismissed).toDateString() === new Date().toDateString();
}

export default function FridayReminder({ onStartSession }) {
  const [visible, setVisible]     = useState(false);
  const [notifAsked, setNotifAsked] = useState(false);

  useEffect(() => {
    if (isFridayAfternoon() && !wasDismissedToday()) {
      setVisible(true);
    }

    // Request notification permission once
    if ("Notification" in window && Notification.permission === "default" && !notifAsked) {
      setNotifAsked(true);
      Notification.requestPermission().then(perm => {
        if (perm === "granted") scheduleWeeklyNotification();
      });
    }
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, new Date().toISOString());
    setVisible(false);
  }

  function handleStart() {
    dismiss();
    onStartSession();
  }

  if (!visible) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-sm animate-fade-in">
      <div className="bg-dark-elevated border border-gold-muted rounded-lg p-5 shadow-2xl">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gold animate-pulse-gold" />
            <span className="text-xs font-semibold text-gold uppercase tracking-widest">
              Friday Review
            </span>
          </div>
          <button onClick={dismiss}
            className="text-gray-600 hover:text-gray-400 text-lg leading-none ml-4">
            ×
          </button>
        </div>
        <p className="text-sm text-white mb-1">Time to close the week.</p>
        <p className="text-xs text-gray-500 mb-4 leading-relaxed">
          Review this week's performance and set your priorities for next week.
        </p>
        <button onClick={handleStart} className="btn-gold w-full text-xs py-2">
          Start Weekly Session
        </button>
      </div>
    </div>
  );
}

function scheduleWeeklyNotification() {
  if (!("Notification" in window) || Notification.permission !== "granted") return;

  // Fire a notification now if it's Friday afternoon and hasn't been shown today
  if (isFridayAfternoon() && !wasDismissedToday()) {
    new Notification("Cadence — Friday Review", {
      body: "Time to close the week and set next week's priorities.",
      icon: "/vite.svg",
      tag: "cadence-friday",
    });
  }
}
