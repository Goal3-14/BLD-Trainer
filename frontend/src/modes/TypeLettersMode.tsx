import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  getNet,
  getScramble,
  getTrace,
  validateMemo,
  type TraceResponse,
  type ValidateResponse,
} from '../api/client'
import { CubeNet } from '../cube/CubeNet'
import { chunkPairs, wordIndex, type Lexicon } from '../lexicon'
import type { ModeProps } from './types'

const WORDS_KEY = 'bld-trainer-type-words'

// Keep only valid Speffz letters (A-X), uppercased, as a flat array.
function parseLetters(input: string): string[] {
  return input.toUpperCase().replace(/[^A-X]/g, '').split('')
}

// Words mode: comma/semicolon/newline separated, since a word may contain
// spaces ("blood pressure"). Anything that isn't a known word but reads as one
// or two Speffz letters passes through as raw letters, so pairs with no word
// yet — and the lone target left by parity — stay typeable.
function parseWords(
  input: string,
  index: Record<string, string>,
): { letters: string[]; unknown: string[] } {
  const letters: string[] = []
  const unknown: string[] = []
  for (const token of input.split(/[,;\n]+/).map((s) => s.trim()).filter(Boolean)) {
    const pair = index[token.toLowerCase()]
    if (pair) {
      letters.push(...pair.split(''))
    } else if (/^[A-Xa-x]{1,2}$/.test(token)) {
      letters.push(...token.toUpperCase().split(''))
    } else {
      unknown.push(token)
    }
  }
  return { letters, unknown }
}

// Render a traced target list as the words it memorizes to, falling back to the
// pair itself where the sheet has no word.
function asWords(letters: string[], lexicon: Lexicon): string {
  return chunkPairs(letters)
    .map((p) => lexicon.entries[p]?.word || p)
    .join(', ')
}

export function TypeLettersMode({ settings, lexicon }: ModeProps) {
  // `moves` is the segment to apply right now; `full` is the whole sequence
  // from solved, which is what the cube logic on the server needs.
  const [moves, setMoves] = useState<string[] | null>(null)
  const [continued, setContinued] = useState(false)
  const [net, setNet] = useState<Record<string, string[]> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cornerInput, setCornerInput] = useState('')
  const [edgeInput, setEdgeInput] = useState('')
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [answer, setAnswer] = useState<TraceResponse | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const [useWords, setUseWords] = useState(() => localStorage.getItem(WORDS_KEY) === '1')
  const startRef = useRef(0)
  const cornerRef = useRef<HTMLInputElement>(null)
  const fullRef = useRef<string[] | null>(null)

  const index = useMemo(() => wordIndex(lexicon), [lexicon])

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setElapsed((performance.now() - startRef.current) / 1000), 100)
    return () => clearInterval(id)
  }, [running])

  useEffect(() => {
    try {
      localStorage.setItem(WORDS_KEY, useWords ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [useWords])

  // continueFrom = true keeps the cube where it is and scrambles on top of it,
  // so a rep can start the moment the letters are typed — no solve in between.
  const newScramble = useCallback(
    async (continueFrom = false) => {
      const prefix = continueFrom ? (fullRef.current ?? []) : []
      setError(null)
      setResult(null)
      setAnswer(null)
      setCornerInput('')
      setEdgeInput('')
      try {
        const s = await getScramble(20, settings.topColor, settings.frontColor, prefix)
        fullRef.current = s.full
        setMoves(s.scramble)
        setContinued(prefix.length > 0)
        setNet(s.net)
        startRef.current = performance.now()
        setElapsed(0)
        setRunning(true)
        cornerRef.current?.focus()
      } catch {
        setError('Cannot reach the backend. Is the API server running on port 8000?')
        setRunning(false)
      }
    },
    [settings.topColor, settings.frontColor],
  )

  // Fetch one scramble on mount.
  useEffect(() => {
    void newScramble()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Recolor the current scramble's net when orientation changes (no new scramble).
  useEffect(() => {
    const full = fullRef.current
    if (!full) return
    getNet(full, settings.topColor, settings.frontColor)
      .then((r) => setNet(r.net))
      .catch(() => {})
  }, [settings.topColor, settings.frontColor])

  async function submit() {
    const full = fullRef.current
    if (!full) return
    let corners: string[]
    let edges: string[]
    if (useWords) {
      const c = parseWords(cornerInput, index)
      const e = parseWords(edgeInput, index)
      const missing = [...c.unknown, ...e.unknown]
      if (missing.length) {
        setError(`Not in your sheet: ${missing.join(', ')}`)
        return
      }
      corners = c.letters
      edges = e.letters
    } else {
      corners = parseLetters(cornerInput)
      edges = parseLetters(edgeInput)
    }
    setError(null)
    setRunning(false)
    try {
      setResult(
        await validateMemo(full, corners, edges, settings.cornerBuffer, settings.edgeBuffer),
      )
    } catch {
      setError('Validation request failed.')
    }
  }

  async function showAnswer() {
    const full = fullRef.current
    if (!full) return
    try {
      setAnswer(await getTrace(full, settings.cornerBuffer, settings.edgeBuffer))
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
        <button
          type="button"
          className="secondary"
          disabled={!moves}
          title="Scramble on top of the cube as it is now — no need to solve first"
          onClick={() => void newScramble(true)}
        >
          Next scramble
        </button>
        <span className="timer">{elapsed.toFixed(1)}s</span>
        <label className="count">
          <input
            type="checkbox"
            checked={useWords}
            onChange={(e) => setUseWords(e.target.checked)}
          />
          answer with words
        </label>
        <span className="buffers">
          buffers — corner <b>{settings.cornerBuffer}</b>, edge <b>{settings.edgeBuffer}</b>
        </span>
      </div>

      {error && <p className="error">{error}</p>}

      {moves && net && (
        <>
          <p className="scramble">{moves.join(' ')}</p>
          {continued && (
            <p className="scramble-note">
              continues from the cube in front of you — don't solve it first
            </p>
          )}
          <CubeNet net={net} />

          <div className="inputs">
            <label>
              Corners
              <input
                ref={cornerRef}
                className={useWords ? 'words' : ''}
                value={cornerInput}
                onChange={(e) => setCornerInput(e.target.value)}
                placeholder={useWords ? 'e.g. FM radio, blood pressure' : 'e.g. FM BP LH'}
                spellCheck={false}
                autoComplete="off"
              />
            </label>
            <label>
              Edges
              <input
                className={useWords ? 'words' : ''}
                value={edgeInput}
                onChange={(e) => setEdgeInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void submit()
                }}
                placeholder={useWords ? 'e.g. lighthouse, vow' : 'e.g. UF DK WC'}
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
              {useWords && answer.corners.length > 0 && (
                <div className="answer-words">{asWords(answer.corners, lexicon)}</div>
              )}
              <div>
                <span className="answer-label">Edges:</span> {answer.edges.join(' ') || '—'}
              </div>
              {useWords && answer.edges.length > 0 && (
                <div className="answer-words">{asWords(answer.edges, lexicon)}</div>
              )}
              <div className="parity">parity: {answer.parity ? 'yes' : 'no'}</div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
