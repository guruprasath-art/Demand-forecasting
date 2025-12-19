/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "#0f172a",
        surface: "#020617",
        card: "#020617",
        primary: {
          DEFAULT: "#38bdf8"
        }
      }
    }
  },
  plugins: []
};


