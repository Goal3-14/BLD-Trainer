import type { ReactNode } from 'react'
import { STICKER_COLORS } from './colors'

// Top-left (row, col) of each face in the unfolded cross, measured in faces.
const FACE_OFFSET: Record<string, [number, number]> = {
  U: [0, 1],
  L: [1, 0],
  F: [1, 1],
  R: [1, 2],
  B: [1, 3],
  D: [2, 1],
}

interface CubeNetProps {
  net: Record<string, string[]>
  cell?: number
}

export function CubeNet({ net, cell }: CubeNetProps) {
  // The size is whatever the backend sent: 9, 16 or 25 stickers per face.
  const perFace = net.U?.length ?? 9
  const n = Math.round(Math.sqrt(perFace))
  // Keep the whole net a similar width on screen as the cube grows, so a 5x5
  // still fits a phone.
  const px = cell ?? Math.max(12, Math.round(78 / n))

  const cells: ReactNode[] = []
  for (const [face, [faceRow, faceCol]] of Object.entries(FACE_OFFSET)) {
    const colors = net[face] ?? []
    for (let i = 0; i < perFace; i++) {
      cells.push(
        <div
          key={`${face}-${i}`}
          title={face}
          style={{
            gridRow: faceRow * n + Math.floor(i / n) + 1,
            gridColumn: faceCol * n + (i % n) + 1,
            background: STICKER_COLORS[colors[i]] ?? '#444',
            width: px,
            height: px,
            border: '1px solid #1c1c1c',
            borderRadius: n > 3 ? 2 : 3,
            boxSizing: 'border-box',
          }}
        />,
      )
    }
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${4 * n}, ${px}px)`,
        gridTemplateRows: `repeat(${3 * n}, ${px}px)`,
        gap: n > 3 ? 1 : 2,
        justifyContent: 'center',
        maxWidth: '100%',
      }}
    >
      {cells}
    </div>
  )
}
