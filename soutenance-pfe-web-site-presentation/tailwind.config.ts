import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        edu: {
          deep: "#0A0806",
          bg: "#0D0B09",
          card: "#161210",
          elevated: "#1E1A16",
          surface: "#261F1A",
          border: "#2A2420",
          "border-strong": "#3D3530",
          accent: "#C46830",
          "accent-bright": "#E07A3C",
          text: "#F2EDE7",
          secondary: "#A8A09A",
          muted: "#6B6359",
          blue: "#3B82F6",
          "blue-dark": "#2563EB",
          green: "#22C55E",
          "green-dim": "#16A34A",
        },
      },
      fontFamily: {
        display: ["'Playfair Display'", "Georgia", "serif"],
        body: ["'DM Sans'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
      },
    },
  },
  plugins: [],
};
export default config;
