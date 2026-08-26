import { useState, useEffect, useCallback } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PRESETS = {
  normal: {
    name: 'Normal Transaction',
    icon: '🟢',
    description: 'Benign baseline payment from established customer',
    data: {
      amount: 450.0,
      customer_avg_amount: 500.0,
      payment_method: 'upi',
      account_age_days: 320,
      previous_transaction_count: 42,
      failed_attempts: 0,
      refund_count: 0,
      transactions_last_10min: 0,
      transactions_last_1hr: 0,
      device_account_count: 1,
      is_new_device: 0,
      is_unusual_time: 0,
      is_unusual_location: 0,
      transaction_id: 'txn_legit_1001',
      customer_id: 'cust_retail_891',
    },
  },
  suspicious: {
    name: 'Suspicious Activity',
    icon: '🟡',
    description: 'Moderate amount elevation, 1 failed retry & new device in off-hours',
    data: {
      amount: 2800.0,
      customer_avg_amount: 1000.0,
      payment_method: 'card',
      account_age_days: 100,
      previous_transaction_count: 12,
      failed_attempts: 1,
      refund_count: 0,
      transactions_last_10min: 0,
      transactions_last_1hr: 1,
      device_account_count: 1,
      is_new_device: 1,
      is_unusual_time: 1,
      is_unusual_location: 0,
      transaction_id: 'txn_sus_2004',
      customer_id: 'cust_retail_412',
    },
  },
  attack: {
    name: 'High-Risk Attack Cluster',
    icon: '🔴',
    description: 'Severe amount spike, multiple failures, rapid velocity & device reuse',
    data: {
      amount: 55000.0,
      customer_avg_amount: 1000.0,
      payment_method: 'card',
      account_age_days: 8,
      previous_transaction_count: 0,
      failed_attempts: 3,
      refund_count: 0,
      transactions_last_10min: 3,
      transactions_last_1hr: 5,
      device_account_count: 4,
      is_new_device: 1,
      is_unusual_time: 1,
      is_unusual_location: 1,
      transaction_id: 'txn_atk_9088',
      customer_id: 'cust_target_092',
    },
  },
}

const DEFAULT_FORM = { ...PRESETS.normal.data }

export default function App() {
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [readiness, setReadiness] = useState({ ready: false, checking: true, error: null })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})
  const [showJson, setShowJson] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState('normal')

  // Check backend and model readiness on mount and periodically
  const checkReadiness = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/health/ready`)
      if (res.ok) {
        const data = await res.json()
        setReadiness({ ready: true, checking: false, error: null, data })
      } else {
        const errData = await res.json().catch(() => ({}))
        setReadiness({
          ready: false,
          checking: false,
          error: errData.detail?.message || `HTTP ${res.status}: Backend Unready`,
        })
      }
    } catch {
      setReadiness({
        ready: false,
        checking: false,
        error: `Cannot connect to backend at ${API_BASE}. Ensure uvicorn server is running.`,
      })
    }
  }, [])

  useEffect(() => {
    checkReadiness()
    const timer = setInterval(checkReadiness, 10000)
    return () => clearInterval(timer)
  }, [checkReadiness])

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
    // Clear validation error for field
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  const loadPreset = (presetKey) => {
    setSelectedPreset(presetKey)
    setFormData({ ...PRESETS[presetKey].data })
    setError(null)
    setValidationErrors({})
  }

  const validateForm = () => {
    const errs = {}
    if (!formData.amount || Number(formData.amount) <= 0) {
      errs.amount = 'Amount must be greater than 0'
    }
    if (Number(formData.account_age_days) < 0) {
      errs.account_age_days = 'Account age cannot be negative'
    }
    if (Number(formData.failed_attempts) < 0) {
      errs.failed_attempts = 'Failed attempts cannot be negative'
    }
    if (Number(formData.transactions_last_10min) < 0) {
      errs.transactions_last_10min = 'Counter cannot be negative'
    }
    if (Number(formData.transactions_last_1hr) < 0) {
      errs.transactions_last_1hr = 'Counter cannot be negative'
    }
    if (Number(formData.device_account_count) < 1) {
      errs.device_account_count = 'Must be at least 1 account'
    }
    setValidationErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleAssess = async (e) => {
    if (e) e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    setError(null)

    // Build payload matching exact backend schema
    const payload = {
      amount: parseFloat(formData.amount),
      customer_avg_amount: parseFloat(formData.customer_avg_amount || 0.0),
      payment_method: formData.payment_method,
      account_age_days: parseInt(formData.account_age_days || 0, 10),
      previous_transaction_count: parseInt(formData.previous_transaction_count || 0, 10),
      failed_attempts: parseInt(formData.failed_attempts || 0, 10),
      refund_count: parseInt(formData.refund_count || 0, 10),
      transactions_last_10min: parseInt(formData.transactions_last_10min || 0, 10),
      transactions_last_1hr: parseInt(formData.transactions_last_1hr || 0, 10),
      device_account_count: parseInt(formData.device_account_count || 1, 10),
      is_new_device: parseInt(formData.is_new_device || 0, 10),
      is_unusual_time: parseInt(formData.is_unusual_time || 0, 10),
      is_unusual_location: parseInt(formData.is_unusual_location || 0, 10),
      transaction_id: formData.transaction_id || undefined,
      customer_id: formData.customer_id || undefined,
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/risk/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        if (response.status === 422) {
          throw new Error(
            `Validation Error (422): ${JSON.stringify(errorData.detail || 'Invalid transaction parameters')}`
          )
        } else if (response.status === 503) {
          throw new Error(
            `Service Unavailable (503): ${errorData.detail || 'Model artifacts offline or loading failed'}`
          )
        } else {
          throw new Error(`Server Error (${response.status}): ${errorData.detail || 'Risk assessment failure'}`)
        }
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Failed to communicate with RISK-X assessment backend.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  // Keyboard shortcut: Ctrl/Cmd + Enter to trigger assessment
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        handleAssess()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [formData])

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="brand-group">
          <div className="brand-badge">
            <span className="pulse-indicator"></span>
            <span className="brand-title">RISK-X</span>
          </div>
          <span className="brand-sub">Risk Investigation System X</span>
        </div>

        <div className="header-meta">
          <div className="buildathon-tag">Razorpay Buildathon 2026</div>
          <div className={`readiness-pill ${readiness.ready ? 'ready' : 'unready'}`}>
            <span className="status-dot"></span>
            {readiness.checking
              ? 'Checking Engine...'
              : readiness.ready
              ? 'ML Detector Online'
              : 'Engine Offline'}
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="dashboard-grid">
        {/* Left Column: Transaction Input Console */}
        <section className="console-panel">
          <div className="panel-header">
            <div>
              <h2>Transaction Assessment Console</h2>
              <p className="panel-sub">Configure observable payment parameters or load audit scenarios.</p>
            </div>
          </div>

          {/* Quick Presets Bar */}
          <div className="presets-wrapper">
            <span className="presets-label">Scenarios:</span>
            <div className="presets-btn-group">
              {Object.entries(PRESETS).map(([key, p]) => (
                <button
                  key={key}
                  type="button"
                  className={`preset-btn ${selectedPreset === key ? 'active' : ''}`}
                  onClick={() => loadPreset(key)}
                  title={p.description}
                >
                  <span className="preset-icon">{p.icon}</span>
                  <span className="preset-name">{p.name}</span>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleAssess} className="assessment-form">
            {/* Fieldset 1: Financial Details */}
            <div className="form-section">
              <h3 className="section-title">
                <span className="section-num">1</span> Financial & Payment Rail
              </h3>
              <div className="form-row two-col">
                <div className="input-group">
                  <label htmlFor="amount">Transaction Amount (INR) *</label>
                  <div className="input-affix-wrapper">
                    <span className="input-prefix">₹</span>
                    <input
                      id="amount"
                      type="number"
                      step="0.01"
                      min="0.01"
                      required
                      value={formData.amount}
                      onChange={(e) => handleInputChange('amount', e.target.value)}
                      className={validationErrors.amount ? 'invalid' : ''}
                    />
                  </div>
                  {validationErrors.amount && (
                    <span className="field-error">{validationErrors.amount}</span>
                  )}
                </div>

                <div className="input-group">
                  <label htmlFor="customer_avg_amount">Customer Avg Amount (INR)</label>
                  <div className="input-affix-wrapper">
                    <span className="input-prefix">₹</span>
                    <input
                      id="customer_avg_amount"
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData.customer_avg_amount}
                      onChange={(e) => handleInputChange('customer_avg_amount', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="input-group">
                  <label htmlFor="payment_method">Payment Method Rail</label>
                  <select
                    id="payment_method"
                    value={formData.payment_method}
                    onChange={(e) => handleInputChange('payment_method', e.target.value)}
                  >
                    <option value="upi">UPI (Unified Payments Interface)</option>
                    <option value="card">Credit / Debit Card</option>
                    <option value="netbanking">Internet Net Banking</option>
                    <option value="wallet">Digital Wallet</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Fieldset 2: Account History */}
            <div className="form-section">
              <h3 className="section-title">
                <span className="section-num">2</span> Account & Historical Profile
              </h3>
              <div className="form-row three-col">
                <div className="input-group">
                  <label htmlFor="account_age_days">Account Age (Days)</label>
                  <input
                    id="account_age_days"
                    type="number"
                    min="0"
                    value={formData.account_age_days}
                    onChange={(e) => handleInputChange('account_age_days', e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="previous_transaction_count">Prior Successful Txns</label>
                  <input
                    id="previous_transaction_count"
                    type="number"
                    min="0"
                    value={formData.previous_transaction_count}
                    onChange={(e) => handleInputChange('previous_transaction_count', e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="refund_count">Historical Refunds</label>
                  <input
                    id="refund_count"
                    type="number"
                    min="0"
                    value={formData.refund_count}
                    onChange={(e) => handleInputChange('refund_count', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Fieldset 3: Velocity & Friction */}
            <div className="form-section">
              <h3 className="section-title">
                <span className="section-num">3</span> Immediate Velocity & Failed Attempts
              </h3>
              <div className="form-row three-col">
                <div className="input-group">
                  <label htmlFor="transactions_last_10min">Txns Last 10 Min</label>
                  <input
                    id="transactions_last_10min"
                    type="number"
                    min="0"
                    value={formData.transactions_last_10min}
                    onChange={(e) => handleInputChange('transactions_last_10min', e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="transactions_last_1hr">Txns Last 1 Hour</label>
                  <input
                    id="transactions_last_1hr"
                    type="number"
                    min="0"
                    value={formData.transactions_last_1hr}
                    onChange={(e) => handleInputChange('transactions_last_1hr', e.target.value)}
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="failed_attempts">Failed Retries</label>
                  <input
                    id="failed_attempts"
                    type="number"
                    min="0"
                    value={formData.failed_attempts}
                    onChange={(e) => handleInputChange('failed_attempts', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Fieldset 4: Device & Environment */}
            <div className="form-section">
              <h3 className="section-title">
                <span className="section-num">4</span> Device & Environmental Signals
              </h3>
              <div className="form-row two-col">
                <div className="input-group">
                  <label htmlFor="device_account_count">Device Associated Accounts</label>
                  <input
                    id="device_account_count"
                    type="number"
                    min="1"
                    value={formData.device_account_count}
                    onChange={(e) => handleInputChange('device_account_count', e.target.value)}
                  />
                </div>
                <div className="toggles-group">
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={formData.is_new_device === 1}
                      onChange={(e) => handleInputChange('is_new_device', e.target.checked ? 1 : 0)}
                    />
                    <span>Unrecognized / New Device</span>
                  </label>
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={formData.is_unusual_time === 1}
                      onChange={(e) => handleInputChange('is_unusual_time', e.target.checked ? 1 : 0)}
                    />
                    <span>Atypical Active Hours</span>
                  </label>
                  <label className="toggle-label">
                    <input
                      type="checkbox"
                      checked={formData.is_unusual_location === 1}
                      onChange={(e) => handleInputChange('is_unusual_location', e.target.checked ? 1 : 0)}
                    />
                    <span>Unusual Location</span>
                  </label>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="form-actions">
              <button
                type="submit"
                disabled={loading || !readiness.ready}
                className="submit-btn"
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    <span>Analyzing Risk via ML Engine...</span>
                  </>
                ) : (
                  <>
                    <span>Run Real-Time Risk Assessment</span>
                    <kbd className="kbd-shortcut">Ctrl+Enter</kbd>
                  </>
                )}
              </button>
            </div>
          </form>
        </section>

        {/* Right Column: Assessment & Evidence Cockpit */}
        <section className="cockpit-panel">
          <div className="panel-header">
            <div>
              <h2>Risk Decision & Evidence Cockpit</h2>
              <p className="panel-sub">Real-time model probability, deterministic score, and ranked signals.</p>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="error-card">
              <div className="error-icon">⚠️</div>
              <div className="error-content">
                <h4>Assessment Error</h4>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && (
            <div className="skeleton-card">
              <div className="skeleton-circle"></div>
              <div className="skeleton-bar lg"></div>
              <div className="skeleton-bar md"></div>
              <div className="skeleton-bar sm"></div>
            </div>
          )}

          {/* Pre-Assessment State */}
          {!loading && !result && !error && (
            <div className="placeholder-card">
              <div className="placeholder-icon">🛡️</div>
              <h3>No Assessment Executed Yet</h3>
              <p>
                Configure payment attributes in the console or select a scenario preset,
                then click <strong>Run Real-Time Risk Assessment</strong>.
              </p>
              <div className="pipeline-mini">
                <span>API Payload</span> → <span>Feature Pipeline</span> → <span>Random Forest</span> → <span>0-100 Score</span> → <span>Policy</span>
              </div>
            </div>
          )}

          {/* Result View */}
          {!loading && result && (
            <div className="result-card">
              {/* Decision & Score Header */}
              <div className={`decision-hero ${result.decision.toLowerCase()}`}>
                <div className="score-meter-box">
                  <div className="score-number">{result.risk_score}</div>
                  <div className="score-scale">/ 100</div>
                  <div className="score-label">Risk Score</div>
                </div>

                <div className="decision-info-box">
                  <div className="badges-row">
                    <span className={`decision-badge ${result.decision.toLowerCase()}`}>
                      {result.decision}
                    </span>
                    <span className={`risk-level-badge ${result.risk_level.toLowerCase()}`}>
                      {result.risk_level} RISK
                    </span>
                  </div>
                  <div className="rf-prob-text">
                    <strong>RF Fraud Probability:</strong> {(result.fraud_probability * 100).toFixed(2)}% ({result.fraud_probability})
                  </div>
                  <div className="decision-meaning">
                    {result.decision === 'ALLOW' && '✅ Frictionless low-risk approval. No step-up required.'}
                    {result.decision === 'REVIEW' && '⚠️ Elevated risk. Recommended for 2FA step-up or analyst triage.'}
                    {result.decision === 'BLOCK' && '🛑 High-risk attack profile. Automated transaction decline.'}
                  </div>
                </div>
              </div>

              {/* Analyst Summary Callout */}
              {result.analyst_summary && (
                <div className="analyst-summary-card">
                  <div className="summary-title">
                    <span className="summary-icon">📋</span>
                    <strong>Analyst Summary</strong>
                  </div>
                  <p className="summary-text">{result.analyst_summary}</p>
                </div>
              )}

              {/* Structured Evidence Signals */}
              <div className="evidence-section">
                <div className="evidence-header">
                  <h3>Structured Risk Evidence Signals</h3>
                  <span className="evidence-count-badge">
                    {result.evidence?.length || 0} Signals Detected
                  </span>
                </div>

                {(!result.evidence || result.evidence.length === 0) ? (
                  <div className="empty-evidence-box">
                    <span>✨ No elevated risk signals detected. Transaction attributes conform to expected baselines.</span>
                  </div>
                ) : (
                  <div className="evidence-list">
                    {result.evidence.map((item, idx) => (
                      <div key={idx} className={`evidence-card severity-${item.severity.toLowerCase()}`}>
                        <div className="evidence-card-header">
                          <div className="evidence-title-group">
                            <span className={`severity-tag ${item.severity.toLowerCase()}`}>
                              {item.severity}
                            </span>
                            <span className="evidence-title">{item.title}</span>
                          </div>
                          <span className="evidence-code">{item.code}</span>
                        </div>

                        <p className="evidence-desc">{item.description}</p>

                        <div className="evidence-meta-row">
                          <span className="meta-item">
                            <strong>Observed:</strong> {String(item.observed_value)}
                          </span>
                          {item.reference_threshold && (
                            <span className="meta-item">
                              <strong>Threshold:</strong> {item.reference_threshold}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Raw JSON Debug Viewer */}
              <div className="json-debug-section">
                <button
                  type="button"
                  className="json-toggle-btn"
                  onClick={() => setShowJson(!showJson)}
                >
                  {showJson ? '▼ Hide API Response JSON' : '▶ View Raw Assessment JSON'}
                </button>
                {showJson && (
                  <pre className="json-code-block">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                )}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
