// User settings, persisted to localStorage so they survive between sessions.

export interface Settings {
  cornerBuffer: string
  edgeBuffer: string
  topColor: string
  frontColor: string
}

export const DEFAULT_SETTINGS: Settings = {
  cornerBuffer: 'C', // UFR (U sticker)
  edgeBuffer: 'C', // UF (U sticker)
  topColor: 'white',
  frontColor: 'green',
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
