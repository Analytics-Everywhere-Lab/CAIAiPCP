import { BrandMark } from './Icons'
import { EXAMPLES } from './PatientPanel'

const STEPS = [
  { title: 'Describe the patient', text: 'Living situation, conditions, support and what matters to them.' },
  { title: 'Contest the arguments', text: 'The care team argues each option. Edit, remove or add arguments before the plan is written.' },
  { title: 'Refine the plan', text: 'Pin feedback notes to any sentence of the plan, then regenerate. The system learns from your review.' }
]

export default function Welcome({ onExample }) {
  return (
    <div className="welcome">
      <div className="welcome-mark"><BrandMark size={64} /></div>
      <h1>Care plans clinicians can contest</h1>
      <p className="welcome-lead">
        An interdisciplinary AI care team weighs each option for aging in place. You review its arguments, and the care plan
        is written from the arguments that hold up.
      </p>
      <ol className="welcome-steps">
        {STEPS.map((step, index) => (
          <li key={step.title}>
            <span className="welcome-step-number">{index + 1}</span>
            <div><strong>{step.title}</strong><p>{step.text}</p></div>
          </li>
        ))}
      </ol>
      <div className="welcome-actions">
        <span>Start with an example:</span>
        <button type="button" className="btn secondary sm" onClick={() => onExample(EXAMPLES.minor)}>Lives alone with falls</button>
        <button type="button" className="btn secondary sm" onClick={() => onExample(EXAMPLES.complex)}>Post-stroke with diabetes</button>
      </div>
    </div>
  )
}
