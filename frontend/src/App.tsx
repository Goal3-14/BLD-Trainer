import { useEffect, useState } from 'react'
import './App.css'
import { getScheme, type SchemeResponse } from './api/client'
import { SettingsPanel } from './components/SettingsPanel'
import { TypeLettersMode } from './modes/TypeLettersMode'
import { loadSettings, saveSettings, type Settings } from './settings'

function App() {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const [scheme, setScheme] = useState<SchemeResponse | null>(null)

  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  useEffect(() => {
    getScheme()
      .then(setScheme)
      .catch(() => {})
  }, [])

  const update = (patch: Partial<Settings>) => setSettings((s) => ({ ...s, ...patch }))

  return (
    <main className="app">
      <header className="app-header">
        <h1>BLD Trainer</h1>
        <p className="subtitle">Blindfolded solving — memorization &amp; tracing</p>
      </header>
      <SettingsPanel settings={settings} scheme={scheme} onChange={update} />
      <TypeLettersMode settings={settings} />
    </main>
  )
}

export default App
