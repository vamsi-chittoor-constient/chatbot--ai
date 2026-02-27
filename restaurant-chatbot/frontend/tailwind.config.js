/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chat-bg': '#212121',
        'chat-secondary': '#2f2f2f',
        'chat-message': '#343541',
        'chat-user': '#2f2f2f',
        'chat-assistant': '#444654',
        'chat-border': '#4e4e5a',
        'accent': '#10a37f',
        'accent-hover': '#1a7f64',
      },
    },
  },
  plugins: [],
}
