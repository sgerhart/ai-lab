export type ViewType = 'dashboard' | 'playground' | 'experiments' | 'monitor' | 'models' | 'datasets'

export interface HostHealth {
  name: string
  role: string
  host: string
  port: number
  status: 'healthy' | 'degraded' | 'offline'
  latencyMs: number
  uptime: string
  details?: Record<string, string>
}

export interface TaskItem {
  task_id: string
  prompt: string
  entry_point: string
  function_contract: string
  difficulty: 'easy' | 'medium' | 'hard'
  split: 'train' | 'validation' | 'test'
  family_id: string
  assertion_count: number
  test_bundle_sha256: string
}

export interface ExecutionResultSummary {
  job_id: string
  task_id: string
  candidate_sha256: string
  status: 'completed' | 'runtime_error' | 'timed_out' | 'compile_error' | 'infra_error'
  passed: number
  total: number
  elapsed_ms: number
  reward: number
  is_scorable: boolean
  failure_class: string
  stdout: string
  stderr: string
}

export interface CheckpointItem {
  checkpoint_id: string
  training_run_id: string
  training_type: 'sft' | 'grpo'
  base_model: string
  step: number
  adapter_hash: string
  initial_adapter_hash: string
  weights_diverged: boolean
  created_at_utc: string
  size_kb: number
  status: 'verified' | 'tampered'
  active_for_inference: boolean
}

export interface ExperimentRun {
  run_id: string
  type: 'SFT (LoRA)' | 'RL (GRPO)'
  base_model: string
  steps_completed: number
  max_steps: number
  status: 'COMPLETED' | 'RUNNING' | 'FAILED' | 'PENDING_APPROVAL'
  learning_rate: number
  group_size?: number
  lora_rank: number
  initial_hash: string
  final_hash: string
  weights_diverged: boolean
  mean_reward: number
  holdout_pass1: number
  loss_history: { step: number; loss: number; val_loss?: number; reward?: number }[]
  created_at: string
}

export interface TelemetryEvent {
  id: string
  timestamp: string
  level: 'INFO' | 'AUDIT' | 'WARN' | 'ERROR'
  source: 'controller' | 'model_worker' | 'sandbox' | 'trainer'
  message: string
  details?: Record<string, unknown>
}
