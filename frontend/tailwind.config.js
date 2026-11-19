/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#14213D",
          900: "#0B1528",
          800: "#14213D",
          700: "#1E2F52",
          600: "#2A3F6B",
        },
        royal: {
          DEFAULT: "#2563EB",
          600: "#2563EB",
          700: "#1D4ED8",
          50: "#EFF6FF",
        },
        ink: "#1E293B",
        canvas: "#F8FAFC",
        credit: "#16A34A",
        debit: "#DC2626",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 28px -18px rgba(15, 23, 42, 0.35)",
        lift: "0 2px 4px rgba(15, 23, 42, 0.05), 0 18px 36px -20px rgba(15, 23, 42, 0.4)",
      },
      borderRadius: {
        "2xl": "1rem",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "toast-in": {
          from: { opacity: "0", transform: "translateY(-8px) scale(0.98)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out both",
        "slide-up": "slide-up 0.3s ease-out both",
        "toast-in": "toast-in 0.22s ease-out both",
      },
    },
  },
  plugins: [],
};
