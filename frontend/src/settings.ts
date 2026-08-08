// User settings, persisted to localStorage so they survive between sessions.

import type { CubeSize } from './api/client'

export interface Settings {
  size: CubeSize
  // Buffer per orbit, per size — a 3BLD edge buffer is UF/C, but a 5BLD midge
  // buffer is conventionally DF/U, so they cannot share one slot. Anything
  // missing falls back to the backend's default for that orbit.
  buffers: Partial<Record<CubeSize, Record<string, string>>>
  cornerBuffer: string
  edgeBuffer: string
  topColor: string
  frontColor: string
}

export const DEFAULT_SETTINGS: Settings = {
  size: 3,
  buffers: {},
  cornerBuffer: 'C', // UFR (U sticker)
  edgeBuffer: 'C', // UF (U sticker)
  topColor: 'white',
  frontColor: 'green',
}

export const CUBE_SIZES: CubeSize[] = [3, 4, 5]

export const SIZE_LABEL: Record<CubeSize, string> = {
  3: '3x3 (3BLD)',
  4: '4x4 (4BLD)',
  5: '5x5 (5BLD)',
}

/** Buffers to send for the active size. The 3x3 corner/edge settings are kept
 *  where they are so existing saved settings keep working. */
export function buffersFor(settings: Settings): Record<string, string> {
  const saved = settings.buffers[settings.size] ?? {}
  if (settings.size !== 3) return { ...saved }
  return { corner: settings.cornerBuffer, edge: settings.edgeBuffer, ...saved }
}

export function withBuffer(settings: Settings, kind: string, letter: string): Partial<Settings> {
  if (settings.size === 3 && kind === 'corner') return { cornerBuffer: letter }
  if (settings.size === 3 && kind === 'edge') return { edgeBuffer: letter }
  return {
    buffers: {
      ...settings.buffers,
      [settings.size]: { ...(settings.buffers[settings.size] ?? {}), [kind]: letter },
    },
  }
}

export const COLOR_LIST = ['white', 'yellow', 'green', 'blue', 'red', 'orange']

export const OPPOSITE: Record<string, string> = {
  white: 'yellow',
  yellow: 'white',
  green: 'blue',
  blue: 'green',
  red: 'orange',
  orange: 'red',
}

const KEY = 'bld-trainer-settings'

export function loadSettings(): Settings {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...(JSON.parse(raw) as Partial<Settings>) }
  } catch {
    /* ignore malformed storage */
  }
  return DEFAULT_SETTINGS
}

export function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(settings))
  } catch {
    /* ignore quota/availability errors */
  }
}
