import { useEffect, useRef } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Alert, Brain, Chat, CheckCircle, NotePlus, Refresh, Send, Sparkle } from './Icons'

const SUGGESTIONS = [
  'Why is the top option recommended?',
  'What are the main risks for this patient?',
  'Explain the plan in plain language for the family.'
]

function ChatMessage({ message, streaming }) {
  if (message.role === 'user') {
    return (
      <div className="chat-row user">
        <div className="bubble user">
          {message.tag && <div className="bubble-tag">{message.tag}</div>}
          <div className="markdown-content"><Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown></div>
        </div>
      </div>
    )
  }
  if (['system', 'memory', 'human_review', 'Error'].includes(message.node)) {
    const Icon = message.node === 'memory' ? Brain : message.node === 'Error' ? Alert : CheckCircle
    return (
      <div className={`chat-event ${message.node === 'Error' ? 'error' : ''}`}>
        <Icon size={14} />
        <div className="markdown-content"><Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown></div>
      </div>
    )
  }
  return (
    <div className="chat-row bot">
      <span className={`chat-avatar ${streaming ? 'is-busy' : ''}`} title="Care assistant"><Sparkle size={14} /></span>
      <div className={`bubble bot ${streaming ? 'is-streaming' : ''}`}>
        <div className="markdown-content"><Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown></div>
        {streaming && <span className="caret" />}
      </div>
    </div>
  )
}

export default function ChatPanel({
  messages, streamingReply, errorMessage, planReady, input, setInput, onSend, onAddNote, onRegenerate, pendingCount, busy
}) {
  const endRef = useRef(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end', behavior: 'smooth' })
  }, [messages, streamingReply, errorMessage])

  const replying = !!streamingReply
  const send = () => input.trim() && !replying && onSend(input)

  return (
    <div className="chat">
      <div className="chat-log" aria-live="polite">
        {messages.length === 0 && !replying && (
          <div className="chat-empty">
            <span className="empty-icon"><Chat size={22} /></span>
            <p>
              {planReady
                ? 'Ask about any option, argument or section of the plan. I know every argument the team weighed.'
                : 'I join once the care plan is ready, knowing every argument and the plan itself.'}
            </p>
            {planReady && (
              <div className="chat-suggestions">
                {SUGGESTIONS.map(text => <button key={text} type="button" className="chip" onClick={() => onSend(text)}>{text}</button>)}
              </div>
            )}
          </div>
        )}
        {messages.map((message, index) => <ChatMessage key={index} message={message} />)}
        {replying && <ChatMessage message={{ role: 'bot', content: streamingReply }} streaming />}
        {errorMessage && <div className="chat-event error"><Alert size={14} /><div>{errorMessage}</div></div>}
        <div ref={endRef} />
      </div>

      <div className="chat-composer">
        <div className="chat-input-wrap">
          <textarea
            className="input chat-input"
            rows={2}
            value={input}
            disabled={!planReady}
            aria-label="Message the care assistant"
            placeholder={planReady ? 'Ask a question, or describe a change to the plan…' : 'Available once the care plan is ready'}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
          />
          <button type="button" className="btn primary chat-send" disabled={!planReady || !input.trim() || replying} onClick={send}
            title="Ask the assistant (Enter)" aria-label="Ask the assistant">
            <Send size={15} />
          </button>
        </div>
        <div className="chat-actions">
          <button type="button" className="btn secondary sm" disabled={!planReady || !input.trim()} onClick={() => onAddNote(input)}
            title="Add your text as a feedback note on the whole plan">
            <NotePlus size={15} /> Add feedback
          </button>
          <button type="button" className="btn soft sm" disabled={!planReady || busy || pendingCount === 0} onClick={onRegenerate}
            title={pendingCount ? 'Regenerate the care plan with your notes and argument changes' : 'Add feedback or contest an argument first'}>
            <Refresh size={15} /> Regenerate plan{pendingCount > 0 && <span className="btn-count">{pendingCount}</span>}
          </button>
        </div>
      </div>
    </div>
  )
}
