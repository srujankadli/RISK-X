import { useState, useEffect } from 'react'

function App() {
  const [backendStatus, setBackendStatus] = useState({
    status: 'checking',
    message: 'Checking connection to backend health endpoint...',
  })

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setBackendStatus({
          status: 'connected',
          message: `${data.service} v${data.version} - ${data.message}`,
        })
      })
      .catch(() => {
        setBackendStatus({
          status: 'disconnected',
          message: 'Backend not running at http://localhost:8000 (Start with: uvicorn app.main:app --port 8000)',
        })
      })
  }, [])

  return (
    <div className="container">
      <div className="card">
        <header className="header">
          <span className="badge">Buildathon Foundation</span>
          <h1>RISK-X</h1>
          <p className="subtitle">Risk Investigation System X</p>
        </header>

        <section className="info-box">
          <h2>Foundation Status</h2>
          <div className={`status-indicator ${backendStatus.status}`}>
            <strong>Backend Connection:</strong> {backendStatus.message}
          </div>
        </section>

        <section className="architecture-preview">
          <h3>Target Pipeline</h3>
          <div className="pipeline-steps">
            <span>Transaction</span>
            <span className="arrow">→</span>
            <span>Detection</span>
            <span className="arrow">→</span>
            <span>Investigation</span>
            <span className="arrow">→</span>
            <span>Evidence</span>
            <span className="arrow">→</span>
            <span>Risk Score</span>
            <span className="arrow">→</span>
            <span>Action</span>
          </div>
        </section>

        <footer className="footer">
          <p>RISK-X Project Foundation Initialized. Ready for Milestone 2.</p>
        </footer>
      </div>
    </div>
  )
}

export default App
