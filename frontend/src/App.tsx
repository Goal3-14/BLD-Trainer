import './App.css'
import { TypeLettersMode } from './modes/TypeLettersMode'

function App() {
  return (
    <main className="app">
      <header className="app-header">
        <h1>BLD Trainer</h1>
        <p className="subtitle">Blindfolded solving — memorization &amp; tracing</p>
      </header>
      <TypeLettersMode />
    </main>
  )
}

export default App
