import { useState } from 'react'
import { Database, Filter, Lock, Search, ShieldCheck } from 'lucide-react'
import type { TaskItem } from '../types'

interface DatasetsViewProps {
  tasks: TaskItem[]
}

export const DatasetsView: React.FC<DatasetsViewProps> = ({ tasks }) => {
  const [selectedSplit, setSelectedSplit] = useState<string>('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [inspectedTask, setInspectedTask] = useState<TaskItem | null>(null)

  const filteredTasks = tasks.filter((t) => {
    if (selectedSplit !== 'all' && t.split !== selectedSplit) return false
    if (selectedDifficulty !== 'all' && t.difficulty !== selectedDifficulty) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        t.task_id.toLowerCase().includes(q) ||
        t.entry_point.toLowerCase().includes(q) ||
        t.prompt.toLowerCase().includes(q) ||
        t.family_id.toLowerCase().includes(q)
      )
    }
    return true
  })

  return (
    <div className="datasets-view">
      {/* View Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--ink)' }}>Curated Tasks & Immutable Test Bundles</h2>
          <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
            105 Python algorithmic tasks partitioned across train, validation, and test splits with zero family leakage
          </p>
        </div>
        <span className="badge badge-live">
          <ShieldCheck size={12} />
          Family Disjointness Verified
        </span>
      </div>

      {/* Filter and Search Bar */}
      <div className="panel" style={{ padding: '16px', marginBottom: '20px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: '1', minWidth: '240px' }}>
            <Search size={16} color="var(--muted)" />
            <input
              type="text"
              placeholder="Search by task ID, function name, or prompt..."
              className="form-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={14} color="var(--muted)" />
              <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Split:</span>
              <select
                className="form-select"
                style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
                value={selectedSplit}
                onChange={(e) => setSelectedSplit(e.target.value)}
              >
                <option value="all">All Splits ({tasks.length})</option>
                <option value="train">Train (75)</option>
                <option value="validation">Validation (15)</option>
                <option value="test">Test (15)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Difficulty:</span>
              <select
                className="form-select"
                style={{ width: 'auto', padding: '4px 8px', fontSize: '12px' }}
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
              >
                <option value="all">All</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Tasks Table Panel */}
      <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="console-table">
          <thead>
            <tr>
              <th>Task ID</th>
              <th>Entry Point</th>
              <th>Difficulty</th>
              <th>Split</th>
              <th>Family</th>
              <th>Assertions</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredTasks.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '30px', color: 'var(--muted)' }}>
                  No tasks match current filter.
                </td>
              </tr>
            ) : (
              filteredTasks.map((t) => (
                <tr key={t.task_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--accent)', fontWeight: 600 }}>
                    {t.task_id}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>
                    {t.entry_point}()
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        t.difficulty === 'easy'
                          ? 'badge-live'
                          : t.difficulty === 'medium'
                          ? 'badge-warn'
                          : 'badge-down'
                      }`}
                    >
                      {t.difficulty}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        t.split === 'train'
                          ? 'badge-purple'
                          : t.split === 'validation'
                          ? 'badge-accent'
                          : 'badge-warn'
                      }`}
                    >
                      {t.split}
                    </span>
                  </td>
                  <td style={{ fontSize: '11px', color: 'var(--muted)' }}>{t.family_id}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{t.assertion_count} tests</td>
                  <td>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '3px 8px', fontSize: '11px' }}
                      onClick={() => setInspectedTask(t)}
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Task Inspection Drawer / Modal */}
      {inspectedTask && (
        <div className="modal-overlay">
          <div className="modal-dialog" style={{ maxWidth: '640px' }}>
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={20} color="var(--accent)" />
                <h3 className="modal-title">Task Specification: {inspectedTask.task_id}</h3>
              </div>
              <button
                style={{ background: 'transparent', border: 'none', color: 'var(--muted)', cursor: 'pointer', fontSize: '18px' }}
                onClick={() => setInspectedTask(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <span className={`badge ${inspectedTask.split === 'train' ? 'badge-purple' : 'badge-accent'}`}>
                  SPLIT: {inspectedTask.split.toUpperCase()}
                </span>
                <span className="badge badge-warn">
                  DIFFICULTY: {inspectedTask.difficulty.toUpperCase()}
                </span>
                <span className="badge badge-live">
                  FAMILY: {inspectedTask.family_id}
                </span>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                  Natural Language Prompt
                </label>
                <div style={{ background: '#090d16', padding: '10px', borderRadius: '6px', border: '1px solid var(--line)', fontSize: '13px' }}>
                  {inspectedTask.prompt}
                </div>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: 'var(--muted)', display: 'block', marginBottom: '4px' }}>
                  Function Contract & Signature
                </label>
                <div className="code-box" style={{ padding: '10px' }}>
                  {inspectedTask.function_contract}
                </div>
              </div>

              <div
                style={{
                  background: 'rgba(0,0,0,0.4)',
                  padding: '12px',
                  borderRadius: '6px',
                  border: '1px solid var(--line)',
                  fontSize: '11px',
                  fontFamily: 'var(--font-mono)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--muted)' }}>Test Bundle Digest:</span>
                  <span style={{ color: 'var(--accent)' }}>{inspectedTask.test_bundle_sha256.slice(0, 24)}...</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--muted)' }}>Hidden Unit Assertions:</span>
                  <span>{inspectedTask.assertion_count} tests (Isolated in VM)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--live)', marginTop: '4px' }}>
                  <Lock size={12} />
                  <span>Hidden test cases quarantined from prompt context (Zero Leakage)</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setInspectedTask(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
