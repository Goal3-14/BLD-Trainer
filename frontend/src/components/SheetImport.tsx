import { useState } from 'react'
import { EXAMPLE_LEXICON, entryList, importText, toCSV } from '../lexicon'
import type { ModeProps } from '../modes/types'

// The phone build's stand-in for the full sheet editor: get a list on and off
// the device, nothing more. Editing stays on the desktop app.
export function SheetImport({ lexicon, updateLexicon }: ModeProps) {
  const [imp, setImp] = useState('')
  const [msg, setMsg] = useState<string | null>(null)
  const [showExport, setShowExport] = useState(false)

  const all = entryList(lexicon)
  const count = all.length
  const usable = all.filter((e) => e.word).length // what the drills can actually use
  const csv = toCSV(lexicon)

  function doImport(replace: boolean) {
    try {
      const imported = importText(imp)
      const n = Object.keys(imported.entries).length
      if (!n) {
        setMsg('Nothing to import — that text had no pairs in it.')
        return
      }
      updateLexicon({
        entries: replace ? imported.entries : { ...lexicon.entries, ...imported.entries },
      })
      // The drills only use pairs that have a word, so a list that imported
      // "successfully" with no words at all leaves every drill empty. Say so
      // here rather than letting the other tabs look broken.
      const withWord = Object.values(imported.entries).filter((e) => e.word).length
      const how = replace ? 'replaced everything' : 'merged'
      setMsg(
        withWord === 0
          ? `Imported ${n} pairs, but none of them have a word, so the drills will be empty. ` +
            `Each line needs the pair and the word together — "AB,abbey" or "AB abbey".`
          : withWord < n
            ? `Imported ${n} pairs (${how}); ${withWord} have words and will show up in drills.`
            : `Imported ${n} pairs (${how}).`,
      )
      setImp('')
    } catch (e) {
      setMsg('Import failed: ' + (e as Error).message)
    }
  }

  async function copyCsv() {
    try {
      await navigator.clipboard.writeText(csv)
      setMsg('Copied your list to the clipboard.')
    } catch {
      setMsg('Could not copy — select the text below and copy it manually.')
    }
  }

  return (
    <section className="mode sheet-import">
      <p className="pair-count">
        {count ? (
          <>
            <b>{count}</b> pairs saved on this device
            {usable < count && <>, {usable} with words</>}
          </>
        ) : (
          <>No pairs on this device yet</>
        )}
      </p>
      {count > 0 && usable === 0 && (
        <p className="error">
          None of these have a word attached, so the drills have nothing to ask you. Re-paste
          your list with the pair and word on the same line.
        </p>
      )}

      <div className="io-block">
        <p className="io-label">Paste your list from the desktop app (CSV or JSON)</p>
        <textarea
          value={imp}
          onChange={(e) => setImp(e.target.value)}
          rows={8}
          spellCheck={false}
          autoComplete="off"
          placeholder={'pair,word,ideas,notes\nAB,abbey,ABBA,\n...'}
        />
        <div className="actions">
          <button type="button" disabled={!imp.trim()} onClick={() => doImport(true)}>
            Replace my list
          </button>
          <button
            type="button"
            className="secondary"
            disabled={!imp.trim()}
            onClick={() => doImport(false)}
          >
            Merge in
          </button>
        </div>
      </div>

      {msg && <p className="io-msg">{msg}</p>}

      <div className="actions">
        <button
          type="button"
          className="secondary"
          onClick={() => updateLexicon({ entries: { ...lexicon.entries, ...EXAMPLE_LEXICON.entries } })}
        >
          Load examples
        </button>
        {count > 0 && (
          <button type="button" className="secondary" onClick={() => setShowExport((v) => !v)}>
            {showExport ? 'Hide' : 'Back up'} my list
          </button>
        )}
      </div>

      {showExport && (
        <div className="io-block">
          <p className="io-label">Your list as CSV — keep a copy somewhere safe</p>
          <textarea value={csv} readOnly rows={6} />
          <div className="actions">
            <button type="button" onClick={() => void copyCsv()}>
              Copy
            </button>
          </div>
        </div>
      )}

      <p className="empty-note">
        Your pairs are saved on this device and stay after you close the app. Editing happens in
        the desktop app — paste the updated list here whenever you change it.
      </p>
    </section>
  )
}
