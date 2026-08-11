/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f7f7f4",
        ink: "#26251e",
        accent: "#1d6b5c",
        accentSoft: "#e6f2ef",
        card: "#ffffff",
        line: "#e6e5e0",
        muted: "rgba(38,37,30,0.6)",
        healthy: "#1d6b5c",
        attention: "#b45309",
        processing: "#1d4ed8",
        paused: "#6b7280",
        complete: "#0f766e",
        failed: "#b91c1c",
      },
      fontFamily: {
        sans: [
          "IBM Plex Sans",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(38,37,30,0.04), 0 8px 24px rgba(38,37,30,0.04)",
      },
    },
  },
  plugins: [],
};