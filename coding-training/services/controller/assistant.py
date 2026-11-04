"""Assistant module for the AI Lab Coding Training Console.

Provides grounded, domain-specific guidance on execution-verified model training,
SFT LoRA, Apple Silicon GRPO reinforcement learning, sandbox isolation, and task datasets.
"""

from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    """Payload for conversational queries to the training assistant."""
    message: str
    context_view: str | None = None
    task_id: str | None = None
    model_id: str | None = None


class AssistantChatResponse(BaseModel):
    """Structured response from the training assistant."""
    reply: str
    context_ref: str | None = None
    suggested_actions: list[str] = Field(default_factory=list)
    code_snippet: str | None = None


KNOWLEDGE_BASE = {
    "grpo": {
        "title": "Group Relative Policy Optimization (GRPO) on Apple Silicon",
        "reply": (
            "**Group Relative Policy Optimization (GRPO)** in FEAT-024 is our on-policy RL algorithm "
            "running on Apple Silicon Metal GPUs (via MLX).\n\n"
            "### How It Works:\n"
            "1. **Group Rollouts:** For each prompt $q$, the policy $\\pi_\\theta$ samples a group of $G$ outputs $\\{o_1, o_2, \\dots, o_G\\}$ (default $G=4$).\n"
            "2. **Sandbox Execution & Reward:** Each completion is dispatched to the air-gapped Proxmox Linux jail where 20 test assertions run.\n"
            "3. **Advantage Normalization:** Rewards $r_i$ are normalized relative to group mean and std: "
            "$$A_i = \\frac{r_i - \\text{mean}(\\{r\\})}{\\text{std}(\\{r\\}) + \\epsilon}$$\n"
            "4. **Surrogate Loss Update:** A clipped surrogate loss trains the LoRA adapter with KL divergence regularized against base $\\pi_{ref}$."
        ),
        "code": (
            "# Group Advantage Calculation in GRPO\n"
            "import numpy as np\n\n"
            "def compute_group_advantages(rewards: list[float], eps: float = 1e-4) -> list[float]:\n"
            "    arr = np.array(rewards, dtype=np.float32)\n"
            "    mean = np.mean(arr)\n"
            "    std = np.std(arr)\n"
            "    if std < eps:\n"
            "        return [0.0] * len(rewards)\n"
            "    return ((arr - mean) / (std + eps)).tolist()\n"
        ),
        "actions": ["Inspect Experiment Loss Curves", "Review Task Bundles", "Launch GRPO Run"],
    },
    "sft": {
        "title": "Supervised Fine-Tuning (SFT) & LoRA Adapter Verification",
        "reply": (
            "**Supervised Fine-Tuning (SFT)** in AI Lab mines passing candidate solutions verified by the Proxmox sandbox "
            "into verified instruction-response pairs.\n\n"
            "### Key Invariants:\n"
            "- **LoRA Parameters:** Target linear layers (`q_proj`, `v_proj`) with rank $r=8$ and $\\alpha=16$.\n"
            "- **Parameter Divergence Proof:** The controller records the initial adapter SHA-256 digest before step 0, "
            "and verifies that the final weights have diverged (`weights_diverged=True`). A run without parameter change is flagged as unverified.\n"
            "- **Holdout Evaluation:** Checkpoints are evaluated on 15 disjoint holdout tasks to ensure generalization."
        ),
        "code": (
            "# Verification of Adapter Weight Divergence\n"
            "import hashlib\n\n"
            "def verify_weight_divergence(init_hash: str, final_weights_path: str) -> bool:\n"
            "    hasher = hashlib.sha256()\n"
            "    with open(final_weights_path, 'rb') as f:\n"
            "        hasher.update(f.read())\n"
            "    final_hash = hasher.hexdigest()\n"
            "    return init_hash != final_hash  # Must be strictly divergent\n"
        ),
        "actions": ["View Trained Checkpoints", "Open Experiments", "Test Adapter in Playground"],
    },
    "sandbox": {
        "title": "Air-Gapped Proxmox Sandbox Isolation",
        "reply": (
            "The **Execution Sandbox Worker** (`127.0.0.1:8002`) provides strict isolation for executing untrusted candidate code:\n\n"
            "### Isolation Guarantees:\n"
            "- **Network Containment:** Ran under Linux network namespaces (`CLONE_NEWNET`) with zero network egress, no DNS, and loopback only.\n"
            "- **Resource Bounds:** Enforced via cgroups v2: max 512 MB memory, 5.0s CPU timeout.\n"
            "- **Rootless Privilege:** Runs under an unprivileged user with restricted seccomp filters.\n"
            "- **Infrastructure Failure Distinction:** If a worker crashes or times out due to VM issues, the run is classified as `unscorable` — never scored as $0.0$ to avoid corrupting training gradients."
        ),
        "code": (
            "# Linux Isolation Flags used by Sandbox Worker\n"
            "# CLONE_NEWNET: unshares network namespace (zero egress)\n"
            "# CLONE_NEWPID: unshares PID tree\n"
            "# CLONE_NEWNS: unshares filesystem mount namespace\n"
            "unshare -n -p -m --mount-proc /usr/bin/python3 candidate.py\n"
        ),
        "actions": ["Inspect Worker Telemetry", "View Security Assessment", "Test Sandbox in Playground"],
    },
    "reward": {
        "title": "Deterministic Reward Engine (v1)",
        "reply": (
            "The **Reward Engine** calculates deterministic scalar rewards $r \\in [0.0, 1.0]$ based on:\n\n"
            "$$r = 0.70 \\cdot \\frac{N_{pass}}{N_{total}} + 0.15 \\cdot R_{runtime} + 0.15 \\cdot R_{memory}$$\n\n"
            "- **Correctness (70%):** Proportion of the 20 assertions passed.\n"
            "- **Runtime Efficiency (15%):** Bonus for sub-100ms execution.\n"
            "- **Memory Efficiency (15%):** Bonus for low peak RSS.\n"
            "- **Syntax Errors:** Reward is fixed at $0.0$.\n"
            "- **Worker Crashes:** Flagged as `unscorable`, excluded from reward updates."
        ),
        "code": (
            "# Reward v1 Calculation\n"
            "def calculate_reward(passed: int, total: int, elapsed_ms: float) -> float:\n"
            "    if total == 0:\n"
            "        return 0.0\n"
            "    correctness = passed / total\n"
            "    speed_bonus = max(0.0, min(1.0, (1000.0 - elapsed_ms) / 1000.0))\n"
            "    return round(0.70 * correctness + 0.30 * speed_bonus, 4)\n"
        ),
        "actions": ["Review Reward Formula", "Open Playground"],
    },
    "tasks": {
        "title": "Curated Coding Tasks & Test Bundles",
        "reply": (
            "The platform features **105 curated Python algorithmic tasks** stored in `coding-training/datasets/`:\n\n"
            "- **Split Division:** 75 Training, 15 Validation, 15 Holdout Test.\n"
            "- **Family Disjointness:** Verified zero family overlap between train and test splits (e.g. all LRU cache tasks stay in train, Trie prefix search in test).\n"
            "- **Immutable Bundles:** Each task has a cryptographic SHA-256 test bundle with 20 assertions that are never leaked into model prompts."
        ),
        "code": (
            "# Sample Tasks Overview\n"
            "# py-fib-001:  Fibonacci DP (Easy, Train, 20 assertions)\n"
            "# py-binsearch-003: Binary Search (Easy, Train, 20 assertions)\n"
            "# py-lru-007:  LRU Cache O(1) (Hard, Train, 20 assertions)\n"
            "# py-trie-prefix-022: Trie Prefix Tree (Medium, Test, 20 assertions)\n"
        ),
        "actions": ["Explore Datasets View", "Test Task in Playground"],
    },
}


def generate_assistant_reply(
    message: str,
    context_view: str | None = None,
    task_id: str | None = None,
    model_id: str | None = None,
) -> AssistantChatResponse:
    """Generates an informed, domain-aware reply to an operator's query."""
    lower = message.lower()

    # Match topic domains
    if any(k in lower for k in ["grpo", "reinforcement", "policy", "advantage", "group size", "surrogate"]):
        kb = KNOWLEDGE_BASE["grpo"]
        return AssistantChatResponse(
            reply=kb["reply"],
            context_ref="docs/architecture.md#rl-grpo",
            suggested_actions=kb["actions"],
            code_snippet=kb["code"],
        )

    if any(k in lower for k in ["sft", "lora", "fine-tune", "finetuning", "adapter", "divergence", "weights_diverged"]):
        kb = KNOWLEDGE_BASE["sft"]
        return AssistantChatResponse(
            reply=kb["reply"],
            context_ref="docs/architecture.md#sft-pipeline",
            suggested_actions=kb["actions"],
            code_snippet=kb["code"],
        )

    if any(k in lower for k in ["sandbox", "isolation", "proxmox", "network", "cgroups", "seccomp", "air-gap", "unshare"]):
        kb = KNOWLEDGE_BASE["sandbox"]
        return AssistantChatResponse(
            reply=kb["reply"],
            context_ref="docs/security/SECURITY_ASSESSMENT.md",
            suggested_actions=kb["actions"],
            code_snippet=kb["code"],
        )

    if any(k in lower for k in ["reward", "score", "metric", "syntax error", "unscorable", "penalty"]):
        kb = KNOWLEDGE_BASE["reward"]
        return AssistantChatResponse(
            reply=kb["reply"],
            context_ref="packages/rewards/engine.py",
            suggested_actions=kb["actions"],
            code_snippet=kb["code"],
        )

    if any(k in lower for k in ["task", "dataset", "split", "disjoint", "holdout", "assertions", "bundles"]):
        kb = KNOWLEDGE_BASE["tasks"]
        return AssistantChatResponse(
            reply=kb["reply"],
            context_ref="packages/datasets/task_loader.py",
            suggested_actions=kb["actions"],
            code_snippet=kb["code"],
        )

    # Specific task question
    if "fib" in lower or task_id == "py-fib-001":
        return AssistantChatResponse(
            reply=(
                "**Task `py-fib-001` (Fibonacci DP):**\n"
                "Requires computing the $n$-th Fibonacci number in $O(n)$ time and $O(1)$ space.\n\n"
                "Common base model failure: Recursive $O(2^n)$ branching causes the sandbox to hit the 5.0s timeout limit on $n \\ge 35$. "
                "The tuned SFT adapter uses iterative accumulator swapping."
            ),
            context_ref="py-fib-001",
            suggested_actions=["Load Fibonacci in Playground", "Run Sandbox Test"],
            code_snippet=(
                "def fibonacci(n: int) -> int:\n"
                "    if n <= 0:\n"
                "        return 0\n"
                "    if n == 1:\n"
                "        return 1\n"
                "    a, b = 0, 1\n"
                "    for _ in range(2, n + 1):\n"
                "        a, b = b, a + b\n"
                "    return b\n"
            ),
        )

    if "lru" in lower or task_id == "py-lru-007":
        return AssistantChatResponse(
            reply=(
                "**Task `py-lru-007` (LRU Cache):**\n"
                "Requires designing an LRU Cache with $O(1)$ `get(key)` and `put(key, value)`.\n\n"
                "Implemented via an `OrderedDict` or a hash map + doubly linked list. "
                "Base models often forget eviction ordering or fail capacity boundary assertions."
            ),
            context_ref="py-lru-007",
            suggested_actions=["Inspect LRU Cache in Datasets", "Open Playground"],
            code_snippet=(
                "from collections import OrderedDict\n\n"
                "class LRUCache:\n"
                "    def __init__(self, capacity: int):\n"
                "        self.capacity = capacity\n"
                "        self.cache = OrderedDict()\n\n"
                "    def get(self, key: int) -> int:\n"
                "        if key not in self.cache:\n"
                "            return -1\n"
                "        self.cache.move_to_end(key)\n"
                "        return self.cache[key]\n\n"
                "    def put(self, key: int, value: int) -> None:\n"
                "        if key in self.cache:\n"
                "            self.cache.move_to_end(key)\n"
                "        self.cache[key] = value\n"
                "        if len(self.cache) > self.capacity:\n"
                "            self.cache.popitem(last=False)\n"
            ),
        )

    # Contextual fallback based on active screen
    context_hint = ""
    if context_view == "playground":
        context_hint = "You are currently in the **Model Playground**. You can prompt candidates and execute them in the Linux sandbox."
    elif context_view == "experiments":
        context_hint = "You are in the **Experiments View**. You can track SFT LoRA loss descent and RL GRPO advantage distributions."
    elif context_view == "monitor":
        context_hint = "You are viewing the **Live Monitor**. Real-time SSE telemetry reflects worker queue depth and sandbox execution rates."

    return AssistantChatResponse(
        reply=(
            f"Hello! I am the **AI Lab Training Copilot**.\n\n"
            f"{context_hint}\n\n"
            "I can assist you with:\n"
            "- **Training Algorithms:** Supervised LoRA fine-tuning and Apple Silicon GRPO reinforcement learning.\n"
            "- **Sandbox Security:** Air-gapped Proxmox VM isolation, cgroups v2, and network isolation.\n"
            "- **Reward Diagnostics:** Syntax error analysis, reward metrics, and failure classification.\n"
            "- **Curated Datasets:** Navigating the 105 Python tasks and verifying test bundle hashes.\n\n"
            "Feel free to ask a specific question, or click any suggested prompt below!"
        ),
        context_ref="general",
        suggested_actions=[
            "How does GRPO work on Apple Silicon?",
            "Explain Sandbox Isolation",
            "Why is Base Pass@1 0%?",
            "What is the Reward Formula?",
        ],
    )
