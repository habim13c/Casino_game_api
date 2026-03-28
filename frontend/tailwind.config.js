/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        heading: ["'Unbounded'", "sans-serif"],
        body: ["'Outfit'", "sans-serif"],
      },
      colors: {
        base: "#0A0A0C",
        surface: "#13111C",
        elevated: "#1C1A27",
        accent: "#00E701",
        "accent-hover": "#00FF01",
        gold: "#FFD700",
        danger: "#FF2A55",
        muted: "#5A5A67",
        "text-secondary": "#A0A0AB",
      },
      animation: {
        'pulse-neon': 'pulse-neon 2s infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        'pulse-neon': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(0,231,1,0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(0,231,1,0.5)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
