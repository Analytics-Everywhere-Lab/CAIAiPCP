import { useState } from 'react'

function App() {
  const [patientInfo, setPatientInfo] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [threadId, setThreadId] = useState(null)
  const [needsReview, setNeedsReview] = useState(false)

  const startGeneration = async () => {
    if (!patientInfo.trim()) return
    setLoading(true)
    setMessages([{ content: "Starting generation...", node: "system" }])
    setNeedsReview(false)

    try {
      const res = await fetch('http://localhost:8002/api/chat/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_info: patientInfo })
      })
      const data = await res.json()
      setThreadId(data.thread_id)

      const eventSource = new EventSource(`http://localhost:8002/api/chat/stream/${data.thread_id}`)
      eventSource.onmessage = (event) => {
        const d = JSON.parse(event.data)
        if (d.type === 'message') {
          setMessages(prev => [...prev, { content: d.content, node: d.node }])
        } else if (d.type === 'review_needed') {
          setNeedsReview(true)
          setLoading(false)
          eventSource.close()
        } else if (d.type === 'done') {
          setLoading(false)
          eventSource.close()
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        setLoading(false)
      }
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const submitAction = async (action) => {
    if (!threadId) return
    setLoading(true)
    setNeedsReview(false)
    try {
      await fetch(`http://localhost:8002/api/chat/action/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action })
      })

      // Re-connect SSE
      const eventSource = new EventSource(`http://localhost:8002/api/chat/stream/${threadId}`)
      eventSource.onmessage = (event) => {
        const d = JSON.parse(event.data)
        if (d.type === 'message') {
          setMessages(prev => [...prev, { content: d.content, node: d.node }])
        } else if (d.type === 'done') {
          setLoading(false)
          eventSource.close()
        }
      }
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div className="glass-panel">
        <h1>Care Plan Generator</h1>
        <p className="text-muted">Multi-agent elderly care plan coordination</p>

        <div className="input-container">
          <textarea
            placeholder="Enter patient information here..."
            value={patientInfo}
            onChange={(e) => setPatientInfo(e.target.value)}
            disabled={loading}
          />
          <button onClick={startGeneration} disabled={loading || !patientInfo.trim()}>
            Generate Plan {loading && <span className="loading-dots"></span>}
          </button>
        </div>
      </div>

      {messages.length > 0 && (
        <div className="glass-panel stream-container">
          <h2>Process Log</h2>
          {messages.map((m, i) => (
            <div key={i} className="message">
              <div className="message-meta">{m.node}</div>
              <div className="markdown-content" style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
            </div>
          ))}

          {needsReview && (
            <div className="input-container" style={{ marginTop: '2rem' }}>
              <h3>Human Review Status: Action Required</h3>
              <p>Type a command to modify argument, add an argument, or accept all options. Examples: 'accept', 'remove 0', 'modify 1 new content'</p>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button onClick={() => submitAction('accept')}>Accept All</button>
                <button onClick={() => submitAction('remove 0')} style={{ background: 'var(--danger)' }}>Remove First Argument</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
