import { useCallback, useEffect, useState } from 'react'
import { imageUrl, type ImageMap } from '../api/images'
import { entryList, normalizePair, type Lexicon, type PairEntry } from '../lexicon'
import { useTimer } from '../useTimer'

export type Direction = 'lettersToWords' | 'wordsToLetters' | 'imagesToLetters'

function pick(entries: PairEntry[], n: number): PairEntry[] {
  const out: PairEntry[] = []
  for (let i = 0; i < n; i++) {
    out.push(entries[Math.floor(Math.random() * entries.length)])
  }
  return out
}

export function isCorrect(direction: Direction, entry: PairEntry, answer: string): boolean {
  const a = answer.trim().toLowerCase()
  if (!a) return false
  if (direction !== 'lettersToWords') return normalizePair(answer) === entry.pair
  return (
    a === entry.word.trim().toLowerCase() ||
    entry.ideas.some((idea) => idea.trim().toLowerCase() === a)
  )
}

export function PairDrill({
  lexicon,
  direction,
  images = {},
  imagesVersion = 0,
}: {
  lexicon: Lexicon
  direction: Direction
  images?: ImageMap
  imagesVersion?: number
}) {
  const [count, setCount] = useState(5)
  const [items, setItems] = useState<PairEntry[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [checked, setChecked] = useState(false)
  const { elapsed, start: startTimer, stop: stopTimer } = useTimer()

  // Images→letters drills over every pair that has an image (a lexicon entry is
  // not required); the word drills need entries with words.
  const pool = useCallback((): PairEntry[] => {
    if (direction === 'imagesToLetters') {
      return Object.keys(images)
        .sort()
        .map((p) => lexicon.entries[p] ?? { pair: p, word: '', ideas: [] })
    }
    return entryList(lexicon).filter((e) => e.word)
  }, [lexicon, images, direction])

  const hasEntries = pool().length > 0

  const start = useCallback(() => {
    const es = pool()
    if (!es.length) {
      setItems([])
      return
    }
    const picked = pick(es, count)
    setItems(picked)
    setAnswers(Array(picked.length).fill(''))
    setChecked(false)
    startTimer()
  }, [pool, count, startTimer])

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
          {direction === 'imagesToLetters' ? (
            <>
              No images yet. Add images to your pairs in the <b>Letter-Pair Sheet</b> tab to use
              this drill.
            </>
          ) : (
            <>
              No letter pairs yet. Add some in the <b>Letter-Pair Sheet</b> tab (or load the
              examples there) to use this drill.
            </>
          )}
        </p>
      </section>
    )
  }

  const score = items.filter((e, i) => isCorrect(direction, e, answers[i] ?? '')).length
  const prompt = (e: PairEntry) =>
    direction === 'imagesToLetters' ? (
      <img className="prompt-img" src={imageUrl(e.pair, imagesVersion)} alt="which pair?" />
    ) : direction === 'lettersToWords' ? (
      e.pair
    ) : (
      e.word
    )
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
