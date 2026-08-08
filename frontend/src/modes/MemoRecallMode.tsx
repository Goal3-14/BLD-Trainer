import { useCallback, useEffect, useRef, useState } from 'react'
import { chunkPairs, entryList, type PairEntry } from '../lexicon'
import { shuffle } from '../shuffle'
import type { ModeProps } from './types'

// The drill the other modes can't do: the pairs go away before you answer.
// Every other mode leaves the prompt on screen, which trains conversion speed;
// holding a sequence after it disappears is the skill a real solve needs.
type Phase = 'idle' | 'memo' | 'recall' | 'done'
type Reveal = 'all' | 'one'
type Hide = 'timer' | 'manual'

interface Mark {
  expected: string
  got: string
  ok: boolean
}

function parsePairs(input: string): string[] {
  return chunkPairs(input.toUpperCase().replace(/[^A-X]/g, '').split(''))
}

export function MemoRecallMode({ lexicon }: ModeProps) {
  const [count, setCount] = useState(11) // ~a 3BLD memo; turn it up for 4/5BLD load
  const [reveal, setReveal] = useState<Reveal>('all')
  const [hide, setHide] = useState<Hide>('manual')
  const [seconds, setSeconds] = useState(20)

  const [phase, setPhase] = useState<Phase>('idle')
  const [items, setItems] = useState<PairEntry[]>([])
  const [shown, setShown] = useState(0) // index during one-at-a-time
  const [answer, setAnswer] = useState('')
  const [marks, setMarks] = useState<Mark[] | null>(null)
  const [memoMs, setMemoMs] = useState(0)
  const [recallMs, setRecallMs] = useState(0)
  const [left, setLeft] = useState(0) // countdown display

  const memoStart = useRef(0)
  const recallStart = useRef(0)
  const stepStart = useRef(0)
  const recallRef = useRef<HTMLInputElement>(null)

  const pool = entryList(lexicon).filter((e) => e.word)
  // Converting pair -> word -> pair is the point, so a pair with no word can't
  // be drilled here.
  const max = pool.length
  const asked = Math.min(count, max) // a small sheet caps how many can be shown

  const toRecall = useCallback(() => {
    setMemoMs(performance.now() - memoStart.current)
    recallStart.current = performance.now()
    setPhase('recall')
  }, [])

  const start = useCallback(() => {
    if (!max) return
    setItems(shuffle(pool).slice(0, asked))
    setShown(0)
    setAnswer('')
    setMarks(null)
    setMemoMs(0)
    setRecallMs(0)
    memoStart.current = performance.now()
    stepStart.current = performance.now()
    setPhase('memo')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pool, asked, max])

  // Auto-hide. For "all at once" the timer covers the whole set; for
  // "one at a time" it runs again for each pair.
  useEffect(() => {
    if (phase !== 'memo' || hide !== 'timer' || !items.length) return
    stepStart.current = performance.now()
    const id = setTimeout(() => {
      if (reveal === 'one' && shown < items.length - 1) setShown((i) => i + 1)
      else toRecall()
    }, seconds * 1000)
    return () => clearTimeout(id)
  }, [phase, hide, reveal, shown, items.length, seconds, toRecall])

  // Countdown readout, kept separate from the timer that actually advances.
  useEffect(() => {
    if (phase !== 'memo' || hide !== 'timer') return
    const id = setInterval(
      () => setLeft(Math.max(0, seconds - (performance.now() - stepStart.current) / 1000)),
      100,
    )
    return () => clearInterval(id)
  }, [phase, hide, seconds, shown])

  useEffect(() => {
    if (phase === 'recall') recallRef.current?.focus()
  }, [phase])

  function next() {
    if (reveal === 'one' && shown < items.length - 1) setShown((i) => i + 1)
    else toRecall()
  }

  function check() {
    setRecallMs(performance.now() - recallStart.current)
    const expected = items.map((e) => e.pair)
    const got = parsePairs(answer)
    const out: Mark[] = []
    for (let i = 0; i < Math.max(expected.length, got.length); i++) {
      out.push({
        expected: expected[i] ?? '—',
        got: got[i] ?? '—',
        ok: expected[i] === got[i],
      })
    }
    setMarks(out)
    setPhase('done')
  }

  if (!max) {
    return (
      <section className="mode">
        <p className="empty-note">
          No letter pairs with words yet. Add some in the <b>Letter-Pair Sheet</b> tab (or load the
          examples there) to use this drill.
        </p>
      </section>
    )
  }

  const solved = marks !== null && marks.every((m) => m.ok)

  return (
    <section className="mode">
      <div className="mode-bar">
        <button type="button" onClick={start}>
          {phase === 'idle' ? 'Start' : 'New'}
        </button>
        <label className="count">
          pairs
          <input
            type="number"
            min={1}
            max={max}
            value={count}
            onChange={(e) => setCount(Math.max(1, Math.min(max, Number(e.target.value) || 1)))}
          />
        </label>
        <label className="count">
          <select value={reveal} onChange={(e) => setReveal(e.target.value as Reveal)}>
            <option value="all">all at once</option>
            <option value="one">one at a time</option>
          </select>
        </label>
        <label className="count">
          <select value={hide} onChange={(e) => setHide(e.target.value as Hide)}>
            <option value="manual">hide when ready</option>
            <option value="timer">hide on timer</option>
          </select>
        </label>
        {hide === 'timer' && (
          <label className="count">
            <input
              type="number"
              min={1}
              max={600}
              value={seconds}
              onChange={(e) => setSeconds(Math.max(1, Math.min(600, Number(e.target.value) || 1)))}
            />
            {reveal === 'one' ? 's each' : 's total'}
          </label>
        )}
      </div>

      {phase === 'idle' && (
        <p className="empty-note">
          {asked} pairs will appear{reveal === 'one' ? ', one at a time' : ' together'}
          {hide === 'timer'
            ? `, hidden after ${seconds}s${reveal === 'one' ? ' each' : ''}`
            : ', hidden when you say so'}
          . Then type them back in order.
        </p>
      )}

      {phase === 'memo' && (
        <>
          <div className="memo-stage">
            {reveal === 'all' ? (
              <div className="memo-pairs">
                {items.map((e, i) => (
                  <span key={i} className="memo-pair">
                    {e.pair}
                  </span>
                ))}
              </div>
            ) : (
              <span className="memo-pair solo">{items[shown]?.pair}</span>
            )}
          </div>
          <div className="mode-bar">
            {reveal === 'one' && (
              <span className="progress">
                {shown + 1} / {items.length}
              </span>
            )}
            {hide === 'timer' ? (
              <span className="timer">{left.toFixed(1)}s</span>
            ) : (
              <button type="button" onClick={next}>
                {reveal === 'one' && shown < items.length - 1 ? 'Next' : 'Hide & recall'}
              </button>
            )}
          </div>
        </>
      )}

      {(phase === 'recall' || phase === 'done') && (
        <>
          <div className="inputs">
            <label>
              Type the {items.length} pairs, in order
              <input
                ref={recallRef}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && phase === 'recall') check()
                }}
                placeholder="e.g. FM BP LH"
                spellCheck={false}
                autoComplete="off"
                readOnly={phase === 'done'}
              />
            </label>
          </div>
          {phase === 'recall' && (
            <div className="actions">
              <button type="button" onClick={check}>
                Check (Enter)
              </button>
            </div>
          )}
        </>
      )}

      {phase === 'done' && marks && (
        <>
          <div className={`result ${solved ? 'good' : 'bad'}`}>
            {solved ? '✓ All correct' : '✗ Not correct'} — memo {(memoMs / 1000).toFixed(1)}s,
            recall {(recallMs / 1000).toFixed(1)}s
          </div>
          {/* All-or-nothing above, but show which pair went wrong. */}
          <div className="marks">
            {marks.map((m, i) => (
              <span key={i} className={`mark ${m.ok ? 'ok' : 'bad'}`}>
                {m.expected}
                {!m.ok && <em>{m.got}</em>}
              </span>
            ))}
          </div>
          <div className="answer">
            <span className="answer-label">Words:</span>{' '}
            {items.map((e) => e.word).join(', ') || '—'}
          </div>
        </>
      )}
    </section>
  )
}
