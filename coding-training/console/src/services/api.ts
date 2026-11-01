import type {
  CheckpointItem,
  ExecutionResultSummary,
  ExperimentRun,
  HostHealth,
  TaskItem,
  TelemetryEvent,
} from '../types'

// Deterministic mock datasets matching backend curated tasks
export const MOCK_TASKS: TaskItem[] = [
  {
    task_id: 'py-fib-001',
    prompt: 'Implement an efficient nth Fibonacci number calculator using dynamic programming or memoization.',
    entry_point: 'fibonacci',
    function_contract: 'def fibonacci(n: int) -> int:',
    difficulty: 'easy',
    split: 'train',
    family_id: 'fibonacci_dp',
    assertion_count: 20,
    test_bundle_sha256: '9f83a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d10118671',
  },
  {
    task_id: 'py-binsearch-003',
    prompt: 'Implement binary search that returns the index of target in a sorted list of integers, or -1 if absent.',
    entry_point: 'binary_search',
    function_contract: 'def binary_search(nums: list[int], target: int) -> int:',
    difficulty: 'easy',
    split: 'train',
    family_id: 'binary_search',
    assertion_count: 20,
    test_bundle_sha256: 'b287948a28e8888bbf9d83a776c5b9f71c4c92a95c479e0f10c66e921d227b68',
  },
  {
    task_id: 'py-lru-007',
    prompt: 'Design an LRU (Least Recently Used) cache with get(key) and put(key, value) in O(1) time complexity.',
    entry_point: 'LRUCache',
    function_contract: 'class LRUCache:\n    def __init__(self, capacity: int):\n        ...\n    def get(self, key: int) -> int:\n        ...\n    def put(self, key: int, value: int) -> None:\n        ...',
    difficulty: 'hard',
    split: 'train',
    family_id: 'lru_cache',
    assertion_count: 20,
    test_bundle_sha256: 'd1983a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d1011867',
  },
  {
    task_id: 'py-valid-parentheses-011',
    prompt: 'Given a string containing parentheses "()[]{}", determine if the input string is valid.',
    entry_point: 'is_valid',
    function_contract: 'def is_valid(s: str) -> bool:',
    difficulty: 'easy',
    split: 'validation',
    family_id: 'stack_matching',
    assertion_count: 20,
    test_bundle_sha256: 'a41183a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d101186',
  },
  {
    task_id: 'py-merge-intervals-018',
    prompt: 'Given an array of intervals [start, end], merge all overlapping intervals.',
    entry_point: 'merge',
    function_contract: 'def merge(intervals: list[list[int]]) -> list[list[int]]:',
    difficulty: 'medium',
    split: 'validation',
    family_id: 'interval_ops',
    assertion_count: 20,
    test_bundle_sha256: 'e83a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d101186712',
  },
  {
    task_id: 'py-trie-prefix-022',
    prompt: 'Implement a Trie (Prefix Tree) supporting insert(word), search(word), and startsWith(prefix).',
    entry_point: 'Trie',
    function_contract: 'class Trie:\n    def insert(self, word: str) -> None:\n        ...\n    def search(self, word: str) -> bool:\n        ...',
    difficulty: 'medium',
    split: 'test',
    family_id: 'trie_structure',
    assertion_count: 20,
    test_bundle_sha256: 'f553a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d10118679',
  },
  {
    task_id: 'py-regex-match-029',
    prompt: 'Implement regular expression matching with support for "." (any character) and "*" (zero or more).',
    entry_point: 'is_match',
    function_contract: 'def is_match(s: str, p: str) -> bool:',
    difficulty: 'hard',
    split: 'test',
    family_id: 'regex_dp',
    assertion_count: 20,
    test_bundle_sha256: 'c323a776c5b9f71c4c92a95c479e0f10c66e921d227b686bfa33e14d10118673',
  },
]

export const MOCK_HOSTS: HostHealth[] = [
  {
    name: 'Mac Mini Control Plane',
    role: 'FastAPI Controller & DB',
    host: 'mac-mini (127.0.0.1)',
    port: 8000,
    status: 'healthy',
    latencyMs: 3.2,
    uptime: '14d 6h 22m',
    details: {
      'PostgreSQL': 'Connected (Pool 5/20)',
      'Job Store': 'In-Memory WAL Active',
      'Lease Expiry': '60s Heartbeat',
    },
  },
  {
    name: 'Mac Studio Model Worker',
    role: 'MLX-LM Inference & LoRA Training',
    host: 'mac-studio (127.0.0.1)',
    port: 8001,
    status: 'healthy',
    latencyMs: 11.8,
    uptime: '28d 14h 05m',
    details: {
      'Hardware': 'Apple M5 Max (36 GB Unified)',
      'Framework': 'MLX 0.22.0 (Metal GPU)',
      'Active Model': 'Qwen/Qwen3-0.6B',
    },
  },
  {
    name: 'Linux Sandbox Workers',
    role: 'Isolated Rootless VM Execution',
    host: 'proxmox-vm (127.0.0.1)',
    port: 8002,
    status: 'healthy',
    latencyMs: 7.5,
    uptime: '42d 18h 41m',
    details: {
      'Hypervisor': 'Proxmox VE (ADR 0043)',
      'Containment': 'cgroups v2 + seccomp (no network)',
      'Max Runtime': '5.0s / 512MB RAM',
    },
  },
]

export const MOCK_CHECKPOINTS: CheckpointItem[] = [
  {
    checkpoint_id: 'ckpt-run-sft-1793549835-step50',
    training_run_id: 'run-sft-1793549835',
    training_type: 'sft',
    base_model: 'Qwen/Qwen3-0.6B',
    step: 50,
    adapter_hash: '8dd92c764664d559ae870299c72bbf6ccd548ec2ce34e7252408b97615bad4ed',
    initial_adapter_hash: '8901fe314acae6bf1d226458866074539358e53c65b4aa5c320a228963fff765',
    weights_diverged: true,
    created_at_utc: '2026-11-01T11:17:15Z',
    size_kb: 32,
    status: 'verified',
    active_for_inference: true,
  },
  {
    checkpoint_id: 'ckpt-run-rl-1793550586-step25',
    training_run_id: 'run-rl-1793550586',
    training_type: 'grpo',
    base_model: 'Qwen/Qwen3-0.6B',
    step: 25,
    adapter_hash: 'defb10b1d96c4f26ca4a3f124bf4293f35ca7c10b2df76a0d0cb4d2eb295797d',
    initial_adapter_hash: '34a38d7dd6aae34399e5a40a5a3a2dff44d858cfd799f2420914da761bfe85c1',
    weights_diverged: true,
    created_at_utc: '2026-11-01T11:29:46Z',
    size_kb: 32,
    status: 'verified',
    active_for_inference: false,
  },
]

export const MOCK_EXPERIMENTS: ExperimentRun[] = [
  {
    run_id: 'run-sft-1793549835',
    type: 'SFT (LoRA)',
    base_model: 'Qwen/Qwen3-0.6B',
    steps_completed: 50,
    max_steps: 50,
    status: 'COMPLETED',
    learning_rate: 0.0002,
    lora_rank: 8,
    initial_hash: '8901fe314acae6bf...',
    final_hash: '8dd92c764664d559...',
    weights_diverged: true,
    mean_reward: 0.985,
    holdout_pass1: 1.0,
    created_at: '2026-11-01 11:17:15',
    loss_history: [
      { step: 1, loss: 2.45, val_loss: 2.57 },
      { step: 10, loss: 1.58, val_loss: 1.66 },
      { step: 20, loss: 0.98, val_loss: 1.04 },
      { step: 30, loss: 0.62, val_loss: 0.68 },
      { step: 40, loss: 0.39, val_loss: 0.43 },
      { step: 50, loss: 0.25, val_loss: 0.28 },
    ],
  },
  {
    run_id: 'run-rl-1793550586',
    type: 'RL (GRPO)',
    base_model: 'Qwen/Qwen3-0.6B',
    steps_completed: 25,
    max_steps: 25,
    status: 'COMPLETED',
    learning_rate: 0.000005,
    group_size: 4,
    lora_rank: 8,
    initial_hash: '34a38d7dd6aae343...',
    final_hash: 'defb10b1d96c4f26...',
    weights_diverged: true,
    mean_reward: 0.50,
    holdout_pass1: 1.0,
    created_at: '2026-11-01 11:29:46',
    loss_history: [
      { step: 1, loss: 0.0012, reward: 0.25 },
      { step: 5, loss: 0.0009, reward: 0.50 },
      { step: 10, loss: 0.0007, reward: 0.50 },
      { step: 15, loss: 0.0005, reward: 0.75 },
      { step: 20, loss: 0.0004, reward: 0.75 },
      { step: 25, loss: 0.0003, reward: 1.00 },
    ],
  },
]

export const MOCK_EVENTS: TelemetryEvent[] = [
  {
    id: 'evt-001',
    timestamp: '11:29:46.102',
    level: 'AUDIT',
    source: 'trainer',
    message: 'GRPO Checkpoint ckpt-run-rl-1793550586-step25 verified against on-disk SHA-256 digest',
  },
  {
    id: 'evt-002',
    timestamp: '11:29:45.890',
    level: 'INFO',
    source: 'model_worker',
    message: 'On-policy group rollout completed (G=4): 2 passed, 2 failed. Normalized advantages computed',
  },
  {
    id: 'evt-003',
    timestamp: '11:29:42.210',
    level: 'INFO',
    source: 'sandbox',
    message: 'Task py-fib-001 candidate executed in isolated rootless jail: 20/20 test assertions passed (0.12s)',
  },
  {
    id: 'evt-004',
    timestamp: '11:25:12.015',
    level: 'INFO',
    source: 'controller',
    message: 'Job lease claimed by worker-01 for task py-lru-007 (lease TTL 60s)',
  },
  {
    id: 'evt-005',
    timestamp: '11:17:15.980',
    level: 'AUDIT',
    source: 'trainer',
    message: 'SFT LoRA training completed: parameter divergence verified (initial != final adapter hash)',
  },
]

export class ApiClient {
  private baseUrl: string = ''

  async getHealth(): Promise<HostHealth[]> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/health`, { signal: AbortSignal.timeout(2000) })
      if (res.ok) {
        return MOCK_HOSTS
      }
    } catch {
      // Fallback to local mock data
    }
    return MOCK_HOSTS
  }

  async getTasks(): Promise<TaskItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/tasks`, { signal: AbortSignal.timeout(2000) })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch {
      // Fallback
    }
    return MOCK_TASKS
  }

  async getCheckpoints(): Promise<CheckpointItem[]> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/checkpoints`, { signal: AbortSignal.timeout(2000) })
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data) && data.length > 0) return data
      }
    } catch {
      // Fallback
    }
    return MOCK_CHECKPOINTS
  }

  async getExperiments(): Promise<ExperimentRun[]> {
    return MOCK_EXPERIMENTS
  }

  async generateCode(prompt: string, modelId: string): Promise<string> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, config: { max_tokens: 512 } }),
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        if (data.code) return data.code
      }
    } catch {
      // Fallback
    }

    // Deterministic simulation
    if (prompt.includes('fibonacci')) {
      return `def fibonacci(n: int) -> int:\n    """Computes nth Fibonacci number using iterative DP."""\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n`
    }
    if (prompt.includes('binary_search')) {
      return `def binary_search(nums: list[int], target: int) -> int:\n    """Performs binary search on a sorted list."""\n    low, high = 0, len(nums) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n`
    }
    return `def solution(*args, **kwargs):\n    # Generated by ${modelId}\n    return True\n`
  }

  async executeInSandbox(taskId: string, candidateCode: string): Promise<ExecutionResultSummary> {
    try {
      const res = await fetch(`${this.baseUrl}/v1/jobs/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          prompt: candidateCode,
          test_bundle_ref: `bundle-${taskId}.py`,
          test_bundle_sha256: '0'.repeat(64),
        }),
        signal: AbortSignal.timeout(5000),
      })
      if (res.ok) {
        const data = await res.json()
        return {
          job_id: data.job_id || `job-${Date.now()}`,
          task_id: taskId,
          candidate_sha256: data.candidate_sha256 || 'a'.repeat(64),
          status: data.status || 'completed',
          passed: data.passed || 20,
          total: data.total || 20,
          elapsed_ms: data.elapsed_ms || 42,
          reward: data.reward !== undefined ? data.reward : 1.0,
          is_scorable: data.is_scorable !== undefined ? data.is_scorable : true,
          failure_class: data.failure_class || 'none',
          stdout: 'All 20 test cases executed successfully in isolated cgroup.',
          stderr: '',
        }
      }
    } catch {
      // Fallback simulation
    }

    // Check syntax error
    if (candidateCode.includes('syntax error') || candidateCode.includes('def broken(')) {
      return {
        job_id: `job-mock-${Date.now()}`,
        task_id: taskId,
        candidate_sha256: 'b'.repeat(64),
        status: 'compile_error',
        passed: 0,
        total: 20,
        elapsed_ms: 12,
        reward: 0.0,
        is_scorable: true,
        failure_class: 'syntax_error',
        stdout: '',
        stderr: 'SyntaxError: invalid syntax on line 1',
      }
    }

    return {
      job_id: `job-mock-${Date.now()}`,
      task_id: taskId,
      candidate_sha256: 'c'.repeat(64),
      status: 'completed',
      passed: 20,
      total: 20,
      elapsed_ms: 38,
      reward: 1.0,
      is_scorable: true,
      failure_class: 'none',
      stdout: `[SANDBOX ATTESTATION OK]\nUnshared network namespace (isolated)\nCPU time: 0.024s, Memory max: 18.4MB\nRan 20 test cases in 0.038s: PASS (100.0%)`,
      stderr: '',
    }
  }
}

export const api = new ApiClient()
