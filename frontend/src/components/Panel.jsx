import { usePersistentState } from '../hooks'
import { ChevronDown } from './Icons'

// A card whose body can be collapsed; the choice is remembered per panel id.
// The body stays mounted while collapsed so drafts and scroll positions survive.
export default function Panel({
  id, title, subtitle, icon, badge, actions, children, defaultOpen = true, className = '', bodyClassName = '',
  open: controlledOpen, onToggle
}) {
  const [storedOpen, setStoredOpen] = usePersistentState(`caiaipcp:panel:${id}`, defaultOpen)
  const open = controlledOpen ?? storedOpen
  const toggle = () => (onToggle ? onToggle(!open) : setStoredOpen(!open))
  return (
    <section className={`panel ${open ? 'is-open' : 'is-collapsed'} ${className}`} data-panel={id}>
      <header className="panel-header">
        <button type="button" className="panel-toggle" onClick={toggle} aria-expanded={open} aria-controls={`panel-body-${id}`}>
          {icon && <span className="panel-icon">{icon}</span>}
          <span className="panel-heading">
            <span className="panel-title">{title}</span>
            {subtitle && <span className="panel-subtitle">{subtitle}</span>}
          </span>
          {badge}
          <ChevronDown className="panel-chevron" />
        </button>
        {actions && open && <div className="panel-actions">{actions}</div>}
      </header>
      <div id={`panel-body-${id}`} className={`panel-body ${bodyClassName}`} hidden={!open}>
        {children}
      </div>
    </section>
  )
}
