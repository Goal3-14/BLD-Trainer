import { PairDrill } from '../components/PairDrill'
import type { ModeProps } from './types'

export function LettersToWordsMode({ lexicon }: ModeProps) {
  return <PairDrill lexicon={lexicon} direction="lettersToWords" />
}
