// Letter-pair images. Stored server-side in an images folder as <PAIR>.<ext>
// (AB.png, AD.jpeg, ...). The frontend keeps a pair -> filename map and a
// version counter used to cache-bust <img> URLs after uploads.

export type ImageMap = Record<string, string>

export async function listImages(): Promise<ImageMap> {
  const res = await fetch('/api/images')
  if (!res.ok) throw new Error(`Listing images failed (${res.status})`)
  return ((await res.json()) as { images: ImageMap }).images
}

export async function uploadImage(pair: string, file: File | Blob): Promise<void> {
  const name = file instanceof File ? file.name : ''
  const ext = /\.([a-z0-9]+)$/i.exec(name)?.[1]?.toLowerCase()
  const q = ext ? `?ext=${ext}` : ''
  const res = await fetch(`/api/images/${pair}${q}`, {
    method: 'PUT',
    body: file,
    headers: file.type ? { 'Content-Type': file.type } : undefined,
  })
  if (!res.ok) {
    const detail = await res
      .json()
      .then((d: { detail?: string }) => d.detail)
      .catch(() => undefined)
    throw new Error(detail ?? `Upload failed (${res.status})`)
  }
}

export async function deleteImage(pair: string): Promise<void> {
  const res = await fetch(`/api/images/${pair}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`Delete failed (${res.status})`)
}

export function imageUrl(pair: string, version: number): string {
  return `/api/images/${pair}?v=${version}`
}

// First image file in a drop or paste payload, if any.
export function imageFromDataTransfer(dt: DataTransfer | null): File | null {
  if (!dt) return null
  for (const item of dt.items) {
    if (item.kind === 'file' && item.type.startsWith('image/')) {
      const f = item.getAsFile()
      if (f) return f
    }
  }
  for (const f of dt.files) {
    if (f.type.startsWith('image/')) return f
  }
  return null
}
