/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        brand: {
          red: '#B5121B',
          indigo: '#4f46e5',
        },
        dark: {
          950: '#0a0a0a',
          900: '#0f0f0f',
          800: '#171717',
          700: '#1e1e1e',
          600: '#262626',
          500: '#2a2a2a',
          400: '#3a3a3a',
        },
        surface: '#1e1e1e',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
