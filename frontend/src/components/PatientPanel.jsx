import { Edit, Sparkle } from './Icons'

export const EXAMPLES = {
  minor: '82-year-old female living alone. Mild cognitive impairment, history of falls but wants to stay at home.',
  complex: '78-year-old male, diabetic with recent stroke affecting left side mobility. Needs daily insulin, wife is primary caregiver but struggling.'
}

const SEVERITIES = [
  { value: 'Default', label: 'Assess automatically' },
  { value: 'Low', label: 'Low' },
  { value: 'Moderate', label: 'Moderate' },
  { value: 'High', label: 'High' },
  { value: 'Very High', label: 'Very high' }
]

export default function PatientPanel({ patientInfo, setPatientInfo, severity, setSeverity, hasStarted, loading, onStart, onEdit }) {
  if (hasStarted) {
    return (
      <div className="patient-summary">
        <p>{patientInfo}</p>
        <div className="patient-summary-row">
          <span className="chip">Severity: {SEVERITIES.find(s => s.value === severity)?.label || severity}</span>
          <button type="button" className="btn ghost xs" onClick={onEdit} disabled={loading}><Edit size={13} /> Edit or new case</button>
        </div>
      </div>
    )
  }
  return (
    <div className="patient-form">
      <label className="field">
        <span className="field-label">Patient description</span>
        <textarea className="input" rows={6} value={patientInfo} disabled={loading}
          placeholder="Age, living situation, conditions, current support, goals and preferences…"
          onChange={e => setPatientInfo(e.target.value)} />
      </label>
      <div className="example-chips">
        <span>Examples:</span>
        <button type="button" className="chip" onClick={() => setPatientInfo(EXAMPLES.minor)}>Lives alone, falls</button>
        <button type="button" className="chip" onClick={() => setPatientInfo(EXAMPLES.complex)}>Post-stroke, diabetes</button>
      </div>
      <label className="field">
        <span className="field-label">Severity</span>
        <select className="input" value={severity} onChange={e => setSeverity(e.target.value)} disabled={loading}>
          {SEVERITIES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
      </label>
      <button type="button" className="btn primary block" onClick={onStart} disabled={loading || !patientInfo.trim()}>
        <Sparkle size={16} /> Generate care plan
      </button>
      <p className="field-hint">Use de-identified information. The plan is decision support and needs clinical review.</p>
    </div>
  )
}
