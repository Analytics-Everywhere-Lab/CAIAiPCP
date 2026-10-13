import { useEffect, useState } from 'react'
import { getJSON, postJSON } from '../api'
import { Brain, ChevronDown, Refresh, Sparkle } from './Icons'

const TYPE_LABELS = { semantic_rule: 'Rule', failure: 'Past error', episodic: 'Past case' }
const STAGE_LABELS = {
  option_generation: 'Care options',
  argument_generation: 'Arguments',
  argument_validation: 'Verification',
  plan_writing: 'Plan writing',
  general: 'General'
}
const FILTERS = [
  { key: 'active', label: 'Active' },
  { key: 'under_review', label: 'Under review' },
  { key: 'pending', label: 'Staged' },
  { key: 'deprecated', label: 'Deprecated' }
]

function MemoryRecord({ record, used, onReview, busy }) {
  const [open, setOpen] = useState(false)
  const reviewable = record.status === 'under_review' || record.verification_status === 'under_review'
  return (
    <div className={`memory-record ${used ? 'is-used' : ''}`}>
      <div className="memory-record-top">
        <span className={`memory-type ${record.memory_type}`}>{TYPE_LABELS[record.memory_type] || record.memory_type}</span>
        <span className="memory-stage">{STAGE_LABELS[record.stage] || record.stage}</span>
        {used && <span className="badge badge-memory">Used in this case</span>}
        <span className="memory-confidence" title="Confidence">
          <span className="meter small"><span style={{ width: `${Math.round(100 * record.confidence)}%` }} /></span>
          {record.confidence.toFixed(2)}
        </span>
      </div>
      <div className="memory-text">{record.text}</div>
      <button type="button" className="link-btn memory-more" onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <ChevronDown size={13} className={`chip-chevron ${open ? 'open' : ''}`} /> {open ? 'Hide details' : 'Details'}
      </button>
      {open && (
        <div className="memory-details">
          {record.recommended_action && !record.text?.includes(record.recommended_action) && (
            <div className="memory-action">Action: {record.recommended_action}</div>
          )}
          <div className="memory-stats">
            <span className="memory-id">{record.memory_id}</span>
            {record.support != null && <span>{record.support} case{record.support === 1 ? '' : 's'}</span>}
            {record.conflicts > 0 && <span className="memory-conflicts">{record.conflicts} conflict{record.conflicts === 1 ? '' : 's'}</span>}
            {record.usage && <span>used {record.usage.used}× ({record.usage.successful} approved, {record.usage.contested} contested)</span>}
            {(record.review_reason || record.reason) && <span className="memory-reason">{(record.review_reason || record.reason).replaceAll('_', ' ')}</span>}
          </div>
        </div>
      )}
      <div className="memory-actions">
        {reviewable && <button type="button" className="btn soft xs" disabled={busy} onClick={() => onReview(record.memory_id, 'approve')}>Approve</button>}
        {record.status === 'active' && <button type="button" className="btn ghost xs" disabled={busy} onClick={() => onReview(record.memory_id, 'hold')}>Hold for review</button>}
        {record.status !== 'deprecated' && <button type="button" className="btn ghost xs danger-text" disabled={busy} onClick={() => onReview(record.memory_id, 'reject')}>Reject</button>}
      </div>
    </div>
  )
}

export default function MemoryPanel({ usedIds = [], refreshKey = 0 }) {
  const [data, setData] = useState(null)
  const [filter, setFilter] = useState('active')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setData(await getJSON('/api/memory'))
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [refreshKey])

  const consolidate = async () => {
    setBusy(true)
    try {
      const result = await postJSON('/api/memory/consolidate', {})
      setData(result)
      const r = result.result
      setNotice(`Consolidation: ${r.promoted} promoted, ${r.merged} merged, ${r.generalized} generalized, ${r.conflicted} conflicts, ${r.deprecated} deprecated.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const review = async (memoryId, decision) => {
    setBusy(true)
    try {
      setData(await postJSON(`/api/memory/${memoryId}/review`, { decision }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (data && data.enabled === false) {
    return <div className="memory-panel"><p className="empty-note">Self-evolving memory is disabled (MEMORY_ENABLED=false).</p></div>
  }

  const longTerm = data?.long_term || []
  const shortTerm = data?.short_term || []
  const lists = {
    active: longTerm.filter(r => r.status === 'active'),
    under_review: [...longTerm.filter(r => r.status === 'under_review'), ...shortTerm.filter(r => r.status === 'under_review')],
    pending: shortTerm.filter(r => r.status === 'staged'),
    deprecated: longTerm.filter(r => r.status === 'deprecated')
  }
  const shown = lists[filter] || []

  return (
    <div className="memory-panel">
      <div className="board-toolbar">
        <p className="board-intro">
          Lessons consolidated from clinicians' contestations across cases. They guide future plans and are never treated as evidence.
        </p>
        <div className="board-actions">
          <button type="button" className="btn ghost sm" disabled={busy} onClick={load}><Refresh size={14} /> Refresh</button>
          <button type="button" className="btn primary sm" disabled={busy} onClick={consolidate}><Sparkle size={14} /> {busy ? 'Working…' : 'Consolidate now'}</button>
        </div>
      </div>

      {notice && <div className="inline-banner info">{notice}</div>}
      {error && <div className="inline-banner warn">{error}</div>}

      <div className="option-tabs" role="tablist" aria-label="Memory status">
        {FILTERS.map(f => (
          <button key={f.key} type="button" role="tab" aria-selected={filter === f.key}
            className={`option-tab ${filter === f.key ? 'active' : ''}`} onClick={() => setFilter(f.key)}>
            <span className="option-tab-label">{f.label}</span><span className="count-pill">{lists[f.key].length}</span>
          </button>
        ))}
      </div>

      <div className="memory-list">
        {!data && !error && <p className="empty-note">Loading memory…</p>}
        {data && shown.length === 0 && (
          <div className="empty-state small">
            <span className="empty-icon"><Brain size={22} /></span>
            <p>
              {filter === 'active'
                ? 'No lessons yet. They are learned when a clinician contests a care plan, and consolidated across cases.'
                : 'Nothing here.'}
            </p>
          </div>
        )}
        {shown.map(record => (
          <MemoryRecord key={record.memory_id} record={record} used={usedIds.includes(record.memory_id)} onReview={review} busy={busy} />
        ))}
      </div>
    </div>
  )
}
