/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#eef4ff",
          100: "#dbe6fe",
          500: "#3b6df0",
          600: "#2f56d1",
          700: "#2545ab",
        },
      },
    },
  },
  plugins: [],
};
