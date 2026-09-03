import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}", "./components/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        foreground: "var(--color-foreground)",
        muted: "var(--color-muted)",
        "muted-foreground": "var(--color-muted-foreground)",
        border: "var(--color-border)",
        "border-strong": "var(--color-border-strong)",
        accent: "var(--color-accent)",
        "accent-foreground": "var(--color-accent-foreground)",
        "accent-solid": "var(--color-accent-solid)",
        "accent-solid-hover": "var(--color-accent-solid-hover)",
        success: "var(--color-success)",
        "success-bg": "var(--color-success-bg)",
        warning: "var(--color-warning)",
        "warning-bg": "var(--color-warning-bg)",
        danger: "var(--color-danger)",
      },
    },
  },
  plugins: [],
};

export default config;
