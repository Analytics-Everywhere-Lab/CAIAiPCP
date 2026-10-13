import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE, downloadFile, getJSON, openEventStream, postJSON, streamPost } from './api'
import { usePersistentState, useTheme } from './hooks'
import ArgumentBoard from './components/ArgumentBoard'
import CarePlanDocument from './components/CarePlanDocument'
import ChatPanel from './components/ChatPanel'
import MemoryPanel from './components/MemoryPanel'
import Panel from './components/Panel'
import PatientPanel from './components/PatientPanel'
import ReasoningTrace from './components/ReasoningTrace'
import SettingsDialog from './components/SettingsDialog'
import Welcome from './components/Welcome'
import {
  Alert, BrandMark, Brain, Chat, Check, ChevronLeft, ChevronRight, FileText, Moon, Scale, Settings, Sun, User, X
} from './components/Icons'

const STEPS = ['Patient', 'Argument review', 'Care plan', 'Approved']

function modelLabel(settings) {
  if (!settings) return 'Model'
  if (settings.provider === 'anthropic') {
    return settings.claude_models?.find(m => m.id === settings.anthropic_model)?.label || settings.anthropic_model
  }
  return `Ollama · ${settings.ollama_model}`
}

function App() {
  const { theme, preference, setPreference, toggle: toggleTheme } = useTheme()
  const [sidebarCollapsed, setSidebarCollapsed] = usePersistentState('caiaipcp:sidebar-collapsed', false)
  const [settings, setSettings] = useState(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [backendDown, setBackendDown] = useState(false)
  const [providerError, setProviderError] = useState('')

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
  const [reasoningSteps, setReasoningSteps] = useState([])
  const [streamingReply, setStreamingReply] = useState('') // live LLM reply to user chat
  const [errorMessage, setErrorMessage] = useState('')
  const eventSourceRef = useRef(null)

  // Argument graph review
  const [needsReview, setNeedsReview] = useState(false)
  const [handlingOptions, setHandlingOptions] = useState([])
  const [argumentsData, setArgumentsData] = useState([])
  const [qbafArgs, setQbafArgs] = useState({})
  const [optionReviews, setOptionReviews] = useState({})
  const [pendingChanges, setPendingChanges] = useState(0)

  // Care plan versions and feedback notes
  const [versions, setVersions] = useState([])
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [notes, setNotes] = useState([])
  const [revisionInfo, setRevisionInfo] = useState(null)
  const [memoryRefresh, setMemoryRefresh] = useState(0)

  const noteSeq = useRef(0)
  const reflectionPoll = useRef(null)

  const loadSettings = useCallback(async () => {
    try {
      setSettings(await getJSON('/api/settings'))
      setBackendDown(false)
    } catch {
      setBackendDown(true)
    }
  }, [])

  useEffect(() => {
    loadSettings()
    return () => clearInterval(reflectionPoll.current)
  }, [loadSettings])

  const latestPlan = versions.length ? versions[versions.length - 1] : null
  const shownPlan = versions.find(v => v.version === selectedVersion) || latestPlan
  const phase = needsReview ? 'review' : latestPlan ? 'plan' : 'idle'
  const savedNotes = notes.filter(n => !n.draft)
  const pendingTotal = savedNotes.length + pendingChanges

  const applyPayload = (d) => {
    if (d.options) setHandlingOptions(d.options)
    if (d.arguments) setArgumentsData(d.arguments)
    if (d.qbaf_arguments) setQbafArgs(d.qbaf_arguments)
    if (d.option_reviews) setOptionReviews(d.option_reviews)
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
        setMessages(prev => [...prev, { content: d.content, node: d.node, role: 'bot' }])
      } else if (d.node === 'progress') {
        setWaitingMessage(d.content.slice(0, 150))
      } else {
        setWaitingMessage(d.content.slice(0, 150))
        pushStep(d.node, d.content)
      }
    } else if (d.type === 'stream_text') {
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
    } else if (d.type === 'provider_error') {
      setProviderError(d.content)
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
    setProviderError('')
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
    setOptionReviews({})
    setPendingChanges(0)
    setNotes([])
    setRevisionInfo(null)
    setActiveTab('graph')
    setIsGeneratingPlan(false)
    setHasStarted(true)
    setWaitingMessage('Initializing processes...')
    setReasoningSteps([])
    setStreamingReply('')

    try {
      const data = await postJSON('/api/chat/start', { patient_info: patientInfo, severity })
      setThreadId(data.thread_id)
      openRun(data.thread_id)
    } catch (err) {
      console.error(err)
      setErrorMessage(err.message)
      setBackendDown(true)
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
    const feedback = savedNotes.map(({ text, section_id, quote }) => ({
      text, section_id: section_id === 'decision' ? null : section_id, quote
    }))
    try {
      await postJSON(`/api/chat/regenerate/${threadId}`, { feedback })
      const parts = []
      if (feedback.length) parts.push(`${feedback.length} feedback note${feedback.length === 1 ? '' : 's'}`)
      if (pendingChanges) parts.push(`${pendingChanges} argument change${pendingChanges === 1 ? '' : 's'}`)
      setMessages(prev => [...prev, { role: 'user', content: `Regenerate the care plan${parts.length ? ` with ${parts.join(' and ')}` : ''}.` }])
      setNotes([])
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

  // Feedback notes. Drafts are notes still being written; only saved notes are sent.
  const createNote = (note) => {
    noteSeq.current += 1
    const localId = `n${noteSeq.current}`
    setNotes(prev => [...prev, { kind: 'general', section_id: null, quote: null, start: null, end: null, ...note, localId }])
    return localId
  }
  const updateNote = (localId, patch) => setNotes(prev => prev.map(n => (n.localId === localId ? { ...n, ...patch } : n)))
  const removeNote = (localId) => setNotes(prev => prev.filter(n => n.localId !== localId))
  const clearNotes = () => setNotes([])

  const addChatNote = (text) => {
    if (!text.trim()) return
    createNote({ kind: 'general', text: text.trim(), draft: false })
    setMessages(prev => [...prev, { content: text.trim(), role: 'user', tag: 'Added as a feedback note · applied when you regenerate' }])
    setChatInput('')
    setActiveTab('plan')
  }

  const sendChatMessage = async (text) => {
    if (!threadId || !text.trim()) return
    setMessages(prev => [...prev, { content: text, role: 'user' }])
    setChatInput('')
    setStreamingReply('')
    setErrorMessage('')
    let fullReply = ''
    try {
      await streamPost(`/api/chat/message/${threadId}`, { message: text }, (d) => {
        if (d.type === 'stream_text') {
          fullReply = d.full
          setStreamingReply(d.full)
        } else if (d.type === 'message') {
          setStreamingReply('')
          setMessages(prev => [...prev, { content: d.content, node: d.node, role: 'bot' }])
          fullReply = ''
        } else if (d.type === 'error') {
          setStreamingReply('')
          setErrorMessage(d.content)
          fullReply = ''
        }
      })
    } catch (err) {
      console.error(err)
      setErrorMessage(err.message)
    } finally {
      setStreamingReply('')
      if (fullReply) setMessages(prev => [...prev, { content: fullReply, node: 'bot', role: 'bot' }])
    }
  }

  const openSettings = () => {
    loadSettings()
    setSettingsOpen(true)
  }
  const closeSettings = useCallback(() => setSettingsOpen(false), [])

  const memoryUsedIds = (latestPlan?.memory_used || []).map(m => m.memory_id)
  const showProgress = (loading && !needsReview && !latestPlan) || isGeneratingPlan
  const showDashboard = !showProgress && (needsReview || latestPlan || activeTab === 'memory')

  const stage = !hasStarted ? 0 : latestPlan ? (latestPlan.status === 'approved' ? 3 : 2) : isGeneratingPlan ? 2 : 1

  const tabs = [
    { id: 'graph', label: 'Arguments', icon: <Scale size={16} />, count: latestPlan ? pendingChanges : 0, disabled: !needsReview && !latestPlan },
    { id: 'plan', label: 'Care plan', icon: <FileText size={16} />, count: savedNotes.length, disabled: !latestPlan,
      extra: latestPlan ? `v${latestPlan.version}` : null },
    { id: 'memory', label: 'Learned memory', icon: <Brain size={16} />, count: 0 }
  ]

  return (
    <div className={`app ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <header className="topbar">
        <div className="topbar-left">
          <button type="button" className="icon-btn sidebar-toggle" onClick={() => setSidebarCollapsed(c => !c)}
            title={sidebarCollapsed ? 'Show patient and assistant' : 'Hide patient and assistant'} aria-label="Toggle side panel">
            {sidebarCollapsed ? <ChevronRight /> : <ChevronLeft />}
          </button>
          <div className="brand">
            <BrandMark size={36} />
            <div className="brand-text">
              <span className="brand-title">Aging-in-Place Care Planner</span>
            </div>
          </div>
        </div>

        <ol className="stepper" aria-label="Progress">
          {STEPS.map((label, index) => (
            <li key={label} className={index < stage ? 'done' : index === stage ? 'current' : ''}>
              <span className="step-dot">{index < stage ? <Check size={12} /> : index + 1}</span>
              <span className="step-label">{label}</span>
            </li>
          ))}
        </ol>

        <div className="topbar-right">
          <button type="button" className="model-chip" onClick={openSettings} title="Language model settings">
            <span className={`status-dot ${providerError || backendDown ? 'warn' : settings?.provider === 'anthropic' ? 'claude' : 'ok'}`} />
            <span className="model-chip-text">{modelLabel(settings)}</span>
          </button>
          <button type="button" className="icon-btn" onClick={toggleTheme} title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            aria-label="Toggle theme">
            {theme === 'dark' ? <Sun /> : <Moon />}
          </button>
          <button type="button" className="icon-btn" onClick={openSettings} title="Settings" aria-label="Settings"><Settings /></button>
        </div>
      </header>

      {backendDown && (
        <div className="app-banner warn" role="alert">
          <Alert size={16} />
          <span>Cannot reach the care-planning server at <code>{API_BASE}</code>. Start it with <code>uvicorn api:app --port 8001</code>.</span>
          <button type="button" className="btn ghost xs" onClick={loadSettings}>Retry</button>
        </div>
      )}
      {providerError && !backendDown && (
        <div className="app-banner warn" role="alert">
          <Alert size={16} />
          <span><strong>The language model reported a problem:</strong> {providerError}</span>
          <button type="button" className="btn soft xs" onClick={openSettings}>Open settings</button>
          <button type="button" className="icon-btn xs" onClick={() => setProviderError('')} aria-label="Dismiss"><X size={14} /></button>
        </div>
      )}

      <div className="layout">
        <aside className="sidebar" aria-label="Patient and assistant">
          {sidebarCollapsed ? (
            <div className="sidebar-rail">
              <button type="button" className="rail-btn" onClick={() => setSidebarCollapsed(false)} title="Patient"><User /></button>
              <button type="button" className="rail-btn" onClick={() => setSidebarCollapsed(false)} title="Care assistant">
                <Chat />{messages.length > 0 && <span className="rail-dot" />}
              </button>
            </div>
          ) : (
            <>
              <Panel id="patient" title="Patient" icon={<User size={16} />}
                subtitle={hasStarted ? 'Current case' : 'Describe the person'}>
                <PatientPanel patientInfo={patientInfo} setPatientInfo={setPatientInfo} severity={severity} setSeverity={setSeverity}
                  hasStarted={hasStarted} loading={loading} onStart={startGeneration} onEdit={() => setHasStarted(false)} />
              </Panel>
              <Panel id="assistant" title="Care assistant" icon={<Chat size={16} />} className="panel-chat" bodyClassName="panel-body-chat"
                subtitle={latestPlan ? 'Knows every argument and the plan' : 'Available once the plan is ready'}>
                <ChatPanel messages={messages} streamingReply={streamingReply} errorMessage={errorMessage}
                  planReady={!!latestPlan} input={chatInput} setInput={setChatInput}
                  onSend={sendChatMessage} onAddNote={addChatNote} onRegenerate={regeneratePlan}
                  pendingCount={pendingTotal} busy={loading} />
              </Panel>
            </>
          )}
        </aside>

        <main className="workspace">
          {showProgress ? (
            <div className="workspace-card">
              <ReasoningTrace
                title={isGeneratingPlan
                  ? (latestPlan ? `Updating the care plan to version ${latestPlan.version + 1}` : 'Writing the care plan')
                  : 'Analyzing the case and arguing the options'}
                steps={reasoningSteps}
                waitingMessage={waitingMessage}
                revision={isGeneratingPlan && latestPlan ? revisionInfo : null}
              />
            </div>
          ) : showDashboard ? (
            <div className="workspace-card">
              <div className="workspace-tabs" role="tablist" aria-label="Workspace">
                {tabs.map(tab => (
                  <button key={tab.id} type="button" role="tab" aria-selected={activeTab === tab.id} disabled={tab.disabled}
                    className={`workspace-tab ${activeTab === tab.id ? 'active' : ''}`} onClick={() => setActiveTab(tab.id)}>
                    {tab.icon}<span>{tab.label}</span>
                    {tab.extra && <span className="tab-extra">{tab.extra}</span>}
                    {tab.count > 0 && <span className="count-pill accent">{tab.count}</span>}
                  </button>
                ))}
              </div>
              <div className="workspace-body">
                {activeTab === 'graph' && (needsReview || latestPlan) && (
                  <ArgumentBoard
                    options={handlingOptions}
                    args={argumentsData}
                    qbafOptions={latestPlan?.options}
                    qbafArgs={qbafArgs}
                    reviews={optionReviews}
                    phase={phase}
                    loading={loading}
                    pendingChanges={pendingChanges}
                    pendingFeedbackCount={savedNotes.length}
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
                    notes={notes}
                    onCreateNote={createNote}
                    onUpdateNote={updateNote}
                    onRemoveNote={removeNote}
                    onClearNotes={clearNotes}
                    pendingChanges={pendingChanges}
                    onRegenerate={regeneratePlan}
                    onDownloadPdf={downloadPdf}
                    onApprove={approvePlan}
                    busy={loading}
                    finishing={finishing}
                  />
                )}
                {activeTab === 'memory' && <MemoryPanel usedIds={memoryUsedIds} refreshKey={memoryRefresh} />}
              </div>
            </div>
          ) : (
            <div className="workspace-card">
              <Welcome onExample={(text) => { setPatientInfo(text); setHasStarted(false); setSidebarCollapsed(false) }} />
            </div>
          )}
        </main>
      </div>

      <SettingsDialog open={settingsOpen} onClose={closeSettings} settings={settings}
        onSaved={(data) => { setSettings(data); setProviderError('') }}
        themePreference={preference} onThemeChange={setPreference} />
    </div>
  )
}

export default App
