import { useState } from "react";

export default function IntroPage({ onEnter }) {
  const [leaving, setLeaving] = useState(false);

  function handleEnter() {
    setLeaving(true);
    setTimeout(onEnter, 500);
  }

  return (
    <div className={`min-h-screen bg-black flex flex-col items-center justify-center px-6 transition-opacity duration-500 ${leaving ? "opacity-0" : "opacity-100"}`}
      style={{ background: "radial-gradient(ellipse 90% 70% at 50% 35%, #1f0f0015 0%, #000 65%)" }}>

      {/* Logo */}
      <div className="flex flex-col items-center animate-slide-up" style={{ animationDelay: "0ms" }}>
        <div className="mb-4 relative">
          <img
            src="/Logo.png"
            alt="Cadence"
            className="w-96 h-96 object-contain"
            onError={e => { e.target.style.display = "none"; e.target.nextSibling.style.display = "block"; }}
          />
          <div style={{ display: "none" }}>
            <CadenceLogo />
          </div>
        </div>
      </div>

      {/* Divider */}
      <div className="w-px h-8 bg-gradient-to-b from-transparent via-gold-muted to-transparent mb-6 animate-fade-in" style={{ animationDelay: "300ms" }} />

      {/* What it is */}
      <div className="max-w-md text-center space-y-4 mb-8 animate-fade-in" style={{ animationDelay: "400ms" }}>
        <p className="text-white text-base font-semibold tracking-wide">
          Your AI-powered weekly operating system.
        </p>
        <p className="text-gray-400 text-sm leading-relaxed">
          Plan your week with strategic precision. Track your execution daily. Review your performance with honest diagnosis — and close the gap between who you intend to be as a leader and how you actually show up.
        </p>
      </div>

      {/* Divider 2 */}
      <div className="w-16 h-px mb-8 animate-fade-in" style={{ animationDelay: "450ms", background: "linear-gradient(90deg, transparent, #8B6914, transparent)" }} />

      {/* Authors */}
      <div className="max-w-md text-center animate-fade-in" style={{ animationDelay: "500ms" }}>
        <p className="text-gray-600 text-xs leading-relaxed">
          Grounded in the principles of the world's most respected thinkers on leadership and execution —{" "}
          <span className="text-gray-400">Cal Newport, Greg McKeown, James Clear, Ray Dalio,</span> and more.
        </p>
      </div>

      {/* CTA */}
      <div className="mt-12 animate-fade-in" style={{ animationDelay: "600ms" }}>
        <button
          onClick={handleEnter}
          className="relative px-10 py-4 rounded text-black font-semibold text-sm tracking-widest uppercase transition-all duration-300 hover:scale-105"
          style={{
            background: "linear-gradient(135deg, #8B6914 0%, #D4A520 40%, #F0C040 65%, #C46A1F 100%)",
            boxShadow: "0 0 40px #D4A52033, 0 4px 20px #00000088",
          }}
        >
          Enter Cadence
        </button>
        <p className="text-center text-xs text-gray-700 mt-4">No account required</p>
      </div>

      {/* Bottom glow line */}
      <div className="absolute bottom-0 left-0 right-0 h-px"
        style={{ background: "linear-gradient(90deg, transparent, #D4A52033, transparent)" }} />
    </div>
  );
}

function CadenceLogo() {
  return (
    <svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6B4F0F" />
          <stop offset="30%" stopColor="#D4A520" />
          <stop offset="60%" stopColor="#F0C040" />
          <stop offset="80%" stopColor="#FFD700" />
          <stop offset="100%" stopColor="#C46A1F" />
        </linearGradient>
        <linearGradient id="waveGrad" x1="0%" y1="50%" x2="100%" y2="50%">
          <stop offset="0%" stopColor="#D4A520" stopOpacity="0.3" />
          <stop offset="50%" stopColor="#F0C040" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#FFD700" stopOpacity="1" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>

      {/* Outer arc — C shape */}
      <path
        d="M 200 60 A 90 90 0 1 0 200 196"
        stroke="url(#goldGrad)" strokeWidth="8" fill="none"
        strokeLinecap="round" filter="url(#glow)"
      />
      {/* Inner arcs */}
      <path d="M 185 75 A 72 72 0 1 0 185 181" stroke="url(#goldGrad)" strokeWidth="5" fill="none" strokeLinecap="round" opacity="0.7" />
      <path d="M 170 90 A 54 54 0 1 0 170 166" stroke="url(#goldGrad)" strokeWidth="3.5" fill="none" strokeLinecap="round" opacity="0.5" />
      <path d="M 158 105 A 36 36 0 1 0 158 151" stroke="url(#goldGrad)" strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.35" />

      {/* Sound wave — horizontal through center */}
      <path
        d="M 60 128 L 75 128 L 80 112 L 88 144 L 96 108 L 104 148 L 110 122 L 116 134 L 124 128 L 200 128"
        stroke="url(#waveGrad)" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"
        filter="url(#glow)"
      />

      {/* Flowing lines emanating from center-right */}
      <path d="M 185 128 Q 220 108 240 100" stroke="url(#goldGrad)" strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.9" />
      <path d="M 185 128 Q 218 120 242 116" stroke="url(#goldGrad)" strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.7" />
      <path d="M 185 128 Q 218 136 242 140" stroke="url(#goldGrad)" strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.7" />
      <path d="M 185 128 Q 220 148 240 156" stroke="url(#goldGrad)" strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.9" />

      {/* Bright point at end of lines */}
      <circle cx="242" cy="128" r="4" fill="#FFD700" filter="url(#glow)" opacity="0.9" />
      <circle cx="242" cy="128" r="8" fill="#FFD700" opacity="0.15" />
    </svg>
  );
}
