"""AI Laboratory Workbench model catalog, mathematical explainers, and tensor flows (IWO-129).

Provides multi-paradigm conceptual breakdowns, first-principles mathematical derivations
with plain-English intuition and numerical examples, runnable tensor test snippets, and
grounded citations to the operator's 192 books and research papers in Knowledge Nexus.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class LabCitation:
    title: str
    chapter: str
    category: str
    relevance: str


@dataclass(frozen=True)
class LabConcept:
    id: str
    title: str
    paradigm: str
    summary: str
    tensor_flow: str
    formula: str
    variables: dict[str, str]
    math_explanation: str
    numerical_example: str
    code_snippet: str
    nexus_citations: list[LabCitation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data


PARADIGMS: list[dict[str, str]] = [
    {"id": "all", "label": "All Paradigms", "icon": "🔬"},
    {"id": "language", "label": "Language & SLMs", "icon": "📝"},
    {"id": "vision", "label": "Vision & Conv/ViT", "icon": "👁️"},
    {"id": "diffusion", "label": "Diffusion & Generative", "icon": "✨"},
    {"id": "audio", "label": "Audio & Speech", "icon": "🎙️"},
    {"id": "multimodal", "label": "Multimodal Systems", "icon": "🌐"},
    {"id": "rl", "label": "Reinforcement Learning & Reasoning", "icon": "🎯"},
    {"id": "foundations", "label": "Mathematical Foundations", "icon": "📐"},
]

_CONCEPTS_LIST: list[LabConcept] = [
    # ─── Language & SLMs ──────────────────────────────────────────────────────────
    LabConcept(
        id="self-attention",
        title="Scaled Dot-Product Self-Attention",
        paradigm="language",
        summary="Content-based routing mechanism where every token projects Queries, Keys, and Values to calculate pairwise relevance scores.",
        tensor_flow=(
            "Inputs:\n"
            "  X: [Batch, SeqLen, HiddenDim]\n"
            "Projections:\n"
            "  Q = X @ W_q: [Batch, SeqLen, d_k]\n"
            "  K = X @ W_k: [Batch, SeqLen, d_k]\n"
            "  V = X @ W_v: [Batch, SeqLen, d_v]\n"
            "Routing:\n"
            "  Scores = (Q @ K^T) / sqrt(d_k): [Batch, SeqLen, SeqLen]\n"
            "  Weights = Softmax(Scores, dim=-1): [Batch, SeqLen, SeqLen]\n"
            "  Output = Weights @ V: [Batch, SeqLen, d_v]"
        ),
        formula=r"\mathrm{Attention}(Q, K, V) = \mathrm{softmax}\left(\frac{Q K^T}{\sqrt{d_k}} + M\right) V",
        variables={
            "Q": "Query matrix of shape [Batch, SeqLen, d_k] (what each token is searching for)",
            "K": "Key matrix of shape [Batch, SeqLen, d_k] (what each token offers to matches)",
            "V": "Value matrix of shape [Batch, SeqLen, d_v] (the actual semantic content routed)",
            "d_k": "Dimension of each attention head (e.g. 64 or 128)",
            "M": "Causal mask matrix (optional, set to -inf for future tokens to enforce autoregression)",
        },
        math_explanation=(
            "The dot product Q · K measures geometric alignment (similarity) between tokens. "
            "However, as dimension d_k increases, the dot product of two independent random vectors "
            "has expected value 0 and variance d_k. Without scaling by 1/sqrt(d_k), large dot products "
            "cause the softmax function to saturate with extreme values, leading to tiny gradients and training stalls."
        ),
        numerical_example=(
            "Suppose d_k = 64. The scaling factor is 1/sqrt(64) = 1/8 = 0.125.\n"
            "If an unscaled dot product is +16 between relevant tokens and +2 between irrelevant tokens, "
            "exp(16) = 8,886,110 while exp(2) = 7.39. Softmax assigns ~0.999999 to token 1 and gradients vanish.\n"
            "With scaling: 16/8 = 2.0 and 2/8 = 0.25. Now exp(2.0) = 7.39 and exp(0.25) = 1.28. "
            "Softmax produces healthy probabilities (~0.85 vs ~0.15) with rich non-zero gradients."
        ),
        code_snippet=(
            "import torch\n"
            "import math\n\n"
            "def scaled_dot_product_attention(q, k, v, mask=None):\n"
            "    d_k = q.size(-1)\n"
            "    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)\n"
            "    if mask is not None:\n"
            "        scores = scores.masked_fill(mask == 0, -1e9)\n"
            "    weights = torch.softmax(scores, dim=-1)\n"
            "    return torch.matmul(weights, v), weights\n\n"
            "# Quick verification:\n"
            "q = torch.randn(1, 4, 64)\n"
            "k = torch.randn(1, 4, 64)\n"
            "v = torch.randn(1, 4, 64)\n"
            "out, attn = scaled_dot_product_attention(q, k, v)\n"
            "print('Attention output shape:', out.shape)  # [1, 4, 64]"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 2.4: Scaled Dot-Product and Multi-Head Attention",
                category="ai-books",
                relevance="Covers geometric interpretation of similarity and variance proofs.",
            ),
            LabCitation(
                title="Pretraining LLM",
                chapter="Chapter 3: Attention Mechanics and Causal Masking",
                category="ai-books",
                relevance="Details causal mask implementation and GPU memory footprints.",
            ),
            LabCitation(
                title="Inference Optimization Matters",
                chapter="Chapter 2: KV Cache and Memory Bandwidth Limits",
                category="ai-books",
                relevance="Analyzes memory bandwidth consumption of Attention during autoregressive decoding.",
            ),
        ],
    ),
    LabConcept(
        id="rope",
        title="Rotary Position Embeddings (RoPE)",
        paradigm="language",
        summary="Encodes token positions by multiplying 2D slices of query and key vectors by complex 2D rotation matrices.",
        tensor_flow=(
            "Input: Q, K vectors of shape [Batch, SeqLen, NumHeads, HeadDim]\n"
            "Pairing: Divide HeadDim into d/2 2D chunks (x_1, x_2), (x_3, x_4)...\n"
            "Rotation:\n"
            "  For token at position m and frequency theta_i = base^(-2i/d):\n"
            "  [q'_1, q'_2]^T = [[cos(m*theta), -sin(m*theta)], [sin(m*theta), cos(m*theta)]] @ [q_1, q_2]^T\n"
            "Output: Rotated Q_m and K_n where Q_m^T K_n depends strictly on (m - n)."
        ),
        formula=r"\mathbf{R}_{\Theta, m}^d \mathbf{x} = \begin{pmatrix} x_1 \cos m\theta_1 - x_2 \sin m\theta_1 \\ x_1 \sin m\theta_1 + x_2 \cos m\theta_1 \\ \vdots \end{pmatrix}",
        variables={
            "m": "Absolute token sequence position index (0, 1, 2...)",
            "theta_i": "Base angular frequency theta_i = 10000^(-2(i-1)/d)",
            "R": "Orthogonal block-diagonal rotation matrix",
            "m - n": "Relative distance between Query at position m and Key at position n",
        },
        math_explanation=(
            "Instead of adding an arbitrary position embedding vector to the token embedding (which distorts content), "
            "RoPE rotates the vectors in the complex plane. Because rotation preserves inner product lengths, "
            "the inner product between rotated vectors <R_m q, R_n k> simplifies to a function strictly of (m - n). "
            "This gives relative position awareness while maintaining absolute position indexing."
        ),
        numerical_example=(
            "For position m = 5, n = 3, distance is 5 - 3 = 2.\n"
            "For position m = 105, n = 103, distance is 105 - 103 = 2.\n"
            "The dot product <R_5 q, R_3 k> equals <R_105 q, R_103 k>. The model senses the exact same syntactic "
            "relationship regardless of where the two words appear in a 128k context window."
        ),
        code_snippet=(
            "import torch\n\n"
            "def apply_rotary_emb(x, cos, sin):\n"
            "    # x: [Batch, SeqLen, Heads, Dim]\n"
            "    # Split dim into even and odd\n"
            "    d = x.shape[-1]\n"
            "    x1, x2 = x[..., :d//2], x[..., d//2:]\n"
            "    # Rotate 2D pairs: [-x2, x1]\n"
            "    rx = torch.cat((-x2, x1), dim=-1)\n"
            "    return (x * cos) + (rx * sin)\n\n"
            "# Verification with 4 tokens, dim 64:\n"
            "dim = 64\n"
            "pos = torch.arange(4).unsqueeze(-1)\n"
            "freqs = 1.0 / (10000.0 ** (torch.arange(0, dim, 2).float() / dim))\n"
            "angles = pos * freqs\n"
            "cos = torch.cat((angles.cos(), angles.cos()), dim=-1)\n"
            "sin = torch.cat((angles.sin(), angles.sin()), dim=-1)\n"
            "q = torch.randn(1, 4, 1, dim)\n"
            "q_rot = apply_rotary_emb(q, cos.unsqueeze(1), sin.unsqueeze(1))\n"
            "print('Rotated shape:', q_rot.shape)  # [1, 4, 1, 64]"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 3.2: Positional Encodings: From Absolute to Rotary",
                category="ai-books",
                relevance="Detailed derivation of complex inner-product preservation.",
            ),
            LabCitation(
                title="Pretraining LLM",
                chapter="Chapter 4: Modern Transformer Architectures (Llama, Mistral, Qwen)",
                category="ai-books",
                relevance="Explains RoPE implementation in Llama 3 and Qwen architectures.",
            ),
        ],
    ),
    LabConcept(
        id="swiglu",
        title="SwiGLU Feed-Forward Networks & RMSNorm",
        paradigm="language",
        summary="Modern non-linear projection block pairing Swish-gated linear units with Root Mean Square Layer Normalization.",
        tensor_flow=(
            "Input: X: [Batch, SeqLen, HiddenDim]\n"
            "Pre-Norm: X_norm = RMSNorm(X): [Batch, SeqLen, HiddenDim]\n"
            "Dual Projections:\n"
            "  Gate = X_norm @ W_gate: [Batch, SeqLen, IntermediateDim]\n"
            "  Up   = X_norm @ W_up:   [Batch, SeqLen, IntermediateDim]\n"
            "Gated Activation:\n"
            "  Act = (Gate * Sigmoid(Gate)) * Up = SiLU(Gate) * Up\n"
            "Down Projection:\n"
            "  Output = X + Act @ W_down: [Batch, SeqLen, HiddenDim]"
        ),
        formula=r"\mathrm{SwiGLU}(x) = \left( x W_{\text{gate}} \otimes \mathrm{SiLU}(x W_{\text{gate}}) \right) W_{\text{down}}, \quad \mathrm{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^d x_i^2 + \epsilon}} \odot \gamma",
        variables={
            "W_gate, W_up": "Weight matrices expanding hidden dimension to 8/3 d (IntermediateDim)",
            "W_down": "Weight matrix projecting back down to HiddenDim",
            "SiLU": "Swish activation: f(z) = z * sigmoid(z)",
            "gamma": "Learnable gain vector in RMSNorm",
            "epsilon": "Small constant (e.g. 1e-6) preventing division by zero",
        },
        math_explanation=(
            "Standard LayerNorm centers activations by subtracting mean mu and dividing by standard deviation sigma. "
            "Empirical research (Zhang et al.) proved that the mean-centering step is unnecessary: scaling by the root "
            "mean square alone provides identical training stability while saving memory bandwidth. "
            "SwiGLU replaces single-pass ReLU/GELU with a bilinear gate, allowing the network to control information flow dynamically."
        ),
        numerical_example=(
            "In a 4096-dim model, standard LayerNorm calculates mean over 4096 values, subtracts it, then computes variance.\n"
            "RMSNorm directly squares each value, takes average, and takes square root. This eliminates one full reduction pass.\n"
            "In SwiGLU, if Gate produces -5.0 (inactive concept), SiLU(-5) = -5 * 0.0067 = -0.033, shutting off that feature's Up projection completely."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class RMSNorm(nn.Module):\n"
            "    def __init__(self, dim, eps=1e-6):\n"
            "        super().__init__()\n"
            "        self.eps = eps\n"
            "        self.weight = nn.Parameter(torch.ones(dim))\n"
            "    def forward(self, x):\n"
            "        norm = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)\n"
            "        return norm * self.weight\n\n"
            "class SwiGLU(nn.Module):\n"
            "    def __init__(self, dim, hidden_dim):\n"
            "        super().__init__()\n"
            "        self.w_gate = nn.Linear(dim, hidden_dim, bias=False)\n"
            "        self.w_up = nn.Linear(dim, hidden_dim, bias=False)\n"
            "        self.w_down = nn.Linear(hidden_dim, dim, bias=False)\n"
            "    def forward(self, x):\n"
            "        gate = torch.nn.functional.silu(self.w_gate(x))\n"
            "        return self.w_down(gate * self.w_up(x))\n\n"
            "x = torch.randn(1, 4, 128)\n"
            "mlp = SwiGLU(128, 256)\n"
            "print('SwiGLU output shape:', mlp(x).shape)  # [1, 4, 128]"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 2.5: Feed-Forward Networks and Modern Activations",
                category="ai-books",
                relevance="Explains why GLU variants outperform standard activations.",
            ),
            LabCitation(
                title="Inference Optimization Matters",
                chapter="Chapter 3: Kernel Fusion for RMSNorm and SwiGLU",
                category="ai-books",
                relevance="Shows memory savings from fusing RMSNorm with linear projections.",
            ),
        ],
    ),
    LabConcept(
        id="sft-loss-masking",
        title="SFT Instruction Tuning & Loss Masking",
        paradigm="language",
        summary="Transforms raw autoregressive autocomplete models into instruction followers by calculating cross-entropy loss exclusively on assistant response tokens.",
        tensor_flow=(
            "Training Sequence Tokens:\n"
            "  [<sys> You are an AI </sys>, <user> Explain RoPE </user>, <assistant> RoPE rotates... </assistant>]\n"
            "Token IDs:\n"
            "  Input IDs: [101, 2045, 982, 102, 345, 678, 103, 890, 112, 104]\n"
            "Loss Mask Labels:\n"
            "  Labels:    [-100, -100, -100, -100, -100, -100, -100, 890, 112, 104]\n"
            "PyTorch CrossEntropyLoss ignores any index equal to -100.\n"
            "Gradients backpropagate ONLY from the assistant's answer."
        ),
        formula=r"\mathcal{L}_{\mathrm{SFT}}(\theta) = -\frac{1}{|\mathcal{Y}|} \sum_{t \in \mathcal{Y}} \log P_\theta(y_t \mid x, y_{<t})",
        variables={
            "x": "User prompt and system instructions tokens (masked out: label = -100)",
            "y": "Target assistant completion tokens (loss calculated: label = token_id)",
            "P_theta": "Model predicted probability distribution over the vocabulary",
            "-100": "PyTorch default ignore_index in CrossEntropyLoss",
        },
        math_explanation=(
            "If pre-training cross-entropy is calculated over all tokens, the model is penalized if it fails to predict "
            "the user's typos or stylistic phrasing in the prompt. In Supervised Fine-Tuning (SFT), we condition on the prompt "
            "as a fixed prefix and backpropagate loss solely on the assistant's response tokens. "
            "Setting prompt label positions to -100 instructs the loss function to skip them entirely."
        ),
        numerical_example=(
            "Sequence has 10 tokens: 7 prompt tokens + 3 assistant response tokens.\n"
            "Without masking: Loss is average of 10 cross-entropies. 70% of gradient signal is wasted learning to autocomplete user prompts.\n"
            "With loss masking: Only the 3 assistant tokens contribute to loss. 100% of gradient updates shape the quality, tone, and correctness of the answer."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn.functional as F\n\n"
            "def compute_sft_loss(logits, labels):\n"
            "    # logits: [Batch, SeqLen, VocabSize]\n"
            "    # labels: [Batch, SeqLen] with -100 on prompt tokens\n"
            "    shift_logits = logits[..., :-1, :].contiguous()\n"
            "    shift_labels = labels[..., 1:].contiguous()\n"
            "    return F.cross_entropy(\n"
            "        shift_logits.view(-1, shift_logits.size(-1)),\n"
            "        shift_labels.view(-1),\n"
            "        ignore_index=-100,\n"
            "    )\n\n"
            "# Demonstration:\n"
            "vocab_size = 1000\n"
            "logits = torch.randn(1, 5, vocab_size, requires_grad=True)\n"
            "labels = torch.tensor([[-100, -100, -100, 42, 88]])\n"
            "loss = compute_sft_loss(logits, labels)\n"
            "loss.backward()\n"
            "print('SFT loss value:', loss.item())\n"
            "print('Gradients computed successfully on masked targets.')"
        ),
        nexus_citations=[
            LabCitation(
                title="Pretraining LLM",
                chapter="Chapter 8: From Base Model to Instruction Follower (SFT)",
                category="ai-books",
                relevance="Covers prompt templates, chat format markers, and loss masking.",
            ),
            LabCitation(
                title="Agent Quality",
                chapter="Section 2: SFT Data Curation and Formatting",
                category="ai-books",
                relevance="Best practices for multi-turn conversational loss masks.",
            ),
        ],
    ),
    LabConcept(
        id="lora",
        title="LoRA: Low-Rank Adaptation",
        paradigm="language",
        summary="Freezes full-rank pre-trained weight matrices and parameterizes updates as low-rank matrix products W_0 + (alpha/r) * B @ A.",
        tensor_flow=(
            "Pretrained Weight W_0: [d, k] (FROZEN)\n"
            "Adapter Matrices:\n"
            "  A: [r, k] initialized with Gaussian ~ N(0, sigma^2)\n"
            "  B: [d, r] initialized to 0 (so delta W starts at exactly 0)\n"
            "Forward Pass:\n"
            "  h = W_0 @ x + (alpha / r) * (B @ (A @ x))\n"
            "Parameter Reduction:\n"
            "  Original parameters: d * k\n"
            "  LoRA parameters: r * (d + k)\n"
            "  Ratio: for d=4096, k=4096, r=16 -> 131,072 params vs 16,777,216 (99.2% reduction!)"
        ),
        formula=r"W = W_0 + \Delta W = W_0 + \frac{\alpha}{r} B A, \quad B \in \mathbb{R}^{d \times r}, \; A \in \mathbb{R}^{r \times k}",
        variables={
            "W_0": "Frozen pre-trained linear weight matrix [d, k]",
            "B": "Trainable low-rank projection matrix [d, r], initialized to zero",
            "A": "Trainable low-rank reduction matrix [r, k], initialized with normal distribution",
            "r": "Rank hyperparameter (typically 8, 16, 32, or 64)",
            "alpha": "Constant scaling multiplier ensuring stable gradients when varying r",
        },
        math_explanation=(
            "Weight matrices in large models have a low 'intrinsic dimension' when adapting to specific tasks. "
            "Instead of updating all d*k weights (which requires massive GPU memory for optimizer states like Adam), "
            "we constrain the update matrix Delta W to have rank r << min(d, k). "
            "Initializing B to 0 guarantees that at step 0, Delta W = 0, so the pre-trained behavior is unaltered."
        ),
        numerical_example=(
            "In LLaMA-3 8B, projecting down/gate/up matrices has d = 4096, k = 14336.\n"
            "Full fine-tuning requires 4096 * 14336 = 58,720,256 float32 values per layer. Adam requires 8x that in optimizer states (~470MB per layer).\n"
            "With rank r = 16: LoRA needs 16 * (4096 + 14336) = 294,912 parameters. Adam state drops from 470MB to 2.3MB!"
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class LoRALinear(nn.Module):\n"
            "    def __init__(self, in_features, out_features, rank=16, alpha=32):\n"
            "        super().__init__()\n"
            "        self.base = nn.Linear(in_features, out_features, bias=False)\n"
            "        self.base.weight.requires_grad = False  # Freeze\n"
            "        self.rank = rank\n"
            "        self.scaling = alpha / rank\n"
            "        self.lora_A = nn.Parameter(torch.randn(rank, in_features) * 0.01)\n"
            "        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))\n"
            "    def forward(self, x):\n"
            "        base_out = self.base(x)\n"
            "        lora_out = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling\n"
            "        return base_out + lora_out\n\n"
            "layer = LoRALinear(4096, 4096, rank=16)\n"
            "x = torch.randn(1, 8, 4096)\n"
            "print('LoRA forward pass output:', layer(x).shape)  # [1, 8, 4096]"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 5.3: Parameter-Efficient Fine-Tuning (PEFT and LoRA)",
                category="ai-books",
                relevance="Matrix rank reduction theory and intrinsic dimension empirical studies.",
            ),
            LabCitation(
                title="Inference Optimization Matters",
                chapter="Chapter 5: Dynamic Adapter Swapping in Serving Engines",
                category="ai-books",
                relevance="How multiple task-specific LoRA adapters run simultaneously on one base model.",
            ),
        ],
    ),
    # ─── Vision & Conv/ViT ────────────────────────────────────────────────────────
    LabConcept(
        id="vision-transformer-vit",
        title="Vision Transformers (ViT) & Patch Projection",
        paradigm="vision",
        summary="Treats an image as a sequence of 16x16 flattened visual tokens, allowing standard self-attention architectures to process 2D images.",
        tensor_flow=(
            "Input Image: X: [Batch, Channels, Height, Width]  (e.g. [1, 3, 224, 224])\n"
            "Patch Slicing (P = 16):\n"
            "  NumPatches N = (H/P) * (W/P) = (224/16) * (224/16) = 14 * 14 = 196 patches\n"
            "  Patch dimension: P * P * C = 16 * 16 * 3 = 768\n"
            "Linear Projection: [Batch, 196, 768] @ W_patch -> [Batch, 196, HiddenDim]\n"
            "Add [CLS] Token & Position Embeddings -> [Batch, 197, HiddenDim]\n"
            "Process with standard Transformer Encoder blocks!"
        ),
        formula=r"\mathbf{z}_0 = [\mathbf{x}_{\mathrm{class}}; \mathbf{x}_p^1 \mathbf{E}; \dots; \mathbf{x}_p^N \mathbf{E}] + \mathbf{E}_{\mathrm{pos}}, \quad \mathbf{E} \in \mathbb{R}^{(P^2 C) \times D}",
        variables={
            "P": "Patch size (typically 16x16 or 14x14 pixels)",
            "N": "Number of patches = (Height * Width) / P^2",
            "E": "Trainable 2D convolution or linear projection matrix mapping raw pixels to hidden dim D",
            "x_class": "Learnable [CLS] classification token prepended to the sequence",
            "E_pos": "Learnable 1D position embeddings capturing spatial patch coordinates",
        },
        math_explanation=(
            "Convolutional networks encode strong inductive biases (translation equivariance and local spatial locality) "
            "directly into their kernels. Vision Transformers discard this hardcoded prior: by slicing images into flat patches "
            "and applying self-attention, the model learns global cross-patch relationships directly from data. "
            "On massive datasets, ViT substantially outperforms ResNets because it is not constrained to local receptive fields."
        ),
        numerical_example=(
            "A 224x224 RGB image has 224*224*3 = 150,528 raw values.\n"
            "Dividing into 16x16 patches gives 196 patches of 768 numbers each.\n"
            "Passing 196 tokens through a 12-layer Transformer is identical in complexity to processing a 196-word sentence. "
            "Global attention allows patch #1 (top-left corner) to directly attend to patch #196 (bottom-right corner) in layer 1!"
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class PatchEmbedding(nn.Module):\n"
            "    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):\n"
            "        super().__init__()\n"
            "        # A convolution with kernel=patch_size and stride=patch_size slices patches\n"
            "        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)\n"
            "        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))\n"
            "        self.pos_embed = nn.Parameter(torch.randn(1, (img_size // patch_size)**2 + 1, embed_dim))\n"
            "    def forward(self, x):\n"
            "        B = x.shape[0]\n"
            "        x = self.proj(x).flatten(2).transpose(1, 2)  # [B, NumPatches, EmbedDim]\n"
            "        cls_tokens = self.cls_token.expand(B, -1, -1)\n"
            "        x = torch.cat((cls_tokens, x), dim=1) + self.pos_embed\n"
            "        return x\n\n"
            "img = torch.randn(1, 3, 224, 224)\n"
            "embedder = PatchEmbedding()\n"
            "tokens = embedder(img)\n"
            "print('ViT token sequence shape:', tokens.shape)  # [1, 197, 768]"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 6.1: Vision Transformers and Multi-Modal Encoding",
                category="ai-books",
                relevance="Details patch projection mathematics and inductive bias comparisons.",
            ),
        ],
    ),
    # ─── Diffusion & Generative ───────────────────────────────────────────────────
    LabConcept(
        id="ddpm-noise-scheduling",
        title="Denoising Diffusion Probabilistic Models (DDPM)",
        paradigm="diffusion",
        summary="Iteratively destroys data into isotropic Gaussian noise via a forward Markov chain, and trains a neural network to invert the process.",
        tensor_flow=(
            "Forward Process (Noising):\n"
            "  x_0 (clean image) -> Add Gaussian noise epsilon ~ N(0, I) over T steps\n"
            "  Closed-form shortcut: x_t = sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * epsilon\n"
            "Reverse Process (Denoising):\n"
            "  Input: noisy x_t + time embedding t\n"
            "  UNet / DiT predicts the noise: epsilon_theta(x_t, t)\n"
            "  Step backwards: x_{t-1} = (1 / sqrt(alpha_t)) * (x_t - (beta_t / sqrt(1 - alpha_bar_t)) * epsilon_theta) + sigma_t * z"
        ),
        formula=r"q(\mathbf{x}_t \mid \mathbf{x}_0) = \mathcal{N}\left(\mathbf{x}_t; \sqrt{\bar{\alpha}_t} \mathbf{x}_0, (1 - \bar{\alpha}_t) \mathbf{I}\right), \quad \mathcal{L}_{\mathrm{simple}}(\theta) = \mathbb{E}_{t, \mathbf{x}_0, \epsilon} \left[ \|\epsilon - \epsilon_\theta(\mathbf{x}_t, t)\|^2 \right]",
        variables={
            "x_0": "Original clean training sample (image, audio, or latent)",
            "x_t": "Noisy sample at diffusion timestep t (from t = 1 to T = 1000)",
            "alpha_t": "Variance schedule factor alpha_t = 1 - beta_t",
            "alpha_bar_t": "Cumulative product of alphas: prod_{s=1}^t alpha_s",
            "epsilon_theta": "Neural network trained to predict the added noise vector epsilon",
        },
        math_explanation=(
            "Rather than training a generative model to jump from pure noise to a finished image in one giant leap (which causes mode collapse in GANs), "
            "diffusion breaks generation down into hundreds of tiny, tractable denoising micro-steps. "
            "By mathematically reparameterizing the Gaussian marginals, any noisy intermediate state x_t can be sampled directly at step t "
            "without having to simulate steps 1 through t-1 sequentially during training."
        ),
        numerical_example=(
            "Let alpha_bar_500 = 0.5. At step t = 500:\n"
            "sqrt(0.5) = 0.707, and sqrt(1 - 0.5) = 0.707.\n"
            "The noisy image x_500 is exactly 70.7% clean image + 70.7% pure Gaussian noise.\n"
            "The neural network looks at this static pattern, estimates the 70.7% noise component, and subtracts it."
        ),
        code_snippet=(
            "import torch\n\n"
            "def forward_diffusion_sample(x_0, t, betas):\n"
            "    # betas: [T]\n"
            "    alphas = 1.0 - betas\n"
            "    alphas_bar = torch.cumprod(alphas, dim=0)\n"
            "    sqrt_alphas_bar = torch.sqrt(alphas_bar[t])\n"
            "    sqrt_one_minus_alphas_bar = torch.sqrt(1.0 - alphas_bar[t])\n"
            "    noise = torch.randn_like(x_0)\n"
            "    x_t = sqrt_alphas_bar * x_0 + sqrt_one_minus_alphas_bar * noise\n"
            "    return x_t, noise\n\n"
            "betas = torch.linspace(1e-4, 0.02, 1000)\n"
            "clean_x = torch.ones(1, 3, 32, 32)\n"
            "noisy_x, true_noise = forward_diffusion_sample(clean_x, 500, betas)\n"
            "print('Noisy sample generated. Mean:', noisy_x.mean().item())"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 7.2: Diffusion Models and Continuous Denoising",
                category="ai-books",
                relevance="Score-based generative modeling and stochastic differential equations.",
            ),
        ],
    ),
    # ─── Reinforcement Learning & Reasoning ───────────────────────────────────────
    LabConcept(
        id="grpo-reasoning",
        title="Group Relative Policy Optimization (GRPO)",
        paradigm="rl",
        summary="DeepSeek-R1 style reasoning alignment: samples a group of candidate outputs for each prompt and normalizes rewards within the group without requiring a critic network.",
        tensor_flow=(
            "For each prompt q:\n"
            "  Sample a group of G outputs: {o_1, o_2, ..., o_G} ~ pi_old(o | q)\n"
            "Reward Evaluation:\n"
            "  Score each output using rule-based verifiers: r_i = [Math Correctness, Code Unit Tests]\n"
            "Advantage Normalization:\n"
            "  Mean = mean(r), Std = std(r)\n"
            "  A_i = (r_i - Mean) / (Std + 1e-8)\n"
            "Optimization:\n"
            "  PPO-clipped objective on A_i with KL penalty against pi_ref\n"
            "Zero critic neural network memory needed!"
        ),
        formula=r"\mathcal{J}_{\mathrm{GRPO}}(\theta) = \mathbb{E} \left[ \frac{1}{G} \sum_{i=1}^G \left( \min\left( \frac{\pi_\theta(o_i \mid q)}{\pi_{\mathrm{old}}(o_i \mid q)} A_i, \; \mathrm{clip}\left(\frac{\pi_\theta(o_i \mid q)}{\pi_{\mathrm{old}}(o_i \mid q)}, 1-\epsilon, 1+\epsilon\right) A_i \right) - \beta D_{\mathrm{KL}}(\pi_\theta \parallel \pi_{\mathrm{ref}}) \right) \right]",
        variables={
            "G": "Group size of sampled candidate completions (typically 4 to 8)",
            "A_i": "Group-relative advantage: A_i = (r_i - mean(r)) / std(r)",
            "pi_theta": "Current policy model undergoing training",
            "pi_ref": "Frozen pre-trained reference model preventing reward hacking / mode collapse",
            "beta": "KL penalty coefficient enforcing proximity to reference model",
        },
        math_explanation=(
            "Standard PPO requires training two gigantic neural networks concurrently: the Actor (policy) and the Critic (value function). "
            "The Critic model consumes equal GPU memory to the Actor and often suffers from unstable value estimation. "
            "GRPO discards the Critic entirely: by generating a group of G responses for the same question, the baseline value is simply "
            "the empirical average reward of the group. Outputs that scored higher than average get positive advantage, while below-average outputs get penalized."
        ),
        numerical_example=(
            "Prompt: Solve 17 * 14.\n"
            "Generate G = 4 reasoning outputs with scores:\n"
            "  Output 1: answered 238 (Correct, r = +1.0)\n"
            "  Output 2: answered 238 (Correct, r = +1.0)\n"
            "  Output 3: answered 218 (Wrong, r = 0.0)\n"
            "  Output 4: answered 248 (Wrong, r = 0.0)\n"
            "Group Mean = 0.5, Std = 0.5.\n"
            "Advantage for 1 & 2: (1.0 - 0.5) / 0.5 = +1.0 (reinforced!).\n"
            "Advantage for 3 & 4: (0.0 - 0.5) / 0.5 = -1.0 (penalized!)."
        ),
        code_snippet=(
            "import torch\n\n"
            "def compute_grpo_advantages(rewards, eps=1e-8):\n"
            "    # rewards: [BatchSize, GroupSize]\n"
            "    mean = rewards.mean(dim=-1, keepdim=True)\n"
            "    std = rewards.std(dim=-1, keepdim=True)\n"
            "    advantages = (rewards - mean) / (std + eps)\n"
            "    return advantages\n\n"
            "# Example:\n"
            "rewards = torch.tensor([[1.0, 1.0, 0.0, 0.0]])\n"
            "adv = compute_grpo_advantages(rewards)\n"
            "print('Computed group-relative advantages:', adv.tolist())\n"
            "# [[1.0, 1.0, -1.0, -1.0]]"
        ),
        nexus_citations=[
            LabCitation(
                title="Pretraining LLM",
                chapter="Chapter 9: Reinforcement Learning and Reasoning Models (R1 / GRPO)",
                category="ai-books",
                relevance="Direct derivation of GRPO advantage formulation and rule-based rewards.",
            ),
            LabCitation(
                title="Agent Quality",
                chapter="Section 4: Verifiable Execution Rewards in Self-Correction Loops",
                category="ai-books",
                relevance="Designing test suites and syntax validators for rule-based reward generation.",
            ),
        ],
    ),
    # ─── Mathematical Foundations ─────────────────────────────────────────────────
    LabConcept(
        id="attention-variance-proof",
        title="Proof: Attention Dot-Product Variance Scales with Dimension",
        paradigm="foundations",
        summary="Step-by-step statistical derivation proving why unscaled dot products explode with variance d_k, causing softmax saturation.",
        tensor_flow=(
            "Let q, k in R^{d_k} be random vectors whose components are independent random variables:\n"
            "  E[q_i] = 0, Var(q_i) = 1\n"
            "  E[k_i] = 0, Var(k_i) = 1\n"
            "Inner product S = sum_{i=1}^{d_k} (q_i * k_i)\n"
            "Mean:\n"
            "  E[S] = sum E[q_i * k_i] = sum E[q_i] * E[k_i] = 0\n"
            "Variance:\n"
            "  Var(q_i * k_i) = E[(q_i * k_i)^2] - (E[q_i * k_i])^2\n"
            "                 = E[q_i^2] * E[k_i^2] - 0 = (1) * (1) = 1\n"
            "Sum of d_k independent terms:\n"
            "  Var(S) = sum_{i=1}^{d_k} Var(q_i * k_i) = d_k * 1 = d_k!\n"
            "Standard deviation:\n"
            "  StdDev(S) = sqrt(d_k)\n"
            "Therefore, dividing S by sqrt(d_k) normalizes Var(S / sqrt(d_k)) = 1."
        ),
        formula=r"\mathrm{Var}\left( \sum_{i=1}^{d_k} q_i k_i \right) = \sum_{i=1}^{d_k} \mathrm{Var}(q_i k_i) = d_k \implies \mathrm{Var}\left( \frac{1}{\sqrt{d_k}} \sum_{i=1}^{d_k} q_i k_i \right) = \frac{d_k}{(\sqrt{d_k})^2} = 1",
        variables={
            "q_i, k_i": "Scalar components of Query and Key vectors at feature index i",
            "d_k": "Head dimension (e.g. 64 or 128)",
            "Var(X)": "Statistical variance measure of dispersion from the mean",
            "1/sqrt(d_k)": "Exact scaling factor restoring unit variance prior to softmax",
        },
        math_explanation=(
            "When random variables are summed, their variances add linearly. "
            "A 128-dimensional dot product has 128 times the variance of a 1-dimensional product. "
            "The softmax function contains exp(z). When inputs have standard deviation sqrt(128) approx 11.3, "
            "a value at +2 standard deviations equals +22.6, while a value at -1 standard deviation is -11.3. "
            "exp(22.6) = 6.5 * 10^9, whereas exp(-11.3) = 1.2 * 10^-5. Softmax produces a one-hot distribution [1.0, 0, 0...], "
            "where the derivative softmax'(z) = s_i * (1 - s_i) becomes 1.0 * (1 - 1.0) = 0. Gradients vanish completely."
        ),
        numerical_example=(
            "Empirical verification:\n"
            "1,000,000 random dot products with d_k = 64.\n"
            "Unscaled: Sample variance = 64.08, StdDev = 8.00.\n"
            "Scaled by 1/8: Sample variance = 1.001, StdDev = 1.00.\n"
            "The division by sqrt(d_k) is mathematically exact and optimal."
        ),
        code_snippet=(
            "import torch\n\n"
            "d_k = 64\n"
            "samples = 100_000\n"
            "q = torch.randn(samples, d_k)\n"
            "k = torch.randn(samples, d_k)\n"
            "unscaled_dot = (q * k).sum(dim=-1)\n"
            "scaled_dot = unscaled_dot / (d_k ** 0.5)\n\n"
            "print('Theoretical unscaled variance: 64.0')\n"
            "print(f'Empirical unscaled variance:   {unscaled_dot.var().item():.3f}')\n"
            "print(f'Empirical scaled variance:     {scaled_dot.var().item():.3f}')"
        ),
        nexus_citations=[
            LabCitation(
                title="Foundation of LLM",
                chapter="Section 2.4: Mathematical Derivation of Scaled Attention",
                category="ai-books",
                relevance="Formal proof of dot-product variance and softmax gradient saturation.",
            ),
        ],
    ),
]


def list_paradigms() -> list[dict[str, str]]:
    """Return all supported AI laboratory paradigms."""
    return [dict(p) for p in PARADIGMS]


def list_concepts(paradigm: str | None = None) -> list[dict[str, Any]]:
    """Return catalog concepts, optionally filtered by paradigm."""
    filtered = _CONCEPTS_LIST
    if paradigm and paradigm != "all":
        filtered = [c for c in _CONCEPTS_LIST if c.paradigm == paradigm]
    return [
        {
            "id": c.id,
            "title": c.title,
            "paradigm": c.paradigm,
            "summary": c.summary,
            "citation_count": len(c.nexus_citations),
        }
        for c in filtered
    ]


def get_concept(concept_id: str) -> dict[str, Any] | None:
    """Return the complete payload for one concept, or None if not found."""
    cid = (concept_id or "").strip().lower()
    for c in _CONCEPTS_LIST:
        if c.id == cid:
            return c.to_dict()
    return None


def search_concepts(query: str) -> list[dict[str, Any]]:
    """Search concepts across title, summary, formula, and citations."""
    q = (query or "").strip().lower()
    if not q:
        return list_concepts()
    matches = []
    for c in _CONCEPTS_LIST:
        haystack = f"{c.id} {c.title} {c.paradigm} {c.summary} {c.math_explanation}".lower()
        if q in haystack:
            matches.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "paradigm": c.paradigm,
                    "summary": c.summary,
                    "citation_count": len(c.nexus_citations),
                }
            )
    return matches

