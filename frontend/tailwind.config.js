/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B2545",
        teal: "#0F5C5C",
        tealbright: "#12897E",
        paper: "#F6F8FA",
        slate: "#5B6B79",
        line: "#E2E8ED",
        critical: "#DC2626",
        high: "#EA580C",
        medium: "#CA8A04",
        low: "#16A34A",
      },
      fontFamily: {
        display: ["'Source Serif 4'", "Georgia", "serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
}
