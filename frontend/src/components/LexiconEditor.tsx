import { useEffect, useState } from 'react'
import { deleteImage, imageFromDataTransfer, imageUrl, uploadImage } from '../api/images'
import {
  EXAMPLE_LEXICON,
  entryList,
  importText,
  normalizePair,
  toCSV,
  type PairEntry,
} from '../lexicon'
import type { ModeProps } from '../modes/types'
import { ImageDrop } from './ImageDrop'

const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWX'.split('')

export function LexiconEditor({
  lexicon,
  updateLexicon,
  images,
  imagesVersion,
  refreshImages,
}: ModeProps) {
  const [pair, setPair] = useState('')
  const [word, setWord] = useState('')
  const [ideas, setIdeas] = useState('')
  const [notes, setNotes] = useState('')
  const [imp, setImp] = useState('')
  const [msg, setMsg] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [letter, setLetter] = useState<string | null>(null)
  const [dropPair, setDropPair] = useState<string | null>(null)

  // Table rows: lexicon entries plus image-only pairs (image uploaded, no words yet).
  const all: PairEntry[] = [
    ...entryList(lexicon),
    ...Object.keys(images)
      .filter((p) => !(p in lexicon.entries))
      .map((p): PairEntry => ({ pair: p, word: '', ideas: [] })),
  ].sort((a, b) => a.pair.localeCompare(b.pair))
  const usedLetters = new Set(all.map((e) => e.pair[0]))
  const q = query.trim().toLowerCase()
  const list = all.filter((e) => {
    if (letter && e.pair[0] !== letter) return false
    if (!q) return true
    return (
      e.pair.toLowerCase().includes(q) ||
      e.word.toLowerCase().includes(q) ||
      e.ideas.some((i) => i.toLowerCase().includes(q)) ||
      (e.notes ?? '').toLowerCase().includes(q)
    )
  })
  const csv = toCSV(lexicon)

  function resetForm() {
    setPair('')
    setWord('')
    setIdeas('')
    setNotes('')
  }

  function saveEntry() {
    const p = normalizePair(pair)
    if (p.length !== 2) {
      setMsg('Pair must be two letters A–X.')
      return
    }
    const entry: PairEntry = {
      pair: p,
      word: word.trim(),
      ideas: ideas
        .split(/[,\n]/)
        .map((s) => s.trim())
        .filter(Boolean),
      notes: notes.trim() || undefined,
    }
    updateLexicon({ entries: { ...lexicon.entries, [p]: entry } })
    setMsg(`Saved ${p}.`)
    resetForm()
  }

  function editEntry(e: PairEntry) {
    setPair(e.pair)
    setWord(e.word)
    setIdeas(e.ideas.join(', '))
    setNotes(e.notes ?? '')
    setMsg(`Editing ${e.pair}.`)
  }

  async function uploadFor(p: string, f: File | Blob) {
    try {
      await uploadImage(p, f)
      refreshImages()
      setMsg(`Image saved for ${p}.`)
    } catch (err) {
      setMsg('Image upload failed: ' + (err as Error).message)
    }
  }

  // Paste an image anywhere in this tab to attach it to the pair currently in
  // the form. Pastes aimed at text fields (with text content) pass through,
  // except the pair box itself, where an image paste is clearly an upload.
  useEffect(() => {
    function onPaste(e: ClipboardEvent) {
      if (e.defaultPrevented) return // ImageDrop already handled it
      const t = e.target as HTMLElement | null
      const isField = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')
      const isPairBox = t?.classList.contains('pair-input')
      if (isField && !isPairBox && e.clipboardData?.getData('text')) return
      const f = imageFromDataTransfer(e.clipboardData)
      if (!f) return
      const p = normalizePair(pair)
      if (p.length !== 2) {
        setMsg('Type or search a two-letter pair before pasting an image.')
        return
      }
      e.preventDefault()
      void uploadFor(p, f)
    }
    document.addEventListener('paste', onPaste)
    return () => document.removeEventListener('paste', onPaste)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pair, lexicon])

  function onSearchChange(v: string) {
    setQuery(v)
    const t = v.trim().toUpperCase()
    if (!/^[A-X]{2}$/.test(t)) return
    const entry = lexicon.entries[t]
    if (entry) {
      editEntry(entry)
    } else {
      setPair(t)
      setWord('')
      setIdeas('')
      setNotes('')
      setMsg(`No entry for ${t} yet — fill in the form to add it.`)
    }
  }

  function deleteEntry(p: string) {
    const next = { ...lexicon.entries }
    delete next[p]
    updateLexicon({ entries: next })
    if (p in images) {
      void deleteImage(p).then(refreshImages, () => {})
    }
    setMsg(`Deleted ${p}.`)
  }

  function doImport(replace: boolean) {
    try {
      const imported = importText(imp)
      const entries = replace
        ? imported.entries
        : { ...lexicon.entries, ...imported.entries }
      updateLexicon({ entries })
      setMsg(
        `Imported ${Object.keys(imported.entries).length} pairs (${replace ? 'replaced' : 'merged'}).`,
      )
      setImp('')
    } catch (e) {
      setMsg('Import failed: ' + (e as Error).message)
    }
  }

  function loadExamples() {
    updateLexicon({ entries: { ...lexicon.entries, ...EXAMPLE_LEXICON.entries } })
    setMsg('Loaded example pairs.')
  }

  function copyCsv() {
    navigator.clipboard?.writeText(csv).then(
      () => setMsg('CSV copied to clipboard.'),
      () => setMsg('Copy failed.'),
    )
  }

  function downloadCsv() {
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'bld-letter-pairs.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section className="mode editor">
      <div className="mode-bar">
        <strong>
          {list.length === all.length ? `${all.length} pairs` : `${list.length} / ${all.length} pairs`}
        </strong>
        <button type="button" className="secondary" onClick={loadExamples}>
          Load examples
        </button>
      </div>
      {msg && <p className="note">{msg}</p>}

      <div className="entry-form">
        <input
          className="pair-input"
          value={pair}
          onChange={(e) => setPair(e.target.value)}
          placeholder="AB"
          maxLength={2}
        />
        <input value={word} onChange={(e) => setWord(e.target.value)} placeholder="Word / image" />
        <input
          value={ideas}
          onChange={(e) => setIdeas(e.target.value)}
          placeholder="Alt ideas (comma separated)"
        />
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes (optional)"
        />
        <button type="button" onClick={saveEntry}>
          Save
        </button>
        <ImageDrop
          pair={normalizePair(pair)}
          images={images}
          imagesVersion={imagesVersion}
          refreshImages={refreshImages}
          onStatus={setMsg}
        />
      </div>

      {all.length > 0 && (
        <div className="list-tools">
          <input
            className="search"
            value={query}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search pair, word, ideas…"
          />
          <div className="letter-filter">
            <button
              type="button"
              className={letter === null ? 'active' : ''}
              onClick={() => setLetter(null)}
            >
              All
            </button>
            {LETTERS.map((l) => (
              <button
                key={l}
                type="button"
                className={letter === l ? 'active' : ''}
                disabled={!usedLetters.has(l) && letter !== l}
                onClick={() => setLetter(letter === l ? null : l)}
              >
                {l}
              </button>
            ))}
          </div>
        </div>
      )}

      {all.length > 0 && list.length === 0 && <p className="note">No pairs match.</p>}

      {list.length > 0 && (
        <table className="entries">
          <thead>
            <tr>
              <th>Pair</th>
              <th>Img</th>
              <th>Word</th>
              <th>Ideas</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((e) => (
              <tr
                key={e.pair}
                className={dropPair === e.pair ? 'drop-target' : ''}
                onDragOver={(ev) => {
                  if (ev.dataTransfer.types.includes('Files')) {
                    ev.preventDefault()
                    setDropPair(e.pair)
                  }
                }}
                onDragLeave={() => setDropPair((d) => (d === e.pair ? null : d))}
                onDrop={(ev) => {
                  ev.preventDefault()
                  setDropPair(null)
                  const f = imageFromDataTransfer(ev.dataTransfer)
                  if (f) void uploadFor(e.pair, f)
                }}
              >
                <td className="mono">{e.pair}</td>
                <td className="thumb-cell">
                  {e.pair in images && (
                    <img className="thumb" src={imageUrl(e.pair, imagesVersion)} alt={e.pair} />
                  )}
                </td>
                <td>{e.word}</td>
                <td className="ideas">{e.ideas.join(', ')}</td>
                <td className="row-actions">
                  <button type="button" className="link" onClick={() => editEntry(e)}>
                    edit
                  </button>
                  <button type="button" className="link danger" onClick={() => deleteEntry(e.pair)}>
                    delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <details className="io">
        <summary>Import / export</summary>
        <div className="io-body">
          <div>
            <p className="io-label">Import (paste CSV or JSON)</p>
            <textarea
              value={imp}
              onChange={(e) => setImp(e.target.value)}
              rows={5}
              placeholder={'pair,word,ideas,notes\nAB,abbey,ABBA,\n...'}
            />
            <div className="actions">
              <button type="button" onClick={() => doImport(false)}>
                Import (merge)
              </button>
              <button type="button" className="secondary" onClick={() => doImport(true)}>
                Replace all
              </button>
            </div>
          </div>
          <div>
            <p className="io-label">Export (CSV)</p>
            <textarea value={csv} readOnly rows={5} />
            <div className="actions">
              <button type="button" onClick={copyCsv}>
                Copy CSV
              </button>
              <button type="button" className="secondary" onClick={downloadCsv}>
                Download .csv
              </button>
            </div>
          </div>
        </div>
      </details>
    </section>
  )
}
