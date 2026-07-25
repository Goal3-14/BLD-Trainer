import { useCallback, useEffect, useState } from 'react'
import { imageUrl } from '../api/images'
import { shuffle } from '../shuffle'
import { useTimer } from '../useTimer'
import type { ModeProps } from './types'

interface Round {
  pair: string
  options: string[] // pairs whose images are shown as choices
}

function makeRounds(pairs: string[], count: number, choices: number): Round[] {
  return Array.from({ length: count }, () => {
    const pair = pairs[Math.floor(Math.random() * pairs.length)]
    const distractors = shuffle(pairs.filter((p) => p !== pair)).slice(0, choices - 1)
    return { pair, options: shuffle([pair, ...distractors]) }
  })
}

// Shown a letter pair, click the matching image among decoys drawn from your
// other pair images.
export function LettersToImagesMode({ images, imagesVersion }: ModeProps) {
  const [count, setCount] = useState(5)
  const [rounds, setRounds] = useState<Round[]>([])
  const [answers, setAnswers] = useState<string[]>([])
  const [idx, setIdx] = useState(0)
  const [done, setDone] = useState(false)
  const { elapsed, start: startTimer, stop: stopTimer } = useTimer()

  const pairs = Object.keys(images).sort()
  const choices = Math.min(4, pairs.length)

  const start = useCallback(() => {
    if (pairs.length < 2) {
      setRounds([])
      return
    }
    setRounds(makeRounds(pairs, count, choices))
    setAnswers([])
    setIdx(0)
    setDone(false)
    startTimer()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [images, count, startTimer])

  useEffect(() => {
    start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function answer(picked: string) {
    const next = [...answers, picked]
    setAnswers(next)
    if (next.length >= rounds.length) {
      setDone(true)
      stopTimer()
    } else {
      setIdx(idx + 1)
    }
  }

  if (pairs.length < 2) {
    return (
      <section className="mode">
        <p className="empty-note">
          This drill needs at least 2 pairs with images. Add images in the{' '}
          <b>Letter-Pair Sheet</b> tab.
        </p>
      </section>
    )
  }

  const misses = rounds
    .map((r, i) => ({ ...r, picked: answers[i] }))
    .filter((r) => r.picked !== undefined && r.picked !== r.pair)
  const score = answers.filter((a, i) => a === rounds[i]?.pair).length

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

      {!done && rounds[idx] && (
        <div className="img-quiz">
          <div className="img-quiz-prompt">
            <span className="prompt big">{rounds[idx].pair}</span>
            <span className="progress">
              {idx + 1}/{rounds.length}
            </span>
          </div>
          <div className="img-choices">
            {rounds[idx].options.map((p) => (
              <button key={p} type="button" className="img-choice" onClick={() => answer(p)}>
                <img src={imageUrl(p, imagesVersion)} alt="option" />
              </button>
            ))}
          </div>
        </div>
      )}

      {done && (
        <>
          <div className={`result ${score === rounds.length ? 'good' : 'bad'}`}>
            {score}/{rounds.length} correct ({elapsed.toFixed(1)}s)
          </div>
          {misses.length > 0 && (
            <div className="miss-review">
              <p className="io-label">Missed:</p>
              {misses.map((m, i) => (
                <div key={i} className="miss-row">
                  <span className="mono">{m.pair}</span>
                  <img src={imageUrl(m.pair, imagesVersion)} alt={`correct for ${m.pair}`} />
                  <span className="arrow">you picked</span>
                  <img src={imageUrl(m.picked, imagesVersion)} alt="your pick" />
                  <span className="mono dim">{m.picked}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
