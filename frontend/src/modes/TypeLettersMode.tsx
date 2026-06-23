import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getScramble,
  getTrace,
  validateMemo,
  type ScrambleResponse,
  type TraceResponse,
  type ValidateResponse,
} from '../api/client'
import { CubeNet } from '../cube/CubeNet'

// Keep only valid Speffz letters (A-X), uppercased, as a flat array.
function parseLetters(input: string): string[] {
  return input.toUpperCase().replace(/[^A-X]/g, '').split('')
}

export function TypeLettersMode() {
  const [scr, setScr] = useState<ScrambleResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cornerInput, setCornerInput] = useState('')
  const [edgeInput, setEdgeInput] = useState('')
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [answer, setAnswer] = useState<TraceResponse | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const startRef = useRef(0)
  const cornerRef = useRef<HTMLInputElement>(null)

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
      const s = await getScramble(20)
      setScr(s)
      startRef.current = performance.now()
      setElapsed(0)
      setRunning(true)
      cornerRef.current?.focus()
    } catch {
      setError('Cannot reach the backend. Is the API server running on port 8000?')
      setRunning(false)
    }
  }, [])

  useEffect(() => {
    void newScramble()
  }, [newScramble])

  async function submit() {
    if (!scr) return
    setRunning(false)
    try {
      const v = await validateMemo(
        scr.scramble,
        parseLetters(cornerInput),
        parseLetters(edgeInput),
        scr.corner_buffer,
        scr.edge_buffer,
      )
      setResult(v)
    } catch {
      setError('Validation request failed.')
    }
  }

  async function showAnswer() {
    if (!scr) return
    try {
      setAnswer(await getTrace(scr.scramble, scr.corner_buffer, scr.edge_buffer))
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
        {scr && (
          <span className="buffers">
            buffers — corner <b>{scr.corner_buffer}</b>, edge <b>{scr.edge_buffer}</b>
          </span>
        )}
      </div>

      {error && <p className="error">{error}</p>}

      {scr && (
        <>
          <p className="scramble">{scr.scramble.join(' ')}</p>
          <CubeNet net={scr.net} />

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
