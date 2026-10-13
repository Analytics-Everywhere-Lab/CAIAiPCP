import { useEffect, useRef } from 'react'

export default function ReasoningTrace({ title, steps, waitingMessage, revision }) {
  const traceScrollRef = useRef(null)

  // Auto-scroll the reasoning trace to always show the latest step
  useEffect(() => {
    if (traceScrollRef.current) {
      traceScrollRef.current.scrollTop = traceScrollRef.current.scrollHeight
    }
  }, [steps])

  return (
    <div className="human-review-dashboard" style={{ alignItems: 'center', padding: '3rem', overflowY: 'auto' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem', flexShrink: 0 }}>
        <div style={{ position: 'relative', width: '80px', height: '80px' }}>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, border: '4px solid #f1f5f9', borderRadius: '50%' }}></div>
          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, border: '4px solid #4f46e5', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        </div>

        <h3 style={{ marginTop: '2rem', color: '#0f172a', textAlign: 'center', fontSize: '1.25rem', fontWeight: '600' }}>
          {title}
        </h3>
        {revision?.strategy_label && (
          <div className="revision-live">
            <strong>{revision.strategy_label}.</strong> {revision.rationale}
          </div>
        )}
      </div>

      {/* Timeline for Reasoning Steps – dedicated scrollable trace area */}
      <div
        ref={traceScrollRef}
        style={{
          width: '100%',
          maxWidth: '700px',
          margin: '0 auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          overflowY: 'auto',
          maxHeight: 'calc(100% - 160px)',
          paddingRight: '4px'
        }}
      >
        {steps.map((step) => (
          <div key={step.id} style={{
            display: 'flex', flexDirection: 'column',
            padding: '0.55rem 0.85rem',
            background: step.status === 'active' ? '#fafafe' : '#f8fafc',
            borderLeft: `3px solid ${step.status === 'active' ? '#4f46e5' : '#10b981'}`,
            transition: 'all 0.25s ease'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.55rem' }}>
              {step.status === 'active' ? (
                <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#4f46e5', flexShrink: 0, animation: 'custom-pulse 1.5s infinite' }}></span>
              ) : (
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}><polyline points="20 6 9 17 4 12"></polyline></svg>
              )}
              <span style={{ fontWeight: 500, color: step.status === 'active' ? '#1e293b' : '#64748b', fontSize: '0.8rem', lineHeight: '1.4' }}>{step.title}</span>
            </div>
            {/* Streaming text — only while active, auto-scrolls to bottom */}
            {step.status === 'active' && step.streamText && (
              <div
                ref={el => { if (el) { el.scrollTop = el.scrollHeight; } }}
                style={{
                  marginTop: '0.45rem',
                  maxHeight: '140px',
                  overflowY: 'auto',
                  fontSize: '0.75rem',
                  lineHeight: '1.55',
                  color: '#334155',
                  background: '#f1f5f9',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0',
                  fontFamily: 'monospace',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}
              >
                {step.streamText}<span style={{ display: 'inline-block', width: '2px', height: '0.85em', background: '#4f46e5', marginLeft: '2px', animation: 'custom-pulse 0.8s infinite', verticalAlign: 'text-bottom' }} />
              </div>
            )}
          </div>
        ))}

        {steps.length === 0 && (
          <p style={{ fontSize: '0.88rem', color: '#64748b', textAlign: 'center', maxWidth: '400px', margin: '0 auto' }}>
            {waitingMessage}
          </p>
        )}
      </div>
    </div>
  )
}
