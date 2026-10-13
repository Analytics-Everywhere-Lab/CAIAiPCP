import { useCallback, useEffect, useState } from 'react'

// Browser storage can be unavailable (private windows, blocked site data); the UI
// must work without it, so every access is guarded.
export function readStored(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key)
    return raw === null ? fallback : JSON.parse(raw)
  } catch {
    return fallback
  }
}

export function writeStored(key, value) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch { /* not persisted; fine */ }
}

// useState that remembers its value in this browser (collapsed panels, theme).
export function usePersistentState(key, initial) {
  const [value, setValue] = useState(() => readStored(key, initial))
  const update = useCallback((next) => {
    setValue(prev => {
      const resolved = typeof next === 'function' ? next(prev) : next
      writeStored(key, resolved)
      return resolved
    })
  }, [key])
  return [value, update]
}

const darkQuery = () => window.matchMedia?.('(prefers-color-scheme: dark)')

// Theme preference: 'light' | 'dark' | 'system'. Applied as <html data-theme>.
export function useTheme() {
  const [preference, setPreference] = usePersistentState('caiaipcp:theme', 'system')
  const [systemDark, setSystemDark] = useState(() => !!darkQuery()?.matches)

  useEffect(() => {
    const query = darkQuery()
    if (!query) return undefined
    const onChange = (event) => setSystemDark(event.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  const theme = preference === 'system' ? (systemDark ? 'dark' : 'light') : preference
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.documentElement.style.colorScheme = theme
  }, [theme])

  const toggle = () => setPreference(theme === 'dark' ? 'light' : 'dark')
  return { theme, preference, setPreference, toggle }
}

// Width of an element, kept current with a ResizeObserver.
export function useElementWidth(ref) {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const element = ref.current
    if (!element || typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(entries => setWidth(Math.round(entries[0].contentRect.width)))
    observer.observe(element)
    return () => observer.disconnect()
  }, [ref])
  return width
}
