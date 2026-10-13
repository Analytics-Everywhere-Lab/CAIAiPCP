import { useEffect, useRef, useState } from 'react'
import { postJSON, putJSON } from '../api'
import { Alert, CheckCircle, Cpu, Eye, EyeOff, Info, Key, Moon, Palette, Refresh, Settings, Sun, X } from './Icons'

const EFFORT_LABELS = {
  auto: 'Auto (recommended): low effort for quick checks, model default for writing',
  low: 'Low: fastest and cheapest',
  medium: 'Medium: balanced',
  high: 'High: most thorough, slowest'
}

function formatTokens(n) {
  return (n || 0).toLocaleString()
}

export default function SettingsDialog({ open, onClose, settings, onSaved, themePreference, onThemeChange }) {
  const [form, setForm] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [removeKey, setRemoveKey] = useState(false)
  const [customModel, setCustomModel] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const dialogRef = useRef(null)

  useEffect(() => {
    if (!open || !settings) return
    setForm({
      provider: settings.provider,
      ollama_base_url: settings.ollama_base_url,
      ollama_model: settings.ollama_model,
      anthropic_model: settings.anthropic_model,
      anthropic_effort: settings.anthropic_effort
    })
    setApiKey('')
    setShowKey(false)
    setRemoveKey(false)
    setTestResult(null)
    setError('')
    setCustomModel(!settings.claude_models?.some(m => m.id === settings.anthropic_model))
  }, [open, settings])

  useEffect(() => {
    if (!open) return undefined
    const onKey = (event) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    dialogRef.current?.focus()
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open || !settings || !form) return null

  const set = (key, value) => {
    setForm(prev => ({ ...prev, [key]: value }))
    setTestResult(null)
  }
  const payload = () => ({
    ...form,
    ...(apiKey.trim() ? { anthropic_api_key: apiKey.trim() } : removeKey ? { anthropic_api_key: '' } : {})
  })

  const test = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      setTestResult(await postJSON('/api/settings/test', payload()))
    } catch (err) {
      setTestResult({ ok: false, message: err.message })
    } finally {
      setTesting(false)
    }
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      onSaved(await putJSON('/api/settings', payload()))
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const keyHint = settings.anthropic_key_source === 'environment'
    ? 'Using ANTHROPIC_API_KEY from the server environment. Enter a key here to override it.'
    : settings.anthropic_key_set && !removeKey
      ? `A key ending ${settings.anthropic_key_hint} is saved on the server. It is never sent back to the browser.`
      : 'Create a key in the Claude Console (console.anthropic.com). It is stored only on this server.'
  const usage = Object.entries(settings.status?.usage || {})
  const lastError = settings.status?.last_error

  return (
    <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="settings-title" tabIndex={-1} ref={dialogRef}>
        <header className="modal-header">
          <div className="modal-title"><Settings size={18} /><h2 id="settings-title">Settings</h2></div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close settings"><X /></button>
        </header>

        <div className="modal-body">
          <section className="settings-section">
            <h3><Cpu size={16} /> Language model</h3>
            <p className="settings-help">
              Every step uses this model: care options, team arguments, verification, plan writing and the assistant.
              Changes apply to the next step; a running generation keeps going.
            </p>
            <div className="segmented" role="radiogroup" aria-label="Model provider">
              {[
                { id: 'ollama', title: 'Local model', sub: 'Ollama on your machine' },
                { id: 'anthropic', title: 'Claude API', sub: 'Anthropic cloud models' }
              ].map(option => (
                <button key={option.id} type="button" role="radio" aria-checked={form.provider === option.id}
                  className={`segment ${form.provider === option.id ? 'active' : ''}`} onClick={() => set('provider', option.id)}>
                  <strong>{option.title}</strong><span>{option.sub}</span>
                </button>
              ))}
            </div>

            {form.provider === 'ollama' ? (
              <div className="field-grid">
                <label className="field">
                  <span className="field-label">Ollama server URL</span>
                  <input className="input" value={form.ollama_base_url} onChange={e => set('ollama_base_url', e.target.value)} spellCheck={false} />
                </label>
                <label className="field">
                  <span className="field-label">Model</span>
                  <input className="input" value={form.ollama_model} onChange={e => set('ollama_model', e.target.value)}
                    list="ollama-model-list" spellCheck={false} />
                  <datalist id="ollama-model-list">
                    {(testResult?.models || []).map(name => <option key={name} value={name} />)}
                  </datalist>
                </label>
              </div>
            ) : (
              <>
                <label className="field">
                  <span className="field-label"><Key size={14} /> API key</span>
                  <span className="input-with-action">
                    <input className="input" type={showKey ? 'text' : 'password'} autoComplete="off" spellCheck={false}
                      placeholder={settings.anthropic_key_set && !removeKey ? `Saved key ${settings.anthropic_key_hint}: leave blank to keep it` : 'sk-ant-…'}
                      value={apiKey} onChange={e => { setApiKey(e.target.value); setRemoveKey(false); setTestResult(null) }} />
                    <button type="button" className="icon-btn" onClick={() => setShowKey(s => !s)} aria-label={showKey ? 'Hide key' : 'Show key'}>
                      {showKey ? <EyeOff /> : <Eye />}
                    </button>
                  </span>
                  <span className="field-hint">
                    {keyHint}
                    {settings.anthropic_key_source === 'settings' && !removeKey && (
                      <> <button type="button" className="link-btn danger" onClick={() => { setRemoveKey(true); setApiKey('') }}>Remove saved key</button></>
                    )}
                    {removeKey && <> The saved key will be removed when you save.</>}
                  </span>
                </label>

                <div className="field">
                  <span className="field-label">Model</span>
                  <div className="model-options">
                    {settings.claude_models.map(model => (
                      <button key={model.id} type="button"
                        className={`model-option ${!customModel && form.anthropic_model === model.id ? 'active' : ''}`}
                        onClick={() => { setCustomModel(false); set('anthropic_model', model.id) }}>
                        <strong>{model.label}</strong><span>{model.note}</span><code>{model.id}</code>
                      </button>
                    ))}
                    <button type="button" className={`model-option ${customModel ? 'active' : ''}`} onClick={() => setCustomModel(true)}>
                      <strong>Other model</strong><span>Enter a model ID</span>
                    </button>
                  </div>
                  {customModel && (
                    <input className="input" placeholder="claude-…" value={form.anthropic_model} spellCheck={false}
                      onChange={e => set('anthropic_model', e.target.value)} aria-label="Custom model ID" />
                  )}
                </div>

                <label className="field">
                  <span className="field-label">Reasoning effort</span>
                  <select className="input" value={form.anthropic_effort} onChange={e => set('anthropic_effort', e.target.value)}>
                    {settings.efforts.map(effort => <option key={effort} value={effort}>{EFFORT_LABELS[effort] || effort}</option>)}
                  </select>
                </label>

                <div className="callout info">
                  <Info size={16} />
                  <div>
                    With Claude selected, the patient description and care-plan content are sent to Anthropic's API.
                    Use de-identified information unless your organization's data policy allows otherwise.
                    If a request is declined by a safety check, Opus, Sonnet and Fable models retry it automatically on a fallback Claude model.
                  </div>
                </div>
              </>
            )}

            <div className="test-row">
              <button type="button" className="btn secondary sm" onClick={test} disabled={testing}>
                <Refresh size={14} className={testing ? 'spin' : ''} /> {testing ? 'Testing…' : 'Test connection'}
              </button>
              {testResult && (
                <span className={`test-result ${testResult.ok ? 'ok' : 'fail'}`} role="status">
                  {testResult.ok ? <CheckCircle size={15} /> : <Alert size={15} />} {testResult.message}
                </span>
              )}
            </div>
          </section>

          <section className="settings-section">
            <h3><Palette size={16} /> Appearance</h3>
            <div className="segmented compact" role="radiogroup" aria-label="Theme">
              {[
                { id: 'light', label: 'Light', icon: <Sun size={15} /> },
                { id: 'dark', label: 'Dark', icon: <Moon size={15} /> },
                { id: 'system', label: 'System', icon: <Settings size={15} /> }
              ].map(option => (
                <button key={option.id} type="button" role="radio" aria-checked={themePreference === option.id}
                  className={`segment ${themePreference === option.id ? 'active' : ''}`} onClick={() => onThemeChange(option.id)}>
                  {option.icon} {option.label}
                </button>
              ))}
            </div>
          </section>

          {(usage.length > 0 || lastError) && (
            <section className="settings-section">
              <h3>This server session</h3>
              {usage.length > 0 && (
                <div className="table-scroll">
                  <table className="usage-table">
                    <thead><tr><th>Model</th><th>Calls</th><th>Input tokens</th><th>Read from cache</th><th>Output tokens</th></tr></thead>
                    <tbody>
                      {usage.map(([model, row]) => (
                        <tr key={model}>
                          <td><code>{model}</code></td><td>{row.calls}</td><td>{formatTokens(row.input_tokens + row.cache_read_input_tokens + row.cache_creation_input_tokens)}</td>
                          <td>{formatTokens(row.cache_read_input_tokens)}</td><td>{formatTokens(row.output_tokens)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              {lastError && (
                <div className="callout warn">
                  <Alert size={16} />
                  <div>Last model error ({lastError.provider}, {new Date(lastError.at * 1000).toLocaleTimeString()}): {lastError.message}</div>
                </div>
              )}
            </section>
          )}
        </div>

        <footer className="modal-footer">
          {error && <span className="form-error" role="alert">{error}</span>}
          <button type="button" className="btn ghost" onClick={onClose}>Cancel</button>
          <button type="button" className="btn primary" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save settings'}</button>
        </footer>
      </div>
    </div>
  )
}
