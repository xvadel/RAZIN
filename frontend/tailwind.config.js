/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#090d16',
        surface: {
          50: '#1e2433',
          100: '#161b26',
          200: '#111520',
          300: '#0d111a',
        },
        forensic: {
          blood: '#ef4444',
          bloodBg: 'rgba(239, 68, 68, 0.15)',
          footprint: '#f97316',
          footprintBg: 'rgba(249, 115, 22, 0.15)',
          device: '#06b6d4',
          deviceBg: 'rgba(6, 182, 212, 0.15)',
          confirmed: '#10b981',
          review: '#f59e0b',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
      },
      boxShadow: {
        'glow-cyan': '0 0 20px -5px rgba(6, 182, 212, 0.3)',
        'glow-red': '0 0 20px -5px rgba(239, 68, 68, 0.3)',
        'glow-amber': '0 0 20px -5px rgba(245, 158, 11, 0.3)',
      }
    },
  },
  plugins: [],
}
