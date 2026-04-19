import { useState, useRef, useEffect } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Custom node components can be used if we want specialized styling, but we can also use built-in 'default' and style them via the `style` prop.

function App() {
  const [patientInfo, setPatientInfo] = useState('')
  const [severity, setSeverity] = useState('Default')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [threadId, setThreadId] = useState(null)
  const [finalCarePlan, setFinalCarePlan] = useState(null)
  const [activeTab, setActiveTab] = useState('graph') // 'graph' or 'plan'
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  const [waitingMessage, setWaitingMessage] = useState('Initiating validation...')
  const [hasStarted, setHasStarted] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [reasoningSteps, setReasoningSteps] = useState([])
  const [streamingReply, setStreamingReply] = useState('') // live LLM reply to user chat
  const eventSourceRef = useRef(null)
  const streamBoxRefs = useRef({}) // keyed by step id for auto-scroll
  const traceScrollRef = useRef(null) // auto-scroll the whole reasoning trace

  // Interactive Review States
  const [needsReview, setNeedsReview] = useState(false)
  const [handlingOptions, setHandlingOptions] = useState([])
  const [argumentsData, setArgumentsData] = useState([])

  // Graph States (now list view)
  const [activeOptionTab, setActiveOptionTab] = useState(null) // which option is shown
  const [selectedArg, setSelectedArg] = useState(null) // Argument currently editing
  const [editContent, setEditContent] = useState('')

  // Add new argument
  const [showAddModal, setShowAddModal] = useState(false)
  const [newArgContent, setNewArgContent] = useState('')
  const [newArgType, setNewArgType] = useState('support')
  const [newArgOption, setNewArgOption] = useState('')
  const [newArgRole, setNewArgRole] = useState('General')

  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, needsReview])

  // Auto-scroll the reasoning trace to always show the latest step
  useEffect(() => {
    if (traceScrollRef.current) {
      traceScrollRef.current.scrollTop = traceScrollRef.current.scrollHeight
    }
  }, [reasoningSteps])

  // Set first option tab by default
  useEffect(() => {
    if (needsReview && handlingOptions.length > 0) {
      setActiveOptionTab(prev => prev && handlingOptions.includes(prev) ? prev : handlingOptions[0]);
    }
  }, [handlingOptions, needsReview]);

  const prefillExample = (type) => {
    if (type === 'minor') setPatientInfo("82-year-old female living alone. Mild cognitive impairment, history of falls but wants to stay at home.")
    if (type === 'complex') setPatientInfo("78-year-old male, diabetic with recent stroke affecting left side mobility. Needs daily insulin, wife is primary caregiver but struggling.")
  }

  const startGeneration = async () => {
    if (!patientInfo.trim()) return
    setLoading(true)
    setMessages([])
    setNeedsReview(false)
    setFinalCarePlan(null)
    setActiveTab('graph')
    setIsGeneratingPlan(false)
    setHasStarted(true)
    setWaitingMessage('Initializing processes...')
    setReasoningSteps([])

    try {
      const res = await fetch('http://localhost:8001/api/chat/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_info: patientInfo, severity })
      })
      const data = await res.json()
      setThreadId(data.thread_id)

      const eventSource = new EventSource(`http://localhost:8001/api/chat/stream/${data.thread_id}`)
      eventSourceRef.current = eventSource

      eventSource.onmessage = (event) => {
        const d = JSON.parse(event.data)
        if (d.type === 'message') {
          if (d.node === 'human_review' || d.node === 'Complete' || d.node === 'system' || d.node === 'Error') {
            setMessages(prev => [...prev, { content: d.content, node: d.node, role: "bot" }])
          } else if (d.node === 'progress') {
            setWaitingMessage(d.content.slice(0, 150))
            // progress messages update the sub-status label if needed
          } else {
            setWaitingMessage(d.content.slice(0, 150))
            // New node started — mark previous as completed (collapses streamText), open new step
            setReasoningSteps(prev => {
              const newSteps = prev.map(s => ({ ...s, status: 'completed' }));
              newSteps.push({ id: d.node + '_' + Date.now(), node: d.node, title: d.content, streamText: '', status: 'active' });
              return newSteps;
            })
          }
        } else if (d.type === 'stream_text') {
          // Append LLM streaming text to the currently active step
          setReasoningSteps(prev => {
            if (prev.length === 0) return prev;
            const newSteps = [...prev];
            const last = { ...newSteps[newSteps.length - 1] };
            if (last.status === 'active') {
              last.streamText = d.full; // use full accumulated text
              newSteps[newSteps.length - 1] = last;
            }
            return newSteps;
          })
        } else if (d.type === 'sub_step') {
          // Granular sub-phase within a node — same card behavior as a new node step
          setReasoningSteps(prev => {
            const newSteps = prev.map(s => ({ ...s, status: 'completed' }));
            newSteps.push({ id: 'sub_' + Date.now(), node: 'sub_step', title: d.title, streamText: '', status: 'active' });
            return newSteps;
          })
        } else if (d.type === 'review_needed') {
          setNeedsReview(true)
          setArgumentsData(d.arguments || [])
          setHandlingOptions(d.options || [])

          const uniqueRoles = Array.from(new Set((d.arguments || []).map(a => a.role).filter(Boolean)));
          if (uniqueRoles.length > 0) setNewArgRole(uniqueRoles[0]);
          else setNewArgRole('General');

          if (d.options && d.options.length > 0) {
            setNewArgOption(d.options[0])
          }
          setLoading(false)
          eventSource.close()
        } else if (d.type === 'final_plan') {
          setFinalCarePlan(d.care_plan)
          setActiveTab('plan')
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

  const submitAction = async (action, payload = {}) => {
    if (!threadId) return
    setLoading(true)
    try {
      await fetch(`http://localhost:8001/api/chat/action/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...payload })
      })

      if (action === 'accept') {
        // Show final approved arguments in chat before clearing review state
        const approvedArgs = argumentsData.map(a => ({ content: a.content, type: a.type }))
        setMessages(prev => [...prev, { role: 'bot', node: 'system', argList: approvedArgs }])
        setNeedsReview(false)
        setSelectedArg(null)
        setIsGeneratingPlan(true)
        setWaitingMessage('Initiating cross-reference validation...')
        setReasoningSteps(prev => prev.map(s => ({ ...s, status: 'completed' })))
        const eventSource = new EventSource(`http://localhost:8001/api/chat/stream/${threadId}`)
        eventSourceRef.current = eventSource

        eventSource.onmessage = (event) => {
          const d = JSON.parse(event.data)
          if (d.type === 'message') {
            if (d.node === 'human_review' || d.node === 'Complete' || d.node === 'system' || d.node === 'Error') {
              setMessages(prev => [...prev, { content: d.content, node: d.node, role: "bot" }])
            } else if (d.node === 'progress') {
              setWaitingMessage(d.content.slice(0, 150))
              // progress messages are sub-step status, no separate card needed
            } else {
              setWaitingMessage(d.content.slice(0, 150))
              setReasoningSteps(prev => {
                const newSteps = prev.map(s => ({ ...s, status: 'completed' }));
                newSteps.push({ id: d.node + '_' + Date.now(), node: d.node, title: d.content, streamText: '', status: 'active' });
                return newSteps;
              })
            }
          } else if (d.type === 'stream_text') {
            setReasoningSteps(prev => {
              if (prev.length === 0) return prev;
              const newSteps = [...prev];
              const last = { ...newSteps[newSteps.length - 1] };
              if (last.status === 'active') {
                last.streamText = d.full;
                newSteps[newSteps.length - 1] = last;
              }
              return newSteps;
            })
          } else if (d.type === 'sub_step') {
            setReasoningSteps(prev => {
              const newSteps = prev.map(s => ({ ...s, status: 'completed' }));
              newSteps.push({ id: 'sub_' + Date.now(), node: 'sub_step', title: d.title, streamText: '', status: 'active' });
              return newSteps;
            })
          } else if (d.type === 'final_plan') {
            setFinalCarePlan(d.care_plan)
            setIsGeneratingPlan(false)
            setActiveTab('plan')
          } else if (d.type === 'done') {
            setIsGeneratingPlan(false)
            setLoading(false)
            eventSource.close()
          }
        }
      } else {
        if (action === 'remove') {
          setArgumentsData(prev => prev.filter((_, i) => i !== payload.target_id))
          setSelectedArg(null)
        } else if (action === 'modify') {
          setArgumentsData(prev => prev.map((arg, i) => i === payload.target_id ? { ...arg, content: payload.new_content } : arg))
          setSelectedArg(null)
        } else if (action === 'add') {
          setArgumentsData(prev => [...prev, {
            id: prev.length,
            content: payload.new_content,
            type: payload.new_type,
            option: payload.new_option,
            role: payload.new_role || 'General'
          }])
          setNewArgContent('')
          setShowAddModal(false)
        }
        setLoading(false)
      }
    } catch (err) {
      console.error(err)
      setLoading(false)
    }
  }

  const availableRoles = Array.from(new Set(argumentsData.map(a => a.role).filter(Boolean)));
  if (availableRoles.length === 0) availableRoles.push('General');

  const stopGeneration = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setLoading(false);
  }

  const sendChatMessage = async (text) => {
    if (!threadId || !text.trim()) return
    setMessages(prev => [...prev, { content: text, role: 'user' }])
    setChatInput('')
    setStreamingReply('')
    setLoading(true)
    try {
      // fetch + ReadableStream for POST streaming (EventSource only supports GET)
      const resp = await fetch(`http://localhost:8001/api/chat/message/${threadId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let fullReply = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        for (const line of text.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const d = JSON.parse(line.slice(6))
              if (d.type === 'stream_text') {
                fullReply = d.full
                setStreamingReply(d.full)
              } else if (d.type === 'message') {
                setStreamingReply('')
                setMessages(prev => [...prev, { content: d.content, node: d.node, role: 'bot' }])
                fullReply = ''
              } else if (d.type === 'done') {
                if (fullReply) {
                  setStreamingReply('')
                  setMessages(prev => [...prev, { content: fullReply, node: 'bot', role: 'bot' }])
                }
              }
            } catch { }
          }
        }
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleChatSubmit = (e) => {
    if (e.key === 'Enter' && chatInput.trim()) {
      if (finalCarePlan) {
        sendChatMessage(chatInput)
      } else {
        setMessages(prev => [...prev, { content: chatInput, role: 'user' }]);
        setChatInput('');
      }
    }
  }

  return (
    <div className="app-container">
      <div className="left-column">
        <div className="glass-panel">
          <h2>Aging in Place Care Plan Coordination</h2>
          <div className="example-buttons" style={{ display: hasStarted ? 'none' : 'flex' }}>
            <button className="example-btn" onClick={() => prefillExample('minor')}>Example 1</button>
            <button className="example-btn" onClick={() => prefillExample('complex')}>Example 2</button>
          </div>

          <div className="input-container">
            {hasStarted ? (
              <div className="collapsed-input" style={{ background: '#f8fafc', padding: '1rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#475569' }}>Patient Information</h4>
                  <span style={{ fontSize: '0.8rem', background: '#e0e7ff', color: '#4338ca', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>{severity}</span>
                </div>
                <p style={{ margin: 0, fontSize: '0.9rem', color: '#1e293b' }}>{patientInfo}</p>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    className="secondary"
                    style={{ marginTop: '0.5rem', padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                    onClick={() => setHasStarted(false)}
                    disabled={loading}
                  >
                    Edit Input
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div style={{ marginBottom: '10px' }}>
                  <label style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748b' }}>Severity Mode:</label>
                  <select className="form-control" value={severity} onChange={e => setSeverity(e.target.value)} disabled={loading} style={{ marginTop: '0.25rem' }}>
                    <option value="Default">AI Analyze (Default)</option>
                    <option value="Low">Low</option>
                    <option value="Moderate">Moderate</option>
                    <option value="High">High</option>
                    <option value="Very High">Very High</option>
                  </select>
                </div>
                <textarea
                  placeholder="Enter patient information here..."
                  value={patientInfo}
                  onChange={(e) => setPatientInfo(e.target.value)}
                  disabled={loading}
                />
                <button onClick={startGeneration} disabled={loading || !patientInfo.trim()}>
                  Generate Plan {loading && <span className="loading-dots"></span>}
                </button>
              </>
            )}
          </div>
        </div>

        {hasStarted && (
          <div className="glass-panel stream-container" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="messages-area" style={{ flexGrow: 1, overflowY: 'auto' }}>
              {messages.length === 0 && !loading && (
                <div style={{ textAlign: 'center', padding: '1.5rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                  Ready to process instructions...
                </div>
              )}
              {messages.map((m, i) => (
                <div key={i} className="message-wrapper" style={{ marginBottom: '6px' }}>
                  <div className={`message ${m.role === 'user' ? 'user' : 'bot'} ${m.node === 'system' ? 'system' : ''}`} style={{ padding: '0.5rem 0.85rem', fontSize: '0.88rem', lineHeight: '1.5' }}>
                    {m.argList ? (
                      <div>
                        <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.85rem', color: '#1e293b' }}>Arguments sent for final care plan generation:</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {m.argList.map((arg, ai) => (
                            <div key={ai} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', padding: '6px 8px', background: arg.type === 'support' ? '#f0fdf4' : '#fff1f2', borderRadius: '6px', border: `1px solid ${arg.type === 'support' ? '#bbf7d0' : '#fecdd3'}` }}>
                              <span style={{ flexShrink: 0, fontSize: '0.7rem', fontWeight: 700, padding: '2px 7px', borderRadius: '999px', background: arg.type === 'support' ? '#22c55e' : '#ef4444', color: 'white', letterSpacing: '0.05em', marginTop: '1px' }}>
                                {arg.type === 'support' ? 'SUPPORT' : 'ATTACK'}
                              </span>
                              <span style={{ fontSize: '0.83rem', color: '#1e293b', lineHeight: '1.5' }}>{arg.content}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="markdown-content">
                        <Markdown remarkPlugins={[remarkGfm]}>{m.content}</Markdown>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {/* Live streaming reply bubble */}
              {streamingReply && (
                <div className="message-wrapper" style={{ marginBottom: '6px' }}>
                  <div className="message bot" style={{ padding: '0.5rem 0.85rem', fontSize: '0.88rem', lineHeight: '1.5', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                    {streamingReply}<span style={{ display: 'inline-block', width: '2px', height: '0.9em', background: '#4f46e5', marginLeft: '2px', animation: 'custom-pulse 0.8s infinite', verticalAlign: 'text-bottom' }} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat input — only shown once the care plan is ready */}
            {finalCarePlan ? (
              <div style={{
                marginTop: '1rem',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                background: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '24px',
                padding: '4px 8px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
              }}>
                <input
                  type="text"
                  placeholder="Ask a question about the care plan..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleChatSubmit}
                  style={{
                    flexGrow: 1,
                    border: 'none',
                    outline: 'none',
                    padding: '10px 12px',
                    fontSize: '0.95rem',
                    background: 'transparent'
                  }}
                  disabled={loading}
                />
                <div style={{ display: 'flex', gap: '8px', paddingRight: '4px' }}>
                  <button
                    onClick={() => sendChatMessage(chatInput)}
                    disabled={loading || !chatInput.trim()}
                    title="Send Message"
                    style={{
                      background: (loading || !chatInput.trim()) ? '#e2e8f0' : '#4f46e5',
                      color: 'white',
                      border: 'none', borderRadius: '50%',
                      width: '32px', height: '32px',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      cursor: (loading || !chatInput.trim()) ? 'not-allowed' : 'pointer',
                      transition: 'background 0.2s', padding: 0
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '-2px' }}>
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                  </button>
                </div>
              </div>
            ) : loading ? (
              <div style={{ marginTop: '0.75rem', textAlign: 'center', fontSize: '0.78rem', color: '#94a3b8', padding: '0.4rem' }}>
                Chat will be available once the care plan is ready…
              </div>
            ) : null}
          </div>
        )}
      </div>

      <style>{`
        @keyframes custom-pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: .5; transform: scale(1.1); }
        }
        @keyframes progress-slide {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(300%); }
        }
      `}</style>

      <div className="right-column">
        {((loading && !needsReview && !finalCarePlan) || (isGeneratingPlan && !finalCarePlan)) && (
          <div className="human-review-dashboard" style={{ alignItems: 'center', padding: '3rem', overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '2rem', flexShrink: 0 }}>
              <div style={{ position: 'relative', width: '80px', height: '80px' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, border: '4px solid #f1f5f9', borderRadius: '50%' }}></div>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, border: '4px solid #4f46e5', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
              </div>

              <h3 style={{ marginTop: '2rem', color: '#0f172a', textAlign: 'center', fontSize: '1.25rem', fontWeight: '600' }}>
                {isGeneratingPlan ? 'Finalizing Care Plan...' : 'Analyzing Conditions and Drafting Care Plan...'}
              </h3>
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
              {reasoningSteps.map((step) => (
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
                      ref={el => { if (el) { streamBoxRefs.current[step.id] = el; el.scrollTop = el.scrollHeight; } }}
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

              {reasoningSteps.length === 0 && (
                <p style={{ fontSize: '0.88rem', color: '#64748b', textAlign: 'center', maxWidth: '400px', margin: '0 auto' }}>
                  {waitingMessage}
                </p>
              )}
            </div>
          </div>
        )}

        {(needsReview || finalCarePlan) && (
          <div className="human-review-dashboard">
            <div className="tabs-header">
              <button
                className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('graph')}
                disabled={!needsReview && !finalCarePlan}
              >
                Interactive Graph Review
              </button>
              <button
                className={`tab-btn ${activeTab === 'plan' ? 'active' : ''}`}
                onClick={() => setActiveTab('plan')}
                disabled={!finalCarePlan}
              >
                Final Care Plan
              </button>
            </div>

            {activeTab === 'graph' && (needsReview || finalCarePlan) && (
              <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1, height: '100%', minHeight: 0 }}>
                {/* Header row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexShrink: 0 }}>
                  <div>
                    <h3 style={{ margin: 0 }}>Interactive Graph Review</h3>
                    <p className="text-muted" style={{ margin: '0.2rem 0 0' }}>
                      {needsReview
                        ? 'Select a care option below, then click argument nodes to edit or remove them.'
                        : 'Read-only view — care plan has been finalized.'}
                    </p>
                  </div>
                  {needsReview && (
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button className="secondary" onClick={() => setShowAddModal(!showAddModal)}>+ Add Argument</button>
                      <button onClick={() => submitAction('accept')}>Accept All &amp; Continue</button>
                    </div>
                  )}
                  {!needsReview && finalCarePlan && (
                    <span style={{ fontSize: '0.8rem', background: '#dcfce7', color: '#166534', padding: '0.3rem 0.8rem', borderRadius: '999px', fontWeight: 600 }}>✓ Finalized</span>
                  )}
                </div>

                {/* Per-option sub-tabs */}
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '0.75rem', flexShrink: 0 }}>
                  {handlingOptions.map((opt, idx) => {
                    const isActive = activeOptionTab === opt;
                    const argCount = argumentsData.filter(a => a.option === opt).length;
                    return (
                      <button
                        key={idx}
                        onClick={() => { setActiveOptionTab(opt); setSelectedArg(null); }}
                        style={{
                          padding: '0.4rem 0.85rem',
                          borderRadius: '8px',
                          border: isActive ? '2px solid #4f46e5' : '1.5px solid #e2e8f0',
                          background: isActive ? '#4f46e5' : 'white',
                          color: isActive ? 'white' : '#475569',
                          fontWeight: isActive ? 700 : 500,
                          fontSize: '0.83rem',
                          cursor: 'pointer',
                          transition: 'all 0.18s',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          boxShadow: isActive ? '0 2px 8px rgba(79,70,229,0.18)' : 'none'
                        }}
                      >
                        <span>Option {idx + 1}</span>
                        <span style={{
                          background: isActive ? 'rgba(255,255,255,0.25)' : '#f1f5f9',
                          color: isActive ? 'white' : '#64748b',
                          borderRadius: '999px',
                          padding: '0 6px',
                          fontSize: '0.74rem',
                          fontWeight: 600
                        }}>{argCount}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Active option label */}
                {activeOptionTab && (
                  <div style={{ padding: '0.5rem 0.75rem', background: '#f0f4ff', borderRadius: '8px', border: '1px solid #c7d2fe', marginBottom: '0.75rem', flexShrink: 0 }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#4338ca', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Viewing: </span>
                    <span style={{ fontSize: '0.88rem', color: '#1e293b', fontWeight: 500 }}>{activeOptionTab}</span>
                  </div>
                )}

                {/* Arguments List View — horizontal scroll by role */}
                <div style={{ flexGrow: 1, border: '1px solid #e2e8f0', borderRadius: '12px', background: '#f8fafc', position: 'relative', overflowY: 'auto', padding: '1rem' }}>
                  {/* Render roles as horizontal columns */}
                  {(() => {
                    const argsForOpt = argumentsData
                      .map((arg, idx) => ({ ...arg, originalIndex: idx }))
                      .filter(a => a.option === activeOptionTab);
                    const rolesMap = {};
                    argsForOpt.forEach(arg => {
                      const role = arg.role || 'General';
                      if (!rolesMap[role]) rolesMap[role] = [];
                      rolesMap[role].push(arg);
                    });
                    const roles = Object.keys(rolesMap);
                    if (roles.length === 0) return <div style={{ textAlign: 'center', color: '#94a3b8', paddingTop: '2rem' }}>No arguments for this option yet.</div>;
                    return (
                      <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '8px', height: '100%' }}>
                        {roles.map(role => (
                          <div key={role} style={{ minWidth: '260px', maxWidth: '300px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            <div style={{ padding: '6px 12px', background: '#e0e7ff', borderRadius: '8px', fontWeight: 700, fontSize: '0.78rem', color: '#3730a3', textAlign: 'center', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                              {role}
                            </div>
                            {rolesMap[role].map(arg => (
                              <div
                                key={arg.originalIndex}
                                onClick={() => needsReview ? (setSelectedArg({ ...arg, index: arg.originalIndex }), setEditContent(arg.content)) : null}
                                style={{
                                  padding: '10px 12px',
                                  borderRadius: '8px',
                                  border: `1.5px solid ${arg.type === 'support' ? '#86efac' : '#fca5a5'}`,
                                  background: arg.type === 'support' ? '#f0fdf4' : '#fff1f2',
                                  cursor: needsReview ? 'pointer' : 'default',
                                  transition: 'box-shadow 0.15s',
                                  fontSize: '0.82rem',
                                  lineHeight: '1.55',
                                  color: '#1e293b',
                                  position: 'relative'
                                }}
                              >
                                <span style={{
                                  display: 'inline-block',
                                  fontSize: '0.65rem',
                                  fontWeight: 700,
                                  padding: '1px 6px',
                                  borderRadius: '999px',
                                  background: arg.type === 'support' ? '#22c55e' : '#ef4444',
                                  color: 'white',
                                  marginBottom: '5px',
                                  letterSpacing: '0.05em',
                                  textTransform: 'uppercase'
                                }}>{arg.type === 'support' ? 'SUPPORT' : 'ATTACK'}</span>
                                <div>{arg.content}</div>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    );
                  })()}

                  {/* Floating Edit Panel */}
                  {selectedArg && (
                    <div style={{
                      position: 'absolute', top: 20, right: 20, width: '350px',
                      background: 'white', padding: '1rem', borderRadius: '12px',
                      boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)', zIndex: 10
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h4 style={{ margin: 0 }}>Edit Argument</h4>
                        <button className="secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setSelectedArg(null)}>x</button>
                      </div>
                      <div style={{ marginBottom: '1rem', fontSize: '0.8rem', color: '#64748b' }}>
                        Option: {selectedArg.option} <br /> Type: {selectedArg.type}
                      </div>
                      <textarea
                        style={{ width: '100%', minHeight: '100px', marginBottom: '1rem' }}
                        value={editContent}
                        onChange={e => setEditContent(e.target.value)}
                      />
                      <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                        <button className="danger secondary" onClick={() => submitAction('remove', { target_id: selectedArg.index })} style={{ color: 'white' }}>Remove Node</button>
                        <button onClick={() => submitAction('modify', { target_id: selectedArg.index, new_content: editContent })}>Save Edits</button>
                      </div>
                    </div>
                  )}

                  {/* Floating Add Modal */}
                  {showAddModal && (
                    <div style={{
                      position: 'absolute', top: 20, left: 20, width: '350px',
                      background: 'white', padding: '1rem', borderRadius: '12px',
                      boxShadow: '0 10px 25px -5px rgba(0,0,0,0.1)', zIndex: 10
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h4 style={{ margin: 0 }}>Add New Argument</h4>
                        <button className="secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setShowAddModal(false)}>x</button>
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Option to Target</label>
                        <select style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} value={newArgOption || activeOptionTab || ''} onChange={e => setNewArgOption(e.target.value)}>
                          {handlingOptions.map((opt, idx) => (
                            <option key={idx} value={opt}>{opt}</option>
                          ))}
                        </select>
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Argument Type</label>
                        <select style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} value={newArgType} onChange={e => setNewArgType(e.target.value)}>
                          <option value="support">Support</option>
                          <option value="attack">Challenge / Attack</option>
                        </select>
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Role</label>
                        <select style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }} value={newArgRole} onChange={e => setNewArgRole(e.target.value)}>
                          {availableRoles.map((role, idx) => (
                            <option key={idx} value={role}>{role}</option>
                          ))}
                        </select>
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ fontSize: '0.85rem', fontWeight: 600 }}>Content</label>
                        <textarea
                          style={{ width: '100%', minHeight: '80px', marginTop: '0.25rem' }}
                          value={newArgContent}
                          onChange={e => setNewArgContent(e.target.value)}
                          placeholder="Type out the argument"
                        />
                      </div>
                      <button style={{ width: '100%' }} onClick={() => submitAction('add', { new_content: newArgContent, new_type: newArgType, new_option: newArgOption || activeOptionTab, new_role: newArgRole })}>Inject Node</button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'plan' && finalCarePlan && (
              <div className="final-care-plan-content" style={{ padding: '1rem', overflowY: 'auto' }}>
                <Markdown remarkPlugins={[remarkGfm]}>{finalCarePlan.recommendations}</Markdown>
                {finalCarePlan.references && (
                  <div style={{ marginTop: '2rem' }}>
                    <h4>References</h4>
                    <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem', color: '#64748b' }}>{finalCarePlan.references}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App

