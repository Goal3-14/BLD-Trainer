import { LexiconEditor } from '../components/LexiconEditor'
import { LettersToWordsMode } from './LettersToWordsMode'
import { TypeLettersMode } from './TypeLettersMode'
import type { ModeDef } from './types'
import { WordsToLettersMode } from './WordsToLettersMode'

export const MODES: ModeDef[] = [
  { id: 'type-letters', title: 'Type the Letters', Component: TypeLettersMode },
  { id: 'letters-to-words', title: 'Letters → Words', Component: LettersToWordsMode },
  { id: 'words-to-letters', title: 'Words → Letters', Component: WordsToLettersMode },
  { id: 'sheet', title: 'Letter-Pair Sheet', Component: LexiconEditor },
]
