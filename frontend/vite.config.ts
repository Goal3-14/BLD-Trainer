import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Proxy API calls to the FastAPI backend during development.
    // Use 127.0.0.1 (not localhost): Node resolves localhost to IPv6 ::1 first,
    // but uvicorn binds IPv4 127.0.0.1 by default, which would break the proxy.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
