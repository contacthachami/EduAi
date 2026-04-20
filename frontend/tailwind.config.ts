import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#F7F5F2",
          secondary: "#EFEDE9",
          card: "#FFFFFF",
        },
        ink: {
          primary: "#1A1816",
          secondary: "#6B6560",
          muted: "#A09890",
        },
        accent: {
          DEFAULT: "#C4622D",
          light: "#F2E8E1",
          hover: "#A84E23",
        },
        border: {
          DEFAULT: "#E2DDD8",
          strong: "#C8C0B8",
        },
        success: {
          DEFAULT: "#2D6A4F",
          light: "#D8F3DC",
        },
        error: {
          DEFAULT: "#9B2226",
          light: "#FFCCD5",
        },
      },
      fontFamily: {
        display: ["Playfair Display", "Georgia", "serif"],
        body: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      maxWidth: {
        content: "760px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(26, 24, 22, 0.08)",
        "card-hover": "0 2px 8px rgba(26, 24, 22, 0.12)",
      },
      borderRadius: {
        card: "6px",
      },
    },
  },
  plugins: [],
};
export default config;
