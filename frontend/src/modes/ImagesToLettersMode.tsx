import { PairDrill } from '../components/PairDrill'
import type { ModeProps } from './types'

export function ImagesToLettersMode({ lexicon, images, imagesVersion }: ModeProps) {
  return (
    <PairDrill
      lexicon={lexicon}
      direction="imagesToLetters"
      images={images}
      imagesVersion={imagesVersion}
    />
  )
}
