import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  getNet,
  getScheme,
  getScramble,
  getTrace,
  validateMemo,
  type OrbitInfo,
  type SchemeResponse,
  type Targets,
  type TraceResponse,
  type ValidateResponse,
} from '../api/client'
import { CubeNet } from '../cube/CubeNet'
import { chunkPairs, wordIndex, type Lexicon } from '../lexicon'
import { buffersFor } from '../settings'
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

const PLACEHOLDER: Record<string, [string, string]> = {
  corner: ['e.g. FM BP LH', 'e.g. FM radio, blood pressure'],
  edge: ['e.g. UF DK WC', 'e.g. lighthouse, vow'],
  wing: ['e.g. QT NP AB', 'e.g. lighthouse, vow'],
  xcenter: ['e.g. AD BE CF', 'e.g. lighthouse, vow'],
  tcenter: ['e.g. AD BE CF', 'e.g. lighthouse, vow'],
}

export function TypeLettersMode({ settings, lexicon }: ModeProps) {
  // `moves` is the segment to apply right now; `full` is the whole sequence
  // from solved, which is what the cube logic on the server needs.
  const [moves, setMoves] = useState<string[] | null>(null)
  const [continued, setContinued] = useState(false)
  const [net, setNet] = useState<Record<string, string[]> | null>(null)
  const [scheme, setScheme] = useState<SchemeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [inputs, setInputs] = useState<Record<string, string>>({})
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [answer, setAnswer] = useState<TraceResponse | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const [useWords, setUseWords] = useState(() => localStorage.getItem(WORDS_KEY) === '1')
  const startRef = useRef(0)
  const firstRef = useRef<HTMLInputElement>(null)
  const fullRef = useRef<string[] | null>(null)

  const index = useMemo(() => wordIndex(lexicon), [lexicon])
  const size = settings.size
  const buffers = useMemo(() => buffersFor(settings), [settings])
  // Which orbits to ask for comes from the backend, so a 4x4 shows wings and
  // centres without the frontend knowing what a 4x4 has.
  const orbits: OrbitInfo[] = scheme?.size === size ? scheme.orbits : []

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

  useEffect(() => {
    getScheme(size)
      .then(setScheme)
      .catch(() => {})
  }, [size])

  // continueFrom = true keeps the cube where it is and scrambles on top of it,
  // so a rep can start the moment the letters are typed — no solve in between.
  const newScramble = useCallback(
    async (continueFrom = false) => {
      const prefix = continueFrom ? (fullRef.current ?? []) : []
      setError(null)
      setResult(null)
      setAnswer(null)
      setInputs({})
      try {
        const s = await getScramble(settings.topColor, settings.frontColor, prefix, size)
        fullRef.current = s.full
        setMoves(s.scramble)
        setContinued(prefix.length > 0)
        setNet(s.net)
        startRef.current = performance.now()
        setElapsed(0)
        setRunning(true)
        firstRef.current?.focus()
      } catch {
        setError('Cannot reach the backend. Is the API server running on port 8000?')
        setRunning(false)
      }
    },
    [settings.topColor, settings.frontColor, size],
  )

  // A new size means a different cube, so start over rather than reinterpret
  // the old scramble.
  useEffect(() => {
    fullRef.current = null
    void newScramble()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size])

  // Recolor the current scramble's net when orientation changes (no new scramble).
  useEffect(() => {
    const full = fullRef.current
    if (!full) return
    getNet(full, settings.topColor, settings.frontColor, size)
      .then((r) => setNet(r.net))
      .catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings.topColor, settings.frontColor])

  async function submit() {
    const full = fullRef.current
    if (!full) return
    const targets: Targets = {}
    const missing: string[] = []
    for (const orbit of orbits) {
      const raw = inputs[orbit.kind] ?? ''
      if (useWords) {
        const parsed = parseWords(raw, index)
        missing.push(...parsed.unknown)
        targets[orbit.kind] = parsed.letters
      } else {
        targets[orbit.kind] = parseLetters(raw)
      }
    }
    if (missing.length) {
      setError(`Not in your sheet: ${missing.join(', ')}`)
      return
    }
    setError(null)
    setRunning(false)
    try {
      setResult(await validateMemo(full, targets, buffers, size))
    } catch {
      setError('Validation request failed.')
    }
  }

  async function showAnswer() {
    const full = fullRef.current
    if (!full) return
    try {
      setAnswer(await getTrace(full, buffers, size))
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
          {orbits.map((o) => (
            <span key={o.kind}>
              {o.title.toLowerCase()} <b>{buffers[o.kind] ?? o.default_buffer}</b>{' '}
            </span>
          ))}
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
            {orbits.map((orbit, i) => (
              <label key={orbit.kind}>
                {orbit.title}
                <input
                  ref={i === 0 ? firstRef : undefined}
                  className={useWords ? 'words' : ''}
                  value={inputs[orbit.kind] ?? ''}
                  onChange={(e) =>
                    setInputs((prev) => ({ ...prev, [orbit.kind]: e.target.value }))
                  }
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && i === orbits.length - 1) void submit()
                  }}
                  placeholder={PLACEHOLDER[orbit.kind]?.[useWords ? 1 : 0] ?? ''}
                  spellCheck={false}
                  autoComplete="off"
                />
              </label>
            ))}
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
                  ✗ Not solved —{' '}
                  {orbits
                    .map((o) => `${o.title.toLowerCase()} ${result.by_orbit[o.kind] ? '✓' : '✗'}`)
                    .join(', ')}
                </>
              )}
            </div>
          )}

          {answer && (
            <div className="answer">
              {orbits.map((orbit) => {
                const targets = answer.targets[orbit.kind] ?? []
                return (
                  <div key={orbit.kind}>
                    <div>
                      <span className="answer-label">{orbit.title}:</span>{' '}
                      {targets.join(' ') || '—'}
                    </div>
                    {useWords && targets.length > 0 && (
                      <div className="answer-words">{asWords(targets, lexicon)}</div>
                    )}
                  </div>
                )
              })}
              <div className="parity">parity: {answer.parity ? 'yes' : 'no'}</div>
            </div>
          )}
        </>
      )}
    </section>
  )
}
