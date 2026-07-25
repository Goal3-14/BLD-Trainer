import type { ReactElement } from 'react'
import type { ImageMap } from '../api/images'
import type { Lexicon } from '../lexicon'
import type { Settings } from '../settings'

// Shared context every mode receives. Modes ignore what they don't need.
export interface ModeProps {
  settings: Settings
  lexicon: Lexicon
  updateLexicon: (lexicon: Lexicon) => void
  images: ImageMap
  imagesVersion: number
  refreshImages: () => void
}

// A mode is just a titled component over the shared core, so new modes slot in
// without touching the engine.
export interface ModeDef {
  id: string
  title: string
  Component: (props: ModeProps) => ReactElement
}
