import { useState, useRef, useEffect } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { downloadFile, getJSON, openEventStream, postJSON, streamPost } from './api'
import ArgumentBoard from './components/ArgumentBoard'
import CarePlanDocument from './components/CarePlanDocument'
import MemoryPanel from './components/MemoryPanel'
import ReasoningTrace from './components/ReasoningTrace'

function App() {
  const [patientInfo, setPatientInfo] = useState('')
  const [severity, setSeverity] = useState('Default')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false) // a graph run is streaming
  const [threadId, setThreadId] = useState(null)
  const [activeTab, setActiveTab] = useState('graph') // 'graph' | 'plan' | 'memory'
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false)
  const [finishing, setFinishing] = useState(false) // plan shown; scheduling/memory still running
  const [waitingMessage, setWaitingMessage] = useState('Initiating validation...')
  const [hasStarted, setHasStarted] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatMode, setChatMode] = useState('ask') // 'ask' questions, or add 'feedback' on the plan
  const [chatContext, setChatContext] = useState(null)
  const [reasoningSteps, setReasoningSteps] = useState([])
  const [streamingReply, setStreamingReply] = useState('') // live LLM reply to user chat
  const [errorMessage, setErrorMessage] = useState('')
  const eventSourceRef = useRef(null)

  // Argument graph review
  const [needsReview, setNeedsReview] = useState(false)
  const [handlingOptions, setHandlingOptions] = useState([])
  const [argumentsData, setArgumentsData] = useState([])
  const [qbafArgs, setQbafArgs] = useState({})
  const [pendingChanges, setPendingChanges] = useState(0)

  // Care plan versions and feedback
  const [versions, setVersions] = useState([])
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [pendingFeedback, setPendingFeedback] = useState([])
  const [revisionInfo, setRevisionInfo] = useState(null)
  const [memoryRefresh, setMemoryRefresh] = useState(0)

  const messagesEndRef = useRef(null)
  const feedbackSeq = useRef(0)
  const reflectionPoll = useRef(null)

  useEffect(() => () => clearInterval(reflectionPoll.current), [])

  const latestPlan = versions.length ? versions[versions.length - 1] : null
  const shownPlan = versions.find(v => v.version === selectedVersion) || latestPlan
  const phase = needsReview ? 'review' : latestPlan ? 'plan' : 'idle'

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingReply])

  const prefillExample = (type) => {
    if (type === 'minor') setPatientInfo("82-year-old female living alone. Mild cognitive impairment, history of falls but wants to stay at home.")
    if (type === 'complex') setPatientInfo("78-year-old male, diabetic with recent stroke affecting left side mobility. Needs daily insulin, wife is primary caregiver but struggling.")
  }

  const applyPayload = (d) => {
    if (d.options) setHandlingOptions(d.options)
    if (d.arguments) setArgumentsData(d.arguments)
    if (d.qbaf_arguments) setQbafArgs(d.qbaf_arguments)
    if (typeof d.pending_changes === 'number') setPendingChanges(d.pending_changes)
    if (d.versions) {
      setVersions(d.versions)
      if (d.versions.length) setSelectedVersion(d.versions[d.versions.length - 1].version)
    }
  }

  const pushStep = (node, title) => {
    setReasoningSteps(prev => {
      const newSteps = prev.map(s => ({ ...s, status: 'completed' }))
      newSteps.push({ id: node + '_' + Date.now() + '_' + newSteps.length, node, title, streamText: '', status: 'active' })
      return newSteps
    })
  }

  // Learning from the clinician's contestations runs in the background; report when it lands.
  const pollReflection = (id) => {
    clearInterval(reflectionPoll.current)
    let tries = 0
    reflectionPoll.current = setInterval(async () => {
      tries += 1
      let status = null
      try {
        status = await getJSON(`/api/memory/reflection/${id}`)
      } catch { /* keep polling */ }
      if (status?.status === 'done' || status?.status === 'failed' || tries > 90) {
        clearInterval(reflectionPoll.current)
        setMemoryRefresh(n => n + 1)
        if (status?.status === 'done' && status.verified > 0) {
          setMessages(prev => [...prev, {
            role: 'bot', node: 'memory',
            content: `Learned from your review: ${status.verified} lesson${status.verified === 1 ? '' : 's'} added to memory for future care plans.`
          }])
        }
      }
    }, 2000)
  }

  // One handler for every graph run: new case, resume after review, and regeneration.
  const handleStreamEvent = (d, source, id) => {
    if (d.type === 'message') {
      if (d.node === 'human_review' || d.node === 'system' || d.node === 'Error') {
        setMessages(prev => [...prev, { content: d.content, node: d.node, role: "bot" }])
      } else if (d.node === 'progress') {
        setWaitingMessage(d.content.slice(0, 150))
      } else {
        setWaitingMessage(d.content.slice(0, 150))
        pushStep(d.node, d.content)
      }
    } else if (d.type === 'stream_text') {
      // Append LLM streaming text to the currently active step
      setReasoningSteps(prev => {
        if (prev.length === 0) return prev
        const newSteps = [...prev]
        const last = { ...newSteps[newSteps.length - 1] }
        if (last.status === 'active') {
          last.streamText = d.full
          newSteps[newSteps.length - 1] = last
        }
        return newSteps
      })
    } else if (d.type === 'sub_step') {
      pushStep('sub_step', d.title)
    } else if (d.type === 'review_needed') {
      applyPayload(d)
      setNeedsReview(true)
      setActiveTab('graph')
      setLoading(false)
      source.close()
    } else if (d.type === 'revision') {
      setRevisionInfo(d)
    } else if (d.type === 'final_plan') {
      applyPayload(d)
      setIsGeneratingPlan(false)
      setFinishing(true)
      setActiveTab('plan')
    } else if (d.type === 'schedule') {
      if (d.versions) setVersions(d.versions)
    } else if (d.type === 'memory') {
      if (d.reflection?.status === 'running') pollReflection(id)
    } else if (d.type === 'error') {
      setErrorMessage(d.content)
      setLoading(false)
      setIsGeneratingPlan(false)
      source.close()
    } else if (d.type === 'done') {
      if (typeof d.pending_changes === 'number') setPendingChanges(d.pending_changes)
      setIsGeneratingPlan(false)
      setFinishing(false)
      setLoading(false)
      source.close()
    }
  }

  const openRun = (id) => {
    setLoading(true)
    setErrorMessage('')
    eventSourceRef.current = openEventStream(`/api/chat/stream/${id}`, (d, source) => handleStreamEvent(d, source, id), () => {
      setLoading(false)
      setIsGeneratingPlan(false)
      setFinishing(false)
    })
  }

  const startGeneration = async () => {
    if (!patientInfo.trim()) return
    eventSourceRef.current?.close()
    clearInterval(reflectionPoll.current)
    setLoading(true)
    setMessages([])
    setNeedsReview(false)
    setVersions([])
    setSelectedVersion(null)
    setArgumentsData([])
    setQbafArgs({})
    setPendingChanges(0)
    setPendingFeedback([])
    setRevisionInfo(null)
    setActiveTab('graph')
    setIsGeneratingPlan(false)
    setHasStarted(true)
    setWaitingMessage('Initializing processes...')
    setReasoningSteps([])
    setChatContext(null)

    try {
      const data = await postJSON('/api/chat/start', { patient_info: patientInfo, severity })
      setThreadId(data.thread_id)
      openRun(data.thread_id)
    } catch (err) {
      console.error(err)
      setErrorMessage(err.message)
      setLoading(false)
    }
  }

  const submitAction = async (action, payload = {}) => {
    if (!threadId) return
    try {
      const data = await postJSON(`/api/chat/action/${threadId}`, { action, ...payload })
      applyPayload(data)
    } catch (err) {
      console.error(err)
      setErrorMessage(err.message)
    }
  }

  const acceptArguments = async () => {
    if (!threadId) return
    try {
      await postJSON(`/api/chat/action/${threadId}`, { action: 'accept' })
      setNeedsReview(false)
      setIsGeneratingPlan(true)
      setWaitingMessage('Initiating cross-reference validation...')
      setReasoningSteps(prev => prev.map(s => ({ ...s, status: 'completed' })))
      openRun(threadId)
    } catch (err) {
      setErrorMessage(err.message)
    }
  }

  const regeneratePlan = async () => {
    if (!threadId) return
    const feedback = pendingFeedback.map(({ text, section_id, quote }) => ({ text, section_id, quote }))
    try {
      await postJSON(`/api/chat/regenerate/${threadId}`, { feedback })
      const parts = []
      if (feedback.length) parts.push(`${feedback.length} feedback item${feedback.length === 1 ? '' : 's'}`)
      if (pendingChanges) parts.push(`${pendingChanges} argument change${pendingChanges === 1 ? '' : 's'}`)
      setMessages(prev => [...prev, { role: 'user', content: `Regenerate the care plan${parts.length ? ` with ${parts.join(' and ')}` : ''}.` }])
      setPendingFeedback([])
      setRevisionInfo(null)
      setReasoningSteps([])
      setWaitingMessage('Re-verifying the argument graph...')
      setIsGeneratingPlan(true)
      openRun(threadId)
    } catch (err) {
      setErrorMessage(err.message)
    }
  }

  const approvePlan = async (version) => {
    try {
      const data = await postJSON(`/api/chat/approve/${threadId}`, { version })
      setVersions(data.versions)
      setMemoryRefresh(n => n + 1)
      setMessages(prev => [...prev, { role: 'bot', node: 'system', content: `Care plan v${version} approved.` }])
    } catch (err) {
      setErrorMessage(err.message)
    }
  }

  const downloadPdf = async (version) => {
    try {
      await downloadFile(`/api/care-plan/${threadId}/pdf?version=${version}`, `care-plan-v${version}.pdf`)
    } catch (err) {
      console.error(err)
      window.print() // the print stylesheet renders the plan document alone
    }
  }

  const addFeedback = (item) => {
    feedbackSeq.current += 1
    setPendingFeedback(prev => [...prev, { ...item, localId: feedbackSeq.current }])
  }

  const removeFeedback = (localId) => setPendingFeedback(prev => prev.filter(item => item.localId !== localId))

  const sendChatMessage = async (text) => {
    if (!threadId || !text.trim()) return
    if (chatMode === 'feedback') {
      addFeedback({ text: text.trim(), section_id: null, quote: null })
      setMessages(prev => [...prev, { content: text.trim(), role: 'user', tag: 'Plan feedback · applied when you regenerate' }])
      setChatInput('')
      return
    }
    setMessages(prev => [...prev, { content: text, role: 'user' }])
    setChatInput('')
    setStreamingReply('')
    try {
      let fullReply = ''
      await streamPost(`/api/chat/message/${threadId}`, { message: text }, (d) => {
        if (d.type === 'stream_text') {
          fullReply = d.full
          setStreamingReply(d.full)
        } else if (d.type === 'message') {
          setStreamingReply('')
          setMessages(prev => [...prev, { content: d.content, node: d.node, role: 'bot' }])
          fullReply = ''
        } else if (d.type === 'done') {
          if (d.context) setChatContext(d.context)
          if (fullReply) {
            setStreamingReply('')
            setMessages(prev => [...prev, { content: fullReply, node: 'bot', role: 'bot' }])
          }
        } else if (d.type === 'error') {
          setStreamingReply('')
          setErrorMessage(d.content)
        }
      })
    } catch (err) {
      console.error(err)
    }
  }

  const handleChatSubmit = (e) => {
    if (e.key === 'Enter' && chatInput.trim()) {
      if (latestPlan) {
        sendChatMessage(chatInput)
      } else {
        setMessages(prev => [...prev, { content: chatInput, role: 'user' }]);
        setChatInput('');
      }
    }
  }

  const memoryUsedIds = (latestPlan?.memory_used || []).map(m => m.memory_id)
  const showProgress = (loading && !needsReview && !latestPlan) || isGeneratingPlan
  const showDashboard = !showProgress && (needsReview || latestPlan || activeTab === 'memory')

  return (
    <div className="app-container">
      <div className="left-column">
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem' }}>
            <h2>Aging in Place Care Plan Coordination</h2>
            <button className="secondary small" style={{ flexShrink: 0 }} onClick={() => setActiveTab('memory')} title="Lessons learned from clinicians' feedback">
              Learned Memory
            </button>
          </div>
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
                  <div className={`message ${m.role === 'user' ? 'user' : 'bot'} ${m.node === 'system' || m.node === 'memory' ? 'system' : ''}`} style={{ padding: '0.5rem 0.85rem', fontSize: '0.88rem', lineHeight: '1.5' }}>
                    {m.tag && <div className="message-tag">{m.tag}</div>}
                    <div className="markdown-content">
                      <Markdown remarkPlugins={[remarkGfm]}>{m.content}</Markdown>
                    </div>
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
              {errorMessage && (
                <div className="message-wrapper" style={{ marginBottom: '6px' }}>
                  <div className="message bot error-message">{errorMessage}</div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat input — only shown once the care plan is ready */}
            {latestPlan ? (
              <div>
                <div className="chat-mode-toggle">
                  <button className={chatMode === 'ask' ? 'active' : ''} onClick={() => setChatMode('ask')}>Ask</button>
                  <button className={chatMode === 'feedback' ? 'active' : ''} onClick={() => setChatMode('feedback')}>Plan feedback</button>
                </div>
                <div className={`chat-input-row ${chatMode === 'feedback' ? 'feedback-mode' : ''}`}>
                  <input
                    type="text"
                    placeholder={chatMode === 'ask' ? 'Ask a question about the care plan...' : 'Describe a change to the care plan...'}
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleChatSubmit}
                    disabled={!!streamingReply}
                  />
                  <button
                    onClick={() => sendChatMessage(chatInput)}
                    disabled={!!streamingReply || !chatInput.trim()}
                    title={chatMode === 'ask' ? 'Send Message' : 'Add as plan feedback'}
                    className="send-button"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '-2px' }}>
                      <line x1="22" y1="2" x2="11" y2="13"></line>
                      <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                    </svg>
                  </button>
                </div>
                {chatContext && (
                  <div className="chat-context-note" title="The assistant sees every argument and the current plan in compact form; older turns are summarized.">
                    Context ~{chatContext.prompt_tokens.toLocaleString()} tokens (compacted){chatContext.compactions ? ` · history summarized ${chatContext.compactions}×` : ''}
                  </div>
                )}
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
        {showProgress && (
          <ReasoningTrace
            title={isGeneratingPlan
              ? (latestPlan ? `Updating Care Plan (v${latestPlan.version + 1})...` : 'Finalizing Care Plan...')
              : 'Analyzing Conditions and Drafting Care Plan...'}
            steps={reasoningSteps}
            waitingMessage={waitingMessage}
            revision={isGeneratingPlan && latestPlan ? revisionInfo : null}
          />
        )}

        {showDashboard && (
          <div className="human-review-dashboard">
            <div className="tabs-header">
              <button
                className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
                onClick={() => setActiveTab('graph')}
                disabled={!needsReview && !latestPlan}
              >
                Interactive Graph Review{pendingChanges > 0 && latestPlan ? ` (${pendingChanges})` : ''}
              </button>
              <button
                className={`tab-btn ${activeTab === 'plan' ? 'active' : ''}`}
                onClick={() => setActiveTab('plan')}
                disabled={!latestPlan}
              >
                Final Care Plan{pendingFeedback.length ? ` (${pendingFeedback.length})` : ''}
              </button>
              <button
                className={`tab-btn ${activeTab === 'memory' ? 'active' : ''}`}
                onClick={() => setActiveTab('memory')}
              >
                Learned Memory
              </button>
            </div>

            {activeTab === 'graph' && (needsReview || latestPlan) && (
              <ArgumentBoard
                options={handlingOptions}
                args={argumentsData}
                qbafOptions={latestPlan?.options}
                qbafArgs={qbafArgs}
                phase={phase}
                loading={loading}
                pendingChanges={pendingChanges}
                pendingFeedbackCount={pendingFeedback.length}
                onAction={submitAction}
                onAccept={acceptArguments}
                onRegenerate={regeneratePlan}
              />
            )}

            {activeTab === 'plan' && shownPlan && (
              <CarePlanDocument
                plan={shownPlan}
                versions={versions}
                isLatest={shownPlan.version === latestPlan?.version}
                onSelectVersion={setSelectedVersion}
                pendingFeedback={pendingFeedback}
                pendingChanges={pendingChanges}
                onAddFeedback={addFeedback}
                onRemoveFeedback={removeFeedback}
                onRegenerate={regeneratePlan}
                onDownloadPdf={downloadPdf}
                onApprove={approvePlan}
                busy={loading}
                finishing={finishing}
              />
            )}

            {activeTab === 'memory' && <MemoryPanel usedIds={memoryUsedIds} refreshKey={memoryRefresh} />}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
