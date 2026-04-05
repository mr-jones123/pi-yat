/** @type {import('tailwindcss').Config} */
export default {
	content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
	theme: {
		extend: {
			fontFamily: {
				sans: ['"Inter"', "system-ui", "sans-serif"],
				mono: ['"JetBrains Mono"', "monospace"],
			},
			colors: {
				surface: {
					0: "#0a0a0b",
					1: "#111113",
					2: "#1a1a1e",
					3: "#232329",
				},
				accent: {
					DEFAULT: "#3b82f6",
					dim: "#2563eb",
				},
			},
		},
	},
	plugins: [],
};
