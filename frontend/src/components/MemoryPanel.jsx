import { useEffect, useState } from 'react'
import { getJSON, postJSON } from '../api'

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
  const reviewable = record.status === 'under_review'
  return (
    <div className={`memory-record ${used ? 'used' : ''}`}>
      <div className="memory-record-header">
        <span className={`memory-type ${record.memory_type}`}>{TYPE_LABELS[record.memory_type] || record.memory_type}</span>
        <span className="memory-stage">{STAGE_LABELS[record.stage] || record.stage}</span>
        {used && <span className="memory-used">Used in this case</span>}
        <span className="memory-id">{record.memory_id}</span>
      </div>
      <div className="memory-text">{record.text}</div>
      {record.recommended_action && !record.text?.includes(record.recommended_action) && (
        <div className="memory-action">Action: {record.recommended_action}</div>
      )}
      <div className="memory-stats">
        <span className="confidence-bar small"><span style={{ width: `${Math.round(100 * record.confidence)}%` }} /></span>
        <span>confidence {record.confidence.toFixed(2)}</span>
        {record.support != null && <span>{record.support} case{record.support === 1 ? '' : 's'}</span>}
        {record.conflicts > 0 && <span className="memory-conflicts">{record.conflicts} conflict{record.conflicts === 1 ? '' : 's'}</span>}
        {record.usage && <span>used {record.usage.used}× ({record.usage.successful} approved, {record.usage.contested} contested)</span>}
        {(record.review_reason || record.reason) && <span className="memory-reason">{(record.review_reason || record.reason).replaceAll('_', ' ')}</span>}
      </div>
      <div className="memory-actions">
        {(reviewable || record.verification_status === 'under_review') && (
          <button className="secondary small" disabled={busy} onClick={() => onReview(record.memory_id, 'approve')}>Approve</button>
        )}
        {record.status === 'active' && (
          <button className="secondary small" disabled={busy} onClick={() => onReview(record.memory_id, 'hold')}>Hold for review</button>
        )}
        {record.status !== 'deprecated' && (
          <button className="secondary small danger-text" disabled={busy} onClick={() => onReview(record.memory_id, 'reject')}>Reject</button>
        )}
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
    return <div className="memory-panel"><p className="text-muted">Self-evolving memory is disabled (MEMORY_ENABLED=false).</p></div>
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
      <div className="board-header">
        <div>
          <h3 style={{ margin: 0 }}>Learned Memory</h3>
          <p className="text-muted" style={{ margin: '0.2rem 0 0' }}>
            Lessons consolidated from clinicians' contestations. They guide future care plans and are never treated as evidence.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="secondary" disabled={busy} onClick={load}>Refresh</button>
          <button disabled={busy} onClick={consolidate}>{busy ? 'Working…' : 'Consolidate Now'}</button>
        </div>
      </div>

      {notice && <div className="memory-notice">{notice}</div>}
      {error && <div className="memory-error">{error}</div>}

      <div className="option-tabs">
        {FILTERS.map(f => (
          <button key={f.key} className={`option-tab ${filter === f.key ? 'active' : ''}`} onClick={() => setFilter(f.key)}>
            <span>{f.label}</span><span className="option-count">{lists[f.key].length}</span>
          </button>
        ))}
      </div>

      <div className="memory-list">
        {!data && !error && <p className="text-muted">Loading memory…</p>}
        {data && shown.length === 0 && (
          <p className="text-muted" style={{ textAlign: 'center', paddingTop: '1.5rem' }}>
            {filter === 'active'
              ? 'No lessons yet. They are learned when a clinician contests a care plan and consolidated across cases.'
              : 'Nothing here.'}
          </p>
        )}
        {shown.map(record => (
          <MemoryRecord key={record.memory_id} record={record} used={usedIds.includes(record.memory_id)} onReview={review} busy={busy} />
        ))}
      </div>
    </div>
  )
}
