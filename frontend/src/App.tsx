import { useEffect, useState } from 'react'
import './App.css'

type HealthState = 'checking…' | 'ok' | 'unreachable'

function App() {
  const [health, setHealth] = useState<HealthState>('checking…')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setHealth(d.status === 'ok' ? 'ok' : 'unreachable'))
      .catch(() => setHealth('unreachable'))
  }, [])

  return (
    <main className="app">
      <h1>BLD Trainer</h1>
      <p className="subtitle">Blindfolded solving — memorization &amp; tracing trainer</p>
      <p className="health">
        backend:{' '}
        <span className={health === 'ok' ? 'ok' : health === 'unreachable' ? 'bad' : ''}>
          {health}
        </span>
      </p>
    </main>
  )
}

export default App
