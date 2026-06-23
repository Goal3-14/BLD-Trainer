import type { SchemeResponse } from '../api/client'
import { COLOR_LIST, OPPOSITE, type Settings } from '../settings'

interface SettingsPanelProps {
  settings: Settings
  scheme: SchemeResponse | null
  onChange: (patch: Partial<Settings>) => void
}

export function SettingsPanel({ settings, scheme, onChange }: SettingsPanelProps) {
  const frontOptions = COLOR_LIST.filter(
    (c) => c !== settings.topColor && OPPOSITE[settings.topColor] !== c,
  )

  function handleTop(top: string) {
    let front = settings.frontColor
    if (front === top || OPPOSITE[top] === front) {
      front = COLOR_LIST.find((c) => c !== top && OPPOSITE[top] !== c) ?? front
    }
    onChange({ topColor: top, frontColor: front })
  }

  const cornerOpts = scheme?.corners ?? [{ letter: settings.cornerBuffer, piece: '?', sticker: '?' }]
  const edgeOpts = scheme?.edges ?? [{ letter: settings.edgeBuffer, piece: '?', sticker: '?' }]

  return (
    <details className="settings">
      <summary>Settings — buffers &amp; orientation</summary>
      <div className="settings-grid">
        <label>
          Corner buffer
          <select
            value={settings.cornerBuffer}
            onChange={(e) => onChange({ cornerBuffer: e.target.value })}
          >
            {cornerOpts.map((c) => (
              <option key={c.letter} value={c.letter}>
                {c.letter} — {c.piece} ({c.sticker})
              </option>
            ))}
          </select>
        </label>

        <label>
          Edge buffer
          <select
            value={settings.edgeBuffer}
            onChange={(e) => onChange({ edgeBuffer: e.target.value })}
          >
            {edgeOpts.map((c) => (
              <option key={c.letter} value={c.letter}>
                {c.letter} — {c.piece} ({c.sticker})
              </option>
            ))}
          </select>
        </label>

        <label>
          Top color
          <select value={settings.topColor} onChange={(e) => handleTop(e.target.value)}>
            {COLOR_LIST.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>

        <label>
          Front color
          <select
            value={settings.frontColor}
            onChange={(e) => onChange({ frontColor: e.target.value })}
          >
            {frontOptions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
      </div>
    </details>
  )
}
