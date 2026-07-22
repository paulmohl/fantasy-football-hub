/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:             '#0B0E14',
        surface:        '#141822',
        'surface-hover':'#1B2030',
        raised:         '#1B2030',
        border:         '#262C3A',
        accent:         '#3DA9FC',
        success:        '#5CC8A9',
        warning:        '#F2B66D',
        danger:         '#F26D6D',
        text:           '#E8ECF1',
        muted:          '#9AA3B2',
        'my-pick':      '#5CC8A9',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
