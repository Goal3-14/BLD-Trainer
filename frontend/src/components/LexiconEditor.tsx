import { useState } from 'react'
import {
  EXAMPLE_LEXICON,
  entryList,
  importText,
  normalizePair,
  toCSV,
  type PairEntry,
} from '../lexicon'
import type { ModeProps } from '../modes/types'

export function LexiconEditor({ lexicon, updateLexicon }: ModeProps) {
  const [pair, setPair] = useState('')
  const [word, setWord] = useState('')
  const [ideas, setIdeas] = useState('')
  const [notes, setNotes] = useState('')
  const [imp, setImp] = useState('')
  const [msg, setMsg] = useState<string | null>(null)

  const list = entryList(lexicon)
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

  function deleteEntry(p: string) {
    const next = { ...lexicon.entries }
    delete next[p]
    updateLexicon({ entries: next })
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
        <strong>{list.length} pairs</strong>
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
      </div>

      {list.length > 0 && (
        <table className="entries">
          <thead>
            <tr>
              <th>Pair</th>
              <th>Word</th>
              <th>Ideas</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {list.map((e) => (
              <tr key={e.pair}>
                <td className="mono">{e.pair}</td>
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
