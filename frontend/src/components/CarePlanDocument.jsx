import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useElementWidth, usePersistentState } from '../hooks'
import { layoutCards, rectsWithin, resolveRange, selectionAnchor } from './annotations'
import { CitedText, ReferenceItem, citationMarkdown, clipCited, ieeeText } from './Citations'
import {
  Check, CheckCircle, ChevronDown, Collapse, Download, Edit, Expand, Eye, EyeOff, Note, NotePlus, Printer, Refresh, Trash, X
} from './Icons'

export const TIER_CLASS = {
  recommended: 'tier-recommended',
  conditional: 'tier-conditional',
  uncertain: 'tier-uncertain',
  set_aside: 'tier-set-aside'
}

const RAIL_MIN_WIDTH = 960 // below this the notes move from the margin into the feedback bar
const DECISION_ID = 'decision'

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return iso
  }
}

export function clip(text, max) {
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  return clean.length > max ? clean.slice(0, max - 1) + '…' : clean
}

function stripRoleTag(content) {
  return content?.startsWith('[') && content.indexOf(']') > 0 ? content.slice(content.indexOf(']') + 1).trim() : content
}

function RevisionNote({ plan, titles }) {
  return (
    <details className="revision-note" open>
      <summary>
        <span>How version {plan.version} was produced: <strong>{plan.strategy_label}</strong></span>
        {plan.decided_by === 'llm' && <span className="revision-note-by">reasoned by the planner</span>}
      </summary>
      <p>{plan.rationale}</p>
      {plan.changed_sections?.length > 0 && (
        <div className="revision-note-row">Updated sections: {plan.changed_sections.map(id => titles[id] || id).join(', ')}</div>
      )}
      {plan.feedback_applied?.length > 0 && (
        <div className="revision-note-row">
          Feedback applied:
          <ul>{plan.feedback_applied.map(item => <li key={item.id}><strong>{item.id}</strong> {item.text}</li>)}</ul>
        </div>
      )}
      {(plan.feedback_ops?.length > 0 || plan.contested_ops?.length > 0) && (
        <div className="revision-note-row">
          Changes to the argument graph:
          <ul className="revision-ops">
            {(plan.feedback_ops?.length ? plan.feedback_ops : plan.contested_ops).map((line, i) => <li key={i}>{ieeeText(line.replace(/^- /, ''))}</li>)}
          </ul>
        </div>
      )}
    </details>
  )
}

function NoteCard({
  note, number, label, editing, active, style, cardRef, onEdit, onSave, onCancel, onDelete, onFocus, onHover, onDraftChange
}) {
  const [draft, setDraft] = useState(note.text || '')
  useEffect(() => { if (editing) setDraft(note.text || '') }, [editing, note.text])
  const change = (text) => {
    setDraft(text)
    onDraftChange(text)
  }
  const save = () => draft.trim() && onSave(draft.trim())
  return (
    <div ref={cardRef} style={style}
      className={`note-card kind-${note.kind} ${editing ? 'is-editing' : ''} ${active ? 'is-active' : ''}`}
      onMouseEnter={() => onHover(note.localId)} onMouseLeave={() => onHover(null)}
      onClick={() => !editing && onFocus(note.localId)}>
      <div className="note-card-head">
        <span className="note-number">{number}</span>
        <span className="note-label">{label}</span>
        {!editing && (
          <span className="note-tools">
            <button type="button" className="icon-btn xs" title="Edit note" onClick={e => { e.stopPropagation(); onEdit(note.localId) }}><Edit size={13} /></button>
            <button type="button" className="icon-btn xs" title="Delete note" onClick={e => { e.stopPropagation(); onDelete(note.localId) }}><Trash size={13} /></button>
          </span>
        )}
      </div>
      {note.quote && <blockquote className="note-quote">{clip(note.quote, 160)}</blockquote>}
      {editing ? (
        <div className="note-editor" onClick={e => e.stopPropagation()}>
          <textarea autoFocus value={draft} rows={3} onChange={e => change(e.target.value)}
            placeholder={note.kind === 'general'
              ? 'Feedback on the whole plan. Tip: select text in the plan to pin a note to it.'
              : 'What should change here?'}
            onKeyDown={e => {
              if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); save() }
              if (e.key === 'Escape') { e.preventDefault(); onCancel(note.localId) }
            }} />
          <div className="note-editor-actions">
            <span className="note-editor-hint">Ctrl+Enter to save</span>
            <button type="button" className="btn ghost sm" onClick={() => onCancel(note.localId)}>Cancel</button>
            <button type="button" className="btn primary sm" disabled={!draft.trim()} onClick={save}><Check size={14} /> Save note</button>
          </div>
        </div>
      ) : (
        <p className="note-text">{note.text}</p>
      )}
    </div>
  )
}

export default function CarePlanDocument({
  plan, versions, isLatest, onSelectVersion, notes, onCreateNote, onUpdateNote, onRemoveNote, onClearNotes,
  pendingChanges, onRegenerate, onDownloadPdf, onApprove, busy, finishing
}) {
  const canvasRef = useRef(null)
  const innerRef = useRef(null)
  const paperRef = useRef(null)
  const cardRefs = useRef({})
  const draftTexts = useRef({})
  const canvasWidth = useElementWidth(canvasRef)
  const railMode = canvasWidth >= RAIL_MIN_WIDTH

  const [selection, setSelection] = useState(null) // { sectionId, quote, start, end, top, left }
  const [editingId, setEditingId] = useState(null)
  const [activeId, setActiveId] = useState(null)
  const [flashId, setFlashId] = useState(null)
  const [collapsed, setCollapsed] = useState(() => new Set())
  const [anchors, setAnchors] = useState({})
  const [heights, setHeights] = useState({})
  const [layoutTick, setLayoutTick] = useState(0)
  const [listOpen, setListOpen] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [notesHidden, setNotesHidden] = usePersistentState('caiaipcp:notes-hidden', false)

  const sections = plan.sections || []
  const titles = { [DECISION_ID]: 'Decision Summary', ...Object.fromEntries(sections.map(s => [s.id, s.title])) }
  const changed = new Set(plan.version > 1 ? plan.changed_sections || [] : [])
  const slots = Object.entries(plan.scheduling?.slots || {}).filter(([, list]) => list?.length)
  // Options the clinician's contest set aside are not part of the plan; they are noted, not ranked as "not recommended".
  const rankedOptions = [...(plan.options || [])].sort((a, b) => a.rank - b.rank)
  const planOptions = rankedOptions.filter(row => row.tier !== 'set_aside')
  const setAside = rankedOptions.filter(row => row.tier === 'set_aside')
  const refIds = new Set((plan.reference_list || []).map(ref => ref.id))
  const visibleNotes = isLatest ? notes : []
  const savedNotes = notes.filter(n => !n.draft)
  // The notes (margin cards, highlights and markers) appear with the first note and can be hidden.
  const showNotes = visibleNotes.length > 0 && !notesHidden
  const railShown = railMode && showNotes
  const numbers = Object.fromEntries(notes.map((n, i) => [n.localId, i + 1]))
  const noteLabel = (note) => (note.kind === 'general' ? 'Whole plan' : titles[note.section_id] || 'Care plan')
  const totalPending = savedNotes.length + pendingChanges
  const canRegenerate = !busy && totalPending > 0
  const allCollapsed = sections.length > 0 && sections.every(s => collapsed.has(s.id))

  // Recompute anchors whenever the document reflows.
  useEffect(() => {
    const paper = paperRef.current
    if (!paper || typeof ResizeObserver === 'undefined') return undefined
    const observer = new ResizeObserver(() => setLayoutTick(t => t + 1))
    observer.observe(paper)
    document.fonts?.ready?.then(() => setLayoutTick(t => t + 1))
    return () => observer.disconnect()
  }, [])

  useLayoutEffect(() => {
    const paper = paperRef.current
    const inner = innerRef.current
    if (!paper || !inner) return
    const innerTop = inner.getBoundingClientRect().top
    const paperTop = paper.getBoundingClientRect().top - innerTop
    const next = {}
    visibleNotes.forEach((note, order) => {
      let rects = []
      let top = 0
      if (note.kind === 'text' && !collapsed.has(note.section_id)) {
        const container = paper.querySelector(`[data-anchor-root="${note.section_id}"]`)
        const range = resolveRange(container, note)
        if (range) rects = rectsWithin(range, paper)
      }
      let bottom = 0
      if (rects.length) {
        const last = rects[rects.length - 1]
        top = paperTop + rects[0].top
        bottom = paperTop + last.top + last.height
      } else if (note.section_id) {
        const header = paper.querySelector(`[data-section-id="${note.section_id}"] .plan-section-header`)
        const box = header?.getBoundingClientRect()
        top = box ? box.top - innerTop : 0
        bottom = box ? box.bottom - innerTop : 0
      }
      next[note.localId] = { rects, top, bottom, order }
    })
    setAnchors(next)
  }, [notes, plan, collapsed, railMode, railShown, layoutTick, isLatest]) // eslint-disable-line react-hooks/exhaustive-deps

  // Measure note cards so they can be stacked without overlapping.
  useLayoutEffect(() => {
    const measured = {}
    let differs = false
    Object.entries(cardRefs.current).forEach(([id, element]) => {
      if (!element) return
      measured[id] = element.offsetHeight
      if (heights[id] !== measured[id]) differs = true
    })
    if (differs) setHeights(measured)
  })

  const positions = layoutCards(
    visibleNotes.map(note => ({ id: note.localId, top: anchors[note.localId]?.top ?? 0, order: numbers[note.localId] })),
    heights
  )
  const railHeight = Math.max(0, ...visibleNotes.map(n => (positions[n.localId] || 0) + (heights[n.localId] || 120)))

  const updateSelection = useCallback(() => {
    if (!isLatest) return setSelection(null)
    const anchor = selectionAnchor(paperRef.current)
    if (!anchor || !innerRef.current) return setSelection(null)
    const rects = anchor.range.getClientRects()
    const last = rects[rects.length - 1] || anchor.range.getBoundingClientRect()
    const box = innerRef.current.getBoundingClientRect()
    const { range, ...rest } = anchor // eslint-disable-line no-unused-vars
    setSelection({
      ...rest,
      top: last.bottom - box.top + 8,
      left: Math.min(Math.max(8, last.right - box.left - 70), Math.max(8, box.width - 160))
    })
  }, [isLatest])

  useEffect(() => {
    const onSelectionChange = () => {
      const current = window.getSelection()
      if (!current || current.isCollapsed) setSelection(null)
    }
    document.addEventListener('selectionchange', onSelectionChange)
    return () => document.removeEventListener('selectionchange', onSelectionChange)
  }, [])

  // Leaving a note that is being edited: keep typed text, drop an empty new note.
  const settleEditing = () => {
    const note = notes.find(n => n.localId === editingId)
    if (!note) return
    const typed = (draftTexts.current[note.localId] || '').trim()
    if (typed) onUpdateNote(note.localId, { text: typed, draft: false })
    else if (note.draft) onRemoveNote(note.localId)
    delete draftTexts.current[note.localId]
  }

  const startNote = (note) => {
    settleEditing()
    setNotesHidden(false)
    const id = onCreateNote({ text: '', draft: true, ...note })
    setEditingId(id)
    setActiveId(id)
    setSelection(null)
    window.getSelection()?.removeAllRanges()
    if (!railMode) setListOpen(false)
  }

  const noteFromSelection = (anchor = selection) => {
    if (!anchor) return false
    startNote({
      kind: 'text',
      section_id: anchor.sectionId,
      quote: anchor.quote,
      start: anchor.start,
      end: anchor.end
    })
    return true
  }

  const addFeedback = () => {
    // A live selection becomes an anchored note; otherwise the note is about the whole plan.
    const anchor = selectionAnchor(paperRef.current)
    if (anchor) {
      const { range, ...rest } = anchor // eslint-disable-line no-unused-vars
      noteFromSelection(rest)
    } else {
      startNote({ kind: 'general', section_id: null, quote: null, start: null, end: null })
    }
  }

  const saveNote = (id, text) => {
    onUpdateNote(id, { text, draft: false })
    delete draftTexts.current[id]
    setEditingId(null)
  }

  const cancelNote = (id) => {
    const note = notes.find(n => n.localId === id)
    if (note?.draft) onRemoveNote(id)
    delete draftTexts.current[id]
    setEditingId(null)
  }

  const editNote = (id) => {
    if (id !== editingId) settleEditing()
    setEditingId(id)
  }

  const deleteNote = (id) => {
    onRemoveNote(id)
    if (editingId === id) setEditingId(null)
  }

  const focusNote = (id) => {
    setNotesHidden(false)
    setActiveId(id)
    setFlashId(id)
    setTimeout(() => setFlashId(current => (current === id ? null : current)), 1200)
    // Works whether the plan scrolls inside its panel (desktop) or with the page (mobile).
    const note = notes.find(n => n.localId === id)
    const paper = paperRef.current
    const target = paper?.querySelector(`[data-note="${id}"]`)
      || (note?.section_id && paper?.querySelector(`[data-section-id="${note.section_id}"]`))
      || paper
    target?.scrollIntoView({ block: target === paper ? 'start' : 'center', behavior: 'smooth' })
  }

  const focusFromBadge = (id) => {
    setActiveId(id)
    if (railMode) {
      cardRefs.current[id]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    } else {
      setListOpen(true)
    }
  }

  const toggleSection = (id) => setCollapsed(prev => {
    const next = new Set(prev)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    return next
  })

  const toggleAll = () => setCollapsed(allCollapsed ? new Set() : new Set(sections.map(s => s.id)))

  const download = async () => {
    setDownloading(true)
    try {
      await onDownloadPdf(plan.version)
    } finally {
      setDownloading(false)
    }
  }

  const notesIn = (sectionId) => visibleNotes.filter(n => n.section_id === sectionId && !n.draft).length
  const editingNote = visibleNotes.find(n => n.localId === editingId)

  const renderCard = (note, style) => (
    <NoteCard key={note.localId} note={note} number={numbers[note.localId]} label={noteLabel(note)}
      editing={editingId === note.localId} active={activeId === note.localId} style={style}
      cardRef={el => { cardRefs.current[note.localId] = el }}
      onEdit={editNote} onSave={(text) => saveNote(note.localId, text)} onCancel={cancelNote}
      onDraftChange={(text) => { draftTexts.current[note.localId] = text }}
      onDelete={deleteNote} onFocus={focusNote} onHover={setActiveId} />
  )

  const sectionHeader = (id, number, title, extra) => (
    <header className="plan-section-header">
      <button type="button" className="section-toggle" onClick={() => toggleSection(id)} aria-expanded={!collapsed.has(id)}>
        <ChevronDown className="section-chevron" size={16} />
        <h2><span className="section-number">{number}</span>{title}</h2>
      </button>
      {extra}
      {notesIn(id) > 0 && <span className="badge badge-notes"><Note size={12} /> {notesIn(id)}</span>}
      {isLatest && (
        <button type="button" className="btn ghost xs section-comment" title={`Add feedback on ${title}`}
          onClick={() => startNote({ kind: 'section', section_id: id, quote: null, start: null, end: null })}>
          <NotePlus size={14} /> <span>Comment</span>
        </button>
      )}
    </header>
  )

  return (
    <div className="plan-view">
      <div className="plan-toolbar">
        <div className="plan-toolbar-group">
          <div className="version-switch" role="tablist" aria-label="Plan versions">
            {versions.map(v => (
              <button key={v.version} type="button" role="tab" aria-selected={v.version === plan.version}
                className={`version-pill ${v.version === plan.version ? 'active' : ''}`} onClick={() => onSelectVersion(v.version)}
                title={`${v.strategy_label} · ${formatDate(v.created_at)}`}>
                v{v.version}{v.status === 'approved' && <Check size={12} />}
              </button>
            ))}
          </div>
          {plan.status === 'approved'
            ? <span className="status-chip approved"><CheckCircle size={13} /> Approved {formatDate(plan.approved_at)}</span>
            : <span className="status-chip draft">Draft for clinical review</span>}
        </div>
        <div className="plan-toolbar-group">
          {visibleNotes.length > 0 && (
            <button type="button" className={`btn ghost sm notes-toggle ${notesHidden ? '' : 'is-on'}`}
              onClick={() => setNotesHidden(hidden => !hidden)} aria-pressed={!notesHidden}
              title={notesHidden ? 'Show your feedback notes beside the plan' : 'Hide the notes to read the plan on its own'}>
              {notesHidden ? <Eye size={15} /> : <EyeOff size={15} />}
              {notesHidden ? `Show notes (${savedNotes.length})` : 'Hide notes'}
            </button>
          )}
          <button type="button" className="icon-btn" onClick={toggleAll} title={allCollapsed ? 'Expand all sections' : 'Collapse all sections'}>
            {allCollapsed ? <Expand /> : <Collapse />}
          </button>
          <button type="button" className="icon-btn" onClick={() => window.print()} title="Print"><Printer /></button>
          <button type="button" className="btn secondary sm" disabled={downloading} onClick={download}>
            <Download size={15} /> {downloading ? 'Preparing…' : 'PDF'}
          </button>
          {plan.status !== 'approved' && (
            <button type="button" className="btn success sm" disabled={busy} onClick={() => onApprove(plan.version)}>
              <CheckCircle size={15} /> Approve
            </button>
          )}
        </div>
      </div>

      {!isLatest && (
        <div className="inline-banner info">
          You are viewing version {plan.version}. Feedback notes go on the latest version.
          <button type="button" className="link-btn" onClick={() => onSelectVersion(versions[versions.length - 1].version)}>Go to latest</button>
        </div>
      )}
      {finishing && <div className="inline-banner subtle">Finishing up: checking provider availability and learning from your review…</div>}

      <div className="plan-canvas" ref={canvasRef} onMouseUp={updateSelection} onKeyUp={updateSelection}
        onTouchEnd={() => setTimeout(updateSelection, 50)}>
        <div className={`plan-canvas-inner ${railShown ? 'with-rail' : ''}`} ref={innerRef}>
          <div className="plan-paper" ref={paperRef}>
            <div className="annotation-layer" aria-hidden="true">
              {showNotes && visibleNotes.map(note => (anchors[note.localId]?.rects || []).map((rect, i) => (
                <span key={`${note.localId}-${i}`} data-note={i === 0 ? note.localId : undefined}
                  className={`note-highlight ${note.draft ? 'is-draft' : ''} ${activeId === note.localId ? 'is-active' : ''} ${flashId === note.localId ? 'is-flash' : ''}`}
                  style={{ top: rect.top - 1, left: rect.left - 1, width: rect.width + 2, height: rect.height + 2 }} />
              )))}
            </div>

            <article className="plan-document" id="care-plan-document">
              <header className="plan-band">
                <div>
                  <div className="plan-band-eyebrow">Aging-in-place care plan</div>
                  <h1>Care Plan · Version {plan.version}</h1>
                  <div className="plan-band-sub">{plan.status === 'approved' ? 'Approved' : 'Draft for clinical review'} · Generated {formatDate(plan.created_at)}</div>
                </div>
              </header>

              <dl className="plan-meta">
                <dt>Patient</dt><dd>{plan.patient_info}</dd>
                <dt>Severity</dt><dd>{plan.severity || 'Not assessed'}</dd>
                <dt>Care team</dt><dd>{(plan.care_team || []).map(m => m.name || m.role).join(', ') || 'Not assigned'}</dd>
                <dt>Decision confidence</dt>
                <dd className="plan-meta-confidence">
                  <span className="meter"><span style={{ width: `${Math.round(100 * (plan.decision_confidence || 0))}%` }} /></span>
                  <strong>{Math.round(100 * (plan.decision_confidence || 0))}%</strong>
                  <span className="plan-meta-hint">how decisively the verified arguments settle each option, scaled by how well they are grounded in evidence</span>
                </dd>
              </dl>

              {plan.version > 1 && <RevisionNote plan={plan} titles={titles} />}

              <section className={`plan-section ${collapsed.has(DECISION_ID) ? 'is-collapsed' : ''}`} data-section-id={DECISION_ID}>
                {sectionHeader(DECISION_ID, 1, 'Decision Summary')}
                {!collapsed.has(DECISION_ID) && (
                  <div className="plan-section-body" data-anchor-root={DECISION_ID}>
                    <p className="plan-note">
                      Each care option was weighed in a quantitative bipolar argumentation framework: supporting and
                      challenging arguments from the care team, verified against the medical knowledge base and contested
                      by the reviewing clinician.
                    </p>
                    <div className="table-scroll">
                      <table className="decision-table">
                        <thead><tr><th>Care option</th><th>Assessment</th><th>Strength</th><th>Leading support</th><th>Leading concern</th></tr></thead>
                        <tbody>
                          {planOptions.length === 0 && (
                            <tr><td colSpan={5} className="empty-cell">No option is supported strongly enough to include. Contest the arguments on the argument board.</td></tr>
                          )}
                          {planOptions.map(row => (
                            <tr key={row.option_id}>
                              <td className="option-cell"><CitedText text={row.option} refIds={refIds} /></td>
                              <td><span className={`tier-pill ${TIER_CLASS[row.tier]}`}>{row.tier_label}</span></td>
                              <td className="strength-cell">
                                <span className="meter small"><span style={{ width: `${Math.round(row.strength * 100)}%` }} /></span>
                                {row.strength.toFixed(2)}
                              </td>
                              <td title={ieeeText(stripRoleTag(row.top_supports?.[0]?.content || ''))}>
                                {row.top_supports?.[0]
                                  ? <CitedText text={clipCited(stripRoleTag(row.top_supports[0].content), 140)} refIds={refIds} /> : '—'}
                              </td>
                              <td title={ieeeText(stripRoleTag(row.top_attacks?.[0]?.content || ''))}>
                                {row.top_attacks?.[0]
                                  ? <CitedText text={clipCited(stripRoleTag(row.top_attacks[0].content), 140)} refIds={refIds} /> : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {setAside.length > 0 && (
                      <p className="set-aside-note">
                        <strong>Set aside after your review:</strong> {ieeeText(setAside.map(row => row.option).join('; '))}. With your
                        changes the weighed arguments no longer support {setAside.length === 1 ? 'it' : 'them'} for this patient, so {setAside.length === 1 ? 'it is' : 'they are'} not
                        part of this plan. Restore or add arguments on the argument board to bring {setAside.length === 1 ? 'it' : 'them'} back.
                      </p>
                    )}
                  </div>
                )}
              </section>

              {sections.map((section, index) => (
                <section key={section.id} data-section-id={section.id}
                  className={`plan-section ${changed.has(section.id) ? 'is-changed' : ''} ${collapsed.has(section.id) ? 'is-collapsed' : ''}`}>
                  {sectionHeader(section.id, index + 2, section.title,
                    changed.has(section.id) ? <span className="badge badge-updated">Updated in v{plan.version}</span> : null)}
                  {!collapsed.has(section.id) && (
                    <div className="markdown-content plan-markdown" data-anchor-root={section.id}>
                      <Markdown remarkPlugins={[remarkGfm]}>{citationMarkdown(section.content, refIds)}</Markdown>
                    </div>
                  )}
                </section>
              ))}

              {slots.length > 0 && (
                <section className="plan-section">
                  <header className="plan-section-header static">
                    <h2><span className="section-number">{sections.length + 2}</span>Provider Availability</h2>
                  </header>
                  <div className="table-scroll">
                    <table className="decision-table">
                      <thead><tr><th>Provider</th><th>Next available</th></tr></thead>
                      <tbody>
                        {slots.map(([provider, list]) => (
                          <tr key={provider}><td>{provider}</td><td>{list.slice(0, 2).map(slot => slot.time_slot).join(', ')}</td></tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}

              {plan.reference_list?.length > 0 && (
                <section className="plan-section references">
                  <header className="plan-section-header static"><h2>References</h2></header>
                  <ol className="reference-list">
                    {plan.reference_list.map(ref => <ReferenceItem key={ref.id} reference={ref} />)}
                  </ol>
                </section>
              )}

              {plan.memory_used?.length > 0 && (
                <div className="memory-used-note">
                  <strong>Learned guidance applied.</strong> {plan.memory_used.length} lesson{plan.memory_used.length === 1 ? '' : 's'} from
                  earlier clinician reviews informed this plan as guidance (not evidence):
                  <ul>{plan.memory_used.map(m => <li key={m.memory_id}>{m.text ? clip(m.text, 160) : m.memory_id}</li>)}</ul>
                </div>
              )}

              <footer className="plan-footer">
                {plan.provenance?.arguments_considered ?? 0} arguments weighed · {plan.provenance?.clinician_changes ?? 0} clinician
                contestations applied. This plan was drafted by an AI decision-support system and must be reviewed by a qualified
                clinician; it does not replace professional judgment.
              </footer>
            </article>

            <div className="annotation-badges">
              {showNotes && visibleNotes.map(note => {
                const rects = anchors[note.localId]?.rects || []
                const last = rects[rects.length - 1]
                if (!last || note.draft) return null
                return (
                  <button key={note.localId} type="button" className={`note-badge ${activeId === note.localId ? 'is-active' : ''}`}
                    style={{ top: last.top - 9, left: last.left + last.width - 4 }}
                    title={note.text} onClick={() => focusFromBadge(note.localId)}
                    onMouseEnter={() => setActiveId(note.localId)} onMouseLeave={() => setActiveId(null)}>
                    {numbers[note.localId]}
                  </button>
                )
              })}
            </div>
          </div>

          {railShown && (
            <aside className="notes-rail" style={{ minHeight: railHeight }} aria-label="Feedback notes">
              {visibleNotes.filter(note => anchors[note.localId]).map(note => renderCard(note, { top: positions[note.localId] }))}
            </aside>
          )}

          {!railMode && editingNote && anchors[editingNote.localId] && (
            <div className="note-popover" style={{ top: anchors[editingNote.localId].bottom + 10 }}>
              {renderCard(editingNote)}
            </div>
          )}

          {selection && (
            <button type="button" className="selection-chip" style={{ top: selection.top, left: selection.left }}
              onMouseDown={e => e.preventDefault()} onClick={() => noteFromSelection()}>
              <NotePlus size={15} /> Add feedback
            </button>
          )}
        </div>
      </div>

      {isLatest && (
        <div className="feedback-bar">
          <div className="feedback-bar-row">
            <div className="feedback-bar-info">
              <button type="button" className={`chip ${savedNotes.length ? 'chip-primary' : ''}`} onClick={() => setListOpen(o => !o)}
                aria-expanded={listOpen} disabled={!savedNotes.length}>
                <Note size={14} /> {savedNotes.length} note{savedNotes.length === 1 ? '' : 's'}
                {savedNotes.length > 0 && <ChevronDown size={13} className={`chip-chevron ${listOpen ? 'open' : ''}`} />}
              </button>
              {pendingChanges > 0 && (
                <span className="chip chip-lavender">{pendingChanges} argument change{pendingChanges === 1 ? '' : 's'}</span>
              )}
              {totalPending === 0 && <span className="feedback-bar-hint">Select text in the plan to leave a note, then regenerate.</span>}
            </div>
            <div className="feedback-bar-actions">
              <button type="button" className="btn secondary" onClick={addFeedback}>
                <NotePlus size={16} /> Add feedback
              </button>
              <button type="button" className="btn primary" disabled={!canRegenerate} onClick={onRegenerate}
                title={canRegenerate ? 'Re-verify the arguments with your notes and write a new version' : 'Add a note or contest an argument first'}>
                <Refresh size={16} /> Regenerate care plan{totalPending > 0 && <span className="btn-count">{totalPending}</span>}
              </button>
            </div>
          </div>
          {listOpen && savedNotes.length > 0 && (
            <ol className="feedback-list">
              {savedNotes.map(note => (
                <li key={note.localId} className={activeId === note.localId ? 'is-active' : ''}>
                  <span className="note-number">{numbers[note.localId]}</span>
                  <button type="button" className="feedback-list-body" onClick={() => focusNote(note.localId)}>
                    <span className="note-label">{noteLabel(note)}</span>
                    {note.quote && <span className="feedback-list-quote">“{clip(note.quote, 70)}”</span>}
                    <span className="feedback-list-text">{note.text}</span>
                  </button>
                  <button type="button" className="icon-btn xs" title="Edit note" onClick={() => { editNote(note.localId); focusNote(note.localId) }}><Edit size={13} /></button>
                  <button type="button" className="icon-btn xs" title="Delete note" onClick={() => deleteNote(note.localId)}><X size={13} /></button>
                </li>
              ))}
              <li className="feedback-list-footer">
                <button type="button" className="link-btn danger" onClick={onClearNotes}>Discard all notes</button>
              </li>
            </ol>
          )}
        </div>
      )}
    </div>
  )
}
