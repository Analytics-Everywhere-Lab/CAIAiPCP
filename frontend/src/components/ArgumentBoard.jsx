import { useEffect, useState } from 'react'
import { TIER_CLASS } from './CarePlanDocument'
import { ChevronDown, Edit, Plus, Refresh, Trash, X, CheckCircle } from './Icons'

const SOURCE_BADGES = {
  human: { label: 'Added by clinician', className: 'badge-human' },
  feedback: { label: 'From plan feedback', className: 'badge-feedback' },
  memory: { label: 'Learned from past reviews', className: 'badge-memory' }
}

function stripRoleTag(content) {
  return content?.startsWith('[') && content.indexOf(']') > 0 ? content.slice(content.indexOf(']') + 1).trim() : content
}

function ArgumentCard({ arg, qbafRow, editable, selected, onSelect, planExists }) {
  const source = SOURCE_BADGES[arg.source]
  const pendingReevaluation = planExists && !qbafRow
  return (
    <button type="button" className={`arg-card ${arg.type} ${selected ? 'is-selected' : ''}`} disabled={!editable}
      onClick={() => onSelect(arg)} title={arg.validation_note ? `Verifier: ${arg.validation_note}` : 'Edit or remove this argument'}>
      <div className="arg-card-top">
        <span className={`stance-pill ${arg.type}`}>{arg.type === 'support' ? 'Supports' : 'Challenges'}</span>
        <span className="arg-id">{arg.arg_id}</span>
        {source && <span className={`badge ${source.className}`}>{source.label}{arg.feedback_id ? ` · ${arg.feedback_id}` : ''}</span>}
        {arg.status === 'edited' && <span className="badge badge-edited">Edited</span>}
        {editable && <Edit size={13} className="arg-edit-hint" />}
      </div>
      {arg.target_arg_id && <div className="arg-target">Responds to {arg.target_arg_id}</div>}
      <div className="arg-text">{stripRoleTag(arg.content)}</div>
      {arg.status === 'edited' && arg.original_content && (
        <div className="arg-original">Was: {stripRoleTag(arg.original_content)}</div>
      )}
      {(arg.score != null || qbafRow) && (
        <div className="arg-metrics">
          {arg.score != null && <span>Validity <strong>{arg.score.toFixed(2)}</strong></span>}
          {qbafRow && <span>Strength <strong>{qbafRow.strength.toFixed(2)}</strong></span>}
          {qbafRow && (
            <span className={qbafRow.contribution >= 0 ? 'impact-up' : 'impact-down'}>
              Impact {qbafRow.contribution >= 0 ? '+' : ''}{qbafRow.contribution.toFixed(2)}
            </span>
          )}
        </div>
      )}
      {pendingReevaluation && <div className="arg-pending">Re-evaluated when you regenerate</div>}
      {arg.flags?.includes('verifier_disagrees') && (
        <div className="arg-warning">The verifier found weak support; it still counts with clinician weight.</div>
      )}
    </button>
  )
}

export default function ArgumentBoard({
  options, args, qbafOptions, qbafArgs, phase, loading, pendingChanges, pendingFeedbackCount,
  onAction, onAccept, onRegenerate
}) {
  const [activeOption, setActiveOption] = useState(null)
  const [selectedArg, setSelectedArg] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [removeReason, setRemoveReason] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [newArgContent, setNewArgContent] = useState('')
  const [newArgType, setNewArgType] = useState('support')
  const [newArgRole, setNewArgRole] = useState('')
  const [showRemoved, setShowRemoved] = useState(false)
  const [collapsedRoles, setCollapsedRoles] = useState(() => new Set())

  const editable = !loading && (phase === 'review' || phase === 'plan')
  const planExists = phase === 'plan'

  useEffect(() => {
    if (options.length > 0) setActiveOption(prev => (prev && options.includes(prev) ? prev : options[0]))
  }, [options])

  const roles = Array.from(new Set(args.filter(a => a.source === 'agent' || a.source === 'human').map(a => a.role)))
  if (roles.length === 0) roles.push('Clinician')
  useEffect(() => {
    if (!newArgRole && roles.length) setNewArgRole(roles[0])
  }, [roles.join('|')]) // eslint-disable-line react-hooks/exhaustive-deps

  const optionArgs = args.filter(a => a.option === activeOption)
  const active = optionArgs.filter(a => a.status !== 'rejected')
  const removed = optionArgs.filter(a => a.status === 'rejected')
  const columns = {}
  active.forEach(arg => {
    const column = arg.role || 'General'
    if (!columns[column]) columns[column] = []
    columns[column].push(arg)
  })
  const qbafByOption = Object.fromEntries((qbafOptions || []).map(row => [row.option, row]))
  const activeRow = qbafByOption[activeOption]

  const select = (arg) => {
    setSelectedArg(arg)
    setEditContent(arg.content)
    setRemoveReason('')
    setShowAdd(false)
  }
  const act = async (action, payload) => {
    await onAction(action, payload)
    setSelectedArg(null)
  }
  const addArgument = async () => {
    if (!newArgContent.trim()) return
    await onAction('add', { new_content: newArgContent, new_type: newArgType, new_option: activeOption, new_role: newArgRole })
    setNewArgContent('')
    setShowAdd(false)
  }
  const toggleRole = (role) => setCollapsedRoles(prev => {
    const next = new Set(prev)
    if (next.has(role)) next.delete(role)
    else next.add(role)
    return next
  })

  const pendingTotal = pendingChanges + pendingFeedbackCount

  return (
    <div className="board">
      <div className="board-toolbar">
        <p className="board-intro">
          {phase === 'review'
            ? 'Each care option was argued by the care team. Click an argument to edit or remove it, or add your own; then accept to write the plan.'
            : 'Contest the arguments behind the plan: edit, remove or add one, then regenerate the plan.'}
        </p>
        <div className="board-actions">
          <button type="button" className="btn secondary sm" disabled={!editable} onClick={() => { setShowAdd(s => !s); setSelectedArg(null) }}>
            <Plus size={15} /> Add argument
          </button>
          {phase === 'review' && (
            <button type="button" className="btn primary sm" disabled={loading} onClick={onAccept}>
              <CheckCircle size={15} /> Accept all &amp; write plan
            </button>
          )}
          {planExists && (
            <button type="button" className="btn primary sm" disabled={loading || pendingTotal === 0} onClick={onRegenerate}
              title={pendingTotal ? '' : 'Contest an argument or add plan feedback first'}>
              <Refresh size={15} /> Regenerate care plan{pendingTotal > 0 && <span className="btn-count">{pendingTotal}</span>}
            </button>
          )}
        </div>
      </div>

      {planExists && pendingTotal > 0 && (
        <div className="inline-banner lavender">
          {pendingChanges > 0 && <span>{pendingChanges} argument change{pendingChanges === 1 ? '' : 's'}</span>}
          {pendingChanges > 0 && pendingFeedbackCount > 0 && <span> and </span>}
          {pendingFeedbackCount > 0 && <span>{pendingFeedbackCount} plan note{pendingFeedbackCount === 1 ? '' : 's'}</span>}
          <span> will be applied when you regenerate the care plan.</span>
        </div>
      )}

      <div className="option-tabs" role="tablist" aria-label="Care options">
        {options.map((option, idx) => {
          const isActive = activeOption === option
          const count = args.filter(a => a.option === option && a.status !== 'rejected').length
          const row = qbafByOption[option]
          return (
            <button key={idx} type="button" role="tab" aria-selected={isActive} className={`option-tab ${isActive ? 'active' : ''}`}
              onClick={() => { setActiveOption(option); setSelectedArg(null) }} title={option}>
              {row && <span className={`tier-dot ${TIER_CLASS[row.tier]}`} />}
              <span className="option-tab-label">Option {idx + 1}</span>
              <span className="count-pill">{count}</span>
            </button>
          )
        })}
      </div>

      {activeOption && (
        <div className="option-summary">
          <div className="option-summary-text">{activeOption}</div>
          {activeRow && (
            <span className={`tier-pill ${TIER_CLASS[activeRow.tier]}`}>{activeRow.tier_label} · {activeRow.strength.toFixed(2)}</span>
          )}
        </div>
      )}

      <div className={`board-canvas ${selectedArg || showAdd ? 'has-sheet' : ''}`}>
        {(selectedArg || showAdd) && (
          <aside className="sheet" role="dialog" aria-label={selectedArg ? 'Edit argument' : 'Add argument'}>
            <div className="sheet-header">
              <h4>{selectedArg ? `Edit argument ${selectedArg.arg_id}` : 'Add an argument'}</h4>
              <button type="button" className="icon-btn" onClick={() => { setSelectedArg(null); setShowAdd(false) }} aria-label="Close"><X /></button>
            </div>
            {selectedArg ? (
              <>
                <div className="sheet-meta">
                  <span className={`stance-pill ${selectedArg.type}`}>{selectedArg.type === 'support' ? 'Supports' : 'Challenges'}</span>
                  <span>{selectedArg.role}</span>
                </div>
                {selectedArg.validation_note && <p className="sheet-note">Verifier: {selectedArg.validation_note}</p>}
                <textarea className="input" rows={5} value={editContent} onChange={e => setEditContent(e.target.value)} />
                <input className="input" placeholder="Why remove it? (optional, helps the system learn)" value={removeReason}
                  onChange={e => setRemoveReason(e.target.value)} />
                <div className="sheet-actions">
                  <button type="button" className="btn danger-soft sm" onClick={() => act('remove', { arg_id: selectedArg.arg_id, reason: removeReason || undefined })}>
                    <Trash size={14} /> Remove
                  </button>
                  <button type="button" className="btn primary sm" disabled={!editContent.trim() || editContent === selectedArg.content}
                    onClick={() => act('modify', { arg_id: selectedArg.arg_id, new_content: editContent })}>
                    Save edits
                  </button>
                </div>
              </>
            ) : (
              <>
                <label className="field"><span className="field-label">Care option</span>
                  <select className="input" value={activeOption || ''} onChange={e => setActiveOption(e.target.value)}>
                    {options.map((opt, idx) => <option key={idx} value={opt}>{`Option ${idx + 1}: ${opt}`}</option>)}
                  </select>
                </label>
                <div className="field-grid">
                  <label className="field"><span className="field-label">Stance</span>
                    <select className="input" value={newArgType} onChange={e => setNewArgType(e.target.value)}>
                      <option value="support">Supports the option</option>
                      <option value="attack">Challenges the option</option>
                    </select>
                  </label>
                  <label className="field"><span className="field-label">Role</span>
                    <select className="input" value={newArgRole} onChange={e => setNewArgRole(e.target.value)}>
                      {roles.map((role, idx) => <option key={idx} value={role}>{role}</option>)}
                    </select>
                  </label>
                </div>
                <label className="field"><span className="field-label">Argument</span>
                  <textarea className="input" rows={4} value={newArgContent} onChange={e => setNewArgContent(e.target.value)}
                    placeholder="e.g. Her daughter visits daily and can supervise the home modifications." />
                </label>
                <div className="sheet-actions">
                  <button type="button" className="btn primary sm" disabled={!newArgContent.trim()} onClick={addArgument}>
                    <Plus size={14} /> Add argument
                  </button>
                </div>
              </>
            )}
          </aside>
        )}

        <div className="board-main">
          {Object.keys(columns).length === 0 ? (
            <div className="empty-note">No arguments for this option yet.</div>
          ) : (
            <div className="role-columns">
              {Object.entries(columns).map(([role, roleArgs]) => {
                const isCollapsed = collapsedRoles.has(role)
                return (
                  <div key={role} className={`role-column ${isCollapsed ? 'is-collapsed' : ''}`}>
                    <button type="button" className="role-header" onClick={() => toggleRole(role)} aria-expanded={!isCollapsed}>
                      <span className="role-name">{role}</span>
                      <span className="count-pill">{roleArgs.length}</span>
                      <ChevronDown size={14} className="role-chevron" />
                    </button>
                    {!isCollapsed && roleArgs.map(arg => (
                      <ArgumentCard key={arg.arg_id} arg={arg} qbafRow={qbafArgs?.[arg.arg_id]} editable={editable}
                        selected={selectedArg?.arg_id === arg.arg_id} onSelect={select} planExists={planExists} />
                    ))}
                  </div>
                )
              })}
            </div>
          )}

          {removed.length > 0 && (
            <div className="removed-args">
              <button type="button" className="link-btn" onClick={() => setShowRemoved(!showRemoved)} aria-expanded={showRemoved}>
                <ChevronDown size={13} className={`chip-chevron ${showRemoved ? 'open' : ''}`} />
                {showRemoved ? 'Hide' : 'Show'} removed arguments ({removed.length})
              </button>
              {showRemoved && removed.map(arg => (
                <div key={arg.arg_id} className="removed-arg">
                  <span className="arg-id">{arg.arg_id}</span>
                  <span className="removed-text">{stripRoleTag(arg.content)}</span>
                  {arg.rejection_reason && <span className="removed-reason">({arg.rejection_reason})</span>}
                  <button type="button" className="btn ghost xs" disabled={!editable} onClick={() => onAction('restore', { arg_id: arg.arg_id })}>Restore</button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
