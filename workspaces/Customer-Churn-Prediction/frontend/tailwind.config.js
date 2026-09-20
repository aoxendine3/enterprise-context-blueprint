/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      colors: {
        brand: {
          primary: '#6d5dfc',
          secondary: '#2f80ed',
          accent: '#19c37d',
        },
      },
      boxShadow: {
        glow: '0 0 35px rgba(109, 93, 252, .35)',
        'glow-green': '0 0 25px rgba(25, 195, 125, .28)',
        'glow-red': '0 0 20px rgba(255, 69, 96, .25)',
      },
      animation: {
        float: 'float 4s ease-in-out infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
      },
    },
  },
  plugins: [],
}
