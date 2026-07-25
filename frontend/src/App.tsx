import { useCallback, useEffect, useState } from 'react'
import './App.css'
import { getScheme, type SchemeResponse } from './api/client'
import { listImages, type ImageMap } from './api/images'
import { SettingsPanel } from './components/SettingsPanel'
import { loadLexicon, saveLexicon, type Lexicon } from './lexicon'
import { MODES } from './modes/registry'
import { loadSettings, saveSettings, type Settings } from './settings'

const MODE_KEY = 'bld-trainer-mode'

function App() {
  const [settings, setSettings] = useState<Settings>(loadSettings)
  const [lexicon, setLexicon] = useState<Lexicon>(loadLexicon)
  const [scheme, setScheme] = useState<SchemeResponse | null>(null)
  const [activeId, setActiveId] = useState<string>(
    () => localStorage.getItem(MODE_KEY) ?? MODES[0].id,
  )
  const [images, setImages] = useState<ImageMap>({})
  const [imagesVersion, setImagesVersion] = useState(0)

  const refreshImages = useCallback(() => {
    listImages()
      .then((m) => {
        setImages(m)
        setImagesVersion((v) => v + 1)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    refreshImages()
  }, [refreshImages])

  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  useEffect(() => {
    saveLexicon(lexicon)
  }, [lexicon])

  useEffect(() => {
    try {
      localStorage.setItem(MODE_KEY, activeId)
    } catch {
      /* ignore */
    }
  }, [activeId])

  useEffect(() => {
    getScheme()
      .then(setScheme)
      .catch(() => {})
  }, [])

  const updateSettings = (patch: Partial<Settings>) => setSettings((s) => ({ ...s, ...patch }))
  const active = MODES.find((m) => m.id === activeId) ?? MODES[0]
  const Active = active.Component

  return (
    <main className="app">
      <header className="app-header">
        <h1>BLD Trainer</h1>
        <p className="subtitle">Blindfolded solving — memorization &amp; tracing</p>
      </header>

      <nav className="tabs">
        {MODES.map((m) => (
          <button
            key={m.id}
            type="button"
            className={m.id === activeId ? 'tab active' : 'tab'}
            onClick={() => setActiveId(m.id)}
          >
            {m.title}
          </button>
        ))}
      </nav>

      {active.id === 'type-letters' && (
        <SettingsPanel settings={settings} scheme={scheme} onChange={updateSettings} />
      )}

      <Active
        settings={settings}
        lexicon={lexicon}
        updateLexicon={setLexicon}
        images={images}
        imagesVersion={imagesVersion}
        refreshImages={refreshImages}
      />
    </main>
  )
}

export default App
