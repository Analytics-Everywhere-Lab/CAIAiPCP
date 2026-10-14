import { useEffect, useState } from 'react'
import { TIER_CLASS } from './CarePlanDocument'
import { CitedText, ReferenceItem, fromIeee, ieeeText } from './Citations'
import { Check, CheckCircle, ChevronDown, Edit, Plus, Refresh, Trash } from './Icons'

const SOURCE_BADGES = {
  human: { label: 'Added by clinician', className: 'badge-human' },
  feedback: { label: 'From plan feedback', className: 'badge-feedback' },
  memory: { label: 'Learned from past reviews', className: 'badge-memory' }
}
const RELEVANCE_LABELS = { high: 'High relevance', moderate: 'Moderate relevance', low: 'Low relevance' }
const ROLE_TAG = /^\[[^\]]{1,60}\]\s*/
const ROLE_COLORS = 6
// Groups that are not a discipline on the care team: the clinician adds arguments
// under a discipline instead.
const NON_DISCIPLINE_ROLES = new Set(['Learned guidance', 'Clinician feedback'])

function stripRoleTag(content) {
  return (content || '').replace(ROLE_TAG, '')
}

function roleInitials(role) {
  const words = (role || 'General').split(/\s+/).filter(Boolean)
  return (words.length > 1 ? words.map(word => word[0]).join('') : words[0].slice(0, 3)).slice(0, 3).toUpperCase()
}

function formatImpact(value) {
  const rounded = Math.round(value * 100) / 100
  if (rounded === 0) return '0.00'
  return `${rounded > 0 ? '+' : ''}${rounded.toFixed(2)}`
}

function impactClass(value) {
  const rounded = Math.round(value * 100) / 100
  return rounded > 0 ? 'impact-up' : rounded < 0 ? 'impact-down' : ''
}

// Shared editor for editing an argument in place and for adding a new one.
function InlineEditor({ value, onChange, onSave, onCancel, saveLabel, placeholder, disabled, children }) {
  return (
    <div className="inline-editor">
      {children}
      <textarea className="input" autoFocus rows={3} value={value} placeholder={placeholder}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); if (!disabled) onSave() }
          if (e.key === 'Escape') { e.preventDefault(); onCancel() }
        }} />
      <div className="inline-actions">
        <span className="inline-hint">Ctrl+Enter to save · Esc to cancel</span>
        <button type="button" className="btn ghost sm" onClick={onCancel}>Cancel</button>
        <button type="button" className="btn primary sm" disabled={disabled} onClick={onSave}><Check size={14} /> {saveLabel}</button>
      </div>
    </div>
  )
}

function StancePill({ stance }) {
  return <span className={`stance-pill ${stance}`}>{stance === 'support' ? 'Supports' : 'Concern'}</span>
}

function ArgumentRow({
  arg, qbafRow, editable, planExists, editing, removing, answeredBy, rebuttal, cite,
  onEdit, onEditChange, onSaveEdit, onCancel, onRemove, onRemoveChange, onConfirmRemove
}) {
  const source = SOURCE_BADGES[arg.source]
  const stance = arg.type === 'support' ? 'support' : 'attack'
  const pendingReevaluation = planExists && !qbafRow
  const answers = [
    ...(arg.rebuts || []).map(target => ({ target, partial: false })),
    ...(arg.partly_rebuts || []).map(target => ({ target, partial: true }))
  ]
  return (
    <article className={`arg-row ${stance} ${editing ? 'is-editing' : ''} ${removing ? 'is-removing' : ''}`} id={`arg-${arg.arg_id}`}>
      <div className="arg-row-meta">
        <div className="arg-row-tags">
          <StancePill stance={stance} />
          <span className="arg-id">{arg.arg_id}</span>
        </div>
        {source && <span className={`badge ${source.className}`}>{source.label}{arg.feedback_id ? ` · ${arg.feedback_id}` : ''}</span>}
        {arg.status === 'edited' && <span className="badge badge-edited">Edited</span>}
      </div>

      <div className="arg-row-body">
        {editing ? (
          <InlineEditor value={editing.text} onChange={onEditChange} onSave={onSaveEdit} onCancel={onCancel}
            saveLabel="Save" disabled={!editing.text.trim() || editing.text.trim() === ieeeText(stripRoleTag(arg.content)).trim()} />
        ) : (
          <p className="arg-text">{cite(stripRoleTag(arg.content))}</p>
        )}
        {removing && (
          <div className="remove-confirm">
            <input className="input" autoFocus placeholder="Why remove it? (optional, helps the system learn)" value={removing.reason}
              onChange={e => onRemoveChange(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') { e.preventDefault(); onConfirmRemove() }
                if (e.key === 'Escape') { e.preventDefault(); onCancel() }
              }} />
            <button type="button" className="btn ghost sm" onClick={onCancel}>Keep</button>
            <button type="button" className="btn danger-soft sm" onClick={onConfirmRemove}><Trash size={14} /> Remove</button>
          </div>
        )}
        {arg.status === 'edited' && arg.original_content && !editing && (
          <p className="arg-original">Was: {ieeeText(stripRoleTag(arg.original_content))}</p>
        )}
        {(arg.target_arg_id || answers.length > 0 || answeredBy?.length > 0 || arg.same_as) && (
          <div className="arg-links">
            {arg.target_arg_id && <a className="arg-link" href={`#arg-${arg.target_arg_id}`}>Responds to {arg.target_arg_id}</a>}
            {answers.map(({ target, partial }) => {
              const reason = rebuttal(arg.arg_id, target)?.reason
              return (
                <a key={target} className="arg-link answers" href={`#arg-${target}`} title={ieeeText(reason)}>
                  {partial ? 'Partly answers' : 'Answers'} {target}{reason ? `: ${ieeeText(reason)}` : ''}
                </a>
              )
            })}
            {answeredBy?.map(({ source: from, partial }) => (
              <a key={from} className="arg-link answered" href={`#arg-${from}`} title={ieeeText(rebuttal(from, arg.arg_id)?.reason)}>
                {partial ? 'Partly answered' : 'Answered'} by {from}, so it weighs less
              </a>
            ))}
            {arg.same_as && <a className="arg-link repeat" href={`#arg-${arg.same_as}`}>Repeats {arg.same_as}, counted once</a>}
          </div>
        )}
        {arg.validation_note && !editing && <p className="arg-note"><strong>Verifier:</strong> {cite(arg.validation_note)}</p>}
        {arg.flags?.includes('verifier_disagrees') && (
          <p className="arg-warning">The verifier found weak support; it still counts with clinician weight.</p>
        )}
        {arg.flags?.includes('unverified') && <p className="arg-warning">Not verified: the panel returned no result for this argument.</p>}
      </div>

      <div className="arg-row-side">
        <div className="arg-metrics">
          {arg.relevance && <span className={`relevance-pill ${arg.relevance}`}>{RELEVANCE_LABELS[arg.relevance]}</span>}
          {arg.score != null && <span className="metric">Validity <strong>{arg.score.toFixed(2)}</strong></span>}
          {qbafRow && (
            <span className="metric" title="Change in the option's strength if this argument were removed">
              Impact <strong className={impactClass(qbafRow.contribution)}>{formatImpact(qbafRow.contribution)}</strong>
            </span>
          )}
          {pendingReevaluation && <span className="metric pending">Weighed when you regenerate</span>}
        </div>
        {editable && !editing && !removing && (
          <div className="arg-actions">
            <button type="button" className="btn ghost xs" onClick={onEdit}><Edit size={13} /> Edit</button>
            <button type="button" className="btn ghost xs danger-text" onClick={onRemove}><Trash size={13} /> Remove</button>
          </div>
        )}
      </div>
    </article>
  )
}

export default function ArgumentBoard({
  options, args, qbafOptions, qbafArgs, reviews, references, phase, loading, pendingChanges, pendingFeedbackCount,
  onAction, onAccept, onRegenerate
}) {
  const [activeOption, setActiveOption] = useState(null)
  const [collapsedRoles, setCollapsedRoles] = useState(() => new Set())
  const [editing, setEditing] = useState(null) // { argId, text }
  const [removing, setRemoving] = useState(null) // { argId, reason }
  const [composer, setComposer] = useState(null) // { role, stance, text }
  const [showRemoved, setShowRemoved] = useState(false)

  const editable = !loading && (phase === 'review' || phase === 'plan')
  const planExists = phase === 'plan'
  const refById = Object.fromEntries((references || []).map(ref => [ref.id, ref]))
  const refIds = new Set(Object.keys(refById).map(Number))

  useEffect(() => {
    if (options.length > 0) setActiveOption(prev => (prev && options.includes(prev) ? prev : options[0]))
  }, [options])

  const cancelAll = () => {
    setEditing(null)
    setRemoving(null)
    setComposer(null)
  }
  useEffect(cancelAll, [activeOption])

  // Every role keeps the same colour on every option.
  const caseRoles = Array.from(new Set(args.map(a => a.role || 'General')))
  const roleColor = (role) => `role-c${Math.max(0, caseRoles.indexOf(role)) % ROLE_COLORS}`

  const optionIndex = options.indexOf(activeOption)
  const oid = optionIndex >= 0 ? `O${optionIndex + 1}` : null
  const qbafByOption = Object.fromEntries((qbafOptions || []).map(row => [row.option, row]))
  const row = qbafByOption[activeOption]
  const review = (oid && reviews?.[oid]) || null
  const verdict = review?.summary || row?.review
  const optionArgs = args.filter(a => a.option === activeOption)
  const active = optionArgs.filter(a => a.status !== 'rejected')
  const removed = optionArgs.filter(a => a.status === 'rejected')
  const answeredBy = {}
  active.forEach(a => {
    ;(a.rebuts || []).forEach(target => { (answeredBy[target] = answeredBy[target] || []).push({ source: a.arg_id, partial: false }) })
    ;(a.partly_rebuts || []).forEach(target => { (answeredBy[target] = answeredBy[target] || []).push({ source: a.arg_id, partial: true }) })
  })
  const rebuttal = (from, to) => review?.rebuttals?.find(r => r.from === from && r.to === to)

  // [n] citations jump to this option's reference box and flash the entry.
  const jumpToReference = (n, event) => {
    const target = document.getElementById(`board-ref-${n}`)
    if (!target) return
    event.preventDefault()
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    target.classList.remove('flash')
    void target.offsetWidth
    target.classList.add('flash')
  }
  const cite = (text) => <CitedText text={text} refIds={refIds} anchor="board-ref-" onCite={jumpToReference} />
  const citedHere = new Set()
  ;[activeOption, verdict, ...optionArgs.flatMap(a => [a.content, a.original_content, a.validation_note])]
    .forEach(text => { for (const m of (text || '').matchAll(/\[REF-(\d+)\]/g)) if (refIds.has(Number(m[1]))) citedHere.add(Number(m[1])) })
  const optionReferences = [...citedHere].sort((a, b) => a - b).map(id => refById[id])
  const pendingTotal = pendingChanges + pendingFeedbackCount
  const counts = {
    support: active.filter(a => a.type === 'support').length,
    attack: active.filter(a => a.type !== 'support').length,
    answered: Object.keys(answeredBy).length,
    repeats: active.filter(a => a.same_as).length
  }

  // Disciplines first, in team order; then learned guidance and feedback-derived arguments.
  const disciplines = caseRoles.filter(role => !NON_DISCIPLINE_ROLES.has(role))
  const groupRoles = [...disciplines, ...caseRoles.filter(role => NON_DISCIPLINE_ROLES.has(role))]
    .filter(role => active.some(a => (a.role || 'General') === role) || (disciplines.includes(role) && editable))
  const groups = groupRoles.map(role => {
    const list = active.filter(a => (a.role || 'General') === role)
    return {
      role,
      args: [...list.filter(a => a.type === 'support'), ...list.filter(a => a.type !== 'support')],
      net: list.reduce((sum, a) => sum + (qbafArgs?.[a.arg_id]?.contribution || 0), 0),
      hasImpact: list.some(a => qbafArgs?.[a.arg_id])
    }
  })

  const toggleRole = (role) => setCollapsedRoles(prev => {
    const next = new Set(prev)
    if (next.has(role)) next.delete(role)
    else next.add(role)
    return next
  })

  const saveEdit = async (arg) => {
    const tag = (arg.content.match(ROLE_TAG) || [''])[0]
    await onAction('modify', { arg_id: arg.arg_id, new_content: tag + fromIeee(editing.text.trim(), refIds) })
    setEditing(null)
  }
  const confirmRemove = async (arg) => {
    await onAction('remove', { arg_id: arg.arg_id, reason: removing?.reason?.trim() || undefined })
    setRemoving(null)
  }
  const addArgument = async () => {
    if (!composer?.text.trim()) return
    await onAction('add', { new_content: composer.text.trim(), new_type: composer.stance, new_option: activeOption, new_role: composer.role })
    setComposer(null)
  }

  const roleGroup = ({ role, args: list, net, hasImpact }) => {
    const collapsed = collapsedRoles.has(role)
    const supports = list.filter(a => a.type === 'support').length
    const concerns = list.length - supports
    const composing = composer?.role === role
    return (
      <section key={role} className={`role-group ${roleColor(role)} ${collapsed ? 'is-collapsed' : ''}`}>
        <button type="button" className="role-group-header" onClick={() => toggleRole(role)} aria-expanded={!collapsed}>
          <span className="role-avatar" aria-hidden="true">{roleInitials(role)}</span>
          <span className="role-group-title">
            <span className="role-group-name">{role}</span>
            <span className="role-group-sub">
              {supports} supporting · {concerns} concern{concerns === 1 ? '' : 's'}
            </span>
          </span>
          {hasImpact && (
            <span className="role-net" title="Combined impact of this role's arguments on the option's strength">
              Net impact <strong className={impactClass(net)}>{formatImpact(net)}</strong>
            </span>
          )}
          <ChevronDown size={16} className="role-group-chevron" />
        </button>
        {!collapsed && (
          <div className="role-group-body">
            {list.length === 0 && !composing && <p className="arg-empty">No arguments from this role for this option.</p>}
            {list.map(arg => (
              <ArgumentRow key={arg.arg_id} arg={arg} qbafRow={qbafArgs?.[arg.arg_id]} editable={editable} planExists={planExists}
                editing={editing?.argId === arg.arg_id ? editing : null}
                removing={removing?.argId === arg.arg_id ? removing : null}
                answeredBy={answeredBy[arg.arg_id]} rebuttal={rebuttal} cite={cite}
                onEdit={() => { cancelAll(); setEditing({ argId: arg.arg_id, text: ieeeText(stripRoleTag(arg.content)) }) }}
                onEditChange={text => setEditing(prev => ({ ...prev, text }))}
                onSaveEdit={() => saveEdit(arg)}
                onCancel={cancelAll}
                onRemove={() => { cancelAll(); setRemoving({ argId: arg.arg_id, reason: '' }) }}
                onRemoveChange={reason => setRemoving(prev => ({ ...prev, reason }))}
                onConfirmRemove={() => confirmRemove(arg)} />
            ))}
            {composing ? (
              <article className="arg-row is-composing">
                <div className="arg-row-meta">
                  <div className="arg-row-tags"><span className="arg-id">New</span></div>
                </div>
                <div className="arg-row-body">
                  <InlineEditor value={composer.text} onChange={text => setComposer(prev => ({ ...prev, text }))}
                    onSave={addArgument} onCancel={() => setComposer(null)} saveLabel="Add argument" disabled={!composer.text.trim()}
                    placeholder={composer.stance === 'support'
                      ? 'e.g. Her daughter visits daily and can supervise the home modifications.'
                      : 'e.g. She has refused grab bars before; the bathroom changes may not be used.'}>
                    <div className="stance-toggle" role="radiogroup" aria-label="Stance">
                      {['support', 'attack'].map(stance => (
                        <button key={stance} type="button" role="radio" aria-checked={composer.stance === stance}
                          className={`stance-option ${stance} ${composer.stance === stance ? 'active' : ''}`}
                          onClick={() => setComposer(prev => ({ ...prev, stance }))}>
                          {stance === 'support' ? 'Supports the option' : 'Raises a concern'}
                        </button>
                      ))}
                    </div>
                  </InlineEditor>
                </div>
              </article>
            ) : editable && disciplines.includes(role) && (
              <button type="button" className="add-row" onClick={() => { cancelAll(); setComposer({ role, stance: 'support', text: '' }) }}>
                <Plus size={15} /> Add an argument as {role}
              </button>
            )}
          </div>
        )}
      </section>
    )
  }

  return (
    <div className="board">
      <div className="board-toolbar">
        {phase !== 'review' && (
          <p className="board-intro">
            Contest the arguments behind the plan: edit, remove or add one right where it is, then regenerate the plan.
          </p>
        )}
        <div className="option-tabs" role="tablist" aria-label="Care options">
          {options.map((option, idx) => {
            const isActive = activeOption === option
            const count = args.filter(a => a.option === option && a.status !== 'rejected').length
            const optionRow = qbafByOption[option]
            return (
              <button key={idx} type="button" role="tab" aria-selected={isActive} className={`option-tab ${isActive ? 'active' : ''}`}
                onClick={() => setActiveOption(option)} title={ieeeText(option)}>
                {optionRow && <span className={`tier-dot ${TIER_CLASS[optionRow.tier]}`} />}
                <span className="option-tab-label">Option {idx + 1}</span>
                <span className="count-pill">{count}</span>
              </button>
            )
          })}
        </div>
        <div className="board-actions">
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

      {activeOption && (
        <section className="option-overview">
          <div className="option-overview-head">
            <div className="option-overview-title">
              <span className="eyebrow">Option {optionIndex + 1}</span>
              <h3>{cite(activeOption)}</h3>
            </div>
            {row && (
              <div className="option-overview-score">
                <span className={`tier-pill ${TIER_CLASS[row.tier]}`}>{row.tier_label}</span>
                <span className="option-strength">
                  <span className="meter"><span style={{ width: `${Math.round(row.strength * 100)}%` }} /></span>
                  Strength <strong>{row.strength.toFixed(2)}</strong>
                </span>
              </div>
            )}
          </div>
          {row?.tier === 'set_aside' && (
            <p className="option-verdict muted">
              After your review the arguments no longer support this option, so it is set aside and left out of the plan.
              Add or restore supporting arguments to bring it back.
            </p>
          )}
          {verdict ? (
            <p className="option-verdict"><strong>Verification panel:</strong> {cite(verdict)}</p>
          ) : phase !== 'review' && (
            <p className="option-verdict muted">This option will be verified again when you regenerate.</p>
          )}
          <div className="option-stats">
            <span>{counts.support} supporting</span>
            <span>{counts.attack} concern{counts.attack === 1 ? '' : 's'}</span>
            {counts.answered > 0 && <span>{counts.answered} answered</span>}
            {counts.repeats > 0 && <span>{counts.repeats} repeated</span>}
          </div>
        </section>
      )}

      {groups.map(roleGroup)}

      {optionReferences.length > 0 && (
        <section className="ref-box" aria-label="References">
          <h4>References</h4>
          <ol className="reference-list">
            {optionReferences.map(ref => <ReferenceItem key={ref.id} reference={ref} anchor="board-ref-" />)}
          </ol>
        </section>
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
              <span className="removed-text">{ieeeText(stripRoleTag(arg.content))}</span>
              {arg.rejection_reason && <span className="removed-reason">({arg.rejection_reason})</span>}
              <button type="button" className="btn ghost xs" disabled={!editable} onClick={() => onAction('restore', { arg_id: arg.arg_id })}>
                <Refresh size={12} /> Restore
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
