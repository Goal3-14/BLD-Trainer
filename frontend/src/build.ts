// Build variants. `vite build --mode pages` produces the phone build: the
// letter-pair drills and a paste box for the sheet, with everything that needs
// the Python backend (scrambles, tracing, images) left out. The default build is
// the full desktop app.
export const DRILLS_ONLY = import.meta.env.MODE === 'pages'
