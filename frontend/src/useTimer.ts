import { useCallback, useEffect, useRef, useState } from 'react'

// Simple count-up timer (seconds). start() resets and runs; stop() freezes.
export function useTimer() {
  const [elapsed, setElapsed] = useState(0)
  const [running, setRunning] = useState(false)
  const startRef = useRef(0)

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => setElapsed((performance.now() - startRef.current) / 1000), 100)
    return () => clearInterval(id)
  }, [running])

  const start = useCallback(() => {
    startRef.current = performance.now()
    setElapsed(0)
    setRunning(true)
  }, [])

  const stop = useCallback(() => setRunning(false), [])

  return { elapsed, running, start, stop }
}
