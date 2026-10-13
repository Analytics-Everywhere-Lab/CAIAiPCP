import { useEffect, useState } from 'react'

const SOURCE_BADGES = {
  human: { label: 'Added by clinician', className: 'badge-human' },
  feedback: { label: 'From plan feedback', className: 'badge-feedback' },
  memory: { label: 'Learned from past reviews', className: 'badge-memory' }
}

const TIER_CLASS = {
  recommended: 'tier-recommended',
  conditional: 'tier-conditional',
  uncertain: 'tier-uncertain',
  deferred: 'tier-deferred',
  not_recommended: 'tier-not-recommended'
}

function stripRoleTag(content) {
  return content?.startsWith('[') && content.indexOf(']') > 0 ? content.slice(content.indexOf(']') + 1).trim() : content
}

function ArgumentCard({ arg, qbafRow, editable, onSelect, planExists }) {
  const source = SOURCE_BADGES[arg.source]
  const pendingReevaluation = planExists && !qbafRow
  return (
    <div
      className={`arg-card ${arg.type} ${editable ? 'editable' : ''}`}
      onClick={() => editable && onSelect(arg)}
      title={arg.validation_note ? `Verifier: ${arg.validation_note}` : undefined}
    >
      <div className="arg-card-badges">
        <span className={`stance-pill ${arg.type}`}>{arg.type === 'support' ? 'SUPPORT' : 'ATTACK'}</span>
        <span className="arg-id">{arg.arg_id}</span>
        {source && <span className={`arg-badge ${source.className}`}>{source.label}{arg.feedback_id ? ` · ${arg.feedback_id}` : ''}</span>}
        {arg.status === 'edited' && <span className="arg-badge badge-edited">Edited</span>}
      </div>
      {arg.target_arg_id && <div className="arg-target">Responds to {arg.target_arg_id}</div>}
      <div className="arg-text">{stripRoleTag(arg.content)}</div>
      {arg.status === 'edited' && arg.original_content && (
        <div className="arg-original">Was: {stripRoleTag(arg.original_content)}</div>
      )}
      {(arg.score != null || qbafRow) && (
        <div className="arg-metrics">
          {arg.score != null && <span>Validity {arg.score.toFixed(2)}</span>}
          {qbafRow && <span>Strength {qbafRow.strength.toFixed(2)}</span>}
          {qbafRow && (
            <span className={qbafRow.contribution >= 0 ? 'impact-up' : 'impact-down'}>
              Impact {qbafRow.contribution >= 0 ? '+' : ''}{qbafRow.contribution.toFixed(2)}
            </span>
          )}
        </div>
      )}
      {pendingReevaluation && <div className="arg-pending">Re-evaluated when you regenerate</div>}
      {arg.flags?.includes('verifier_disagrees') && (
        <div className="arg-warning">The verifier found weak support for this argument; it still counts with clinician weight.</div>
      )}
    </div>
  )
}

export default function ArgumentBoard({
  options, args, qbafOptions, qbafArgs, phase, loading, pendingChanges, pendingFeedbackCount,
  onAction, onAccept, onRegenerate
}) {
  const [activeOption, setActiveOption] = useState(null)
  const [selectedArg, setSelectedArg] = useState(null)
  const [editContent, setEditContent] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [newArgContent, setNewArgContent] = useState('')
  const [newArgType, setNewArgType] = useState('support')
  const [newArgRole, setNewArgRole] = useState('')
  const [showRemoved, setShowRemoved] = useState(false)

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

  const select = (arg) => {
    setSelectedArg(arg)
    setEditContent(arg.content)
  }
  const act = async (action, payload) => {
    await onAction(action, payload)
    setSelectedArg(null)
  }
  const addArgument = async () => {
    if (!newArgContent.trim()) return
    await onAction('add', { new_content: newArgContent, new_type: newArgType, new_option: activeOption, new_role: newArgRole })
    setNewArgContent('')
    setShowAddModal(false)
  }

  const canRegenerate = pendingChanges > 0 || pendingFeedbackCount > 0

  return (
    <div className="argument-board">
      <div className="board-header">
        <div>
          <h3 style={{ margin: 0 }}>Interactive Graph Review</h3>
          <p className="text-muted" style={{ margin: '0.2rem 0 0' }}>
            {phase === 'review'
              ? 'Select a care option, then click an argument to edit or remove it.'
              : 'Contest the arguments behind the plan, then regenerate it.'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="secondary" disabled={!editable} onClick={() => setShowAddModal(!showAddModal)}>+ Add Argument</button>
          {phase === 'review' && <button disabled={loading} onClick={onAccept}>Accept All &amp; Continue</button>}
          {planExists && (
            <button disabled={loading || !canRegenerate} onClick={onRegenerate} title={canRegenerate ? '' : 'Contest an argument or add plan feedback first'}>
              Regenerate Care Plan
            </button>
          )}
        </div>
      </div>

      {planExists && canRegenerate && (
        <div className="pending-banner">
          {pendingChanges > 0 && <span>{pendingChanges} argument change{pendingChanges === 1 ? '' : 's'}</span>}
          {pendingChanges > 0 && pendingFeedbackCount > 0 && <span> and </span>}
          {pendingFeedbackCount > 0 && <span>{pendingFeedbackCount} plan feedback item{pendingFeedbackCount === 1 ? '' : 's'}</span>}
          <span> will be applied when you regenerate the care plan.</span>
        </div>
      )}

      <div className="option-tabs">
        {options.map((option, idx) => {
          const isActive = activeOption === option
          const count = args.filter(a => a.option === option && a.status !== 'rejected').length
          const row = qbafByOption[option]
          return (
            <button key={idx} className={`option-tab ${isActive ? 'active' : ''}`} onClick={() => { setActiveOption(option); setSelectedArg(null) }}>
              <span>Option {idx + 1}</span>
              <span className="option-count">{count}</span>
              {row && <span className={`tier-dot ${TIER_CLASS[row.tier]}`} title={`${row.tier_label} (strength ${row.strength.toFixed(2)})`} />}
            </button>
          )
        })}
      </div>

      {activeOption && (
        <div className="option-label">
          <span className="option-label-prefix">Viewing: </span>
          <span className="option-label-text">{activeOption}</span>
          {qbafByOption[activeOption] && (
            <span className={`tier-pill ${TIER_CLASS[qbafByOption[activeOption].tier]}`}>
              {qbafByOption[activeOption].tier_label} · {qbafByOption[activeOption].strength.toFixed(2)}
            </span>
          )}
        </div>
      )}

      <div className="board-canvas">
        {Object.keys(columns).length === 0 ? (
          <div style={{ textAlign: 'center', color: '#94a3b8', paddingTop: '2rem' }}>No arguments for this option yet.</div>
        ) : (
          <div className="role-columns">
            {Object.entries(columns).map(([role, roleArgs]) => (
              <div key={role} className="role-column">
                <div className="role-header">{role}</div>
                {roleArgs.map(arg => (
                  <ArgumentCard key={arg.arg_id} arg={arg} qbafRow={qbafArgs?.[arg.arg_id]} editable={editable}
                    onSelect={select} planExists={planExists} />
                ))}
              </div>
            ))}
          </div>
        )}

        {removed.length > 0 && (
          <div className="removed-args">
            <button className="link-button" onClick={() => setShowRemoved(!showRemoved)}>
              {showRemoved ? 'Hide' : 'Show'} removed arguments ({removed.length})
            </button>
            {showRemoved && removed.map(arg => (
              <div key={arg.arg_id} className="removed-arg">
                <span className="arg-id">{arg.arg_id}</span>
                <span className="removed-text">{stripRoleTag(arg.content)}</span>
                {arg.rejection_reason && <span className="removed-reason">({arg.rejection_reason})</span>}
                <button className="secondary small" disabled={!editable} onClick={() => onAction('restore', { arg_id: arg.arg_id })}>Restore</button>
              </div>
            ))}
          </div>
        )}

        {selectedArg && (
          <div className="floating-panel" style={{ top: 20, right: 20 }}>
            <div className="floating-panel-header">
              <h4 style={{ margin: 0 }}>Edit Argument {selectedArg.arg_id}</h4>
              <button className="secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setSelectedArg(null)}>x</button>
            </div>
            <div style={{ marginBottom: '1rem', fontSize: '0.8rem', color: '#64748b' }}>
              Option: {selectedArg.option} <br /> Type: {selectedArg.type}
              {selectedArg.validation_note && <><br />Verifier: {selectedArg.validation_note}</>}
            </div>
            <textarea style={{ width: '100%', minHeight: '100px', marginBottom: '1rem' }} value={editContent} onChange={e => setEditContent(e.target.value)} />
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
              <button className="danger" onClick={() => act('remove', { arg_id: selectedArg.arg_id })}>Remove Node</button>
              <button onClick={() => act('modify', { arg_id: selectedArg.arg_id, new_content: editContent })}>Save Edits</button>
            </div>
          </div>
        )}

        {showAddModal && (
          <div className="floating-panel" style={{ top: 20, left: 20 }}>
            <div className="floating-panel-header">
              <h4 style={{ margin: 0 }}>Add New Argument</h4>
              <button className="secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setShowAddModal(false)}>x</button>
            </div>
            <label className="field-label">Option to Target</label>
            <select className="form-control" value={activeOption || ''} onChange={e => setActiveOption(e.target.value)}>
              {options.map((opt, idx) => <option key={idx} value={opt}>{opt}</option>)}
            </select>
            <label className="field-label">Argument Type</label>
            <select className="form-control" value={newArgType} onChange={e => setNewArgType(e.target.value)}>
              <option value="support">Support</option>
              <option value="attack">Challenge / Attack</option>
            </select>
            <label className="field-label">Role</label>
            <select className="form-control" value={newArgRole} onChange={e => setNewArgRole(e.target.value)}>
              {roles.map((role, idx) => <option key={idx} value={role}>{role}</option>)}
            </select>
            <label className="field-label">Content</label>
            <textarea style={{ width: '100%', minHeight: '80px', marginBottom: '1rem' }} value={newArgContent} onChange={e => setNewArgContent(e.target.value)} placeholder="Type out the argument" />
            <button style={{ width: '100%' }} disabled={!newArgContent.trim()} onClick={addArgument}>Inject Node</button>
          </div>
        )}
      </div>
    </div>
  )
}
