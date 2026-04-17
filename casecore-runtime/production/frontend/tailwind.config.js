/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
          600: "#475569",
          500: "#64748b",
          400: "#94a3b8",
          300: "#cbd5e1",
          200: "#e2e8f0",
          100: "#f1f5f9",
          50: "#f8fafc",
        },
        blue: {
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
        }
      },
      spacing: {
        "safe-top": "max(1rem, env(safe-area-inset-top))",
        "safe-bottom": "max(1rem, env(safe-area-inset-bottom))",
      }
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
  ],
}
