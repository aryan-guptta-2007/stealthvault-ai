import { useState, useEffect, useRef, useCallback, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useNavigate, Link } from 'react-router-dom'
import './index.css'

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api/v1`
const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws`

// ═══ AUTH CONTEXT ═══
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const savedToken = localStorage.getItem('sv_token')
    const savedUser = localStorage.getItem('sv_user')
    if (savedToken && savedUser) {
      setUser({ token: savedToken, ...JSON.parse(savedUser) })
    }
    setLoading(false)
  }, [])

  const login = (token, userData) => {
    localStorage.setItem('sv_token', token)
    localStorage.setItem('sv_user', JSON.stringify(userData))
    setUser({ token, ...userData })
  }

  const logout = () => {
    localStorage.removeItem('sv_token')
    localStorage.removeItem('sv_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

const useAuth = () => useContext(AuthContext)

// ═══ UTILITY ═══
function timeAgo(timestamp) {
  const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000)
  if (seconds < 5) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${Math.floor(seconds / 3600)}h ago`
}

function formatRisk(score) {
  return (score * 100).toFixed(0)
}

// ═══ HOOKS ═══
function useWebSocket() {
  const { user } = useAuth()
  const [connected, setConnected] = useState(false)
  const [lastAlert, setLastAlert] = useState(null)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    try {
      const url = user?.token ? `${WS_URL}?token=${user.token}` : WS_URL
      const ws = new WebSocket(url)
      
      ws.onopen = () => {
        setConnected(true)
        console.log('🔌 WebSocket connected')
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'ALERT') {
          setLastAlert(data.data)
        }
      }
      
      ws.onclose = () => {
        setConnected(false)
        reconnectTimer.current = setTimeout(connect, 3000)
      }
      
      ws.onerror = () => setConnected(false)
      wsRef.current = ws
    } catch {
      setConnected(false)
    }
  }, [user])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  return { connected, lastAlert }
}

function useApi(endpoint, interval = 3000) {
  const { user, logout } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const headers = {}
      if (user?.token) {
        headers['Authorization'] = `Bearer ${user.token}`
      }

      const res = await fetch(`${API_BASE}${endpoint}`, { headers })
      if (res.status === 401) {
        logout()
        return
      }
      if (res.ok) {
        setData(await res.json())
        setLoading(false)
      }
    } catch (err) {
      console.error('API Error:', err)
    }
  }, [endpoint, user, logout])

  useEffect(() => {
    let active = true
    if (active) fetchData()
    const timer = setInterval(() => { if (active) fetchData() }, interval)
    return () => { active = false; clearInterval(timer) }
  }, [fetchData, interval])

  return { data, loading, refetch: fetchData }
}

// ═══ COMPONENTS ═══

function StatCard({ label, value, color, icon }) {
  return (
    <div className={`stat-card ${color}`}>
      <span className="stat-label">{icon} {label}</span>
      <span className={`stat-value ${color}`}>{value ?? '—'}</span>
    </div>
  )
}

function AlertFeed({ alerts, onSelectAlert, selectedAlertId }) {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="brain-empty">
        <div className="brain-empty-icon">🛡️</div>
        <div className="brain-empty-text">No alerts yet.<br />System is monitoring...</div>
      </div>
    )
  }

  return (
    <div>
      {alerts.map((alert) => (
        <div 
          key={alert.id}
          className={`alert-item ${alert.risk?.severity} ${selectedAlertId === alert.id ? 'selected' : ''}`}
          onClick={() => onSelectAlert(alert)}
        >
          <span className={`alert-severity ${alert.risk?.severity}`}>
            {alert.risk?.severity?.toUpperCase()}
          </span>
          <div className="alert-content">
            <div className="alert-type">
              {alert.classification?.attack_type || 'Unknown'}
            </div>
            <div className="alert-meta">
              <span>{alert.packet?.src_ip} → {alert.packet?.dst_ip}</span>
              <span>{timeAgo(alert.timestamp)}</span>
            </div>
          </div>
          <div className={`alert-risk`} style={{ color: riskColor(alert.risk?.score) }}>
            {formatRisk(alert.risk?.score || 0)}
          </div>
        </div>
      ))}
    </div>
  )
}

function riskColor(score) {
  if (score >= 0.85) return 'var(--red)'
  if (score >= 0.65) return 'var(--orange)'
  if (score >= 0.4) return 'var(--yellow)'
  return 'var(--green)'
}

function RiskMeter({ score }) {
  const displayScore = score ?? 0
  const angle = -90 + (displayScore * 180)
  
  return (
    <div className="risk-meter">
      <div className="risk-gauge">
        <div className="risk-gauge-bg" />
        <div 
          className="risk-gauge-fill" 
          style={{ transform: `rotate(${angle}deg)` }}
        />
      </div>
      <div className="risk-score-display" style={{ color: riskColor(displayScore) }}>
        {formatRisk(displayScore)}
      </div>
      <div className="risk-label">Average Risk Score</div>
    </div>
  )
}

function AttackChart({ distribution }) {
  if (!distribution || Object.keys(distribution).length === 0) {
    return <div className="brain-empty-text" style={{ padding: '20px', color: 'var(--text-dim)' }}>No attack data yet</div>
  }

  const maxCount = Math.max(...Object.values(distribution), 1)
  
  const typeStyles = {
    'DDoS': 'ddos',
    'PortScan': 'portscan',
    'BruteForce': 'bruteforce',
    'Malware': 'malware',
    'SQLInjection': 'sql',
    'XSS': 'xss',
  }

  return (
    <div className="attack-chart">
      {Object.entries(distribution).map(([type, count]) => (
        <div key={type} className="attack-bar">
          <span className="attack-bar-label">{type}</span>
          <div className="attack-bar-track">
            <div 
              className={`attack-bar-fill ${typeStyles[type] || 'ddos'}`}
              style={{ width: `${(count / maxCount) * 100}%` }}
            />
          </div>
          <span className="attack-bar-count">{count}</span>
        </div>
      ))}
    </div>
  )
}

function TopAttackers({ attackers }) {
  if (!attackers || attackers.length === 0) {
    return <div className="brain-empty-text" style={{ padding: '20px', color: 'var(--text-dim)' }}>No attackers detected</div>
  }

  return (
    <div>
      {attackers.slice(0, 8).map((attacker, i) => (
        <div key={i} className="attacker-item">
          <span className="attacker-ip">⚡ {attacker.ip}</span>
          <span className="attacker-count">{attacker.count} hits</span>
        </div>
      ))}
    </div>
  )
}

function BrainPanel({ alert, onFeedback }) {
  const { user } = useAuth()
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!alert) {
      setAnalysis(null)
      return
    }

    async function analyze() {
      setLoading(true)
      try {
        const headers = { 'Content-Type': 'application/json' }
        if (user?.token) headers['Authorization'] = `Bearer ${user.token}`

        const res = await fetch(`${API_BASE}/brain/analyze`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ 
            alert_id: alert.id,
            attack_type: alert.classification?.attack_type 
          }),
        })
        if (res.ok) {
          setAnalysis(await res.json())
        }
      } catch {
        // Brain API unavailable
      }
      setLoading(false)
    }

    analyze()
  }, [alert, user])

  const submitFeedback = async (isFP) => {
    setSubmitting(true)
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (user?.token) headers['Authorization'] = `Bearer ${user.token}`

      const res = await fetch(`${API_BASE}/capture/feedback`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          alert_id: alert.id,
          confirmed_label: alert.classification?.attack_type,
          is_false_positive: isFP
        })
      })
      if (res.ok) {
        onFeedback?.(alert.id, isFP)
      }
    } catch (err) {
      console.error('Feedback Error:', err)
    }
    setSubmitting(false)
  }

  if (!alert) {
    return (
      <div className="brain-empty">
        <div className="brain-empty-icon">🧠</div>
        <div className="brain-empty-text">
          Select an alert to get<br />AI-powered threat analysis
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="brain-empty">
        <div className="brain-empty-icon" style={{ animation: 'pulse 1s infinite' }}>🧠</div>
        <div className="brain-empty-text">Analyzing threat...</div>
      </div>
    )
  }

  if (!analysis) return null

  const severityClass = alert.risk?.severity || 'medium'

  return (
    <div className="brain-analysis">
      <div className={`brain-danger ${severityClass}`}>
        {analysis.danger_level}
      </div>

      <div className="brain-section">
        <div className="brain-section-title">🎯 Attack Identified</div>
        <div className="brain-section-content" style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '15px' }}>
          {analysis.attack_name}
        </div>
      </div>

      <div className="brain-section">
        <div className="brain-section-title">⚡ What Is Happening</div>
        <div className="brain-section-content">{analysis.what_is_happening}</div>
      </div>

      <div className="brain-section">
        <div className="brain-section-title">🛡️ How To Stop It</div>
        <div className="brain-section-content">{analysis.how_to_stop}</div>
      </div>

      <div className="brain-section">
        <div className="brain-section-title">📋 Recommended Actions</div>
        <ul className="brain-actions">
          {analysis.recommended_actions?.map((action, i) => (
            <li key={i}>{action}</li>
          ))}
        </ul>
      </div>

      <div className="brain-feedback">
        <div className="brain-section-title">⚖️ Operator Feedback</div>
        <div className="feedback-hint">Your input improves the AI model accuracy over time.</div>
        <div className="feedback-btns">
          <button 
            className="feedback-btn confirm" 
            onClick={() => submitFeedback(false)}
            disabled={submitting}
          >
            CONFIRM ATTACK
          </button>
          <button 
            className="feedback-btn refutation" 
            onClick={() => submitFeedback(true)}
            disabled={submitting}
          >
            FALSE POSITIVE
          </button>
        </div>
      </div>
    </div>
  )
}

function ModelHealth() {
  const { data: metrics, loading } = useApi('/capture/metrics', 5000)
  const { data: status } = useApi('/capture/learning/status', 5000)

  if (loading) return <div className="brain-empty-text">Loading model telemetry...</div>
  if (!metrics || metrics.length === 0) {
    return <div className="brain-empty-text">System is collecting enough sample data to start performance baseline...</div>
  }

  const latest = metrics[0]
  const history = [...metrics].reverse()

  return (
    <div className="model-health">
      <div className="metrics-grid">
        <div className="metric-box">
          <span className="metric-label">Latest Accuracy</span>
          <span className="metric-val">{(latest.accuracy * 100).toFixed(1)}%</span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Model Resolution</span>
          <span className="metric-val">v{latest.version}</span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Precision (Quality)</span>
          <span className="metric-val">{(latest.precision * 100).toFixed(1)}%</span>
        </div>
        <div className="metric-box">
          <span className="metric-label">Recall (Coverage)</span>
          <span className="metric-val">{(latest.recall * 100).toFixed(1)}%</span>
        </div>
      </div>

      <div className="trend-container">
        <div className="trend-title">Performance Trajectory (Last 20 Retrains)</div>
        <div className="trend-chart">
          {history.map((m, i) => (
            <div 
              key={i} 
              className="trend-bar" 
              style={{ height: `${m.accuracy * 100}%` }}
              title={`v${m.version}: ${(m.accuracy * 100).toFixed(1)}%`}
            />
          ))}
        </div>
      </div>

      <div className="learning-status">
        <div className="learning-status-title">Continuous Learning Status</div>
        <div className="status-row">
          <span>Feedback Samples:</span>
          <span className="status-val">{status?.buffer_size} / {status?.retrain_threshold}</span>
        </div>
        <div className="status-progress">
          <div className="status-progress-fill" style={{ width: `${(status?.buffer_size / status?.retrain_threshold) * 100}%` }} />
        </div>
        <div className="status-hint">Target: 500 samples for next neural adjustment.</div>
      </div>
    </div>
  )
}

// ═══ DEFENSE DASHBOARD COMPONENTS ═══

function DefenseView() {
  const { user } = useAuth()
  const { data: stats, refetch: refetchStats } = useApi('/defender/status', 3000)
  const { data: blocks, refetch: refetchBlocks } = useApi('/defender/blocks/active', 3000)
  const [actioning, setActioning] = useState(null)

  const handleAction = async (type, payload = null) => {
    setActioning(type)
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (user?.token) headers['Authorization'] = `Bearer ${user.token}`

      let url = `${API_BASE}/defender`
      if (type === 'arm') url += '/mode/arm'
      if (type === 'disarm') url += '/mode/disarm'
      if (type === 'brake') url += '/mode/emergency-brake'
      if (type === 'unblock') url += `/blocks/unblock/${payload}`

      const res = await fetch(url, { method: 'POST', headers })
      if (res.ok) {
        refetchStats()
        refetchBlocks()
      }
    } catch (err) {
      console.error('Defense Action Error:', err)
    }
    setActioning(null)
  }

  const shadowMode = stats?.shadow_mode ?? true

  return (
    <div className="defense-view">
      <div className="defense-controls">
        <div className="defense-status-card">
          <div className="status-header">
            <span className="status-title">DEFENSE SYSTEM STATUS</span>
            <span className={`status-badge ${shadowMode ? 'shadow' : 'armed'}`}>
              {shadowMode ? 'SHADOW MODE (INACTIVE)' : 'ARMED (ACTIVE)'}
            </span>
          </div>
          <div className="status-desc">
            {shadowMode 
              ? 'Agent is simulating blocks but NOT modifying firewall rules. Safe for testing.'
              : '🚨 WARNING: Agent is autonomously modifying OS firewall rules based on Neural Thresholds.'}
          </div>
          <div className="status-btns">
            <button 
              className={`ctrl-btn ${shadowMode ? 'arm' : 'disarm'}`}
              onClick={() => handleAction(shadowMode ? 'arm' : 'disarm')}
              disabled={actioning !== null}
            >
              {shadowMode ? '⚡ ARM NEURAL DEFENSE' : '🛡️ RETURN TO SHADOW MODE'}
            </button>
            <button 
              className="ctrl-btn emergency"
              onClick={() => handleAction('brake')}
              disabled={actioning !== null}
            >
              🛑 EMERGENCY BRAKE (FLUSH ALL)
            </button>
          </div>
        </div>
      </div>

      <div className="blocks-section">
        <div className="section-title">🛡️ Active Neural Blocks ({blocks?.length || 0})</div>
        <div className="blocks-table-wrapper">
          <table className="blocks-table">
            <thead>
              <tr>
                <th>TARGET IP</th>
                <th>REASON / ATTACK</th>
                <th>CONFIDENCE</th>
                <th>RISK</th>
                <th>EXPIRY</th>
                <th>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {blocks?.map((block, i) => (
                <tr key={i}>
                  <td className="ip-cell">{block.ip}</td>
                  <td>{block.attack_type || block.reason}</td>
                  <td>{(block.confidence * 100).toFixed(0)}%</td>
                  <td style={{ color: riskColor(block.risk) }}>{formatRisk(block.risk)}</td>
                  <td>{block.expires_at ? timeAgo(block.expires_at).replace('ago', 'left') : 'Permanent'}</td>
                  <td>
                    <button className="unblock-mini-btn" onClick={() => handleAction('unblock', block.ip)}>RELEASE</button>
                  </td>
                </tr>
              ))}
              {(!blocks || blocks.length === 0) && (
                <tr>
                  <td colSpan="6" className="empty-row">No active blocks. Neural perimeter is clear.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="defense-history">
        <div className="section-title">📋 Defense Log</div>
        <div className="log-list">
          {stats?.recent_actions?.reverse().map((action, i) => (
            <div key={i} className={`log-item ${action.success ? 'success' : 'fail'}`}>
              <span className="log-time">{new Date(action.timestamp * 1000).toLocaleTimeString()}</span>
              <span className="log-type">[{action.action_type.toUpperCase()}]</span>
              <span className="log-msg">{action.target} — {action.reason}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ═══ PAGES ═══

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const formData = new URLSearchParams()
      formData.append('username', username)
      formData.append('password', password)

      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      })

      const data = await res.json()
      if (res.ok) {
        const userRes = await fetch(`${API_BASE}/saas/tenant`, {
          headers: { 'Authorization': `Bearer ${data.access_token}` }
        })
        if (userRes.ok) {
          const userData = await userRes.json()
          login(data.access_token, { username, ...userData })
          navigate('/')
        }
      } else {
        setError(data.detail || 'Login failed')
      }
    } catch {
      setError('Connection refused by security grid.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-brand">
            <div className="auth-logo">SV</div>
            <div className="auth-title">StealthVault AI</div>
          </div>
          <p className="auth-subtitle">Initialize neural command connection to your security perimeter.</p>
        </div>
        {error && <div className="auth-error">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label className="auth-label">Operator Identity</label>
            <input className="auth-input" type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
          </div>
          <div className="auth-field">
            <label className="auth-label">Access Key</label>
            <input className="auth-input" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Decrypting...' : 'Authorize Access'}
          </button>
        </form>
        <div className="auth-footer">New sector? <Link to="/register" className="auth-link">Provision Tenant</Link></div>
      </div>
    </div>
  )
}

function RegisterPage() {
  const [tenantName, setTenantName] = useState('')
  const [adminUser, setAdminUser] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/saas/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_name: tenantName,
          admin_username: adminUser,
          admin_password: password
        })
      })

      const data = await res.json()
      if (res.ok) {
        navigate('/login')
      } else {
        setError(data.detail || 'Registration failed')
      }
    } catch {
      setError('Failed to provision environment.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-brand">
            <div className="auth-logo">SV</div>
            <div className="auth-title">StealthVault AI</div>
          </div>
          <p className="auth-subtitle">Provision your isolated enterprise SaaS environment.</p>
        </div>
        {error && <div className="auth-error">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-field">
            <label className="auth-label">Organization / Tenant Name</label>
            <input className="auth-input" type="text" placeholder="e.g. CyberDyne Systems" value={tenantName} onChange={(e) => setTenantName(e.target.value)} required />
          </div>
          <div className="auth-field">
            <label className="auth-label">Admin Username</label>
            <input className="auth-input" type="text" placeholder="admin_prime" value={adminUser} onChange={(e) => setAdminUser(e.target.value)} required />
          </div>
          <div className="auth-field">
            <label className="auth-label">Global Access Key</label>
            <input className="auth-input" type="password" placeholder="Min 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Provisioning...' : 'Deploy Environment'}
          </button>
        </form>
        <div className="auth-footer">Already verified? <Link to="/login" className="auth-link">Connect to Sector</Link></div>
      </div>
    </div>
  )
}

function Dashboard() {
  const [selectedAlert, setSelectedAlert] = useState(null)
  const [view, setView] = useState('alerts') // 'alerts' | 'health' | 'defense'
  const { user, logout } = useAuth()
  const { connected, lastAlert } = useWebSocket()
  const { data: dashboard } = useApi('/dashboard', 2000)
  const { data: alerts, refetch: refetchAlerts } = useApi('/alerts?limit=50', 2000)
  const { data: captureStatus } = useApi('/capture/status', 5000)
  const { data: defenderStatus } = useApi('/defender/status', 3000)
  const { data: storiesData } = useApi('/soc/stories', 3000)

  const stories = storiesData?.stories || []

  useEffect(() => {
    if (!selectedAlert && alerts && alerts.length > 0) {
      setSelectedAlert(alerts[0])
    }
  }, [alerts, selectedAlert])

  const handleFeedback = (alertId, isFP) => {
    refetchAlerts()
  }

  const modelVersion = captureStatus?.learner?.model_version || 1
  const pps = captureStatus?.processor?.packets_per_second || 0
  const isArmed = defenderStatus?.shadow_mode === false

  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">SV</div>
          <span className="topbar-title">StealthVault AI</span>
        </div>
        
        <div className="topbar-status">
          <div className="status-indicator">
            <span className={`status-dot ${connected ? 'active' : 'error'}`} />
            <span>{connected ? 'LIVE' : 'OFFLINE'}</span>
          </div>
          <div className="status-indicator" onClick={() => setView('defense')} style={{ cursor: 'pointer' }}>
            <span className={`status-dot ${isArmed ? 'armed' : 'warning'}`} />
            <span>{isArmed ? 'DEFENSE ARMED' : 'SHADOW MODE'}</span>
          </div>
          <div className="status-indicator">
            <span className={`status-dot ${pps > 0 ? 'active' : 'warning'}`} />
            <span>{pps} pkt/s</span>
          </div>
          <span className="model-version" onClick={() => setView('health')} style={{ cursor: 'pointer' }}>
            AI Health: v{modelVersion}
          </span>
          
          <div className="user-profile">
            <div className="user-info">
              <span className="user-name">{user?.username}</span>
              <span className="tenant-tag">{user?.name}</span>
            </div>
            <button className="logout-btn" onClick={logout}>LOGOUT</button>
          </div>
        </div>
      </header>

      <main className="dashboard">
        <div className="stats-row">
          <StatCard icon="📊" label="Packets Analyzed" value={dashboard?.total_packets_analyzed?.toLocaleString()} color="cyan" />
          <StatCard icon="🚨" label="Total Alerts" value={dashboard?.total_alerts} color="orange" />
          <StatCard icon="🔴" label="Critical" value={dashboard?.critical_alerts} color="red" />
          <StatCard icon="🟠" label="High" value={dashboard?.high_alerts} color="orange" />
          <StatCard icon="🟡" label="Medium" value={dashboard?.medium_alerts} color="yellow" />
          <StatCard icon="🟢" label="Low" value={dashboard?.low_alerts} color="green" />
        </div>

        <div className="panel" style={{ gridRow: '2 / 3' }}>
          <div className="panel-header">
            <div className="panel-tabs">
              <button className={`panel-tab ${view === 'alerts' ? 'active' : ''}`} onClick={() => setView('alerts')}>ALERTS</button>
              <button className={`panel-tab ${view === 'health' ? 'active' : ''}`} onClick={() => setView('health')}>AI HEALTH</button>
              <button className={`panel-tab ${view === 'defense' ? 'active' : ''}`} onClick={() => setView('defense')}>DEFENSE</button>
            </div>
            {view === 'alerts' && <span className="panel-badge live">● LIVE</span>}
            {view === 'defense' && <span className={`panel-badge ${isArmed ? 'armed' : 'warning'}`}>{isArmed ? 'ARMED' : 'SHADOW'}</span>}
          </div>
          <div className="panel-body">
            {view === 'alerts' && <AlertFeed alerts={alerts} onSelectAlert={setSelectedAlert} selectedAlertId={selectedAlert?.id} />}
            {view === 'health' && <ModelHealth />}
            {view === 'defense' && <DefenseView />}
          </div>
        </div>

        <div className="center-column" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)', overflowY: 'auto', paddingRight: '4px' }}>
          {stories?.length > 0 && (
            <div className="panel" style={{ flex: '0 0 auto', borderColor: 'var(--purple)', boxShadow: 'var(--purple-dim) 0px 0px 15px' }}>
              <div className="panel-header" style={{ background: 'linear-gradient(90deg, var(--bg-card), var(--purple-dim))' }}>
                <span className="panel-title" style={{ color: 'var(--purple)' }}>
                  <span className="icon">🎬</span> Live Attack Stories
                </span>
              </div>
              <div className="panel-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px' }}>
                {stories.map(story => (
                  <div key={story.story_id} className="story-card">
                    <div className="story-header">
                      <div className="story-title">{story.title}</div>
                      <div className="story-meta">{story.duration} • {story.total_events} events • <span style={{color: 'var(--orange)'}}>{story.sophistication}</span></div>
                    </div>
                    <div className="story-phases">
                      {story.phases?.map((phase, i) => (
                        <div key={i} className={`story-phase ${phase.is_predicted ? 'predicted' : ''}`}>
                          <div className="phase-icon">{phase.icon}</div>
                          <div className="phase-content">
                            <div className="phase-name">Phase {phase.phase}: {phase.name} {phase.is_predicted && <span className="pred-badge">PREDICTED</span>}</div>
                            <div className="phase-narrative">{phase.narrative}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="story-insight"><span className="insight-icon">🧠</span><span>{story.ai_insight}</span></div>
                    <div className="story-action"><span className="action-icon">🛡️</span><span>{story.defense_action}</span></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 'var(--gap)', flex: '0 0 auto' }}>
            <div className="panel" style={{ flex: 1 }}>
              <div className="panel-header"><span className="panel-title"><span className="icon">⚡</span> Threat Level</span></div>
              <RiskMeter score={dashboard?.avg_risk_score} />
            </div>
          </div>

          <div className="panel" style={{ flex: 1 }}>
            <div className="panel-header"><span className="panel-title"><span className="icon">📈</span> Attack Distribution</span></div>
            <div className="panel-body">
              <AttackChart distribution={dashboard?.attack_distribution} />
              <div style={{ marginTop: '16px' }}>
                <div className="panel-title" style={{ marginBottom: '10px', padding: '0 2px' }}><span className="icon">🎯</span> Top Attackers</div>
                <TopAttackers attackers={dashboard?.top_attackers} />
              </div>
            </div>
          </div>
        </div>

        <div className="panel brain-panel">
          <div className="panel-header">
            <span className="panel-title"><span className="icon">🧠</span> AI Security Brain</span>
          </div>
          <div className="panel-body">
            <BrainPanel alert={selectedAlert} onFeedback={handleFeedback} />
          </div>
        </div>
      </main>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
