/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#D4A520",
          light:   "#F0C040",
          bright:  "#FFD700",
          muted:   "#8B6914",
          dark:    "#6B4F0F",
          ember:   "#C46A1F",
        },
        neon: {
          orange: "#F97316",
          teal:   "#06B6D4",
          pink:   "#F43F5E",
          blue:   "#60A5FA",
          purple: "#A855F7",
          green:  "#10B981",
        },
        dark: {
          DEFAULT:  "#050816",
          surface:  "#0C0F1E",
          elevated: "#131629",
          border:   "#1E2245",
          hover:    "#181D38",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-gold":  "pulse-gold 2s cubic-bezier(0.4,0,0.6,1) infinite",
        "fade-in":     "fade-in 0.4s ease-out",
        "slide-up":    "slide-up 0.6s ease-out",
        "glow-pulse":  "glow-pulse 3s ease-in-out infinite",
        "spin-slow":   "spin 12s linear infinite",
      },
      keyframes: {
        "pulse-gold": {
          "0%,100%": { opacity: 1 },
          "50%":     { opacity: 0.5 },
        },
        "fade-in": {
          from: { opacity: 0, transform: "translateY(6px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
        "slide-up": {
          from: { opacity: 0, transform: "translateY(24px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
        "glow-pulse": {
          "0%,100%": { boxShadow: "0 0 20px #D4A52033, 0 0 60px #D4A52011" },
          "50%":     { boxShadow: "0 0 40px #D4A52055, 0 0 100px #D4A52022" },
        },
      },
      backgroundImage: {
        "gold-gradient": "linear-gradient(135deg, #8B6914 0%, #D4A520 40%, #F0C040 60%, #C46A1F 100%)",
        "gold-radial":   "radial-gradient(ellipse at center, #D4A52022 0%, transparent 70%)",
      },
    },
  },
  plugins: [],
}
