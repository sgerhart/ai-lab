import { Activity, CheckCircle, Database, Flame, HardDrive, Play, Server, Zap } from 'lucide-react'
import type { CheckpointItem, ExperimentRun, HostHealth, ViewType } from '../types'

interface DashboardViewProps {
  hosts: HostHealth[]
  checkpoints: CheckpointItem[]
  experiments: ExperimentRun[]
  onNavigate: (view: ViewType) => void
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  hosts,
  checkpoints,
  experiments,
  onNavigate,
}) => {
  return (
    <div className="dashboard-view">
      {/* Platform KPI Grid */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Curated Tasks</span>
            <Database size={18} color="var(--accent)" />
          </div>
          <div className="kpi-value">105</div>
          <div className="kpi-subtitle">75 Train · 15 Val · 15 Test</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Base Model Pass@1</span>
            <Activity size={18} color="var(--warn)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--warn)' }}>0.0%</div>
          <div className="kpi-subtitle">Untrained Mock / Qwen3-0.6B</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Tuned Pass@1 (Ceiling)</span>
            <Zap size={18} color="var(--live)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--live)' }}>100.0%</div>
          <div className="kpi-subtitle">Holdout Validation & Test</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Verified Adapters</span>
            <HardDrive size={18} color="var(--purple)" />
          </div>
          <div className="kpi-value" style={{ color: 'var(--purple)' }}>{checkpoints.length}</div>
          <div className="kpi-subtitle">SFT LoRA & RL GRPO Checkpoints</div>
        </div>
      </div>

      {/* Host Health & Infrastructure Panel */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="panel-title">
            <Server size={18} color="var(--accent)" />
            Distributed Training Topology
          </h2>
          <span className="badge badge-live">All Hosts Operational</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          {hosts.map((host) => (
            <div
              key={host.name}
              style={{
                background: '#090d16',
                border: '1px solid var(--line)',
                borderRadius: '8px',
                padding: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--ink)' }}>{host.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{host.role}</div>
                </div>
                <span className="badge badge-live">
                  <span className="status-dot healthy" />
                  {host.status}
                </span>
              </div>

              <div style={{ display: 'flex', gap: '16px', fontSize: '11px', color: 'var(--ink-secondary)', margin: '12px 0' }}>
                <div>
                  <span style={{ color: 'var(--muted)' }}>Endpoint: </span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{host.host}:{host.port}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--muted)' }}>Latency: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>{host.latencyMs}ms</span>
                </div>
                <div>
                  <span style={{ color: 'var(--muted)' }}>Uptime: </span>
                  <span>{host.uptime}</span>
                </div>
              </div>

              {host.details && (
                <div style={{ borderTop: '1px solid var(--line)', paddingTop: '10px', fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {Object.entries(host.details).map(([k, v]) => (
                    <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--muted)' }}>{k}:</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-secondary)' }}>{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Launch & Recent Runs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '20px' }}>
        {/* Quick Launch Actions */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <Play size={16} color="var(--accent)" />
              Operator Quick Actions
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px',
                background: '#090d16',
                border: '1px solid var(--line)',
                borderRadius: '8px',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Model Playground Testing</div>
                <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Prompt candidate code, execute in Linux sandbox, inspect unit tests</div>
              </div>
              <button className="btn btn-secondary" onClick={() => onNavigate('playground')}>
                Open Playground
              </button>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px',
                background: '#090d16',
                border: '1px solid var(--line)',
                borderRadius: '8px',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Launch Training Experiment</div>
                <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Configure SFT LoRA or GRPO on Apple Silicon with approval gate</div>
              </div>
              <button className="btn btn-primary" onClick={() => onNavigate('experiments')}>
                New Experiment
              </button>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px',
                background: '#090d16',
                border: '1px solid var(--line)',
                borderRadius: '8px',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '13px' }}>Browse Curated Tasks</div>
                <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Explore 105 tasks across train/validation/test splits</div>
              </div>
              <button className="btn btn-secondary" onClick={() => onNavigate('datasets')}>
                Browse Datasets
              </button>
            </div>
          </div>
        </div>

        {/* Recent Training Runs */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <Flame size={16} color="var(--purple)" />
              Recent Training Runs
            </h3>
            <button className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '11px' }} onClick={() => onNavigate('experiments')}>
              View All
            </button>
          </div>

          <table className="console-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Type</th>
                <th>Steps</th>
                <th>Pass@1</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((exp) => (
                <tr key={exp.run_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent)' }}>
                    {exp.run_id}
                  </td>
                  <td>
                    <span className={`badge ${exp.type.includes('SFT') ? 'badge-purple' : 'badge-accent'}`}>
                      {exp.type.split(' ')[0]}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>
                    {exp.steps_completed} / {exp.max_steps}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--live)' }}>
                    {(exp.holdout_pass1 * 100).toFixed(1)}%
                  </td>
                  <td>
                    <span className="badge badge-live">
                      <CheckCircle size={10} />
                      {exp.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
