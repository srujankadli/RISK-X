import { useState, useEffect, useCallback, useMemo } from 'react'

const API_BASE = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

const PRESETS = {
  normal: {
    id: 'normal',
    name: 'Normal Transaction',
    icon: '🟢',
    badge: 'BENIGN BASELINE → ALLOW',
    description: 'Clean transaction from established customer matching spending baseline. Zero risk flags.',
    expected: 'ALLOW · Risk Score: 1 · Low Risk',
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
      transaction_id: 'txn_demo_001',
      customer_id: 'cust_ind_1048',
    },
  },
  suspicious: {
    id: 'suspicious',
    name: 'Suspicious Velocity',
    icon: '🟡',
    badge: 'STEP-UP REVIEW',
    description: 'Moderate amount spike, 1 failed retry & unrecognized device in off-hours. Requires scrutiny.',
    expected: 'REVIEW · Risk Score: 67 · Medium Risk',
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
      transaction_id: 'txn_demo_004',
      customer_id: 'cust_biz_3910',
    },
  },
  attack: {
    id: 'attack',
    name: 'High-Risk Attack Cluster',
    icon: '🔴',
    badge: 'AUTOMATED BLOCK',
    description: 'Severe 55x amount spike, 3 failed retries, rapid velocity & multi-account device association.',
    expected: 'BLOCK · Risk Score: 93 · High Risk',
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
      transaction_id: 'txn_demo_005',
      customer_id: 'cust_ind_8402',
    },
  },
}

const DEFAULT_FORM = { ...PRESETS.normal.data }

export default function App() {
  const [activeTab, setActiveTab] = useState('core') // 'core' | 'stream' | 'webhook'
  const [formData, setFormData] = useState(DEFAULT_FORM)
  const [loading, setLoading] = useState(false)
  const [readiness, setReadiness] = useState({ ready: false, checking: true, error: null })
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})
  const [showJson, setShowJson] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState('normal')
  const [activeSignalIndex, setActiveSignalIndex] = useState(null)
  const [initialAssessed, setInitialAssessed] = useState(false)

  // History ledger state
  const [historyItems, setHistoryItems] = useState([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [historyFilter, setHistoryFilter] = useState('ALL')
  const [historyLoading, setHistoryLoading] = useState(false)
  const [stats, setStats] = useState(null)

  // Webhook Simulator state
  const [webhookPaymentId, setWebhookPaymentId] = useState('pay_demo_7821')
  const [webhookAmount, setWebhookAmount] = useState(3500.0)
  const [webhookMethod, setWebhookMethod] = useState('card')
  const [webhookSecret, setWebhookSecret] = useState('risk_x_buildathon_secret_2026')
  const [webhookResult, setWebhookResult] = useState(null)
  const [webhookLoading, setWebhookLoading] = useState(false)
  const [webhookError, setWebhookError] = useState(null)

  // Check backend readiness
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
        error: `Cannot connect to backend at ${API_BASE}. Ensure backend server is running.`,
      })
    }
  }, [])

  // Fetch aggregate risk statistics
  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/transactions/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch {
      // Ignored if backend offline
    }
  }, [])

  // Fetch transactions history stream
  const fetchHistory = useCallback(async (decisionFilter = 'ALL') => {
    setHistoryLoading(true)
    try {
      const filterParam = decisionFilter !== 'ALL' ? `&decision=${decisionFilter}` : ''
      const res = await fetch(`${API_BASE}/api/v1/transactions?limit=30${filterParam}`)
      if (res.ok) {
        const data = await res.json()
        setHistoryItems(data.items || [])
        setHistoryTotal(data.total || 0)
      }
    } catch (e) {
      console.error('Failed to fetch transaction stream:', e)
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  // Assess transaction helper
  const assessWithPayload = useCallback(async (dataToAssess) => {
    setLoading(true)
    setError(null)
    setActiveSignalIndex(null)

    const payload = {
      amount: parseFloat(dataToAssess.amount),
      customer_avg_amount: parseFloat(dataToAssess.customer_avg_amount || 0.0),
      payment_method: dataToAssess.payment_method,
      account_age_days: parseInt(dataToAssess.account_age_days || 0, 10),
      previous_transaction_count: parseInt(dataToAssess.previous_transaction_count || 0, 10),
      failed_attempts: parseInt(dataToAssess.failed_attempts || 0, 10),
      refund_count: parseInt(dataToAssess.refund_count || 0, 10),
      transactions_last_10min: parseInt(dataToAssess.transactions_last_10min || 0, 10),
      transactions_last_1hr: parseInt(dataToAssess.transactions_last_1hr || 0, 10),
      device_account_count: parseInt(dataToAssess.device_account_count || 1, 10),
      is_new_device: parseInt(dataToAssess.is_new_device || 0, 10),
      is_unusual_time: parseInt(dataToAssess.is_unusual_time || 0, 10),
      is_unusual_location: parseInt(dataToAssess.is_unusual_location || 0, 10),
      transaction_id: dataToAssess.transaction_id || undefined,
      customer_id: dataToAssess.customer_id || undefined,
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
      fetchStats()
      fetchHistory(historyFilter)
    } catch (err) {
      setError(err.message || 'Failed to communicate with RISK-X assessment backend.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }, [fetchStats, fetchHistory, historyFilter])

  useEffect(() => {
    checkReadiness()
    fetchStats()
    fetchHistory('ALL')
    const timer = setInterval(() => {
      checkReadiness()
      fetchStats()
    }, 8000)
    return () => clearInterval(timer)
  }, [checkReadiness, fetchStats, fetchHistory])

  // Automatically assess initial normal preset once backend is ready
  useEffect(() => {
    if (readiness.ready && !initialAssessed && !result) {
      assessWithPayload(DEFAULT_FORM)
      setInitialAssessed(true)
    }
  }, [readiness.ready, initialAssessed, result, assessWithPayload])

  useEffect(() => {
    if (activeTab === 'stream') {
      fetchHistory(historyFilter)
    }
  }, [activeTab, historyFilter, fetchHistory])

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
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
    const presetData = { ...PRESETS[presetKey].data }
    setFormData(presetData)
    setError(null)
    setValidationErrors({})
    setActiveSignalIndex(null)
    if (readiness.ready) {
      assessWithPayload(presetData)
    }
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
    assessWithPayload(formData)
  }

  // Keyboard shortcut: Ctrl/Cmd + Enter
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        handleAssess()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [formData])

  // Select a transaction from history stream to inspect in the central Risk Core
  const inspectHistoryItem = (item) => {
    setResult({
      risk_score: item.risk_score,
      fraud_probability: item.fraud_probability,
      decision: item.decision,
      risk_level: item.risk_level,
      reasons: item.reasons || [],
      evidence: item.evidence || [],
      analyst_summary: item.analyst_summary,
      transaction_id: item.transaction_id,
      amount: item.amount,
      customer_id: item.customer_id,
      payment_method: item.payment_method,
      source: item.source,
      created_at: item.created_at,
    })
    if (item.raw_request) {
      setFormData((prev) => ({
        ...prev,
        amount: item.amount || prev.amount,
        customer_avg_amount: item.customer_avg_amount || prev.customer_avg_amount,
        payment_method: item.payment_method || prev.payment_method,
        transaction_id: item.transaction_id,
        customer_id: item.customer_id || prev.customer_id,
      }))
    }
    setActiveTab('core')
  }

  // Webhook Simulator submit
  const handleWebhookSubmit = async (customConfig = {}) => {
    setWebhookLoading(true)
    setWebhookError(null)
    setWebhookResult(null)

    const paymentId = customConfig.paymentId || webhookPaymentId
    const amount = customConfig.amount || webhookAmount
    const method = customConfig.method || webhookMethod
    const secret = customConfig.secret !== undefined ? customConfig.secret : webhookSecret
    const forceInvalidSig = customConfig.forceInvalidSig || false

    const payload = {
      entity: 'event',
      account_id: 'acc_buildathon_rzp_01',
      event: 'payment.authorized',
      contains: ['payment'],
      payload: {
        payment: {
          entity: {
            id: paymentId,
            amount: Math.round(amount * 100), // paise
            currency: 'INR',
            status: 'authorized',
            method: method,
            notes: {
              customer_id: 'cust_hook_7821',
              customer_avg_amount: String(Math.round(amount * 0.4)),
              account_age_days: '60',
              previous_transaction_count: '5',
              failed_attempts: '1',
              is_new_device: '1',
              is_unusual_time: '1',
            },
          },
        },
      },
    }

    const bodyText = JSON.stringify(payload)

    try {
      let hexSignature = ''
      if (forceInvalidSig) {
        hexSignature = 'invalid_hmac_tampered_signature_782190abcdef'
      } else {
        const encoder = new TextEncoder()
        const keyData = encoder.encode(secret)
        const msgData = encoder.encode(bodyText)

        const cryptoKey = await window.crypto.subtle.importKey(
          'raw',
          keyData,
          { name: 'HMAC', hash: 'SHA-256' },
          false,
          ['sign']
        )
        const signatureBuffer = await window.crypto.subtle.sign('HMAC', cryptoKey, msgData)
        const hashArray = Array.from(new Uint8Array(signatureBuffer))
        hexSignature = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
      }

      const res = await fetch(`${API_BASE}/api/v1/webhooks/razorpay`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Razorpay-Signature': hexSignature,
        },
        body: bodyText,
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || `Webhook Rejected (HTTP ${res.status}): Invalid Signature`)
      }

      setWebhookResult(data)
      fetchStats()
      fetchHistory(historyFilter)
    } catch (err) {
      setWebhookError(err.message || 'Webhook transmission failed.')
    } finally {
      setWebhookLoading(false)
    }
  }

  // Active decision state for theme transitions
  const activeDecision = result?.decision?.toLowerCase() || 'neutral'
  const activeRiskScore = result?.risk_score ?? '--'

  // Severity metrics calculation for telemetry
  const severityCounts = useMemo(() => {
    if (!result?.evidence) return { high: 0, medium: 0, low: 0 }
    return result.evidence.reduce(
      (acc, curr) => {
        const sev = (curr.severity || '').toLowerCase()
        if (sev === 'high') acc.high++
        else if (sev === 'medium') acc.medium++
        else if (sev === 'low') acc.low++
        return acc
      },
      { high: 0, medium: 0, low: 0 }
    )
  }, [result])

  return (
    <div className={`space-stage theme-${activeDecision}`}>
      {/* Background Spatial Grid and Glow Effects */}
      <div className="spatial-bg-grid" aria-hidden="true"></div>
      <div className="spatial-core-glow" aria-hidden="true"></div>

      <div className="app-container">
        {/* =========================================================================
            1. TOP SYSTEM BAR (Futuristic HUD)
           ========================================================================= */}
        <header className="system-hud-bar">
          <div className="brand-zone">
            <div className="brand-emblem">
              <div className="emblem-hex">
                <span className="emblem-core"></span>
              </div>
              <div className="brand-text-block">
                <div className="brand-heading">
                  <span className="brand-title">RISK-X</span>
                  <span className="brand-subtag">INTELLIGENCE CORE</span>
                </div>
                <span className="brand-dept">Payment Risk Investigation & Automated Response</span>
              </div>
            </div>
          </div>

          {/* Center: System Status Diagnostics */}
          <div className="system-diagnostics">
            <div className="diag-item">
              <span className="diag-label">SYSTEM:</span>
              <span className={`diag-pill ${readiness.ready ? 'online' : 'offline'}`}>
                <span className="status-ping"></span>
                {readiness.checking ? 'PROBING...' : readiness.ready ? 'ENGINE ONLINE' : 'ENGINE OFFLINE'}
              </span>
            </div>
            <div className="diag-item">
              <span className="diag-label">MODEL:</span>
              <span className="diag-val">RANDOM FOREST</span>
            </div>
            <div className="diag-item">
              <span className="diag-label">STORAGE:</span>
              <span className="diag-val">SQLITE WAL</span>
            </div>
            <div className="diag-item hide-mobile">
              <span className="diag-label">EVENT:</span>
              <span className="diag-tag">RAZORPAY 2026</span>
            </div>
          </div>

          {/* Right: Spatial Nav Tabs */}
          <nav className="spatial-nav-tabs">
            <button
              type="button"
              className={`nav-pill ${activeTab === 'core' ? 'active' : ''}`}
              onClick={() => setActiveTab('core')}
            >
              <span className="nav-icon">🛡️</span>
              <span>Risk Core</span>
            </button>
            <button
              type="button"
              className={`nav-pill ${activeTab === 'stream' ? 'active' : ''}`}
              onClick={() => setActiveTab('stream')}
            >
              <span className="nav-icon">📊</span>
              <span>Live Stream ({stats?.total_transactions || historyTotal})</span>
            </button>
            <button
              type="button"
              className={`nav-pill ${activeTab === 'webhook' ? 'active' : ''}`}
              onClick={() => setActiveTab('webhook')}
            >
              <span className="nav-icon">⚡</span>
              <span>Webhook Link</span>
            </button>
          </nav>
        </header>

        {/* =========================================================================
            2. TELEMETRY KPI RIBBON
           ========================================================================= */}
        {stats && (
          <section className="telemetry-ribbon" aria-label="System Telemetry">
            <div className="telemetry-node">
              <span className="tel-label">Total Transactions</span>
              <span className="tel-value">{stats.total_transactions}</span>
            </div>
            <div className="telemetry-node node-allow">
              <span className="tel-label">ALLOW Rate</span>
              <span className="tel-value">
                {stats.allow_rate}% <small>({stats.allow_count})</small>
              </span>
            </div>
            <div className="telemetry-node node-review">
              <span className="tel-label">REVIEW Rate</span>
              <span className="tel-value">
                {stats.review_rate}% <small>({stats.review_count})</small>
              </span>
            </div>
            <div className="telemetry-node node-block">
              <span className="tel-label">BLOCK Rate</span>
              <span className="tel-value">
                {stats.block_rate}% <small>({stats.block_count})</small>
              </span>
            </div>
            <div className="telemetry-node node-score">
              <span className="tel-label">Average Risk Score</span>
              <span className="tel-value">
                {stats.average_risk_score} <small>/ 100</small>
              </span>
            </div>
            {result && (
              <div className="telemetry-node node-matrix hide-tablet">
                <span className="tel-label">Signal Matrix</span>
                <span className="tel-matrix-breakdown">
                  <span className="mat-high">{severityCounts.high}H</span>
                  <span className="mat-med">{severityCounts.medium}M</span>
                  <span className="mat-low">{severityCounts.low}L</span>
                </span>
              </div>
            )}
          </section>
        )}

        {/* =========================================================================
            2.5. 5-STAGE RISK INVESTIGATION PIPELINE (Judge Explainability Ribbon)
           ========================================================================= */}
        <section className="pipeline-narrative-bar" aria-label="End-to-End Decision Pipeline">
          <div className="pipe-stage-node done">
            <span className="pipe-badge">1. INGEST</span>
            <span className="pipe-title">13 Observables</span>
            <span className="pipe-sub">Amount, Velocity, Device</span>
          </div>
          <span className="pipe-chevron">➔</span>
          <div className={`pipe-stage-node ${result ? 'done' : ''}`}>
            <span className="pipe-badge">2. ML INFERENCE</span>
            <span className="pipe-title">Random Forest</span>
            <span className="pipe-sub">
              {result ? `${(result.fraud_probability * 100).toFixed(1)}% Fraud Prob` : 'Standby'}
            </span>
          </div>
          <span className="pipe-chevron">➔</span>
          <div className={`pipe-stage-node ${result ? 'done' : ''}`}>
            <span className="pipe-badge">3. SCORING</span>
            <span className="pipe-title">Deterministic Score</span>
            <span className="pipe-sub">
              {result ? `${result.risk_score} / 100` : '0 - 100 Scale'}
            </span>
          </div>
          <span className="pipe-chevron">➔</span>
          <div className={`pipe-stage-node ${result ? `active-${activeDecision}` : ''}`}>
            <span className="pipe-badge">4. DECISION</span>
            <span className="pipe-title">{result ? result.decision : 'Policy Guardrail'}</span>
            <span className="pipe-sub">
              {result ? `${result.risk_level} Risk` : 'ALLOW / REVIEW / BLOCK'}
            </span>
          </div>
          <span className="pipe-chevron">➔</span>
          <div className={`pipe-stage-node ${result ? 'done' : ''}`}>
            <span className="pipe-badge">5. AUDIT TRAIL</span>
            <span className="pipe-title">SQLite WAL</span>
            <span className="pipe-sub">Immutable Storage</span>
          </div>
        </section>

        {/* =========================================================================
            TAB 1: RISK CORE & SPATIAL INVESTIGATION STAGE
           ========================================================================= */}
        {activeTab === 'core' && (
          <div className="spatial-theatre-layout">
            {/* LEFT WING: Scenario Controls & Input Console */}
            <aside className="theatre-wing left-wing">
              {/* Scenario Control Deck */}
              <div className="cyber-panel">
                <div className="panel-hud-header">
                  <span className="hud-corner-tag">JUDGE SCENARIOS</span>
                  <h3>Audit Presets (One-Click)</h3>
                  <p className="panel-subtext">Select a scenario to evaluate immediately in the Risk Core.</p>
                </div>
                <div className="scenarios-deck">
                  {Object.entries(PRESETS).map(([key, p]) => (
                    <button
                      key={key}
                      type="button"
                      className={`scenario-card ${selectedPreset === key ? 'selected' : ''}`}
                      onClick={() => loadPreset(key)}
                    >
                      <div className="scenario-top">
                        <span className="scenario-icon">{p.icon}</span>
                        <span className="scenario-name">{p.name}</span>
                      </div>
                      <span className="scenario-badge">{p.badge}</span>
                      <p className="scenario-desc">{p.description}</p>
                      <span className="scenario-expected">{p.expected}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Assessment Form Console */}
              <div className="cyber-panel">
                <div className="panel-hud-header">
                  <span className="hud-corner-tag">INPUT DECK</span>
                  <h3>Transaction Parameters</h3>
                </div>

                <form onSubmit={handleAssess} className="cyber-form">
                  {/* Section 1: Financial */}
                  <div className="form-group-box">
                    <span className="box-title">1. Financial Rail</span>
                    <div className="grid-2col">
                      <div className="field-block">
                        <label htmlFor="amount">Amount (INR) *</label>
                        <div className="input-wrap">
                          <span className="curr-sym">₹</span>
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
                          <span className="field-warn">{validationErrors.amount}</span>
                        )}
                      </div>

                      <div className="field-block">
                        <label htmlFor="customer_avg_amount">Customer Avg (INR)</label>
                        <div className="input-wrap">
                          <span className="curr-sym">₹</span>
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

                    <div className="field-block single-col">
                      <label htmlFor="payment_method">Payment Rail</label>
                      <select
                        id="payment_method"
                        value={formData.payment_method}
                        onChange={(e) => handleInputChange('payment_method', e.target.value)}
                      >
                        <option value="upi">UPI (Unified Payments Interface)</option>
                        <option value="card">Credit / Debit Card</option>
                        <option value="netbanking">Net Banking</option>
                        <option value="wallet">Digital Wallet</option>
                      </select>
                    </div>
                  </div>

                  {/* Section 2: History & Account */}
                  <div className="form-group-box">
                    <span className="box-title">2. Account Profile</span>
                    <div className="grid-3col">
                      <div className="field-block">
                        <label htmlFor="account_age_days">Account Days</label>
                        <input
                          id="account_age_days"
                          type="number"
                          min="0"
                          value={formData.account_age_days}
                          onChange={(e) => handleInputChange('account_age_days', e.target.value)}
                        />
                      </div>
                      <div className="field-block">
                        <label htmlFor="previous_transaction_count">Prior Txns</label>
                        <input
                          id="previous_transaction_count"
                          type="number"
                          min="0"
                          value={formData.previous_transaction_count}
                          onChange={(e) =>
                            handleInputChange('previous_transaction_count', e.target.value)
                          }
                        />
                      </div>
                      <div className="field-block">
                        <label htmlFor="refund_count">Refunds</label>
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

                  {/* Section 3: Velocity & Retries */}
                  <div className="form-group-box">
                    <span className="box-title">3. Velocity & Retries</span>
                    <div className="grid-3col">
                      <div className="field-block">
                        <label htmlFor="transactions_last_10min">10m Velocity</label>
                        <input
                          id="transactions_last_10min"
                          type="number"
                          min="0"
                          value={formData.transactions_last_10min}
                          onChange={(e) =>
                            handleInputChange('transactions_last_10min', e.target.value)
                          }
                        />
                      </div>
                      <div className="field-block">
                        <label htmlFor="transactions_last_1hr">1h Velocity</label>
                        <input
                          id="transactions_last_1hr"
                          type="number"
                          min="0"
                          value={formData.transactions_last_1hr}
                          onChange={(e) => handleInputChange('transactions_last_1hr', e.target.value)}
                        />
                      </div>
                      <div className="field-block">
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

                  {/* Section 4: Device & Signals */}
                  <div className="form-group-box">
                    <span className="box-title">4. Device & Environmental Signals</span>
                    <div className="field-block single-col">
                      <label htmlFor="device_account_count">Device Associated Accounts</label>
                      <input
                        id="device_account_count"
                        type="number"
                        min="1"
                        value={formData.device_account_count}
                        onChange={(e) => handleInputChange('device_account_count', e.target.value)}
                      />
                    </div>
                    <div className="cyber-toggles">
                      <label className="toggle-chip">
                        <input
                          type="checkbox"
                          checked={formData.is_new_device === 1}
                          onChange={(e) =>
                            handleInputChange('is_new_device', e.target.checked ? 1 : 0)
                          }
                        />
                        <span>New / Unseen Device</span>
                      </label>
                      <label className="toggle-chip">
                        <input
                          type="checkbox"
                          checked={formData.is_unusual_time === 1}
                          onChange={(e) =>
                            handleInputChange('is_unusual_time', e.target.checked ? 1 : 0)
                          }
                        />
                        <span>Atypical Hours</span>
                      </label>
                      <label className="toggle-chip">
                        <input
                          type="checkbox"
                          checked={formData.is_unusual_location === 1}
                          onChange={(e) =>
                            handleInputChange('is_unusual_location', e.target.checked ? 1 : 0)
                          }
                        />
                        <span>Unusual Location</span>
                      </label>
                    </div>
                  </div>

                  {/* Assessment Execution Trigger */}
                  <button
                    type="submit"
                    disabled={loading || !readiness.ready}
                    className="cyber-assess-btn"
                  >
                    {loading ? (
                      <span className="btn-glow-pulse">
                        <span className="radar-spinner"></span>
                        <span>Evaluating via Random Forest Engine...</span>
                      </span>
                    ) : (
                      <span className="btn-content">
                        <span>⚡ RUN RISK ASSESSMENT</span>
                        <kbd className="key-hint">Ctrl+Enter</kbd>
                      </span>
                    )}
                  </button>
                </form>
              </div>
            </aside>

            {/* CENTER STAGE: THE RISK CORE (Visual Focal Point) */}
            <main className="theatre-center" aria-label="Risk Core Focal Stage">
              {/* Error Notice */}
              {error && (
                <div className="cyber-alert-banner">
                  <span className="alert-glyph">⚠️</span>
                  <div className="alert-body">
                    <strong>ASSESSMENT FAILURE</strong>
                    <p>{error}</p>
                  </div>
                </div>
              )}

              {/* Central Risk Core Container */}
              <div className={`risk-core-stage state-${activeDecision}`}>
                {/* 1. TOP DOCK: Transaction Identity Banner */}
                <div className="core-top-dock">
                  <div className="core-identity-bar">
                    <div className="id-chip">
                      <span className="id-label">TXN:</span>
                      <span className="id-val">
                        {result?.transaction_id || formData.transaction_id || 'STANDBY'}
                      </span>
                    </div>
                    <div className="id-chip">
                      <span className="id-label">AMOUNT:</span>
                      <span className="id-val amount-val">
                        ₹{parseFloat(formData.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </div>
                    <div className="id-chip">
                      <span className="id-label">POLICY:</span>
                      <span className={`id-val risk-${(result?.risk_level || 'standby').toLowerCase()}`}>
                        {result?.decision ? `${result.decision} (${result.risk_level} RISK)` : 'READY'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. CENTER ORBITAL ARENA (Bounded & Centered) */}
                <div className="core-orbital-arena">
                  {/* Concentric Orbital Geometry Rings */}
                  <div className="orbit-system" aria-hidden="true">
                    <div className="orbit-ring ring-outer"></div>
                    <div className="orbit-ring ring-middle"></div>
                    <div className="orbit-ring ring-inner"></div>
                    <div className="orbit-crosshair-h"></div>
                    <div className="orbit-crosshair-v"></div>
                  </div>

                  {/* Central Luminous Sphere & Score Display */}
                  <div className="core-sphere-anchor">
                    <div className="core-luminous-orb">
                      <div className="core-inner-glow"></div>
                      <div className="core-scan-beam" aria-hidden="true"></div>

                      <div className="core-content-hud">
                        <span className="core-kicker">RISK SCORE</span>
                        <div className="core-score-num">
                          {loading ? (
                            <span className="score-calculating">...</span>
                          ) : (
                            activeRiskScore
                          )}
                        </div>
                        <span className="core-scale-tag">/ 100</span>

                        {result && !loading && (
                          <div className="core-decision-tag">
                            <span className={`decision-pill pill-${activeDecision}`}>
                              {result.decision}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Orbiting Satellite Evidence Nodes */}
                  <div className="satellite-nodes-orbit" aria-label="Detected Risk Signal Nodes">
                    {result && result.evidence && result.evidence.length > 0 ? (
                      result.evidence.map((item, idx) => {
                        const total = result.evidence.length
                        // Distribute nodes evenly around the orbital sphere
                        const angle = (idx / total) * 360 - 90
                        const rad = (angle * Math.PI) / 180
                        // Bounded orbital radii
                        const rx = total <= 4 ? 155 : 170
                        const ry = total <= 4 ? 115 : 125
                        const x = Math.round(Math.cos(rad) * rx)
                        const y = Math.round(Math.sin(rad) * ry)
                        const isSelected = activeSignalIndex === idx

                        return (
                          <button
                            key={item.code || idx}
                            type="button"
                            className={`satellite-node sev-${item.severity.toLowerCase()} ${isSelected ? 'active-node' : ''}`}
                            style={{
                              transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                            }}
                            onClick={() => setActiveSignalIndex(isSelected ? null : idx)}
                            title={`${item.title} (${item.severity})`}
                          >
                            <span className="node-beacon"></span>
                            <div className="node-cardlet">
                              <span className="node-sev-tag">{item.severity}</span>
                              <span className="node-title">{item.title}</span>
                            </div>
                          </button>
                        )
                      })
                    ) : null}
                  </div>
                </div>

                {/* 3. BOTTOM DOCK: Status Halo or Inspection Callout (Zero Overlap) */}
                <div className="core-bottom-dock">
                  {result && activeSignalIndex !== null && result.evidence?.[activeSignalIndex] ? (
                    <div className="node-inspection-callout">
                      <div className="callout-header">
                        <span className={`callout-sev sev-${result.evidence[activeSignalIndex].severity.toLowerCase()}`}>
                          {result.evidence[activeSignalIndex].severity} SEVERITY SIGNAL
                        </span>
                        <h4>{result.evidence[activeSignalIndex].title}</h4>
                        <button
                          type="button"
                          className="close-callout"
                          onClick={() => setActiveSignalIndex(null)}
                        >
                          ✕
                        </button>
                      </div>
                      <p className="callout-desc">{result.evidence[activeSignalIndex].description}</p>
                      <div className="callout-meta">
                        <span className="meta-col">
                          <strong>Observed:</strong> {String(result.evidence[activeSignalIndex].observed_value)}
                        </span>
                        {result.evidence[activeSignalIndex].reference_threshold && (
                          <span className="meta-col">
                            <strong>Threshold:</strong> {result.evidence[activeSignalIndex].reference_threshold}
                          </span>
                        )}
                      </div>
                    </div>
                  ) : result && (!result.evidence || result.evidence.length === 0) ? (
                    <div className="calm-core-halo">
                      <span className="halo-icon">✨</span>
                      <span className="halo-text">Zero Elevated Risk Signals · Clean Baseline</span>
                    </div>
                  ) : (
                    <div className="standby-core-hint">
                      <span>Ready for Risk Assessment. Select a scenario or run evaluation.</span>
                    </div>
                  )}
                </div>
              </div>
            </main>

            {/* RIGHT WING: Deep Investigation & Narrative Dossier */}
            <aside className="theatre-wing right-wing">
              {/* Analyst Briefing Dossier */}
              <div className="cyber-panel">
                <div className="panel-hud-header">
                  <span className="hud-corner-tag">INVESTIGATION DOSSIER</span>
                  <h3>Risk Explainability</h3>
                  <p className="panel-subtext">Deconstructs ML probability, policy guardrails, and signals.</p>
                </div>

                {!result && !loading && (
                  <div className="empty-dossier-state">
                    <div className="dossier-glyph">🛡️</div>
                    <h4>Investigation Standby</h4>
                    <p>
                      Execute a transaction assessment in the console to inspect probability,
                      decision policy metrics, and severity-ranked signals.
                    </p>
                    <div className="workflow-crumbs">
                      <span>Payload</span> → <span>ColumnTransformer</span> → <span>Random Forest</span> → <span>Score</span> → <span>Guarded Action</span>
                    </div>
                  </div>
                )}

                {loading && (
                  <div className="dossier-loading-skeleton">
                    <div className="skeleton-pulse-circle"></div>
                    <div className="skeleton-pulse-bar lg"></div>
                    <div className="skeleton-pulse-bar md"></div>
                    <div className="skeleton-pulse-bar sm"></div>
                  </div>
                )}

                {result && !loading && (
                  <div className="investigation-dossier">
                    {/* Prob & Decision HUD */}
                    <div className="dossier-stat-grid">
                      <div className="dossier-metric">
                        <span className="dm-label">Random Forest Prob</span>
                        <span className="dm-val font-mono">
                          {(result.fraud_probability * 100).toFixed(2)}%
                        </span>
                        <span className="dm-sub">({result.fraud_probability})</span>
                      </div>
                      <div className="dossier-metric">
                        <span className="dm-label">Deterministic Score</span>
                        <span className="dm-val score-highlight">
                          {result.risk_score} / 100
                        </span>
                        <span className="dm-sub">{result.risk_level} Risk Level</span>
                      </div>
                    </div>

                    {/* Policy Guardrail Card */}
                    <div className={`policy-guardrail-card policy-${activeDecision}`}>
                      <div className="policy-head">
                        <span className="policy-shield-glyph">
                          {result.decision === 'ALLOW' ? '🛡️' : result.decision === 'REVIEW' ? '⚖️' : '🚫'}
                        </span>
                        <div>
                          <span className="policy-rule-tag">
                            {result.decision === 'ALLOW'
                              ? 'DIRECT SETTLEMENT (SCORE 0–39)'
                              : result.decision === 'REVIEW'
                              ? 'STEP-UP REVIEW (SCORE 40–69)'
                              : 'CRITICAL GUARDRAIL BLOCK (SCORE 70–100)'}
                          </span>
                          <h4 className="policy-decision-title">
                            {result.decision === 'ALLOW'
                              ? 'Low-Risk Baseline · Auto-Approved'
                              : result.decision === 'REVIEW'
                              ? 'Moderate Risk · Step-Up Verification Required'
                              : 'Critical Threat · Automated Decline'}
                          </h4>
                        </div>
                      </div>
                      <p className="policy-narrative">
                        {result.decision === 'ALLOW'
                          ? 'Payment parameters conform to established baseline. Score (1/100) is below the 40 step-up threshold. Direct capture approved.'
                          : result.decision === 'REVIEW'
                          ? 'This transaction is not automatically blocked, but it requires additional scrutiny before settlement. 3 risk signals detected.'
                          : 'High threat cluster detected. Score (93/100) breaches the 70 critical threshold. Automated decline enforced to prevent fraud loss.'}
                      </p>
                    </div>

                    {/* Analyst Narrative Summary */}
                    {result.analyst_summary && (
                      <div className="analyst-narrative-box">
                        <div className="narrative-head">
                          <span className="narrative-icon">📋</span>
                          <strong>Analyst Narrative Briefing</strong>
                        </div>
                        <p className="narrative-body">{result.analyst_summary}</p>
                      </div>
                    )}

                    {/* Evidence Signals Matrix */}
                    <div className="evidence-matrix-zone">
                      <div className="matrix-title-bar">
                        <h4>Structured Evidence Signals</h4>
                        <span className="signal-count-badge">
                          {result.evidence?.length || 0} Detected
                        </span>
                      </div>

                      {(!result.evidence || result.evidence.length === 0) ? (
                        <div className="clean-evidence-pill">
                          <span>✨ No elevated risk signals detected. Transaction attributes conform to established baseline.</span>
                        </div>
                      ) : (
                        <div className="signals-accordion-list">
                          {result.evidence.map((item, idx) => (
                            <div
                              key={idx}
                              className={`signal-dossier-card sev-${item.severity.toLowerCase()} ${activeSignalIndex === idx ? 'focused' : ''}`}
                              onClick={() => setActiveSignalIndex(activeSignalIndex === idx ? null : idx)}
                            >
                              <div className="signal-card-header">
                                <div className="signal-title-row">
                                  <span className={`sev-tag ${item.severity.toLowerCase()}`}>
                                    {item.severity}
                                  </span>
                                  <span className="sig-name">{item.title}</span>
                                </div>
                                <span className="sig-code">{item.code}</span>
                              </div>
                              <p className="sig-desc">{item.description}</p>
                              <div className="sig-metric-chips">
                                <span className="chip-item">
                                  <strong>Observed:</strong> {String(item.observed_value)}
                                </span>
                                {item.reference_threshold && (
                                  <span className="chip-item">
                                    <strong>Threshold:</strong> {item.reference_threshold}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Raw JSON Toggle */}
                    <div className="raw-json-drawer">
                      <button
                        type="button"
                        className="json-drawer-btn"
                        onClick={() => setShowJson(!showJson)}
                      >
                        {showJson ? '▼ Hide Raw Assessment Payload' : '▶ Inspect Raw Assessment JSON'}
                      </button>
                      {showJson && (
                        <pre className="json-output-block">
                          {JSON.stringify(result, null, 2)}
                        </pre>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </aside>
          </div>
        )}

        {/* =========================================================================
            TAB 2: LIVE TRANSACTION STREAM & AUDIT LEDGER
           ========================================================================= */}
        {activeTab === 'stream' && (
          <section className="cyber-panel stream-theatre-panel">
            <div className="panel-hud-header stream-header-wrap">
              <div>
                <span className="hud-corner-tag">IMMUTABLE AUDIT TRAIL</span>
                <h2>Transaction Stream & Investigation Ledger</h2>
                <p className="panel-subtext">
                  Every assessed transaction is immutably logged in SQLite WAL mode for compliance, dispute resolution, and audit investigation.
                </p>
              </div>
              <div className="stream-filter-bar">
                <span className="filter-bar-label">FILTER:</span>
                {['ALL', 'ALLOW', 'REVIEW', 'BLOCK'].map((filterKey) => (
                  <button
                    key={filterKey}
                    type="button"
                    className={`stream-filter-btn filter-btn-${filterKey.toLowerCase()} ${historyFilter === filterKey ? 'active' : ''}`}
                    onClick={() => {
                      setHistoryFilter(filterKey)
                      fetchHistory(filterKey)
                    }}
                  >
                    <span className="filter-dot"></span>
                    <span>{filterKey}</span>
                    {filterKey === 'ALL' && stats && (
                      <span className="filter-count-chip">{stats.total_transactions}</span>
                    )}
                    {filterKey === 'ALLOW' && stats && (
                      <span className="filter-count-chip">{stats.allow_count}</span>
                    )}
                    {filterKey === 'REVIEW' && stats && (
                      <span className="filter-count-chip">{stats.review_count}</span>
                    )}
                    {filterKey === 'BLOCK' && stats && (
                      <span className="filter-count-chip">{stats.block_count}</span>
                    )}
                  </button>
                ))}
                <button
                  type="button"
                  className="stream-refresh-btn"
                  onClick={() => fetchHistory(historyFilter)}
                  title="Reload ledger from SQLite"
                >
                  🔄 Refresh
                </button>
              </div>
            </div>

            {historyLoading ? (
              <div className="stream-loading-box">
                <div className="radar-spinner lg"></div>
                <span>Synchronizing Transaction Ledger...</span>
              </div>
            ) : historyItems.length === 0 ? (
              <div className="empty-stream-card">
                <div className="empty-glyph">📂</div>
                <h3>
                  {historyFilter === 'ALL'
                    ? 'No Transactions in Ledger'
                    : `No ${historyFilter} Transactions Found`}
                </h3>
                <p>
                  {historyFilter === 'ALL'
                    ? 'Execute an assessment in the Risk Core or transmit a webhook to populate the stream.'
                    : `No transaction records matching the ${historyFilter} decision policy are currently logged.`}
                </p>
                {historyFilter !== 'ALL' && (
                  <button
                    type="button"
                    className="clear-filter-btn"
                    onClick={() => {
                      setHistoryFilter('ALL')
                      fetchHistory('ALL')
                    }}
                  >
                    View All Transactions
                  </button>
                )}
              </div>
            ) : (
              <div className="stream-table-responsive">
                <table className="stream-data-table">
                  <thead>
                    <tr>
                      <th>Transaction ID</th>
                      <th>Customer</th>
                      <th>Amount</th>
                      <th>Rail</th>
                      <th>Risk Score</th>
                      <th>Policy Decision</th>
                      <th>Channel</th>
                      <th>Timestamp</th>
                      <th>Investigation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyItems.map((tx) => (
                      <tr key={tx.transaction_id} className={`row-decision-${tx.decision.toLowerCase()}`}>
                        <td className="font-mono text-cyan">{tx.transaction_id}</td>
                        <td>{tx.customer_id || '—'}</td>
                        <td className="font-bold">
                          ₹{tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </td>
                        <td>
                          <span className="rail-pill">{tx.payment_method.toUpperCase()}</span>
                        </td>
                        <td>
                          <span className={`score-badge score-sev-${tx.risk_score >= 70 ? 'high' : tx.risk_score >= 40 ? 'med' : 'low'}`}>
                            {tx.risk_score}
                          </span>
                        </td>
                        <td>
                          <span className={`decision-pill sm pill-${tx.decision.toLowerCase()}`}>
                            {tx.decision}
                          </span>
                        </td>
                        <td>
                          <span className="channel-tag">{tx.source}</span>
                        </td>
                        <td className="time-muted">
                          {new Date(tx.created_at).toLocaleTimeString()}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="inspect-core-btn"
                            onClick={() => inspectHistoryItem(tx)}
                          >
                            <span>Load in Core →</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* =========================================================================
            TAB 3: RAZORPAY WEBHOOK LINK TERMINAL
           ========================================================================= */}
        {activeTab === 'webhook' && (
          <section className="cyber-panel webhook-theatre-panel">
            <div className="panel-hud-header">
              <div>
                <span className="hud-corner-tag">WEBHOOK TERMINAL</span>
                <h2>Razorpay Webhook Link & Automated Ingestion</h2>
                <p className="panel-subtext">
                  Demonstrates live HMAC-SHA256 signature verification, atomic idempotency deduplication, and zero-touch ledger ingestion.
                </p>
              </div>
            </div>

            {/* Architecture Pipeline Diagram */}
            <div className="webhook-pipeline-diagram">
              <div className="pipe-step">
                <span className="step-num">1</span>
                <span className="step-txt">RAZORPAY EVENT</span>
              </div>
              <span className="pipe-arrow">➔</span>
              <div className="pipe-step">
                <span className="step-num">2</span>
                <span className="step-txt">HMAC-SHA256 VERIFIED</span>
              </div>
              <span className="pipe-arrow">➔</span>
              <div className="pipe-step">
                <span className="step-num">3</span>
                <span className="step-txt">IDEMPOTENCY CHECK</span>
              </div>
              <span className="pipe-arrow">➔</span>
              <div className="pipe-step">
                <span className="step-num">4</span>
                <span className="step-txt">RISK CORE ML</span>
              </div>
              <span className="pipe-arrow">➔</span>
              <div className="pipe-step">
                <span className="step-num">5</span>
                <span className="step-txt">IMMUTABLE LEDGER</span>
              </div>
            </div>

            {/* Judge Quick-Test Webhook Scenarios */}
            <div className="webhook-scenarios-deck">
              <button
                type="button"
                className="wb-scenario-btn"
                onClick={() => handleWebhookSubmit({ paymentId: 'pay_demo_7821', forceInvalidSig: false })}
                disabled={webhookLoading}
              >
                <span className="wb-btn-icon">⚡</span>
                <div className="wb-btn-text">
                  <strong>1. Valid Ingestion</strong>
                  <small>Signs payload with secret → 200 Scored & Logged</small>
                </div>
              </button>
              <button
                type="button"
                className="wb-scenario-btn"
                onClick={() => handleWebhookSubmit({ paymentId: 'pay_demo_7821', forceInvalidSig: false })}
                disabled={webhookLoading}
              >
                <span className="wb-btn-icon">🔄</span>
                <div className="wb-btn-text">
                  <strong>2. Idempotent Replay</strong>
                  <small>Re-transmits same payment ID → Returns cached result</small>
                </div>
              </button>
              <button
                type="button"
                className="wb-scenario-btn reject-btn"
                onClick={() => handleWebhookSubmit({ paymentId: 'pay_tampered_9999', forceInvalidSig: true })}
                disabled={webhookLoading}
              >
                <span className="wb-btn-icon">🚫</span>
                <div className="wb-btn-text">
                  <strong>3. Tampered Signature</strong>
                  <small>Mismatched HMAC → 401 Unauthorized Rejection</small>
                </div>
              </button>
            </div>

            <div className="webhook-terminal-grid">
              {/* Left Column: Form Simulator */}
              <form onSubmit={(e) => { e.preventDefault(); handleWebhookSubmit(); }} className="webhook-sim-form">
                <div className="field-block single-col">
                  <label htmlFor="wb_pid">Razorpay Payment ID (Idempotency Key)</label>
                  <input
                    id="wb_pid"
                    type="text"
                    required
                    value={webhookPaymentId}
                    onChange={(e) => setWebhookPaymentId(e.target.value)}
                  />
                </div>

                <div className="field-block single-col">
                  <label htmlFor="wb_amt">Payment Amount (INR)</label>
                  <div className="input-wrap">
                    <span className="curr-sym">₹</span>
                    <input
                      id="wb_amt"
                      type="number"
                      step="0.01"
                      min="1"
                      required
                      value={webhookAmount}
                      onChange={(e) => setWebhookAmount(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                </div>

                <div className="field-block single-col">
                  <label htmlFor="wb_method">Payment Method Rail</label>
                  <select
                    id="wb_method"
                    value={webhookMethod}
                    onChange={(e) => setWebhookMethod(e.target.value)}
                  >
                    <option value="card">Card (Credit/Debit)</option>
                    <option value="upi">UPI</option>
                    <option value="netbanking">Net Banking</option>
                    <option value="wallet">Wallet</option>
                  </select>
                </div>

                <div className="field-block single-col">
                  <label htmlFor="wb_sec">Webhook Secret (X-Razorpay-Signature Key)</label>
                  <input
                    id="wb_sec"
                    type="password"
                    value={webhookSecret}
                    onChange={(e) => setWebhookSecret(e.target.value)}
                  />
                </div>

                <button
                  type="submit"
                  disabled={webhookLoading || !readiness.ready}
                  className="cyber-assess-btn webhook-btn"
                >
                  {webhookLoading ? (
                    <span className="btn-glow-pulse">
                      <span className="radar-spinner"></span>
                      <span>Transmitting & Verifying HMAC...</span>
                    </span>
                  ) : (
                    <span>🚀 Transmit Signed Webhook to /api/v1/webhooks/razorpay</span>
                  )}
                </button>
              </form>

              {/* Right Column: Webhook Response Terminal */}
              <div className="webhook-output-terminal">
                <div className="terminal-hud-bar">
                  <span className="term-dot red"></span>
                  <span className="term-dot yellow"></span>
                  <span className="term-dot green"></span>
                  <span className="term-title">API RESPONSE TERMINAL</span>
                </div>

                {webhookError && (
                  <div className="term-error-box">
                    <strong>401 / 500 INGESTION ERROR:</strong>
                    <p>{webhookError}</p>
                  </div>
                )}

                {webhookResult && (
                  <div className="term-result-card">
                    <div className="term-hero-row">
                      <div className="term-score-block">
                        <span className="ts-num">{webhookResult.risk_score}</span>
                        <span className="ts-lbl">/ 100</span>
                      </div>
                      <div className="term-meta-block">
                        <div className="term-badges">
                          <span className={`decision-pill pill-${webhookResult.decision.toLowerCase()}`}>
                            {webhookResult.decision}
                          </span>
                          {webhookResult.idempotent_replay && (
                            <span className="replay-pill">IDEMPOTENT REPLAY</span>
                          )}
                        </div>
                        <span className="term-pid font-mono">Payment ID: {webhookResult.payment_id}</span>
                      </div>
                    </div>

                    {webhookResult.analyst_summary && (
                      <p className="term-summary-text">{webhookResult.analyst_summary}</p>
                    )}

                    <pre className="term-json-code">
                      {JSON.stringify(webhookResult, null, 2)}
                    </pre>
                  </div>
                )}

                {!webhookResult && !webhookError && (
                  <div className="term-standby-box">
                    <span className="standby-glyph">⚡</span>
                    <h4>Ready for Webhook Simulation</h4>
                    <p>
                      Click one of the quick scenario buttons or customize the payload to test timing-safe HMAC validation and automatic ledger logging.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
