import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#0c1117", 900: "#111822", 800: "#17202c", 700: "#223042", 600: "#2f4056" },
        mist: { 100: "#e8edf4", 300: "#a9b6c8", 500: "#74839a" },
        pdf: "#6aa9ff",
        web: "#4fd1a5",
        direct: "#c3a6ff",
        warn: "#f2b25c",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
