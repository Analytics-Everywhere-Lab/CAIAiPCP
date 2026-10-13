import { useEffect, useRef, useState } from 'react'
import { Check, ChevronDown, Sparkle } from './Icons'

export default function ReasoningTrace({ title, steps, waitingMessage, revision }) {
  const scrollRef = useRef(null)
  const [showDone, setShowDone] = useState(true)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [steps])

  const done = steps.filter(s => s.status !== 'active')
  const active = steps.filter(s => s.status === 'active')

  return (
    <div className="trace">
      <div className="trace-hero">
        <div className="trace-spinner" aria-hidden="true"><Sparkle size={22} /></div>
        <div className="trace-copy">
          <h3 className="trace-title">{title}</h3>
          <p className="trace-sub">{active[0]?.title || waitingMessage}</p>
          {revision?.strategy_label && (
            <div className="trace-revision"><strong>{revision.strategy_label}.</strong> {revision.rationale}</div>
          )}
          <div className="progress-track" aria-hidden="true"><span /></div>
        </div>
      </div>

      <div className="trace-steps" ref={scrollRef}>
        {done.length > 0 && (
          <button type="button" className="trace-group-toggle" onClick={() => setShowDone(s => !s)} aria-expanded={showDone}>
            <ChevronDown size={14} className={`chip-chevron ${showDone ? 'open' : ''}`} />
            {done.length} completed step{done.length === 1 ? '' : 's'}
          </button>
        )}
        {showDone && done.map(step => (
          <div key={step.id} className="trace-step done">
            <span className="trace-mark"><Check size={12} /></span>
            <span className="trace-step-title">{step.title}</span>
          </div>
        ))}
        {active.map(step => (
          <div key={step.id} className="trace-step active">
            <span className="trace-mark"><span className="pulse-dot" /></span>
            <div className="trace-step-body">
              <span className="trace-step-title">{step.title}</span>
              {step.streamText && (
                <div className="trace-stream" ref={el => { if (el) el.scrollTop = el.scrollHeight }}>
                  {step.streamText}<span className="caret" />
                </div>
              )}
            </div>
          </div>
        ))}
        {steps.length === 0 && <p className="trace-waiting">{waitingMessage}</p>}
      </div>
    </div>
  )
}
