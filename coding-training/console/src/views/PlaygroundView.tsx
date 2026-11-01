import { useState } from 'react'
import { Code, Cpu, Play, Shield, Terminal } from 'lucide-react'
import { api } from '../services/api'
import type { ExecutionResultSummary, TaskItem } from '../types'

interface PlaygroundViewProps {
  tasks: TaskItem[]
}

export const PlaygroundView: React.FC<PlaygroundViewProps> = ({ tasks }) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string>(tasks[0]?.task_id || 'py-fib-001')
  const [selectedModel, setSelectedModel] = useState<string>('Qwen/Qwen3-0.6B + SFT LoRA (ckpt-step50)')
  const [prompt, setPrompt] = useState<string>(tasks[0]?.prompt || 'Implement nth Fibonacci number calculation.')
  const [code, setCode] = useState<string>(
    'def fibonacci(n: int) -> int:\n    """Computes nth Fibonacci number using dynamic programming."""\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n'
  )
  const [isGenerating, setIsGenerating] = useState<boolean>(false)
  const [isExecuting, setIsExecuting] = useState<boolean>(false)
  const [result, setResult] = useState<ExecutionResultSummary | null>(null)

  const handleSelectTask = (taskId: string) => {
    setSelectedTaskId(taskId)
    const task = tasks.find((t) => t.task_id === taskId)
    if (task) {
      setPrompt(task.prompt)
      setCode(`${task.function_contract}\n    # Complete implementation here\n    pass\n`)
      setResult(null)
    }
  }

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const generated = await api.generateCode(prompt, selectedModel)
      setCode(generated)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExecute = async () => {
    setIsExecuting(true)
    try {
      const execResult = await api.executeInSandbox(selectedTaskId, code)
      setResult(execResult)
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="playground-view">
      {/* Top Configuration Bar */}
      <div className="panel" style={{ padding: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '6px' }}>
              Select Task Template
            </label>
            <select
              className="form-select"
              value={selectedTaskId}
              onChange={(e) => handleSelectTask(e.target.value)}
            >
              {tasks.map((t) => (
                <option key={t.task_id} value={t.task_id}>
                  [{t.difficulty.toUpperCase()}] {t.task_id} — {t.entry_point}()
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--muted)', display: 'block', marginBottom: '6px' }}>
              Target Model & Checkpoint
            </label>
            <select
              className="form-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              <option value="Qwen/Qwen3-0.6B (Base Model, Untrained)">
                Qwen/Qwen3-0.6B (Base Model, Untrained)
              </option>
              <option value="Qwen/Qwen3-0.6B + SFT LoRA (ckpt-step50)">
                Qwen/Qwen3-0.6B + SFT LoRA (ckpt-step50, Pass@1: 100%)
              </option>
              <option value="Qwen/Qwen3-0.6B + RL GRPO (ckpt-step25)">
                Qwen/Qwen3-0.6B + RL GRPO (ckpt-step25, Pass@1: 100%)
              </option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Workspace: Left Editor, Right Execution & Results */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '20px' }}>
        {/* Left Column: Prompt & Candidate Code */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <Code size={16} color="var(--accent)" />
              Programming Prompt & Candidate Code
            </h3>
            <button
              className="btn btn-primary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
              onClick={handleGenerate}
              disabled={isGenerating}
            >
              <Cpu size={14} />
              {isGenerating ? 'Generating...' : 'Prompt Model'}
            </button>
          </div>

          <div style={{ marginBottom: '14px' }}>
            <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
              Instruction Prompt
            </label>
            <textarea
              className="form-input"
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              style={{ resize: 'vertical' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <label style={{ fontSize: '11px', color: 'var(--muted)' }}>
                Candidate Python Code
              </label>
              <span style={{ fontSize: '11px', color: 'var(--ink-secondary)', fontFamily: 'var(--font-mono)' }}>
                {code.split('\n').length} lines
              </span>
            </div>
            <textarea
              className="form-input code-box"
              rows={14}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={{ resize: 'vertical', width: '100%' }}
            />
          </div>

          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              className="btn btn-primary"
              onClick={handleExecute}
              disabled={isExecuting}
            >
              <Play size={14} />
              {isExecuting ? 'Executing in Sandbox...' : 'Run in Linux Sandbox'}
            </button>
          </div>
        </div>

        {/* Right Column: Execution Output & Reward Assessment */}
        <div className="panel">
          <div className="panel-header">
            <h3 className="panel-title">
              <Shield size={16} color="var(--live)" />
              Isolated Execution & Reward Scoring
            </h3>
            {result && (
              <span className={`badge ${result.status === 'completed' ? 'badge-live' : 'badge-down'}`}>
                {result.status}
              </span>
            )}
          </div>

          {!result ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '360px',
                color: 'var(--muted)',
                textAlign: 'center',
              }}
            >
              <Terminal size={40} style={{ opacity: 0.3, marginBottom: '12px' }} />
              <div style={{ fontWeight: 600, fontSize: '14px' }}>No execution results yet</div>
              <div style={{ fontSize: '12px', marginTop: '4px', maxWidth: '320px' }}>
                Click "Run in Linux Sandbox" to dispatch code to the air-gapped Proxmox worker.
              </div>
            </div>
          ) : (
            <div>
              {/* Outcome Badges & Metrics Bar */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ background: '#090d16', padding: '12px', borderRadius: '8px', border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Test Cases Passed</div>
                  <div style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: result.passed === result.total ? 'var(--live)' : 'var(--warn)' }}>
                    {result.passed} / {result.total}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '12px', borderRadius: '8px', border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Deterministic Reward</div>
                  <div style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent)' }}>
                    {result.reward.toFixed(4)}
                  </div>
                </div>

                <div style={{ background: '#090d16', padding: '12px', borderRadius: '8px', border: '1px solid var(--line)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--muted)' }}>Elapsed Time</div>
                  <div style={{ fontSize: '20px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>
                    {result.elapsed_ms}ms
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ height: '8px', width: '100%', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${(result.passed / Math.max(1, result.total)) * 100}%`,
                      background: result.passed === result.total ? 'var(--live)' : 'var(--warn)',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              {/* Standard Output / Log Console */}
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '6px' }}>
                  Sandbox Standard Output
                </div>
                <div className="code-box" style={{ minHeight: '90px', maxHeight: '160px' }}>
                  {result.stdout || '(no stdout produced)'}
                </div>
              </div>

              {result.stderr && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--down)', marginBottom: '6px' }}>
                    Standard Error / Exception Trace
                  </div>
                  <div className="code-box" style={{ color: 'var(--down)', borderColor: 'rgba(244,63,94,0.3)', maxHeight: '120px' }}>
                    {result.stderr}
                  </div>
                </div>
              )}

              {/* Provenance Footer */}
              <div style={{ borderTop: '1px solid var(--line)', paddingTop: '10px', fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--muted)', display: 'flex', justifyContent: 'space-between' }}>
                <span>Job: {result.job_id}</span>
                <span>Candidate SHA: {result.candidate_sha256.slice(0, 16)}...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
