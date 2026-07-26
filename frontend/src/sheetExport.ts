// Builds a self-contained printable HTML sheet of every letter pair: big pair
// letters, image (embedded as a data URI), word, and ideas, laid out as a
// grid of cards. Open in any browser; print to PDF for paper practice.

export interface SheetCard {
  pair: string
  word: string
  ideas: string[]
  notes?: string
  dataUri: string | null
}

function esc(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function buildSheetHtml(cards: SheetCard[], title: string): string {
  const body = cards
    .map((c) => {
      // Fixed-height image box + object-fit: contain normalizes any image size.
      const img = c.dataUri
        ? `<div class="img"><img src="${c.dataUri}" alt="${esc(c.pair)}"></div>`
        : ''
      const word = c.word ? `<div class="word">${esc(c.word)}</div>` : ''
      const ideas = c.ideas.length ? `<div class="ideas">${esc(c.ideas.join(', '))}</div>` : ''
      const notes = c.notes ? `<div class="notes">${esc(c.notes)}</div>` : ''
      return `<div class="card"><div class="pair">${esc(c.pair)}</div>${img}${word}${ideas}${notes}</div>`
    })
    .join('\n')

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; margin: 1.5rem; color: #222; }
  header { display: flex; align-items: baseline; gap: 1rem; margin-bottom: 1rem; }
  h1 { font-size: 1.3rem; margin: 0; }
  .meta { color: #888; font-size: 0.85rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; }
  .card { border: 1px solid #ccc; border-radius: 8px; padding: 8px; text-align: center;
          break-inside: avoid; page-break-inside: avoid; }
  .pair { font-family: ui-monospace, Consolas, monospace; font-weight: 700;
          font-size: 1.5rem; letter-spacing: 0.12em; }
  .img { height: 130px; display: flex; align-items: center; justify-content: center;
         background: #f4f4f4; border-radius: 6px; margin: 6px 0; overflow: hidden; }
  .img img { max-width: 100%; max-height: 100%; object-fit: contain; }
  .word { font-weight: 600; margin-top: 2px; }
  .ideas { font-size: 0.8rem; color: #666; }
  .notes { font-size: 0.75rem; color: #999; font-style: italic; }
  @media print {
    body { margin: 0.5cm; }
    .grid { grid-template-columns: repeat(4, 1fr); }
    .img { height: 100px; }
  }
</style>
</head>
<body>
<header><h1>${esc(title)}</h1><span class="meta">${cards.length} pairs · ${esc(
    new Date().toLocaleDateString(),
  )}</span></header>
<div class="grid">
${body}
</div>
</body>
</html>`
}

export function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result as string)
    r.onerror = () => reject(r.error ?? new Error('read failed'))
    r.readAsDataURL(blob)
  })
}
