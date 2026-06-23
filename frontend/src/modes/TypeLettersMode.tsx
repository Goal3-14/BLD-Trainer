import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getNet,
  getScramble,
  getTrace,
  validateMemo,
  type TraceResponse,
  type ValidateResponse,
} from '../api/client'
import { CubeNet } from '../cube/CubeNet'
import type { Settings } from '../settings'

// Keep only valid Speffz letters (A-X), uppercased, as a flat array.
function parseLetters(input: string): string[] {
  return input.toUpperCase().replace(/[^A-X]/g, '').split('')
}

export function TypeLettersMode({ settings }: { settings: Settings }) {
  const [scramble, setScramble] = useState<string[] | null>(null)
  const [net, setNet] = useState<Record<string, string[]> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cornerInput, setCornerInput] = useState('')
  const [edgeInput, setEdgeInput] = useState('')
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [answer, setAnswer] = useState<TraceResponse | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const startRef = useRef(0)
  const cornerRef = useRef<HTMLInputElement>(null)
  const scrambleRef = useRef<string[] | null>(null)

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setElapsed((performance.now() - startRef.current) / 1000), 100)
    return () => clearInterval(id)
  }, [running])

  const newScramble = useCallback(async () => {
    setError(null)
    setResult(null)
    setAnswer(null)
    setCornerInput('')
    setEdgeInput('')
    try {
      const s = await getScramble(20, settings.topColor, settings.frontColor)
      scrambleRef.current = s.scramble
      setScramble(s.scramble)
      setNet(s.net)
      startRef.current = performance.now()
      setElapsed(0)
      setRunning(true)
      cornerRef.current?.focus()
    } catch {
      setError('Cannot reach the backend. Is the API server running on port 8000?')
      setRunning(false)
    }
  }, [settings.topColor, settings.frontColor])

  // Fetch one scramble on mount.
  useEffect(() => {
    void newScramble()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recolor the current scramble's net when orientation changes (no new scramble).
  useEffect(() => {
    const scr = scrambleRef.current
    if (!scr) return
    getNet(scr, settings.topColor, settings.frontColor)
      .then((r) => setNet(r.net))
      .catch(() => {})
  }, [settings.topColor, settings.frontColor])

  async function submit() {
    if (!scramble) return
    setRunning(false)
    try {
      const v = await validateMemo(
        scramble,
        parseLetters(cornerInput),
        parseLetters(edgeInput),
        settings.cornerBuffer,
        settings.edgeBuffer,
      )
      setResult(v)
    } catch {
      setError('Validation request failed.')
    }
  }

  async function showAnswer() {
    if (!scramble) return
    try {
      setAnswer(await getTrace(scramble, settings.cornerBuffer, settings.edgeBuffer))
    } catch {
      setError('Trace request failed.')
    }
  }

  return (
    <section className="mode">
      <div className="mode-bar">
        <button type="button" onClick={() => void newScramble()}>
          New scramble
        </button>
        <span className="timer">{elapsed.toFixed(1)}s</span>
        <span className="buffers">
          buffers — corner <b>{settings.cornerBuffer}</b>, edge <b>{settings.edgeBuffer}</b>
        </span>
      </div>

      {error && <p className="error">{error}</p>}

      {scramble && net && (
        <>
          <p className="scramble">{scramble.join(' ')}</p>
          <CubeNet net={net} />

          <div className="inputs">
            <label>
              Corners
              <input
                ref={cornerRef}
                value={cornerInput}
                onChange={(e) => setCornerInput(e.target.value)}
                placeholder="e.g. FM BP LH"
                spellCheck={false}
                autoComplete="off"
              />
            </label>
            <label>
              Edges
              <input
                value={edgeInput}
                onChange={(e) => setEdgeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void submit()
                }}
                placeholder="e.g. UF DK WC"
                spellCheck={false}
                autoComplete="off"
              />
            </label>
          </div>

          <div className="actions">
            <button type="button" onClick={() => void submit()}>
              Check (Enter)
            </button>
            <button type="button" className="secondary" onClick={() => void showAnswer()}>
              Show answer
            </button>
          </div>

          {result && (
            <div className={`result ${result.solved ? 'good' : 'bad'}`}>
              {result.solved ? (
                <>✓ Solved! ({elapsed.toFixed(1)}s)</>
              ) : (
                <>
                  ✗ Not solved — corners {result.corners_solved ? '✓' : '✗'}, edges{' '}
                  {result.edges_solved ? '✓' : '✗'}
                </>
              )}
            </div>
          )}

          {answer && (
            <div className="answer">
              <div>
                <span className="answer-label">Corners:</span> {answer.corners.join(' ') || '—'}
              </div>
              <div>
                <span className="answer-label">Edges:</span> {answer.edges.join(' ') || '—'}
              </div>
              <div className="parity">parity: {answer.parity ? 'yes' : 'no'}</div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
