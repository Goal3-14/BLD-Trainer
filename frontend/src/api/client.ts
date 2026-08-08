// Typed client for the BLD Trainer backend. Cube logic lives server-side; the
// frontend only sends/receives plain data.

// Cube sizes the engine supports. Memos are keyed by orbit because which
// orbits exist depends on the size: a 4x4 has wings and centres but no midges.
export type CubeSize = 3 | 4 | 5
export type Targets = Record<string, string[]>
export type Buffers = Record<string, string>

export interface ScrambleResponse {
  scramble: string[] // the new moves to apply now
  full: string[] // prefix + scramble: the whole sequence from solved
  net: Record<string, string[]>
  size: CubeSize
  buffers: Buffers
  corner_buffer: string
  edge_buffer: string
}

export interface NetResponse {
  net: Record<string, string[]>
  size: CubeSize
}

export interface TraceResponse {
  targets: Targets
  buffers: Buffers
  parity: boolean
  parity_by_orbit: Record<string, boolean>
  size: CubeSize
  corners: string[]
  edges: string[]
}

export interface ValidateResponse {
  solved: boolean
  by_orbit: Record<string, boolean>
  size: CubeSize
  corners_solved: boolean
  edges_solved: boolean
}

export interface LetterLabel {
  letter: string
  piece: string
  sticker: string
}

export interface OrbitInfo {
  kind: string
  title: string
  default_buffer: string
  labels: LetterLabel[]
}

export interface SchemeResponse {
  size: CubeSize
  orbits: OrbitInfo[]
  colors: string[]
  corners: LetterLabel[]
  edges: LetterLabel[]
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Request to ${path} failed (${res.status})`)
  return (await res.json()) as T
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new Error(`Request to ${path} failed (${res.status})`)
  return (await res.json()) as T
}

export function getScheme(size: CubeSize = 3): Promise<SchemeResponse> {
  return getJson<SchemeResponse>(`/api/scheme?size=${size}`)
}

// `prefix` = moves already on the cube. Pass it to continue scrambling from the
// current state instead of from solved. `length` omitted means the usual length
// for the size (20 / 40 / 60).
export function getScramble(
  topColor: string,
  frontColor: string,
  prefix: string[] = [],
  size: CubeSize = 3,
): Promise<ScrambleResponse> {
  return postJson<ScrambleResponse>('/api/scramble', {
    prefix,
    size,
    top_color: topColor,
    front_color: frontColor,
  })
}

export function getNet(
  scramble: string[],
  topColor: string,
  frontColor: string,
  size: CubeSize = 3,
): Promise<NetResponse> {
  return postJson<NetResponse>('/api/net', {
    scramble,
    size,
    top_color: topColor,
    front_color: frontColor,
  })
}

export function getTrace(
  scramble: string[],
  buffers: Buffers,
  size: CubeSize = 3,
): Promise<TraceResponse> {
  return postJson<TraceResponse>('/api/trace', { scramble, buffers, size })
}

export function validateMemo(
  scramble: string[],
  targets: Targets,
  buffers: Buffers,
  size: CubeSize = 3,
): Promise<ValidateResponse> {
  return postJson<ValidateResponse>('/api/validate', { scramble, targets, buffers, size })
}
