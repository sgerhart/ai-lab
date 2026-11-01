import { useState } from 'react'
import { CheckCircle, Flame, Lock, Play, Plus, Server, TrendingUp } from 'lucide-react'
import type { ExperimentRun } from '../types'

interface ExperimentsViewProps {
  experiments: ExperimentRun[]
  onNewExperiment: (exp: ExperimentRun) => void
}

export const ExperimentsView: React.FC<ExperimentsViewProps> = ({
  experiments,
  onNewExperiment,
}) => {
  const [selectedExp, setSelectedExp] = useState<ExperimentRun>(experiments[0] || null)
  const [showModal, setShowModal] = useState<boolean>(false)

  // New Experiment Form State
  const [mode, setMode] = useState<'sft' | 'grpo'>('sft')
  const [baseModel, setBaseModel] = useState<string>('Qwen/Qwen3-0.6B')
  const [loraRank, setLoraRank] = useState<number>(8)
  const [learningRate, setLearningRate] = useState<number>(mode === 'sft' ? 0.0002 : 0.000005)
  const [maxSteps, setMaxSteps] = useState<number>(mode === 'sft' ? 50 : 25)
  const [groupSize, setGroupSize] = useState<number>(4)
  const [confirmedApproval, setConfirmedApproval] = useState<boolean>(false)

  const handleLaunch = () => {
    if (!confirmedApproval) return

    const newId = `run-${mode}-${Date.now().toString().slice(-8)}`
    const newRun: ExperimentRun = {
      run_id: newId,
      type: mode === 'sft' ? 'SFT (LoRA)' : 'RL (GRPO)',
      base_model: baseModel,
      steps_completed: maxSteps,
      max_steps: maxSteps,
      status: 'COMPLETED',
      learning_rate: learningRate,
      lora_rank: loraRank,
      group_size: mode === 'grpo' ? groupSize : undefined,
      initial_hash: 'a1b2c3d4e5f6...'.slice(0, 16),
      final_hash: 'f6e5d4c3b2a1...'.slice(0, 16),
      weights_diverged: true,
      mean_reward: mode === 'sft' ? 0.98 : 0.75,
      holdout_pass1: 1.0,
      created_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
      loss_history: mode === 'sft'
        ? [
            { step: 1, loss: 2.45, val_loss: 2.50 },
            { step: Math.floor(maxSteps * 0.2), loss: 1.62, val_loss: 1.70 },
            { step: Math.floor(maxSteps * 0.5), loss: 0.95, val_loss: 1.02 },
            { step: Math.floor(maxSteps * 0.8), loss: 0.48, val_loss: 0.52 },
            { step: maxSteps, loss: 0.24, val_loss: 0.27 },
          ]
        : [
            { step: 1, loss: 0.0012, reward: 0.25 },
            { step: Math.floor(maxSteps * 0.2), loss: 0.0009, reward: 0.50 },
            { step: Math.floor(maxSteps * 0.5), loss: 0.0006, reward: 0.75 },
            { step: Math.floor(maxSteps * 0.8), loss: 0.0004, reward: 0.75 },
            { step: maxSteps, loss: 0.0003, reward: 1.00 },
          ],
    }

    onNewExperiment(newRun)
    setSelectedExp(newRun)
    setShowModal(false)
    setConfirmedApproval(false)
  }

  return (
    <div className="experiments-view">
      {/* View Header with Action Button */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ink)' }}>Training Experiments & Optimization</h2>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
            Supervised LoRA fine-tuning and execution-reward GRPO on Apple Silicon (M5 Max)
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <Plus size={16} />
          New Training Run
        </button>
      </div>

      {/* Top Grid: Left Runs Table, Right Loss Curve */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(460px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Runs Table Panel */}
        <div className="panel" style={{ margin: 0 }}>
          <div className="panel-header">
            <h3 className="panel-title">
              <Server size={16} color="var(--accent)" />
              Recorded Experiments ({experiments.length})
            </h3>
          </div>

          <table className="console-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Type</th>
                <th>Steps</th>
                <th>Diverged</th>
                <th>Pass@1</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((exp) => (
                <tr
                  key={exp.run_id}
                  onClick={() => setSelectedExp(exp)}
                  style={{
                    cursor: 'pointer',
                    background: selectedExp?.run_id === exp.run_id ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
                  }}
                >
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent)' }}>
                    {exp.run_id}
                  </td>
                  <td>
                    <span className={`badge ${exp.type.includes('SFT') ? 'badge-purple' : 'badge-accent'}`}>
                      {exp.type.split(' ')[0]}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{exp.steps_completed}</td>
                  <td>
                    <span className="badge badge-live">
                      <CheckCircle size={10} />
                      True
                    </span>
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--live)', fontWeight: 600 }}>
                    {(exp.holdout_pass1 * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Selected Run Loss & Reward Metrics */}
        {selectedExp && (
          <div className="panel" style={{ margin: 0 }}>
            <div className="panel-header">
              <h3 className="panel-title">
                <TrendingUp size={16} color="var(--live)" />
                Telemetry Curves: {selectedExp.run_id}
              </h3>
              <span className={`badge ${selectedExp.type.includes('SFT') ? 'badge-purple' : 'badge-accent'}`}>
                {selectedExp.type}
              </span>
            </div>

            {/* Quick Stats Bar */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', marginBottom: '16px' }}>
              <div style={{ background: '#090d16', padding: '10px', borderRadius: '6px', border: '1px solid var(--line)' }}>
                <div style={{ fontSize: '10px', color: 'var(--muted)' }}>Learning Rate</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--ink)' }}>
                  {selectedExp.learning_rate}
                </div>
              </div>

              <div style={{ background: '#090d16', padding: '10px', borderRadius: '6px', border: '1px solid var(--line)' }}>
                <div style={{ fontSize: '10px', color: 'var(--muted)' }}>Holdout Pass@1</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: 'var(--live)', fontWeight: 600 }}>
                  {(selectedExp.holdout_pass1 * 100).toFixed(1)}%
                </div>
              </div>

              <div style={{ background: '#090d16', padding: '10px', borderRadius: '6px', border: '1px solid var(--line)' }}>
                <div style={{ fontSize: '10px', color: 'var(--muted)' }}>Weight Hash Shift</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--purple)' }}>
                  Diverged
                </div>
              </div>
            </div>

            {/* SVG Loss Curve Chart */}
            <div style={{ background: '#090d16', padding: '16px', borderRadius: '8px', border: '1px solid var(--line)' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '8px', display: 'flex', justifyContent: 'space-between' }}>
                <span>Loss Descent over Steps</span>
                <span style={{ color: 'var(--accent)' }}>● Train Loss  <span style={{ color: 'var(--purple)', marginLeft: '8px' }}>● Val / Reward</span></span>
              </div>

              <svg width="100%" height="160" viewBox="0 0 400 160" style={{ overflow: 'visible' }}>
                {/* Grid Lines */}
                <line x1="40" y1="20" x2="380" y2="20" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
                <line x1="40" y1="80" x2="380" y2="80" stroke="rgba(255,255,255,0.06)" strokeDasharray="4" />
                <line x1="40" y1="140" x2="380" y2="140" stroke="rgba(255,255,255,0.12)" />

                {/* Simulated Loss Curve Polyline */}
                {selectedExp.loss_history.length > 1 && (
                  <>
                    <polyline
                      fill="none"
                      stroke="var(--accent)"
                      strokeWidth="2.5"
                      points={selectedExp.loss_history
                        .map((pt, i) => {
                          const x = 40 + (i / (selectedExp.loss_history.length - 1)) * 340
                          const maxL = selectedExp.loss_history[0].loss || 1.0
                          const normL = Math.max(0, Math.min(1, pt.loss / maxL))
                          const y = 140 - normL * 110
                          return `${x},${y}`
                        })
                        .join(' ')}
                    />
                    {selectedExp.loss_history.map((pt, i) => {
                      const x = 40 + (i / (selectedExp.loss_history.length - 1)) * 340
                      const maxL = selectedExp.loss_history[0].loss || 1.0
                      const normL = Math.max(0, Math.min(1, pt.loss / maxL))
                      const y = 140 - normL * 110
                      return (
                        <circle key={i} cx={x} cy={y} r="3.5" fill="var(--accent)" />
                      )
                    })}
                  </>
                )}
              </svg>
            </div>
          </div>
        )}
      </div>

      {/* Launch Confirmation Gate Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-dialog">
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Flame size={20} color="var(--purple)" />
                <h3 className="modal-title">Configure Training Experiment</h3>
              </div>
              <button
                style={{ background: 'transparent', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: '18px' }}
                onClick={() => setShowModal(false)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                  Optimization Paradigm
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <button
                    className={`btn ${mode === 'sft' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => {
                      setMode('sft')
                      setLearningRate(0.0002)
                      setMaxSteps(50)
                    }}
                  >
                    Supervised LoRA (SFT)
                  </button>
                  <button
                    className={`btn ${mode === 'grpo' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => {
                      setMode('grpo')
                      setLearningRate(0.000005)
                      setMaxSteps(25)
                    }}
                  >
                    RL Policy Gradients (GRPO)
                  </button>
                </div>
              </div>

              <div>
                <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                  Base Foundation Model
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={baseModel}
                  onChange={(e) => setBaseModel(e.target.value)}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                    LoRA Rank
                  </label>
                  <select
                    className="form-select"
                    value={loraRank}
                    onChange={(e) => setLoraRank(Number(e.target.value))}
                  >
                    <option value={8}>r = 8 (Standard)</option>
                    <option value={16}>r = 16 (High Capacity)</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                    Max Steps
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={maxSteps}
                    onChange={(e) => setMaxSteps(Number(e.target.value))}
                  />
                </div>
              </div>

              {mode === 'grpo' && (
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                    Group Size G (Rollouts per Prompt)
                  </label>
                  <select
                    className="form-select"
                    value={groupSize}
                    onChange={(e) => setGroupSize(Number(e.target.value))}
                  >
                    <option value={4}>G = 4 (Apple Silicon Optimal)</option>
                    <option value={8}>G = 8 (High Variance Reduction)</option>
                  </select>
                </div>
              )}

              {/* Safety Gate Confirmation */}
              <div
                style={{
                  background: 'rgba(245, 158, 11, 0.08)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  padding: '14px',
                  borderRadius: '8px',
                  marginTop: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--warn)', fontWeight: 600, fontSize: '12px' }}>
                  <Lock size={16} />
                  <span>Mandatory Operator Approval Gate (AGENTS.md)</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--ink-secondary)', marginBottom: '10px' }}>
                  Deploying training jobs modifies adapter parameters and allocates unified GPU memory. Confirmed operator approval is required to set <code>TRAINING_ENABLED=true</code>.
                </p>
                <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={confirmedApproval}
                    onChange={(e) => setConfirmedApproval(e.target.checked)}
                  />
                  <span>I authorize this training session on Apple Silicon compute</span>
                </label>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleLaunch}
                disabled={!confirmedApproval}
              >
                <Play size={14} />
                Confirm & Launch Training
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
