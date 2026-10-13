import { useRef, useState } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export const TIER_CLASS = {
  recommended: 'tier-recommended',
  conditional: 'tier-conditional',
  uncertain: 'tier-uncertain',
  deferred: 'tier-deferred',
  not_recommended: 'tier-not-recommended'
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function clip(text, max) {
  const clean = (text || '').replace(/\s+/g, ' ').trim()
  return clean.length > max ? clean.slice(0, max - 1) + '…' : clean
}

function stripRoleTag(content) {
  return content?.startsWith('[') && content.indexOf(']') > 0 ? content.slice(content.indexOf(']') + 1).trim() : content
}

// [REF-3] -> a link to the reference list entry.
function withCitationLinks(markdown) {
  return (markdown || '').replace(/\[REF-(\d+)\]/g, '[[REF-$1]](#ref-$1)')
}

function CommentIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
  )
}

function RevisionNote({ plan, titles }) {
  return (
    <div className="revision-note">
      <div className="revision-note-title">
        How version {plan.version} was produced: <strong>{plan.strategy_label}</strong>
        {plan.decided_by === 'llm' && <span className="revision-note-by"> (reasoned by the planner)</span>}
      </div>
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
        <details>
          <summary>Changes to the argument graph</summary>
          <ul className="revision-ops">
            {(plan.feedback_ops?.length ? plan.feedback_ops : plan.contested_ops).map((line, i) => <li key={i}>{line.replace(/^- /, '')}</li>)}
          </ul>
        </details>
      )}
    </div>
  )
}

export default function CarePlanDocument({
  plan, versions, isLatest, onSelectVersion, pendingFeedback, pendingChanges, onAddFeedback,
  onRemoveFeedback, onRegenerate, onDownloadPdf, onApprove, busy, finishing
}) {
  const scrollRef = useRef(null)
  const [selection, setSelection] = useState(null) // { quote, sectionId, x, y }
  const [composer, setComposer] = useState(null) // { sectionId, quote }
  const [draft, setDraft] = useState('')
  const [downloading, setDownloading] = useState(false)

  const titles = Object.fromEntries((plan.sections || []).map(section => [section.id, section.title]))
  const changed = new Set(plan.version > 1 ? plan.changed_sections || [] : [])
  const feedbackBySection = {}
  pendingFeedback.forEach(item => {
    if (item.section_id) feedbackBySection[item.section_id] = (feedbackBySection[item.section_id] || 0) + 1
  })
  const slots = Object.entries(plan.scheduling?.slots || {}).filter(([, list]) => list?.length)
  const canRegenerate = !busy && (pendingFeedback.length > 0 || pendingChanges > 0)

  const handleMouseUp = () => {
    if (!isLatest) return
    const sel = window.getSelection()
    const text = sel?.toString().trim()
    if (!text || text.length < 3 || !sel.rangeCount) {
      setSelection(null)
      return
    }
    const range = sel.getRangeAt(0)
    const node = range.commonAncestorContainer
    const element = node.nodeType === 1 ? node : node.parentElement
    const sectionEl = element?.closest('[data-section-id]')
    if (!sectionEl || !scrollRef.current?.contains(sectionEl)) {
      setSelection(null)
      return
    }
    const rect = range.getBoundingClientRect()
    const host = scrollRef.current.getBoundingClientRect()
    setSelection({
      quote: text.slice(0, 400),
      sectionId: sectionEl.dataset.sectionId,
      x: Math.max(60, rect.left - host.left + rect.width / 2),
      y: rect.top - host.top + scrollRef.current.scrollTop - 38
    })
  }

  const openComposer = (sectionId, quote = null) => {
    setComposer({ sectionId, quote })
    setSelection(null)
    window.getSelection()?.removeAllRanges()
  }

  const submitDraft = () => {
    if (!draft.trim()) return
    onAddFeedback({ text: draft.trim(), section_id: composer?.sectionId || null, quote: composer?.quote || null })
    setDraft('')
    setComposer(null)
  }

  const download = async () => {
    setDownloading(true)
    try {
      await onDownloadPdf(plan.version)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className="plan-view">
      <div className="plan-toolbar">
        <div className="version-pills">
          {versions.map(v => (
            <button key={v.version} className={`version-pill ${v.version === plan.version ? 'active' : ''}`} onClick={() => onSelectVersion(v.version)}
              title={`${v.strategy_label} · ${formatDate(v.created_at)}`}>
              v{v.version}{v.status === 'approved' ? ' ✓' : ''}
            </button>
          ))}
        </div>
        <div className="plan-toolbar-actions">
          {plan.status === 'approved'
            ? <span className="approved-badge">Approved {formatDate(plan.approved_at)}</span>
            : <button className="secondary" disabled={busy} onClick={() => onApprove(plan.version)}>Approve Plan</button>}
          <button className="secondary" onClick={() => window.print()}>Print</button>
          <button disabled={downloading} onClick={download}>{downloading ? 'Preparing PDF…' : 'Download PDF'}</button>
        </div>
      </div>

      {!isLatest && (
        <div className="older-version-note">
          You are viewing version {plan.version}. Feedback applies to the latest version.
          <button className="link-button" onClick={() => onSelectVersion(versions[versions.length - 1].version)}>Go to latest</button>
        </div>
      )}
      {finishing && <div className="finishing-note">Finishing up: checking provider availability and learning from your review…</div>}

      <div className="plan-scroll" ref={scrollRef} onMouseUp={handleMouseUp}>
        <article className="plan-document" id="care-plan-document">
          <header className="plan-band">
            <div>
              <h1>Aging-in-Place Care Plan</h1>
              <div className="plan-band-sub">Version {plan.version} · {plan.status === 'approved' ? 'Approved' : 'Draft for clinical review'}</div>
            </div>
            <div className="plan-band-right">Generated {formatDate(plan.created_at)}</div>
          </header>

          <dl className="plan-meta">
            <dt>Patient</dt><dd>{plan.patient_info}</dd>
            <dt>Severity</dt><dd>{plan.severity || 'Not assessed'}</dd>
            <dt>Care team</dt><dd>{(plan.care_team || []).map(m => m.name || m.role).join(', ') || 'Not assigned'}</dd>
            <dt>Decision confidence</dt>
            <dd>
              <span className="confidence-bar"><span style={{ width: `${Math.round(100 * (plan.decision_confidence || 0))}%` }} /></span>
              {Math.round(100 * (plan.decision_confidence || 0))}%
              <span className="plan-meta-hint"> how decisively the weighed arguments separate the options</span>
            </dd>
          </dl>

          {plan.version > 1 && <RevisionNote plan={plan} titles={titles} />}

          <section className="plan-section">
            <div className="plan-section-header"><h2>1. Decision Summary</h2></div>
            <p className="plan-note">
              Each care option was weighed by a quantitative bipolar argumentation framework: supporting and challenging
              arguments from the care team, verified against the medical knowledge base and contested by the reviewing clinician.
            </p>
            <table className="decision-table">
              <thead><tr><th>Care option</th><th>Assessment</th><th>Strength</th><th>Leading support</th><th>Leading concern</th></tr></thead>
              <tbody>
                {[...(plan.options || [])].sort((a, b) => a.rank - b.rank).map(row => (
                  <tr key={row.option_id}>
                    <td>{row.option}</td>
                    <td><span className={`tier-pill ${TIER_CLASS[row.tier]}`}>{row.tier_label}</span></td>
                    <td>
                      <span className="strength-bar"><span style={{ width: `${Math.round(row.strength * 100)}%` }} /></span>
                      {row.strength.toFixed(2)}
                    </td>
                    <td>{row.top_supports?.[0] ? clip(stripRoleTag(row.top_supports[0].content), 140) : '—'}</td>
                    <td>{row.top_attacks?.[0] ? clip(stripRoleTag(row.top_attacks[0].content), 140) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {(plan.sections || []).map((section, index) => (
            <section key={section.id} data-section-id={section.id} className={`plan-section ${changed.has(section.id) ? 'changed' : ''}`}>
              <div className="plan-section-header">
                <h2>{index + 2}. {section.title}</h2>
                {changed.has(section.id) && <span className="updated-badge">Updated in v{plan.version}</span>}
                {feedbackBySection[section.id] && <span className="feedback-count">{feedbackBySection[section.id]} pending feedback</span>}
                {isLatest && (
                  <button className="comment-button" onClick={() => openComposer(section.id)} title="Leave feedback on this section">
                    <CommentIcon /> Feedback
                  </button>
                )}
              </div>
              <div className="markdown-content plan-markdown">
                <Markdown remarkPlugins={[remarkGfm]}>{withCitationLinks(section.content)}</Markdown>
              </div>
            </section>
          ))}

          {slots.length > 0 && (
            <section className="plan-section">
              <div className="plan-section-header"><h2>{(plan.sections || []).length + 2}. Provider Availability</h2></div>
              <table className="decision-table">
                <thead><tr><th>Provider</th><th>Next available</th></tr></thead>
                <tbody>
                  {slots.map(([provider, list]) => (
                    <tr key={provider}><td>{provider}</td><td>{list.slice(0, 2).map(slot => slot.time_slot).join(', ')}</td></tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {plan.reference_list?.length > 0 && (
            <section className="plan-section references">
              <div className="plan-section-header"><h2>References</h2></div>
              <ol className="reference-list">
                {plan.reference_list.map(ref => (
                  <li key={ref.id} id={`ref-${ref.id}`}>
                    <span className="ref-id">[REF-{ref.id}]</span> {ref.title} · {ref.source} · relevance {ref.relevance.toFixed(2)}
                    <div className="ref-preview">{clip(ref.preview, 260)}</div>
                  </li>
                ))}
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

        {selection && (
          <button className="selection-feedback-button" style={{ left: selection.x, top: selection.y }}
            onMouseDown={e => e.preventDefault()} onClick={() => openComposer(selection.sectionId, selection.quote)}>
            <CommentIcon /> Add feedback
          </button>
        )}
      </div>

      {isLatest && (
        <div className="feedback-tray">
          {pendingFeedback.length > 0 && (
            <ul className="feedback-items">
              {pendingFeedback.map(item => (
                <li key={item.localId}>
                  {item.section_id && <span className="feedback-anchor">{titles[item.section_id] || item.section_id}</span>}
                  {item.quote && <span className="feedback-quote">“{clip(item.quote, 80)}”</span>}
                  <span className="feedback-text">{item.text}</span>
                  <button className="link-button" onClick={() => onRemoveFeedback(item.localId)} title="Remove">×</button>
                </li>
              ))}
            </ul>
          )}
          {composer && (
            <div className="composer-anchor">
              Feedback on <strong>{composer.sectionId ? titles[composer.sectionId] : 'the whole plan'}</strong>
              {composer.quote && <span className="feedback-quote"> “{clip(composer.quote, 120)}”</span>}
              <button className="link-button" onClick={() => setComposer(null)}>Clear</button>
            </div>
          )}
          <div className="feedback-input-row">
            <textarea
              className="feedback-input"
              placeholder={composer ? 'What should change here?' : 'Suggest a change to the care plan, or select text in the plan to comment on it…'}
              value={draft}
              onChange={e => setDraft(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitDraft() } }}
            />
            <div className="feedback-actions">
              <button className="secondary" disabled={!draft.trim()} onClick={submitDraft}>Add Feedback</button>
              <button disabled={!canRegenerate} onClick={onRegenerate}
                title={canRegenerate ? '' : 'Add feedback or contest an argument first'}>
                Regenerate Care Plan
              </button>
            </div>
          </div>
          {pendingChanges > 0 && (
            <div className="tray-hint">{pendingChanges} argument change{pendingChanges === 1 ? '' : 's'} from the argument table will also be applied.</div>
          )}
        </div>
      )}
    </div>
  )
}
