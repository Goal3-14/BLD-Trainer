// Letter-pair lexicon: pairs (e.g. "AB") -> a word/image association, plus a
// list of alternative ideas and optional notes. Persisted to localStorage and
// importable/exportable as CSV or JSON.

export interface PairEntry {
  pair: string // two Speffz letters, e.g. "AB"
  word: string // primary association
  ideas: string[] // alternative ideas
  notes?: string
}

export interface Lexicon {
  entries: Record<string, PairEntry>
}

export const EMPTY_LEXICON: Lexicon = { entries: {} }

const KEY = 'bld-trainer-lexicon'

export function loadLexicon(): Lexicon {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as Lexicon
      if (parsed && parsed.entries) return parsed
    }
  } catch {
    /* ignore malformed storage */
  }
  return EMPTY_LEXICON
}

export function saveLexicon(lexicon: Lexicon): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(lexicon))
  } catch {
    /* ignore */
  }
}

export function normalizePair(s: string): string {
  return s.toUpperCase().replace(/[^A-X]/g, '').slice(0, 2)
}

export function entryList(lexicon: Lexicon): PairEntry[] {
  return Object.values(lexicon.entries).sort((a, b) => a.pair.localeCompare(b.pair))
}

// Reverse index for answering with words instead of letters: each word and idea
// (lowercased) maps to its pair. Built from the sorted entry list so a word used
// by two pairs resolves to the alphabetically first one, whatever the key order.
export function wordIndex(lexicon: Lexicon): Record<string, string> {
  const index: Record<string, string> = {}
  for (const e of entryList(lexicon)) {
    for (const w of [e.word, ...e.ideas]) {
      const key = w.trim().toLowerCase()
      if (key && !(key in index)) index[key] = e.pair
    }
  }
  return index
}

// Chunk a flat target list into pairs. An odd count (parity) leaves a lone
// letter as the last chunk.
export function chunkPairs(letters: string[]): string[] {
  const out: string[] = []
  for (let i = 0; i < letters.length; i += 2) out.push(letters.slice(i, i + 2).join(''))
  return out
}

// --- CSV / JSON import-export -------------------------------------------------

function csvCell(s: string): string {
  return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s
}

export function toCSV(lexicon: Lexicon): string {
  const rows = [['pair', 'word', 'ideas', 'notes']]
  for (const e of entryList(lexicon)) {
    rows.push([e.pair, e.word, e.ideas.join('|'), e.notes ?? ''])
  }
  return rows.map((r) => r.map(csvCell).join(',')).join('\n')
}

// A pasted list is not always comma-separated: copying out of a spreadsheet
// gives tabs, and Excel in some locales exports semicolons. Guessing from the
// first non-blank line beats silently reading the whole line as the pair —
// which still yields a valid-looking pair (the first two A-X letters) but no
// word, so the drills end up empty while the import claims success.
function detectDelimiter(text: string): string {
  const first = text.split(/\r?\n/).find((l) => l.trim()) ?? ''
  for (const d of ['\t', ',', ';']) {
    if (first.includes(d)) return d
  }
  return ','
}

function parseCSV(text: string, delim: string): string[][] {
  const rows: string[][] = []
  let row: string[] = []
  let field = ''
  let inQuotes = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        field += c
      }
    } else if (c === '"') {
      inQuotes = true
    } else if (c === delim) {
      row.push(field)
      field = ''
    } else if (c === '\n') {
      row.push(field)
      rows.push(row)
      row = []
      field = ''
    } else if (c !== '\r') {
      field += c
    }
  }
  if (field !== '' || row.length) {
    row.push(field)
    rows.push(row)
  }
  return rows
}

export function fromCSV(text: string): Lexicon {
  let rows = parseCSV(text, detectDelimiter(text)).filter((r) => r.some((c) => c.trim() !== ''))
  if (!rows.length) return EMPTY_LEXICON
  // No delimiter anywhere: accept a plain "AB word" list, splitting off the
  // leading pair and keeping the rest of the line as the word (which may
  // itself contain spaces).
  if (rows.every((r) => r.length === 1)) {
    rows = rows.map((r) => {
      const m = /^\s*([A-Xa-x]{2})[\s.:-]+(.+)$/.exec(r[0])
      return m ? [m[1], m[2]] : r
    })
  }
  const start = rows[0][0]?.trim().toLowerCase() === 'pair' ? 1 : 0
  const entries: Record<string, PairEntry> = {}
  for (let i = start; i < rows.length; i++) {
    const [pairRaw = '', word = '', ideasRaw = '', notes = ''] = rows[i]
    const pair = normalizePair(pairRaw)
    if (pair.length !== 2) continue
    const ideas = ideasRaw
      .split('|')
      .map((s) => s.trim())
      .filter(Boolean)
    entries[pair] = { pair, word: word.trim(), ideas, notes: notes.trim() || undefined }
  }
  return { entries }
}

export function importText(text: string): Lexicon {
  const t = text.trim()
  if (t.startsWith('{')) {
    const parsed = JSON.parse(t) as Lexicon
    if (!parsed || !parsed.entries) throw new Error('not a lexicon object')
    return parsed
  }
  return fromCSV(t)
}

export const EXAMPLE_LEXICON: Lexicon = {
  entries: {
    AB: { pair: 'AB', word: 'abbey', ideas: ['ABBA'] },
    FM: { pair: 'FM', word: 'FM radio', ideas: ['firmament'] },
    BP: { pair: 'BP', word: 'blood pressure', ideas: ['BP petrol'] },
    LH: { pair: 'LH', word: 'lighthouse', ideas: [] },
    VO: { pair: 'VO', word: 'vow', ideas: ['volcano'] },
    UK: { pair: 'UK', word: 'United Kingdom', ideas: ['Ukraine'] },
  },
}
