/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "Manrope", "ui-sans-serif", "system-ui"] },
      colors: {
        brand: {
          DEFAULT: "#7653D6",
          deep: "#5535A5",
          lavender: "#B9A5F5",
          light: "#EAE3FF",
          background: "#F8F7FC",
          text: "#242036",
          muted: "#858096",
        },
      },
      boxShadow: { soft: "0 18px 50px rgba(91, 58, 150, 0.10)" },
    },
  },
  plugins: [],
};