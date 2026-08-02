import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { DRILLS_ONLY } from './build'

// On the phone the pair list lives only in this device's storage, so ask the
// browser not to evict it when space runs low. Best-effort: not all browsers
// implement it, and it may be refused.
if (DRILLS_ONLY) {
  void navigator.storage?.persist?.().catch(() => {})
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
