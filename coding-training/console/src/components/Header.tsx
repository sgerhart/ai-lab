import { Activity, Cpu, Server, Shield } from 'lucide-react'
import type { HostHealth, ViewType } from '../types'

interface HeaderProps {
  hosts: HostHealth[]
  currentView: ViewType
  onSelectView: (view: ViewType) => void
}

export const Header: React.FC<HeaderProps> = ({ hosts, currentView, onSelectView }) => {
  return (
    <header className="console-header">
      <div className="header-inner">
        <div className="brand-section">
          <div className="brand-icon-box">
            <Cpu size={20} />
          </div>
          <div className="brand-title-group">
            <h1>AI Lab Coding Training Console</h1>
            <p>FEAT-024 / WO-10 — Execution-Verified LLM Alignment</p>
          </div>
        </div>

        <div className="header-hosts-bar">
          {hosts.map((h) => (
            <div key={h.name} className="host-badge" title={`${h.name} (${h.host}:${h.port}) - ${h.role}`}>
              <span className={`status-dot ${h.status}`} />
              <span>{h.name.split(' ')[0]}</span>
              <span style={{ opacity: 0.6 }}>{h.port}</span>
            </div>
          ))}
          <div className="host-badge" style={{ borderColor: 'rgba(56, 189, 248, 0.3)', color: 'var(--accent)' }}>
            <Shield size={12} />
            <span>Air-Gapped Sandbox</span>
          </div>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${currentView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onSelectView('dashboard')}
        >
          <Activity size={16} />
          Dashboard
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'playground' ? 'active' : ''}`}
          onClick={() => onSelectView('playground')}
        >
          <Cpu size={16} />
          Playground
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'experiments' ? 'active' : ''}`}
          onClick={() => onSelectView('experiments')}
        >
          <Server size={16} />
          Experiments
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'monitor' ? 'active' : ''}`}
          onClick={() => onSelectView('monitor')}
        >
          <Activity size={16} />
          Live Monitor
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'models' ? 'active' : ''}`}
          onClick={() => onSelectView('models')}
        >
          <Cpu size={16} />
          Models & Checkpoints
        </button>
        <button
          className={`nav-tab-btn ${currentView === 'datasets' ? 'active' : ''}`}
          onClick={() => onSelectView('datasets')}
        >
          <Shield size={16} />
          Datasets & Tasks
        </button>
      </nav>
    </header>
  )
}
