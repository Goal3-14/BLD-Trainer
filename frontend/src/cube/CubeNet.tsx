import type { ReactNode } from 'react'
import { STICKER_COLORS } from './colors'

// Top-left (row, col) of each face in a 9-row x 12-col grid (unfolded cross).
const FACE_OFFSET: Record<string, [number, number]> = {
  U: [0, 3],
  L: [3, 0],
  F: [3, 3],
  R: [3, 6],
  B: [3, 9],
  D: [6, 3],
}

interface CubeNetProps {
  net: Record<string, string[]>
  cell?: number
}

export function CubeNet({ net, cell = 26 }: CubeNetProps) {
  const cells: ReactNode[] = []
  for (const [face, [rowStart, colStart]] of Object.entries(FACE_OFFSET)) {
    const colors = net[face] ?? []
    for (let i = 0; i < 9; i++) {
      const r = Math.floor(i / 3)
      const c = i % 3
      cells.push(
        <div
          key={`${face}-${i}`}
          title={face}
          style={{
            gridRow: rowStart + r + 1,
            gridColumn: colStart + c + 1,
            background: STICKER_COLORS[colors[i]] ?? '#444',
            width: cell,
            height: cell,
            border: '1px solid #1c1c1c',
            borderRadius: 3,
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
        gridTemplateColumns: `repeat(12, ${cell}px)`,
        gridTemplateRows: `repeat(9, ${cell}px)`,
        gap: 2,
        justifyContent: 'center',
      }}
    >
      {cells}
    </div>
  )
}
