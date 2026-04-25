import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#F6F3EF",
          secondary: "#ECE7E1",
          subtle: "#FAF8F5",
          card: "#FFFFFF",
        },
        ink: {
          primary: "#171412",
          secondary: "#5F5750",
          muted: "#8D837A",
        },
        accent: {
          DEFAULT: "#B85B2A",
          light: "#F0E3DA",
          soft: "#F8EFE9",
          hover: "#93451F",
        },
        border: {
          DEFAULT: "#DED8D1",
          strong: "#BDB4AA",
        },
        success: {
          DEFAULT: "#2F6A4E",
          light: "#E5F2EA",
        },
        error: {
          DEFAULT: "#9B2F2F",
          light: "#F8E6E4",
        },
        warning: {
          DEFAULT: "#8A5A16",
          light: "#F5EAD5",
        },
      },
      fontFamily: {
        display: ["Playfair Display", "Georgia", "serif"],
        body: ["DM Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      maxWidth: {
        content: "920px",
        workspace: "1120px",
        prose: "760px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(23, 20, 18, 0.05), 0 12px 30px rgba(23, 20, 18, 0.035)",
        "card-hover": "0 2px 4px rgba(23, 20, 18, 0.06), 0 18px 40px rgba(23, 20, 18, 0.055)",
      },
      borderRadius: {
        card: "6px",
        panel: "8px",
      },
    },
  },
  plugins: [],
};
export default config;
