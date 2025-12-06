/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0f172a', // Main background (Slate 900)
          800: '#1e293b', // Card background (Slate 800)
          700: '#334155', // Border/Hover (Slate 700)
        },
        accent: {
          500: '#3b82f6', // Blue 500
          600: '#2563eb', // Blue 600
        }
      }
    },
  },
  plugins: [],
}
