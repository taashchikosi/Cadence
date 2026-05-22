/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#C9A84C",
          light:   "#E5C472",
          muted:   "#7A6330",
          dark:    "#8B6914",
        },
        dark: {
          DEFAULT:  "#0A0A0A",
          surface:  "#111111",
          elevated: "#1A1A1A",
          border:   "#222222",
          hover:    "#1E1E1E",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-gold": "pulse-gold 2s cubic-bezier(0.4,0,0.6,1) infinite",
        "fade-in":    "fade-in 0.3s ease-out",
      },
      keyframes: {
        "pulse-gold": {
          "0%,100%": { opacity: 1 },
          "50%":     { opacity: 0.5 },
        },
        "fade-in": {
          from: { opacity: 0, transform: "translateY(4px)" },
          to:   { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
}
