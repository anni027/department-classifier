import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        taqneeq: {
          purple: "#6d28d9",
          violet: "#8b5cf6",
          ink: "#0f0b1e",
        },
      },
    },
  },
  plugins: [],
};

export default config;
