import { useState, useRef, useEffect } from "react";

const DEMO_USERS = [
  { id: "00000000-0000-0000-0000-000000000001", name: "Ligia",   role: "Chief Operations Officer" },
  { id: "00000000-0000-0000-0000-000000000002", name: "Tifano",  role: "VP Marketing" },
  { id: "00000000-0000-0000-0000-000000000003", name: "Qasim",   role: "Head of Operations" },
  { id: "00000000-0000-0000-0000-000000000004", name: "Dilorom", role: "Strategy Director" },
  { id: "00000000-0000-0000-0000-000000000005", name: "Sherzod", role: "Founder & CEO" },
  { id: "00000000-0000-0000-0000-000000000006", name: "Taash",   role: "Chief Executive Officer" },
];

const DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001";

function getStoredUserId() {
  return localStorage.getItem("cadence_demo_user_id") || DEFAULT_USER_ID;
}

function getInitial(name) {
  return name ? name.charAt(0).toUpperCase() : "?";
}

export default function UserSwitcher() {
  const [open, setOpen] = useState(false);
  const [activeId, setActiveId] = useState(getStoredUserId);
  const ref = useRef(null);

  const activeUser = DEMO_USERS.find((u) => u.id === activeId) || DEMO_USERS[0];

  useEffect(() => {
    function handleClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  function switchUser(userId) {
    localStorage.setItem("cadence_demo_user_id", userId);
    setActiveId(userId);
    setOpen(false);
    window.location.reload();
  }

  return (
    <div ref={ref} className="relative">
      {/* Trigger button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 px-2 py-1 rounded border border-dark-border hover:border-gold-muted transition-all"
        style={{ borderColor: "#2A2A2A" }}
        title="Switch demo user"
      >
        {/* Avatar circle */}
        <span
          className="flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold flex-shrink-0"
          style={{
            background: "linear-gradient(135deg, #D4A520, #C46A1F)",
            color: "#0A0A0A",
          }}
        >
          {getInitial(activeUser.name)}
        </span>
        <span className="text-xs text-gray-300 hidden sm:block max-w-[72px] truncate">
          {activeUser.name}
        </span>
        <svg
          className={`w-3 h-3 text-gray-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-56 rounded-lg border shadow-xl z-50 overflow-hidden"
          style={{
            background: "#111111",
            borderColor: "#2A2A2A",
          }}
        >
          <div
            className="px-3 py-2 border-b text-xs font-medium tracking-wide uppercase"
            style={{ borderColor: "#2A2A2A", color: "#6B6B6B" }}
          >
            Demo Users
          </div>
          {DEMO_USERS.map((user) => {
            const isActive = user.id === activeId;
            return (
              <button
                key={user.id}
                onClick={() => switchUser(user.id)}
                className="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-dark-elevated"
                style={{
                  background: isActive ? "#1A1A1A" : "transparent",
                }}
              >
                {/* Avatar */}
                <span
                  className="flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold flex-shrink-0"
                  style={{
                    background: isActive
                      ? "linear-gradient(135deg, #D4A520, #C46A1F)"
                      : "linear-gradient(135deg, #3A3A3A, #2A2A2A)",
                    color: isActive ? "#0A0A0A" : "#999999",
                  }}
                >
                  {getInitial(user.name)}
                </span>
                {/* Name + role */}
                <div className="min-w-0 flex-1">
                  <div
                    className="text-xs font-semibold truncate"
                    style={{ color: isActive ? "#D4A520" : "#E0E0E0" }}
                  >
                    {user.name}
                  </div>
                  <div className="text-xs truncate" style={{ color: "#6B6B6B" }}>
                    {user.role}
                  </div>
                </div>
                {/* Active check */}
                {isActive && (
                  <svg
                    className="w-3.5 h-3.5 flex-shrink-0"
                    style={{ color: "#D4A520" }}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
