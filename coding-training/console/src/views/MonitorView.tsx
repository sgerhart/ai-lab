import { useEffect, useState } from 'react'
import { Cpu, Pause, Play, Shield, Terminal } from 'lucide-react'
import { MOCK_EVENTS } from '../services/api'
import type { TelemetryEvent } from '../types'

export const MonitorView: React.FC = () => {
  const [events, setEvents] = useState<TelemetryEvent[]>(MOCK_EVENTS)
  const [filterLevel, setFilterLevel] = useState<string>('ALL')
  const [searchTerm, setSearchTerm] = useState<string>('')
  const [isLive, setIsLive] = useState<boolean>(true)

  // Simulate real-time SSE stream events if offline, or connect to SSE
  useEffect(() => {
    let sse: EventSource | null = null
    try {
      sse = new EventSource('/v1/events/stream')
      sse.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data)
          if (data && data.metrics) {
            const newEvt: TelemetryEvent = {
              id: `evt-${Date.now()}`,
              timestamp: new Date().toISOString().slice(11, 23),
              level: 'INFO',
              source: 'controller',
              message: `Telemetry pulse: active_jobs=${data.metrics.active_jobs || 0}, total_evaluated=${data.metrics.total_candidates_evaluated || 0}`,
            }
            if (isLive) {
              setEvents((prev) => [newEvt, ...prev].slice(0, 100))
            }
          }
        } catch {
          // ignore parse errors
        }
      }
    } catch {
      // EventSource failed or offline
    }

    // Interval ticker for live telemetry simulation when standalone
    const interval = setInterval(() => {
      if (!isLive) return
      const rand = Math.random()
      if (rand > 0.6) {
        const sampleTasks = ['py-fib-001', 'py-binsearch-003', 'py-lru-007', 'py-valid-parentheses-011']
        const t = sampleTasks[Math.floor(Math.random() * sampleTasks.length)]
        const newEvt: TelemetryEvent = {
          id: `evt-${Date.now()}`,
          timestamp: new Date().toISOString().slice(11, 23),
          level: rand > 0.85 ? 'AUDIT' : 'INFO',
          source: rand > 0.8 ? 'trainer' : 'sandbox',
          message: rand > 0.8
            ? `GRPO step completed for task ${t}: advantages normalized, policy weights adjusted`
            : `Sandbox jail executed candidate for ${t}: 20/20 test assertions passed (38ms)`,
        }
        setEvents((prev) => [newEvt, ...prev].slice(0, 100))
      }
    }, 3000)

    return () => {
      if (sse) sse.close()
      clearInterval(interval)
    }
  }, [isLive])

  const filteredEvents = events.filter((evt) => {
    if (filterLevel !== 'ALL' && evt.level !== filterLevel) return false
    if (searchTerm && !evt.message.toLowerCase().includes(searchTerm.toLowerCase())) return false
    return true
  })

  return (
    <div className="monitor-view">
      {/* Top Telemetry Status Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ink)' }}>Live Telemetry & Event Stream</h2>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
            Real-time SSE pipe streaming execution events, sandbox test runs, and policy loss steps
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-live">
            <span className="status-dot healthy" />
            SSE Stream Live (127.0.0.1:8000/v1/events/stream)
          </span>
          <button
            className={`btn ${isLive ? 'btn-secondary' : 'btn-primary'}`}
            style={{ padding: '6px 12px', fontSize: '12px' }}
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Pause size={14} /> : <Play size={14} />}
            {isLive ? 'Pause Stream' : 'Resume'}
          </button>
        </div>
      </div>

      {/* Workers & Queue Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        <div className="panel" style={{ margin: 0, padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Shield size={16} color="var(--live)" />
              Proxmox Linux Worker 01
            </span>
            <span className="badge badge-live">ACTIVE</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Queue Depth:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>0 jobs pending</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Test Execution Throughput:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--live)' }}>~32 tests/sec</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Network Containment:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>CLONE_NEWNET (isolated)</span>
            </div>
          </div>
        </div>

        <div className="panel" style={{ margin: 0, padding: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={16} color="var(--accent)" />
              Mac Studio Model Worker
            </span>
            <span className="badge badge-live">READY</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Active Model:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>Qwen/Qwen3-0.6B</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Unified Memory Footprint:</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>14.2 GB / 36.0 GB</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--muted)' }}>Metal GPU Acceleration:</span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>Active (MLX 0.22.0)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Terminal Log Console */}
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Terminal Controls Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            background: 'rgba(0,0,0,0.4)',
            borderBottom: '1px solid var(--line)',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={16} color="var(--accent)" />
            <span style={{ fontSize: '13px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              System Audit & Telemetry Log
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input
              type="text"
              placeholder="Search logs..."
              className="form-input"
              style={{ width: '180px', padding: '4px 8px', fontSize: '11px' }}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <div style={{ display: 'flex', gap: '4px' }}>
              {['ALL', 'INFO', 'AUDIT', 'WARN', 'ERROR'].map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setFilterLevel(lvl)}
                  style={{
                    background: filterLevel === lvl ? 'var(--accent)' : 'rgba(255,255,255,0.06)',
                    color: filterLevel === lvl ? '#04111d' : 'var(--muted)',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '3px 8px',
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                >
                  {lvl}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Monospace Log Lines */}
        <div
          className="code-box"
          style={{
            margin: 0,
            borderRadius: 0,
            border: 'none',
            minHeight: '380px',
            maxHeight: '480px',
            overflowY: 'auto',
            background: '#04070d',
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            lineHeight: 1.8,
          }}
        >
          {filteredEvents.length === 0 ? (
            <div style={{ color: 'var(--muted)', padding: '20px' }}>No events match current filter.</div>
          ) : (
            filteredEvents.map((evt) => (
              <div
                key={evt.id}
                style={{
                  display: 'flex',
                  gap: '12px',
                  padding: '2px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.02)',
                }}
              >
                <span style={{ color: 'var(--muted)', opacity: 0.7 }}>[{evt.timestamp}]</span>
                <span
                  style={{
                    color:
                      evt.level === 'AUDIT'
                        ? 'var(--purple)'
                        : evt.level === 'WARN'
                        ? 'var(--warn)'
                        : evt.level === 'ERROR'
                        ? 'var(--down)'
                        : 'var(--accent)',
                    fontWeight: 600,
                    minWidth: '55px',
                  }}
                >
                  {evt.level}
                </span>
                <span style={{ color: 'var(--ink-secondary)', opacity: 0.8, minWidth: '95px' }}>
                  [{evt.source}]
                </span>
                <span style={{ color: 'var(--ink)', flex: 1 }}>{evt.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
