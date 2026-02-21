import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      borderRadius: {
        xl: "1rem",
        "2xl": "1.5rem"
      },
      boxShadow: {
        card: "0 10px 35px -18px rgba(9, 38, 43, 0.35)"
      },
      fontFamily: {
        sans: ["Space Grotesk", "Avenir Next", "Segoe UI", "sans-serif"],
        serif: ["Literata", "Georgia", "serif"]
      }
    }
  },
  plugins: []
};

export default config;
