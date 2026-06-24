import { PairDrill } from '../components/PairDrill'
import type { ModeProps } from './types'

export function WordsToLettersMode({ lexicon }: ModeProps) {
  return <PairDrill lexicon={lexicon} direction="wordsToLetters" />
}
