// Typed client for the BLD Trainer backend. Cube logic lives server-side; the
// frontend only sends/receives plain data.

export interface ScrambleResponse {
  scramble: string[]
  net: Record<string, string[]>
  corner_buffer: string
  edge_buffer: string
}

export interface TraceResponse {
  corners: string[]
  edges: string[]
  parity: boolean
}

export interface ValidateResponse {
  solved: boolean
  corners_solved: boolean
  edges_solved: boolean
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

export function getScramble(length = 20): Promise<ScrambleResponse> {
  return postJson<ScrambleResponse>('/api/scramble', { length })
}

export function getTrace(
  scramble: string[],
  cornerBuffer: string,
  edgeBuffer: string,
): Promise<TraceResponse> {
  return postJson<TraceResponse>('/api/trace', {
    scramble,
    corner_buffer: cornerBuffer,
    edge_buffer: edgeBuffer,
  })
}

export function validateMemo(
  scramble: string[],
  cornerTargets: string[],
  edgeTargets: string[],
  cornerBuffer: string,
  edgeBuffer: string,
): Promise<ValidateResponse> {
  return postJson<ValidateResponse>('/api/validate', {
    scramble,
    corner_targets: cornerTargets,
    edge_targets: edgeTargets,
    corner_buffer: cornerBuffer,
    edge_buffer: edgeBuffer,
  })
}
