import { useCallback, useEffect, useState } from 'react'
import { isCorrect, type Direction } from '../components/PairDrill'
import { entryList, type PairEntry } from '../lexicon'
import { shuffle } from '../shuffle'
import { useTimer } from '../useTimer'
import type { ModeProps } from './types'

type SweepDirection = Exclude<Direction, 'imagesToLetters'>

// Every pair in the sheet exactly once — alphabetical or shuffled — answering
// word from pair or pair from word. The guaranteed full-coverage drill.
export function FullSweepMode({ lexicon }: ModeProps) {
  const [direction, setDirection] = useState<SweepDirection>('lettersToWords')
  const [shuffled, setShuffled] = useState(true)
  const [items, setItems] = useState<PairEntry[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [checked, setChecked] = useState(false)
  const { elapsed, start: startTimer, stop: stopTimer } = useTimer()

  const start = useCallback(() => {
    const pool = entryList(lexicon).filter((e) => e.word)
    setItems(shuffled ? shuffle(pool) : pool)
    setAnswers(Array(pool.length).fill(''))
    setChecked(false)
    startTimer()
  }, [lexicon, shuffled, startTimer])

  useEffect(() => {
    start()
  }, [start, direction])

  function check() {
    setChecked(true)
    stopTimer()
  }

  if (!items.length) {
    return (
      <section className="mode">
        <p className="empty-note">
          No letter pairs with words yet. Add some in the <b>Letter-Pair Sheet</b> tab (or load
          the examples there) to use this drill.
        </p>
      </section>
    )
  }

  const filled = answers.filter((a) => a.trim()).length
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
          <select
            value={direction}
            onChange={(e) => setDirection(e.target.value as SweepDirection)}
          >
            <option value="lettersToWords">letters → words</option>
            <option value="wordsToLetters">words → letters</option>
          </select>
        </label>
        <label className="count">
          <input
            type="checkbox"
            checked={shuffled}
            onChange={(e) => setShuffled(e.target.checked)}
          />
          shuffle
        </label>
        <span className="progress">
          {filled}/{items.length}
        </span>
        <span className="timer">{elapsed.toFixed(1)}s</span>
      </div>

      <div className="drill">
        {items.map((e, i) => {
          const ok = isCorrect(direction, e, answers[i] ?? '')
          return (
            <div key={e.pair} className="drill-row">
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

      <div className="actions">
        <button type="button" onClick={check}>
          Check (Enter)
        </button>
      </div>

      {checked && (
        <div className={`result ${score === items.length ? 'good' : 'bad'}`}>
          {score}/{items.length} correct ({elapsed.toFixed(1)}s)
        </div>
      )}
    </section>
  )
}
