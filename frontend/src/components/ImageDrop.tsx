import { useRef, useState } from 'react'
import {
  deleteImage,
  imageFromDataTransfer,
  imageUrl,
  uploadImage,
  type ImageMap,
} from '../api/images'

interface Props {
  pair: string // normalized pair from the entry form; may still be incomplete
  images: ImageMap
  imagesVersion: number
  refreshImages: () => void
  onStatus: (msg: string) => void
}

// Image slot for the entry form: click to pick a file, drag & drop onto it, or
// focus it and paste. Shows the current image for the pair when there is one.
export function ImageDrop({ pair, images, imagesVersion, refreshImages, onStatus }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const ready = pair.length === 2
  const hasImage = ready && pair in images

  async function send(file: File | Blob | null) {
    if (!file) return
    if (!ready) {
      onStatus('Enter a two-letter pair before adding an image.')
      return
    }
    try {
      await uploadImage(pair, file)
      refreshImages()
      onStatus(`Image saved for ${pair}.`)
    } catch (e) {
      onStatus('Image upload failed: ' + (e as Error).message)
    }
  }

  async function remove() {
    try {
      await deleteImage(pair)
      refreshImages()
      onStatus(`Image removed for ${pair}.`)
    } catch (e) {
      onStatus('Image delete failed: ' + (e as Error).message)
    }
  }

  return (
    <div
      className={'image-drop' + (over ? ' over' : '') + (ready ? '' : ' disabled')}
      tabIndex={0}
      role="button"
      title="Click, drag & drop, or paste (Ctrl+V) an image"
      onClick={() => ready && fileRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && ready) {
          e.preventDefault()
          fileRef.current?.click()
        }
      }}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        send(imageFromDataTransfer(e.dataTransfer))
      }}
      onPaste={(e) => {
        const f = imageFromDataTransfer(e.clipboardData)
        if (f) {
          e.preventDefault()
          send(f)
        }
      }}
    >
      {hasImage ? (
        <>
          <img src={imageUrl(pair, imagesVersion)} alt={pair} />
          <button
            type="button"
            className="remove"
            title="Remove image"
            onClick={(e) => {
              e.stopPropagation()
              remove()
            }}
          >
            ×
          </button>
        </>
      ) : (
        <span className="hint">{ready ? 'image: drop / paste / click' : 'image'}</span>
      )}
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => {
          send(e.target.files?.[0] ?? null)
          e.currentTarget.value = ''
        }}
      />
    </div>
  )
}
