import type { CubeSize, SchemeResponse } from '../api/client'
import {
  buffersFor,
  COLOR_LIST,
  CUBE_SIZES,
  OPPOSITE,
  SIZE_LABEL,
  withBuffer,
  type Settings,
} from '../settings'

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

  // One buffer picker per orbit the cube actually has, as the backend reports
  // them — so a 4x4 offers wings and centres, and never midges.
  const active = buffersFor(settings)
  const orbits = scheme?.size === settings.size ? scheme.orbits : []

  return (
    <details className="settings">
      <summary>Settings — cube, buffers &amp; orientation</summary>
      <div className="settings-grid">
        <label>
          Cube
          <select
            value={settings.size}
            onChange={(e) => onChange({ size: Number(e.target.value) as CubeSize })}
          >
            {CUBE_SIZES.map((s) => (
              <option key={s} value={s}>
                {SIZE_LABEL[s]}
              </option>
            ))}
          </select>
        </label>

        {orbits.map((orbit) => (
          <label key={orbit.kind}>
            {orbit.title} buffer
            <select
              value={active[orbit.kind] ?? orbit.default_buffer}
              onChange={(e) => onChange(withBuffer(settings, orbit.kind, e.target.value))}
            >
              {orbit.labels.map((l) => (
                <option key={l.letter} value={l.letter}>
                  {l.letter} — {l.piece} ({l.sticker})
                </option>
              ))}
            </select>
          </label>
        ))}

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
