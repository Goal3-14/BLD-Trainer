import { DRILLS_ONLY } from '../build'
import { LexiconEditor } from '../components/LexiconEditor'
import { SheetImport } from '../components/SheetImport'
import { FullSweepMode } from './FullSweepMode'
import { ImagesToLettersMode } from './ImagesToLettersMode'
import { LettersToImagesMode } from './LettersToImagesMode'
import { LettersToWordsMode } from './LettersToWordsMode'
import { MemoRecallMode } from './MemoRecallMode'
import { TypeLettersMode } from './TypeLettersMode'
import type { ModeDef } from './types'
import { WordsToLettersMode } from './WordsToLettersMode'

const FULL: ModeDef[] = [
  { id: 'type-letters', title: 'Type the Letters', Component: TypeLettersMode },
  { id: 'letters-to-words', title: 'Letters → Words', Component: LettersToWordsMode },
  { id: 'words-to-letters', title: 'Words → Letters', Component: WordsToLettersMode },
  { id: 'letters-to-images', title: 'Letters → Images', Component: LettersToImagesMode },
  { id: 'images-to-letters', title: 'Images → Letters', Component: ImagesToLettersMode },
  { id: 'full-sweep', title: 'Full Sweep', Component: FullSweepMode },
  { id: 'memo-recall', title: 'Memo & Recall', Component: MemoRecallMode },
  { id: 'sheet', title: 'Letter-Pair Sheet', Component: LexiconEditor },
]

// The phone build keeps only what needs no cube logic and no backend: the word
// drills, plus a paste box in place of the full sheet editor.
const DRILLS: ModeDef[] = [
  { id: 'letters-to-words', title: 'Letters → Words', Component: LettersToWordsMode },
  { id: 'words-to-letters', title: 'Words → Letters', Component: WordsToLettersMode },
  { id: 'full-sweep', title: 'Full Sweep', Component: FullSweepMode },
  { id: 'memo-recall', title: 'Memo & Recall', Component: MemoRecallMode },
  { id: 'sheet', title: 'Letter-Pair Sheet', Component: SheetImport },
]

export const MODES: ModeDef[] = DRILLS_ONLY ? DRILLS : FULL
