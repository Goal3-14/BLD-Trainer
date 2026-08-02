import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

// `--mode pages` builds the phone app: drills only, installable, offline, and
// served from a subfolder on GitHub Pages. Anything else is the full desktop app.
// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const pages = mode === 'pages'

  return {
    // GitHub Pages serves the repo at /<repo>/, so assets must be looked up
    // there rather than at the domain root.
    base: pages ? '/BLD-Trainer/' : '/',
    plugins: [
      react(),
      // Only the phone build is installable. A service worker in the desktop
      // build would sit in front of the dev proxy and cache /api responses.
      ...(pages
        ? [
            VitePWA({
              registerType: 'autoUpdate',
              includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
              manifest: {
                name: 'BLD Letter Pairs',
                short_name: 'BLD Pairs',
                description: 'Letter-pair memorization practice for blindfolded cubing.',
                theme_color: '#2563eb',
                background_color: '#ffffff',
                display: 'standalone',
                orientation: 'portrait',
                icons: [
                  { src: 'pwa-192.png', sizes: '192x192', type: 'image/png' },
                  { src: 'pwa-512.png', sizes: '512x512', type: 'image/png' },
                  {
                    src: 'pwa-maskable-512.png',
                    sizes: '512x512',
                    type: 'image/png',
                    purpose: 'maskable',
                  },
                ],
              },
            }),
          ]
        : []),
    ],
    server: {
      // Proxy API calls to the FastAPI backend during development.
      // Use 127.0.0.1 (not localhost): Node resolves localhost to IPv6 ::1 first,
      // but uvicorn binds IPv4 127.0.0.1 by default, which would break the proxy.
      proxy: {
        '/api': 'http://127.0.0.1:8000',
      },
    },
  }
})
