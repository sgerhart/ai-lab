import React, { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { api, MOCK_CHECKPOINTS, MOCK_EXPERIMENTS, MOCK_HOSTS, MOCK_TASKS } from './services/api'
import type { CheckpointItem, ExperimentRun, HostHealth, TaskItem, ViewType } from './types'
import { DashboardView } from './views/DashboardView'
import { DatasetsView } from './views/DatasetsView'
import { ExperimentsView } from './views/ExperimentsView'
import { ModelsView } from './views/ModelsView'
import { MonitorView } from './views/MonitorView'
import { PlaygroundView } from './views/PlaygroundView'

export const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard')
  const [hosts, setHosts] = useState<HostHealth[]>(MOCK_HOSTS)
  const [tasks, setTasks] = useState<TaskItem[]>(MOCK_TASKS)
  const [checkpoints, setCheckpoints] = useState<CheckpointItem[]>(MOCK_CHECKPOINTS)
  const [experiments, setExperiments] = useState<ExperimentRun[]>(MOCK_EXPERIMENTS)

  useEffect(() => {
    // Load initial data from API client
    api.getHealth().then(setHosts)
    api.getTasks().then(setTasks)
    api.getCheckpoints().then(setCheckpoints)
    api.getExperiments().then(setExperiments)
  }, [])

  const handleNewExperiment = (newExp: ExperimentRun) => {
    setExperiments((prev) => [newExp, ...prev])
  }

  const handleVerifyCheckpoint = (checkpointId: string) => {
    setCheckpoints((prev) =>
      prev.map((c) => (c.checkpoint_id === checkpointId ? { ...c, status: 'verified' } : c))
    )
  }

  const handleDeployCheckpoint = (checkpointId: string) => {
    setCheckpoints((prev) =>
      prev.map((c) => ({
        ...c,
        active_for_inference: c.checkpoint_id === checkpointId,
      }))
    )
  }

  return (
    <div className="console-app">
      <Header hosts={hosts} currentView={currentView} onSelectView={setCurrentView} />

      <main className="console-main">
        {currentView === 'dashboard' && (
          <DashboardView
            hosts={hosts}
            checkpoints={checkpoints}
            experiments={experiments}
            onNavigate={setCurrentView}
          />
        )}

        {currentView === 'playground' && <PlaygroundView tasks={tasks} />}

        {currentView === 'experiments' && (
          <ExperimentsView
            experiments={experiments}
            onNewExperiment={handleNewExperiment}
          />
        )}

        {currentView === 'monitor' && <MonitorView />}

        {currentView === 'models' && (
          <ModelsView
            checkpoints={checkpoints}
            onVerifyCheckpoint={handleVerifyCheckpoint}
            onDeployCheckpoint={handleDeployCheckpoint}
          />
        )}

        {currentView === 'datasets' && <DatasetsView tasks={tasks} />}
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--line)',
          padding: '16px 24px',
          textAlign: 'center',
          fontSize: '11px',
          color: 'var(--muted)',
          background: 'rgba(9, 13, 22, 0.9)',
        }}
      >
        <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
          <div>
            AI Lab Coding Model Training Platform · <span style={{ color: 'var(--accent)' }}>FEAT-024</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)' }}>
            Loopback Binds: 127.0.0.1:8000 (Mini) · 127.0.0.1:8001 (Studio) · 127.0.0.1:8002 (Proxmox)
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
