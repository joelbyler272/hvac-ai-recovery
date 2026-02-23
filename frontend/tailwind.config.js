/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: "#1B2A4A",
          deep: "#111D35",
          light: "#243556",
        },
        ember: {
          DEFAULT: "#E86A2A",
          dark: "#D15A1E",
          glow: "#F4813F",
        },
        warm: {
          white: "#FAF7F2",
        },
        slate: {
          DEFAULT: "#4A5568",
          light: "#718096",
          muted: "#A0AEC0",
        },
        teal: {
          DEFAULT: "#38B2AC",
        },
        // Keep 'brand' as alias mapped to ember so any missed references render orange
        brand: {
          50: "#FFF5F0",
          100: "#FFEAD9",
          200: "#FFD0B0",
          300: "#FFB088",
          400: "#F4813F",
          500: "#E86A2A",
          600: "#E86A2A",
          700: "#D15A1E",
          800: "#B04A15",
          900: "#8A3810",
        },
      },
      borderRadius: {
        card: "12px",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(27, 42, 74, 0.06), 0 1px 2px -1px rgba(27, 42, 74, 0.06)",
        "card-hover":
          "0 4px 6px -1px rgba(27, 42, 74, 0.08), 0 2px 4px -2px rgba(27, 42, 74, 0.06)",
      },
      fontFamily: {
        mono: ["var(--font-jetbrains)", "JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
