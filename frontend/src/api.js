export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'

export async function postJSON(path, body = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
  return data
}

export async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`)
  return data
}

// Server-sent events over GET (graph runs).
export function openEventStream(path, onEvent, onError) {
  const source = new EventSource(`${API_BASE}${path}`)
  source.onmessage = (event) => onEvent(JSON.parse(event.data), source)
  source.onerror = () => {
    source.close()
    onError?.()
  }
  return source
}

// Server-sent events over POST (chat), read from the response body.
export async function streamPost(path, body, onEvent) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        onEvent(JSON.parse(line.slice(6)))
      } catch { /* ignore partial lines */ }
    }
  }
}

export async function downloadFile(path, filename) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`Download failed (${res.status})`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
