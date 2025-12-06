/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // New Educational Palette: "Comforting Slate & Teal"
        // Base: Deep Slate (Backgrounds)
        navy: {
          950: '#020617', // Darkest background
          900: '#0f172a', // Main background (Slate 900)
          800: '#1e293b', // Card background (Slate 800)
          700: '#334155', // Border/Hover (Slate 700)
          600: '#475569', // Muted text
        },
        // Primary Accent: Teal/Emerald (Calm, Success, Learning)
        accent: {
          400: '#2dd4bf', // Teal 400 (Highlights)
          500: '#14b8a6', // Teal 500 (Primary Buttons/Active)
          600: '#0d9488', // Teal 600 (Hover)
          900: '#134e4a', // Teal 900 (Deep background accent)
        },
        // Secondary Accent: Indigo/Violet (Structure, Depth)
        secondary: {
          500: '#6366f1', // Indigo 500
          900: '#312e81', // Indigo 900
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}
