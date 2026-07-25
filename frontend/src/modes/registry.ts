import { LexiconEditor } from '../components/LexiconEditor'
import { FullSweepMode } from './FullSweepMode'
import { ImagesToLettersMode } from './ImagesToLettersMode'
import { LettersToImagesMode } from './LettersToImagesMode'
import { LettersToWordsMode } from './LettersToWordsMode'
import { TypeLettersMode } from './TypeLettersMode'
import type { ModeDef } from './types'
import { WordsToLettersMode } from './WordsToLettersMode'

export const MODES: ModeDef[] = [
  { id: 'type-letters', title: 'Type the Letters', Component: TypeLettersMode },
  { id: 'letters-to-words', title: 'Letters → Words', Component: LettersToWordsMode },
  { id: 'words-to-letters', title: 'Words → Letters', Component: WordsToLettersMode },
  { id: 'letters-to-images', title: 'Letters → Images', Component: LettersToImagesMode },
  { id: 'images-to-letters', title: 'Images → Letters', Component: ImagesToLettersMode },
  { id: 'full-sweep', title: 'Full Sweep', Component: FullSweepMode },
  { id: 'sheet', title: 'Letter-Pair Sheet', Component: LexiconEditor },
]
