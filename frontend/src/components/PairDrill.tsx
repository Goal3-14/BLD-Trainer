import { useCallback, useEffect, useState } from 'react'
import { entryList, normalizePair, type Lexicon, type PairEntry } from '../lexicon'
import { useTimer } from '../useTimer'

export type Direction = 'lettersToWords' | 'wordsToLetters'

function pick(entries: PairEntry[], n: number): PairEntry[] {
  const out: PairEntry[] = []
  for (let i = 0; i < n; i++) {
    out.push(entries[Math.floor(Math.random() * entries.length)])
  }
  return out
}

function isCorrect(direction: Direction, entry: PairEntry, answer: string): boolean {
  const a = answer.trim().toLowerCase()
  if (!a) return false
  if (direction === 'wordsToLetters') return normalizePair(answer) === entry.pair
  return (
    a === entry.word.trim().toLowerCase() ||
    entry.ideas.some((idea) => idea.trim().toLowerCase() === a)
  )
}

export function PairDrill({ lexicon, direction }: { lexicon: Lexicon; direction: Direction }) {
  const [count, setCount] = useState(5)
  const [items, setItems] = useState<PairEntry[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [checked, setChecked] = useState(false)
  const { elapsed, start: startTimer, stop: stopTimer } = useTimer()

  const hasEntries = entryList(lexicon).some((e) => e.word)

  const start = useCallback(() => {
    const es = entryList(lexicon).filter((e) => e.word)
    if (!es.length) {
      setItems([])
      return
    }
    const picked = pick(es, count)
    setItems(picked)
    setAnswers(Array(picked.length).fill(''))
    setChecked(false)
    startTimer()
  }, [lexicon, count, startTimer])

  useEffect(() => {
    start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function check() {
    setChecked(true)
    stopTimer()
  }

  if (!hasEntries) {
    return (
      <section className="mode">
        <p className="empty-note">
          No letter pairs yet. Add some in the <b>Letter-Pair Sheet</b> tab (or load the examples
          there) to use this drill.
        </p>
      </section>
    )
  }

  const score = items.filter((e, i) => isCorrect(direction, e, answers[i] ?? '')).length
  const prompt = (e: PairEntry) => (direction === 'lettersToWords' ? e.pair : e.word)
  const expected = (e: PairEntry) =>
    direction === 'lettersToWords' ? [e.word, ...e.ideas].filter(Boolean).join(' / ') : e.pair

  return (
    <section className="mode">
      <div className="mode-bar">
        <button type="button" onClick={start}>
          New
        </button>
        <label className="count">
          count
          <input
            type="number"
            min={1}
            max={50}
            value={count}
            onChange={(e) => setCount(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
          />
        </label>
        <span className="timer">{elapsed.toFixed(1)}s</span>
      </div>

      <div className="drill">
        {items.map((e, i) => {
          const ok = isCorrect(direction, e, answers[i] ?? '')
          return (
            <div key={i} className="drill-row">
              <span className="prompt">{prompt(e)}</span>
              <input
                value={answers[i] ?? ''}
                onChange={(ev) => {
                  const next = answers.slice()
                  next[i] = ev.target.value
                  setAnswers(next)
                }}
                onKeyDown={(ev) => {
                  if (ev.key === 'Enter') check()
                }}
                spellCheck={false}
                autoComplete="off"
                className={checked ? (ok ? 'ok' : 'bad') : ''}
              />
              {checked && !ok && <span className="expected">{expected(e)}</span>}
            </div>
          )
        })}
      </div>

      {items.length > 0 && (
        <div className="actions">
          <button type="button" onClick={check}>
            Check (Enter)
          </button>
        </div>
      )}

      {checked && (
        <div className={`result ${score === items.length ? 'good' : 'bad'}`}>
          {score}/{items.length} correct ({elapsed.toFixed(1)}s)
        </div>
      )}
    </section>
  )
}
