/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                epitech: {
                    blue: '#013afb',     // Primary Blue from "Pixels"
                    green: '#00ff97',    // Accent Green
                    pink: '#ff1ef7',     // Accent Pink
                    purple: '#ff5f3a',   // Accent Orange (named purple in some contexts but visual is orange/red)
                    dark: '#141414',     // Dark background
                    gray: '#f3f4f6',     // Light background
                }
            },
            fontFamily: {
                heading: ['Anton', 'sans-serif'],
                body: ['"IBM Plex Sans"', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
