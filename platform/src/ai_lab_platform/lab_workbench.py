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
    {"id": "all", "label": "All Topics", "icon": "🔬"},
    {"id": "foundations", "label": "1. Math & Statistics", "icon": "📐"},
    {"id": "language", "label": "2. Language & LLMs", "icon": "📝"},
    {"id": "rl", "label": "3. RL & Reasoning", "icon": "🎯"},
    {"id": "vision", "label": "4. Vision & ViT", "icon": "👁️"},
    {"id": "diffusion", "label": "5. Diffusion & GenAI", "icon": "✨"},
    {"id": "multimodal", "label": "6. Multimodal Systems", "icon": "🌐"},
    {"id": "audio", "label": "7. Audio & Speech", "icon": "🎙️"},
]

_CONCEPTS_LIST: list[LabConcept] = [
    # ══════════════════════════════════════════════════════════════════════════════
    # TIER 1: MATHEMATICAL & STATISTICAL FOUNDATIONS
    # ══════════════════════════════════════════════════════════════════════════════
    LabConcept(
        id="linear-algebra-scalars-vectors",
        title="Linear Algebra 101: Scalars, Vectors & 2D Geometry",
        paradigm="foundations",
        summary="The fundamental primitives of mathematics: scalars as magnitudes, vectors as directional arrows in 2D space, addition, scaling, and length.",
        tensor_flow=(
            "Scalars (Single Real Numbers):\n"
            "  c ∈ ℝ (e.g. c = 2.5, a magnitude without direction)\n"
            "2D Vectors (Arrows in a Cartesian Plane):\n"
            "  v = [x, y] (e.g. [3, 2] = 3 steps right along X, 2 steps up along Y)\n"
            "Elementary Geometric Operations:\n"
            "  1. Vector Addition (Tip-to-Tail): [x1, y1] + [x2, y2] = [x1+x2, y1+y2]\n"
            "  2. Scalar Multiplication: c · [x, y] = [c·x, c·y] (Stretch / shrink / flip)\n"
            "  3. Length (Pythagorean Theorem): ||v||_2 = sqrt(x^2 + y^2)\n"
            "  4. Unit Vector (Direction Only): v_hat = v / ||v||_2 (Length = 1.0)"
        ),
        formula=r"\mathbf{v} = \begin{bmatrix} x \\ y \end{bmatrix}, \quad \|\mathbf{v}\|_2 = \sqrt{x^2 + y^2}, \quad \hat{\mathbf{v}} = \frac{\mathbf{v}}{\|\mathbf{v}\|_2}",
        variables={
            "c": "A scalar: a single number representing magnitude (speed, temperature, loss value)",
            "v": "A vector: an ordered list of numbers with both magnitude and direction",
            "x, y": "Coordinates indicating horizontal and vertical displacement from the origin (0, 0)",
            "||v||_2": "Euclidean length (L2 norm) calculated using the classic Pythagorean theorem (a^2 + b^2 = c^2)",
            "v_hat": "Normalized unit vector of length exactly 1.0, preserving pure direction",
        },
        math_explanation=(
            "A scalar is just a single number (e.g., speed = 60 mph, temperature = 72°F). It has magnitude, but no direction. "
            "A vector is an ordered list of numbers with both magnitude and direction (e.g., velocity = 60 mph heading North-East). "
            "In 2D space, a vector [x, y] represents an arrow starting at the origin (0, 0) and pointing to coordinate (x, y). "
            "Vector addition is geometric: you place the tail of the second arrow at the tip of the first arrow (the tip-to-tail rule). "
            "Scalar multiplication scales the arrow's length: multiplying by 2 doubles its length; multiplying by -1 flips its direction 180°. "
            "Every advanced concept in AI—from 4096-dimensional word embeddings to deep transformer weights—is constructed by combining these two basic operations: scaling and adding."
        ),
        numerical_example=(
            "Let arrow v1 = [3, 2] (3 steps right, 2 steps up) and arrow v2 = [1, 4] (1 step right, 4 steps up).\n"
            "1. Vector Addition: v1 + v2 = [3+1, 2+4] = [4, 6]. The combined journey ends at coordinate (4, 6).\n"
            "2. Scalar Multiplication: 2 × v1 = [2×3, 2×2] = [6, 4]. The arrow is now twice as long in the same direction.\n"
            "3. Direction Reversal: -1 × v1 = [-3, -2]. The arrow flips 180° into the negative quadrant.\n"
            "4. Length (Magnitude): ||v1|| = sqrt(3^2 + 2^2) = sqrt(9 + 4) = sqrt(13) ≈ 3.6055 units long.\n"
            "5. Unit Vector: v1_hat = [3 / 3.6055, 2 / 3.6055] ≈ [0.8321, 0.5547].\n"
            "   Verification: sqrt(0.8321^2 + 0.5547^2) = sqrt(0.6923 + 0.3077) = 1.0000."
        ),
        code_snippet=(
            "import torch\n\n"
            "# 1. Define two 2D vectors (arrows in space):\n"
            "v1 = torch.tensor([3.0, 2.0])\n"
            "v2 = torch.tensor([1.0, 4.0])\n\n"
            "# 2. Vector addition (tip-to-tail combined displacement):\n"
            "v_sum = v1 + v2  # tensor([4., 6.])\n"
            "print(f'v1 + v2 = {v_sum.tolist()}')\n\n"
            "# 3. Scalar multiplication (stretching by 2x):\n"
            "v_scaled = 2.0 * v1  # tensor([6., 4.])\n"
            "print(f'2 * v1 = {v_scaled.tolist()}')\n\n"
            "# 4. Vector length (L2 norm via Pythagorean theorem):\n"
            "length_v1 = torch.linalg.norm(v1)\n"
            "print(f'Length of v1: {length_v1.item():.4f}')  # ~3.6055\n\n"
            "# 5. Normalize to unit vector (length 1.0):\n"
            "v1_hat = v1 / length_v1\n"
            "print(f'Unit vector v1_hat: {v1_hat.tolist()}')\n"
            "assert abs(torch.linalg.norm(v1_hat).item() - 1.0) < 1e-6"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 1: Linear Algebra — Vectors, Dot Products, and Coordinate Systems",
                category="Data_Science",
                relevance="First-principles tutorial on Cartesian coordinates, vector arithmetic, and geometric intuition.",
            ),
            LabCitation(
                title="Mathematics for Machine Learning",
                chapter="Chapter 2: Linear Algebra — Vector Spaces and Linear Independence",
                category="AI_and_Machine_Learning",
                relevance="Rigorous definitions of vector addition, scalar closure, and coordinate representations.",
            ),
        ],
    ),
    LabConcept(
        id="matrix-transformations-101",
        title="Linear Algebra 102: Matrices as Space Transformations",
        paradigm="foundations",
        summary="A matrix is not just a table of numbers: it is a machine that transforms space. How basis vectors i-hat and j-hat determine where every point lands.",
        tensor_flow=(
            "Standard Basis Vectors in 2D:\n"
            "  i_hat = [1, 0] (unit step right along X-axis)\n"
            "  j_hat = [0, 1] (unit step up along Y-axis)\n"
            "Any Vector as Linear Combination:\n"
            "  x = [x1, x2] = x1 * i_hat + x2 * j_hat\n"
            "Matrix Transformation A:\n"
            "  A = [ [a, b],\n"
            "        [c, d] ]\n"
            "  Column 1 [a, c] tells you where i_hat lands!\n"
            "  Column 2 [b, d] tells you where j_hat lands!\n"
            "Matrix-Vector Product A @ x:\n"
            "  A @ x = x1 * [a, c] + x2 * [b, d] = [a*x1 + b*x2, c*x1 + d*x2]\n"
            "Neural Network Linear Layer:\n"
            "  y = W @ x + b (W transforms space, b shifts the origin)"
        ),
        formula=r"A = \begin{bmatrix} a & b \\ c & d \end{bmatrix}, \quad A \begin{bmatrix} x \\ y \end{bmatrix} = x \begin{bmatrix} a \\ c \end{bmatrix} + y \begin{bmatrix} b \\ d \end{bmatrix} = \begin{bmatrix} ax + by \\ cx + dy \end{bmatrix}",
        variables={
            "i_hat, j_hat": "Standard unit basis vectors along the X and Y axes",
            "A": "A 2x2 matrix representing a linear transformation of the 2D plane",
            "Column 1 [a, c]^T": "The new landing coordinate of i-hat after the transformation",
            "Column 2 [b, d]^T": "The new landing coordinate of j-hat after the transformation",
            "x = [x, y]^T": "Any arbitrary input vector in the coordinate plane",
            "A @ x": "The output coordinate after applying the transformation",
            "y = Wx + b": "The fundamental linear layer of all neural networks",
        },
        math_explanation=(
            "Do not think of a matrix as just a spreadsheet of numbers. Geometrically, a matrix is a transformation that warps space. "
            "Because the transformation is linear, grid lines remain straight and parallel, and the origin (0, 0) never moves. "
            "To know where every single point in the infinite plane moves, you only need to track where two tiny unit vectors land: "
            "i-hat = [1, 0] (one step right) and j-hat = [0, 1] (one step up). "
            "The first column of matrix A is literally where i-hat lands. The second column is where j-hat lands. "
            "When you multiply A times [x, y], you take x copies of the transformed i-hat plus y copies of the transformed j-hat. "
            "In deep learning, every linear layer y = Wx + b is doing this exact geometric operation: rotating, stretching, and shearing the input data into a new space where categories are easily separated."
        ),
        numerical_example=(
            "Let's construct a transformation that rotates 2D space 90 degrees counter-clockwise.\n"
            "1. Where does i-hat [1, 0] land? Rotating 90° CCW points it straight up: [0, 1]. This is Column 1.\n"
            "2. Where does j-hat [0, 1] land? Rotating 90° CCW points it to the left: [-1, 0]. This is Column 2.\n"
            "3. Assemble the rotation matrix: R = [[0, -1], [1, 0]].\n"
            "4. Now transform an arbitrary vector x = [3, 2] (3 units right, 2 units up):\n"
            "   R @ x = 3 × [0, 1] + 2 × [-1, 0] = [0, 3] + [-2, 0] = [-2, 3].\n"
            "5. Verification: If you take graph paper and rotate point (3, 2) 90° counter-clockwise, it lands precisely at (-2, 3)!\n"
            "   Matrix multiplication successfully predicted the exact geometric motion."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "# 1. Define a 90-degree counter-clockwise rotation matrix:\n"
            "# Col 1 = where [1, 0] lands -> [0, 1]\n"
            "# Col 2 = where [0, 1] lands -> [-1, 0]\n"
            "R = torch.tensor([[0.0, -1.0],\n"
            "                  [1.0,  0.0]])\n\n"
            "# 2. Transform the vector x = [3, 2]:\n"
            "x = torch.tensor([3.0, 2.0])\n"
            "x_rotated = R @ x  # tensor([-2., 3.])\n"
            "print(f'Point (3, 2) rotated 90° CCW: {x_rotated.tolist()}')\n\n"
            "# 3. In PyTorch, an nn.Linear layer is this exact matrix transformation:\n"
            "linear = nn.Linear(in_features=2, out_features=2, bias=False)\n"
            "linear.weight.data = R\n"
            "output = linear(x)\n"
            "print(f'nn.Linear output: {output.tolist()}')\n"
            "assert torch.allclose(output, torch.tensor([-2.0, 3.0]))"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 1: Linear Algebra — Matrix Transformations and Basis Vectors",
                category="Data_Science",
                relevance="Detailed geometric illustrations of basis vectors and spatial coordinate changes.",
            ),
            LabCitation(
                title="Deep Learning",
                chapter="Chapter 2: Linear Algebra — Matrices, Linear Transformations, and Inverses",
                category="AI_and_Machine_Learning",
                relevance="Foundational textbook explanation of how neural network layers parameterize linear maps.",
            ),
        ],
    ),
    LabConcept(
        id="dot-product-101",
        title="Linear Algebra 103: The Dot Product & Geometric Projections",
        paradigm="foundations",
        summary="Why multiplying two vectors and summing pairwise products measures directional alignment, how projection works, and how artificial neurons fire.",
        tensor_flow=(
            "Input Vectors in 2D Space:\n"
            "  a = [a1, a2]\n"
            "  b = [b1, b2]\n"
            "Algebraic Definition:\n"
            "  a · b = (a1 * b1) + (a2 * b2)\n"
            "Geometric Definition:\n"
            "  a · b = ||a||_2 * ||b||_2 * cos(θ)\n"
            "Geometric Projection:\n"
            "  Length of shadow of 'a' onto line of 'b' = ||a|| * cos(θ)\n"
            "Three Core Geometric Cases:\n"
            "  θ = 0°   --> cos(θ) = +1.0 (Parallel, max alignment)\n"
            "  θ = 90°  --> cos(θ) =  0.0 (Perpendicular / Orthogonal, zero correlation)\n"
            "  θ = 180° --> cos(θ) = -1.0 (Opposite, maximum disagreement)\n"
            "The Artificial Neuron:\n"
            "  Activation = σ(w · x + b)"
        ),
        formula=r"\mathbf{a} \cdot \mathbf{b} = a_1 b_1 + a_2 b_2 = \|\mathbf{a}\|_2 \|\mathbf{b}\|_2 \cos(\theta), \quad \cos(\theta) = \frac{\mathbf{a} \cdot \mathbf{b}}{\|\mathbf{a}\|_2 \|\mathbf{b}\|_2}",
        variables={
            "a, b": "Two vectors in the same coordinate space",
            "a · b": "The scalar dot product (inner product)",
            "||a||_2, ||b||_2": "Euclidean lengths (magnitudes) of the two vectors",
            "θ": "Angle between the two vectors (0° to 180°)",
            "cos(θ)": "Directional similarity score ranging from -1.0 to +1.0",
            "w · x + b": "Artificial neuron: weight vector w dotted with input feature vector x",
        },
        math_explanation=(
            "Why do we multiply matching coordinates and add them together? "
            "Geometrically, the dot product projects one arrow onto another. Imagine a light shining directly perpendicular to vector b: "
            "the shadow of vector a falling along vector b has length ||a|| cos(θ). "
            "Multiplying this shadow length by the length of vector b gives the dot product: a · b = ||a|| ||b|| cos(θ). "
            "This reveals three crucial geometric insights: "
            "1. When two vectors point in the exact same direction (θ = 0°), cos(0°) = 1, giving the maximum possible positive value. "
            "2. When two vectors are perpendicular (θ = 90°), vector a casts NO shadow onto vector b at all! The dot product is exactly 0. In AI, this means the two features share zero correlation. "
            "3. When they point in opposite directions (θ = 180°), the dot product is negative. "
            "In an artificial neuron, the inputs x are dotted with weights w: if input features align with the weights, the neuron fires strongly; if they are orthogonal, the neuron ignores them."
        ),
        numerical_example=(
            "Let vector a = [3.0, 0.0] (length 3, lies along the horizontal X-axis) and vector b = [2.0, 2.0] (length sqrt(2^2 + 2^2) = sqrt(8) ≈ 2.828, at a 45° angle).\n"
            "1. Algebraic Dot Product: a · b = (3.0 × 2.0) + (0.0 × 2.0) = 6.0 + 0.0 = 6.0.\n"
            "2. Geometric Lengths: ||a|| = 3.0, ||b|| = 2.8284.\n"
            "3. Cosine of Angle: cos(θ) = (a · b) / (||a|| × ||b||) = 6.0 / (3.0 × 2.8284) = 6.0 / 8.4853 = 0.7071.\n"
            "4. Recover Angle: arccos(0.7071) = 45.0°! The algebraic calculation matches the geometric angle perfectly.\n"
            "5. Orthogonal Test: Let c = [0.0, 4.0] (points straight up at 90° to a):\n"
            "   a · c = (3.0 × 0.0) + (0.0 × 4.0) = 0.0. cos(θ) = 0 / 12 = 0.0 (θ = 90°). Exactly zero shadow, completely independent."
        ),
        code_snippet=(
            "import math\n"
            "import torch\n\n"
            "# 1. Define vectors a along X-axis, b at 45°, and c perpendicular at 90°:\n"
            "a = torch.tensor([3.0, 0.0])\n"
            "b = torch.tensor([2.0, 2.0])\n"
            "c = torch.tensor([0.0, 4.0])\n\n"
            "# 2. Compute dot products:\n"
            "dot_ab = torch.dot(a, b)  # (3*2) + (0*2) = 6.0\n"
            "dot_ac = torch.dot(a, c)  # (3*0) + (0*4) = 0.0 (Orthogonal!)\n\n"
            "print(f'Dot product a · b: {dot_ab.item():.1f}')\n"
            "print(f'Dot product a · c (orthogonal): {dot_ac.item():.1f}')\n\n"
            "# 3. Calculate angle between a and b:\n"
            "cos_theta = dot_ab / (torch.linalg.norm(a) * torch.linalg.norm(b))\n"
            "angle_deg = math.degrees(math.acos(cos_theta.item()))\n"
            "print(f'Angle between a and b: {angle_deg:.1f}°')  # 45.0°\n"
            "assert abs(angle_deg - 45.0) < 1e-4\n"
            "assert dot_ac.item() == 0.0"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 1: The Dot Product and Orthogonality",
                category="Data_Science",
                relevance="First-principles geometric proofs of dot products, shadows, and angle cosine formulas.",
            ),
            LabCitation(
                title="Mathematics for Machine Learning",
                chapter="Chapter 3: Analytic Geometry — Norms, Angles, and Inner Products",
                category="AI_and_Machine_Learning",
                relevance="Rigorous inner product definitions and geometric interpretations for machine learning.",
            ),
        ],
    ),
    LabConcept(
        id="statistics-101",
        title="Statistics 101: Mean, Variance, Std Deviation & Normal Distribution",
        paradigm="foundations",
        summary="The statistical foundation of machine learning: expected values, spread, the Gaussian bell curve, and how activations are standardized.",
        tensor_flow=(
            "Sample Dataset of N Observations:\n"
            "  x = [x1, x2, ..., xN]\n"
            "Mean (Expected Value / Center of Mass):\n"
            "  μ = (1/N) * sum(x_i)\n"
            "Deviations from Center:\n"
            "  (x_i - μ)  [Note: sum of raw deviations is always 0!]\n"
            "Variance (Mean Squared Deviation):\n"
            "  σ^2 = (1/N) * sum((x_i - μ)^2)\n"
            "Standard Deviation (Spread in original units):\n"
            "  σ = sqrt(σ^2)\n"
            "Standard Normal Distribution N(0, 1):\n"
            "  68.2% of samples fall within μ ± 1σ\n"
            "  95.4% of samples fall within μ ± 2σ\n"
            "Standardization (Z-Score / LayerNorm):\n"
            "  z = (x - μ) / σ  --> Centers data at Mean=0, Variance=1"
        ),
        formula=r"\mu = \frac{1}{N}\sum_{i=1}^N x_i, \quad \sigma^2 = \frac{1}{N}\sum_{i=1}^N (x_i - \mu)^2, \quad \sigma = \sqrt{\sigma^2}, \quad z_i = \frac{x_i - \mu}{\sigma}",
        variables={
            "N": "Number of observations or data points in the sample",
            "x_i": "An individual data point or neural network activation value",
            "μ (Mu)": "Mean (expected value): the arithmetic average and center of gravity",
            "σ^2 (Sigma Squared)": "Variance: the average squared distance from the mean",
            "σ (Sigma)": "Standard deviation: the spread of data expressed in the original units",
            "z_i": "Standardized Z-score: how many standard deviations a point is from the mean",
            "N(0, 1)": "Standard Gaussian (Normal) distribution with zero mean and unit variance",
        },
        math_explanation=(
            "Before jumping into entropy or KL divergence, we must understand how numbers scatter. "
            "The Mean (μ) tells you where the center of the distribution sits. "
            "The Variance (σ²) measures how widely the data is scattered around that center. We square the differences (x - μ)² so that negative and positive deviations don't cancel each other out, and to penalize large outliers. "
            "Because variance is in squared units (e.g. 'squared dollars' or 'squared tokens'), we take the square root to get the Standard Deviation (σ), which returns the spread to the original units. "
            "The Normal (Gaussian) distribution emerges naturally whenever many independent random factors combine (the Central Limit Theorem). "
            "In deep learning, every weight initialization scheme (like Xavier or Kaiming He initialization) carefully tunes σ so that signals neither explode to infinity nor vanish to zero as they pass through 50 transformer layers."
        ),
        numerical_example=(
            "Consider a tiny batch of 4 token activations: x = [2.0, 4.0, 4.0, 6.0].\n"
            "1. Mean: μ = (2.0 + 4.0 + 4.0 + 6.0) / 4 = 16.0 / 4 = 4.0.\n"
            "2. Deviations from Mean (x - μ): [2 - 4, 4 - 4, 4 - 4, 6 - 4] = [-2.0, 0.0, 0.0, +2.0]. (Notice their sum is 0!)\n"
            "3. Squared Deviations: [(-2)^2, 0^2, 0^2, 2^2] = [4.0, 0.0, 0.0, 4.0].\n"
            "4. Variance (σ²): Sum = 8.0. Average = 8.0 / 4 = 2.0.\n"
            "5. Standard Deviation (σ): sqrt(2.0) ≈ 1.4142.\n"
            "6. Standardization (Z-score normalization like in LayerNorm):\n"
            "   z = (x - μ) / σ = [-2/1.4142, 0, 0, 2/1.4142] = [-1.4142, 0.0, 0.0, +1.4142].\n"
            "   The normalized activations now have Mean = 0.0 and Variance = 1.0!"
        ),
        code_snippet=(
            "import torch\n\n"
            "# 1. A batch of 4 activations:\n"
            "x = torch.tensor([2.0, 4.0, 4.0, 6.0])\n\n"
            "# 2. Calculate mean and variance:\n"
            "mu = torch.mean(x)\n"
            "var = torch.var(x, unbiased=False)  # Population variance (divide by N)\n"
            "std = torch.std(x, unbiased=False)\n\n"
            "print(f'Mean (μ): {mu.item():.2f}')       # 4.00\n"
            "print(f'Variance (σ²): {var.item():.2f}')  # 2.00\n"
            "print(f'Std Dev (σ): {std.item():.4f}')   # 1.4142\n\n"
            "# 3. Standardize (Z-score normalization):\n"
            "z = (x - mu) / std\n"
            "print(f'Standardized z-scores: {z.tolist()}')\n"
            "print(f'New Mean: {torch.mean(z).item():.2f}, New Std: {torch.std(z, unbiased=False).item():.2f}')\n"
            "assert abs(torch.mean(z).item()) < 1e-6\n"
            "assert abs(torch.std(z, unbiased=False).item() - 1.0) < 1e-6"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 2: Probability and Statistics",
                category="Data_Science",
                relevance="Complete treatment of descriptive statistics, normal distributions, and variance.",
            ),
            LabCitation(
                title="Practical Statistics for Data Scientists",
                chapter="Chapter 1: Exploratory Data Analysis — Estimates of Location and Variability",
                category="Data_Science",
                relevance="Hands-on guide to mean, standard deviation, and data distributions.",
            ),
        ],
    ),
    LabConcept(
        id="vector-geometry-cosine",
        title="Vector Spaces & Cosine Distance in AI (From 2D to High Dimensions)",
        paradigm="foundations",
        summary="Scaling vector geometry from 2D coordinates to 4096-dimensional embeddings, semantic document search in Qdrant, and attention routing.",
        tensor_flow=(
            "Inputs:\n"
            "  u: [Batch, HiddenDim] (e.g. Query Embedding [1, 4096])\n"
            "  v: [NumDocs, HiddenDim] (e.g. Document Chunks in Qdrant [1000, 4096])\n"
            "Operations:\n"
            "  Inner Product = u @ v.T: [Batch, NumDocs]\n"
            "  Norms: ||u||_2 = sqrt(sum(u^2, dim=-1)), ||v||_2 = sqrt(sum(v^2, dim=-1))\n"
            "  Cosine Similarity = Inner Product / (||u|| * ||v||): [Batch, NumDocs]\n"
            "Output:\n"
            "  Ranking Scores in range [-1.0, +1.0]"
        ),
        formula=r"\mathrm{CosineSim}(u, v) = \frac{u \cdot v}{\|u\|_2 \|v\|_2} = \frac{\sum_{i=1}^D u_i v_i}{\sqrt{\sum_{i=1}^D u_i^2} \sqrt{\sum_{i=1}^D v_i^2}} = \cos(\theta)",
        variables={
            "u, v": "Embedding vectors in high-dimensional continuous space (e.g. D = 4,096)",
            "u · v": "Dot product measuring directional projection and alignment",
            "||u||_2": "Euclidean L2 norm measuring absolute vector length (magnitude)",
            "θ": "Geometric angle between the two concept vectors",
            "cos(θ)": "Normalized similarity score: +1.0 (identical), 0.0 (orthogonal), -1.0 (opposite)",
        },
        math_explanation=(
            "In high-dimensional space, the dot product u · v measures how much vector u projects along vector v. "
            "However, raw dot products are biased by vector magnitude: longer text or frequent tokens naturally yield larger vectors. "
            "Cosine similarity normalizes both vectors to unit length (||u|| = 1), isolating pure semantic direction. "
            "In 4,096 dimensions, two completely random independent vectors are almost guaranteed to be orthogonal (cos θ ≈ 0) "
            "because the volume of a high-dimensional hypersphere is concentrated near its equator."
        ),
        numerical_example=(
            "Suppose D = 3. Let doctor u = [1.0, 2.0, 3.0], nurse v = [1.2, 1.8, 2.9], and apple w = [3.0, 0.1, -1.0].\n"
            "1. Dot Product: u · v = (1.0×1.2) + (2.0×1.8) + (3.0×2.9) = 1.2 + 3.6 + 8.7 = 13.5.\n"
            "2. Norms: ||u|| = sqrt(1+4+9) = 3.741; ||v|| = sqrt(1.44+3.24+8.41) = 3.618.\n"
            "3. Cosine Sim (Doctor <-> Nurse): 13.5 / (3.741 × 3.618) = 13.5 / 13.535 = 0.9974 (θ ≈ 4.1°, nearly identical).\n"
            "4. Contrast with Apple: u · w = (1×3) + (2×0.1) + (3×-1) = 0.2. ||w|| = 3.163.\n"
            "   Cosine Sim (Doctor <-> Apple): 0.2 / (3.741 × 3.163) = 0.0169 (θ ≈ 89.0°, completely orthogonal)."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn.functional as F\n\n"
            "# 3 semantic embedding vectors:\n"
            "doctor = torch.tensor([[1.0, 2.0, 3.0]])\n"
            "nurse  = torch.tensor([[1.2, 1.8, 2.9]])\n"
            "apple  = torch.tensor([[3.0, 0.1, -1.0]])\n\n"
            "sim_nurse = F.cosine_similarity(doctor, nurse)\n"
            "sim_apple = F.cosine_similarity(doctor, apple)\n\n"
            "print(f'Cosine Similarity (Doctor <-> Nurse): {sim_nurse.item():.4f}')  # ~0.9974\n"
            "print(f'Cosine Similarity (Doctor <-> Apple): {sim_apple.item():.4f}')  # ~0.0169\n"
            "assert sim_nurse.item() > 0.99, 'Semantically related vectors must align'"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 1: Linear Algebra — Vectors, Dot Products, and Coordinate Systems",
                category="Data_Science",
                relevance="First-principles geometric proofs of dot products, unit sphere normalization, and high-dimensional orthogonality.",
            ),
            LabCitation(
                title="AI-Powered Search",
                chapter="Chapter 3: Dense Vectors and Semantic Retrieval",
                category="AI_and_Machine_Learning",
                relevance="Explains how Qdrant and HNSW vector indices utilize cosine similarity for sub-millisecond retrieval.",
            ),
        ],
    ),

    LabConcept(
        id="matrix-svd-lora",
        title="Singular Value Decomposition (SVD) & Low-Rank Adaptation (LoRA)",
        paradigm="foundations",
        summary="Factoring high-dimensional weight transformations into low-rank representations, enabling 99% VRAM reduction during fine-tuning.",
        tensor_flow=(
            "Full Base Matrix:\n"
            "  W_0: [d_out, d_in] (Frozen, e.g. [4096, 4096] = 16.7M params)\n"
            "LoRA Factorization:\n"
            "  Input x: [Batch, SeqLen, d_in]\n"
            "  Down-Projection: h_low = x @ A.T  where A: [r, d_in] (e.g. r=16 -> 65.5K params)\n"
            "  Up-Projection:   delta_h = h_low @ B.T where B: [d_out, r] (e.g. r=16 -> 65.5K params)\n"
            "Forward Combination:\n"
            "  Output = (x @ W_0.T) + (alpha / r) * delta_h: [Batch, SeqLen, d_out]"
        ),
        formula=r"W = U \Sigma V^T = \sum_{i=1}^{\min(m, n)} \sigma_i u_i v_i^T, \quad W_{\text{new}} = W_0 + \Delta W = W_0 + \frac{\alpha}{r} (B \cdot A)",
        variables={
            "W_0": "Original pre-trained weight matrix (frozen in memory during fine-tuning)",
            "ΔW": "Learned parameter update matrix decomposed as B · A",
            "A": "Down-projection adapter matrix initialized with Gaussian noise ~ N(0, σ²)",
            "B": "Up-projection adapter matrix initialized with zeros (ensuring ΔW = 0 at step 0)",
            "r": "Intrinsic low-rank bottleneck dimension (typically r = 8, 16, or 32)",
            "α": "Constant scaling hyperparameter (typically α = 2r or α = 16)",
        },
        math_explanation=(
            "The Eckart-Young-Mirsky theorem proves that any matrix can be optimal-approximated by keeping only its top r singular values. "
            "Aghajanyan et al. (2020) demonstrated that when fine-tuning massive pre-trained language models on specific tasks, "
            "the parameter updates ΔW have an extremely low 'intrinsic dimension'. "
            "Although W_0 operates in 4,096 dimensions, the new task-specific knowledge occupies a subspace of rank r ≤ 16. "
            "By training two small matrices B and A instead of the full dense matrix, we preserve representation expressivity "
            "while reducing optimizer memory footprint by orders of magnitude."
        ),
        numerical_example=(
            "Consider a single projection layer in a 7B model where d_in = d_out = 4,096.\n"
            "1. Full Fine-Tuning: 4,096 × 4,096 = 16,777,216 parameters (67.1 MB in FP32 weights + 134.2 MB AdamW states = 201.3 MB per matrix).\n"
            "2. LoRA with rank r = 16:\n"
            "   - Matrix A: 16 × 4,096 = 65,536 parameters.\n"
            "   - Matrix B: 4,096 × 16 = 65,536 parameters.\n"
            "   - Total LoRA parameters: 131,072 parameters (0.52 MB weights + 1.05 MB AdamW states = 1.57 MB total).\n"
            "3. Memory Reduction: 201.3 MB -> 1.57 MB (99.22% memory savings). Across 32 transformer layers, this drops training VRAM from 64 GB down to 8 GB!"
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class LoRALinear(nn.Module):\n"
            "    def __init__(self, in_features, out_features, r=16, alpha=32):\n"
            "        super().__init__()\n"
            "        self.w0 = nn.Linear(in_features, out_features, bias=False)\n"
            "        self.w0.weight.requires_grad = False  # Freeze base weights\n"
            "        self.r = r\n"
            "        self.scale = alpha / r\n"
            "        self.lora_A = nn.Parameter(torch.randn(r, in_features) * 0.01)\n"
            "        self.lora_B = nn.Parameter(torch.zeros(out_features, r))\n\n"
            "    def forward(self, x):\n"
            "        base_out = self.w0(x)\n"
            "        lora_out = (x @ self.lora_A.T @ self.lora_B.T) * self.scale\n"
            "        return base_out + lora_out\n\n"
            "layer = LoRALinear(4096, 4096, r=16)\n"
            "x = torch.randn(2, 8, 4096)\n"
            "out = layer(x)\n"
            "print('LoRA output shape:', out.shape)  # [2, 8, 4096]\n"
            "trainable = sum(p.numel() for p in layer.parameters() if p.requires_grad)\n"
            "print(f'Trainable parameters: {trainable:,} (vs 16,777,216 base)')"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 3: Singular Value Decomposition and Matrix Approximations",
                category="Data_Science",
                relevance="Mathematical proof of low-rank matrix decomposition and singular value spectra.",
            ),
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 6: Fine-Tuning for Instructions — Parameter-Efficient LoRA",
                category="AI_and_Machine_Learning",
                relevance="Step-by-step PyTorch implementation of LoRA adapter injection and scaling factor derivations.",
            ),
        ],
    ),

    LabConcept(
        id="gradient-descent-autograd",
        title="Multivariate Gradients & The Autograd Chain Rule",
        paradigm="foundations",
        summary="Calculus of multivariable optimization, reverse-mode automatic differentiation, and loss surfaces.",
        tensor_flow=(
            "Forward Graph:\n"
            "  x: Input [B, D_in]\n"
            "  h = x @ W_1 + b_1: [B, D_h]\n"
            "  a = ReLU(h): [B, D_h]\n"
            "  y_hat = a @ W_2 + b_2: [B, D_out]\n"
            "  Loss = 0.5 * mean((y_hat - y)^2): Scalar\n"
            "Backward Sweep (Reverse Autograd):\n"
            "  dL/dy_hat: [B, D_out]\n"
            "  dL/dW_2 = a.T @ (dL/dy_hat): [D_h, D_out]\n"
            "  dL/dh = (dL/dy_hat @ W_2.T) * (h > 0): [B, D_h]\n"
            "  dL/dW_1 = x.T @ (dL/dh): [D_in, D_h]"
        ),
        formula=r"\nabla_W \mathcal{L} = \left[ \frac{\partial \mathcal{L}}{\partial W_1}, \frac{\partial \mathcal{L}}{\partial W_2}, \dots, \frac{\partial \mathcal{L}}{\partial W_P} \right]^T, \quad W_{t+1} = W_t - \eta \cdot \nabla_W \mathcal{L}",
        variables={
            "L": "Scalar loss value quantifying total prediction discrepancy",
            "∇_W L": "Gradient vector pointing in the direction of steepest loss ascent",
            "η": "Learning rate (step size multiplier)",
            "∂L/∂W_ij": "Partial derivative indicating how an infinitesimal change in weight W_ij affects L",
            "J": "Jacobian matrix of intermediate vector-valued partial derivatives",
        },
        math_explanation=(
            "Training a neural network is an unconstrained non-convex optimization problem across millions of dimensions. "
            "The gradient vector ∇L contains the local slope along every coordinate axis. "
            "To compute gradients across dozens of nested layers, the Multivariable Chain Rule states that the derivative "
            "of composite function f(g(x)) is f'(g(x)) · g'(x). "
            "Reverse-mode automatic differentiation (autograd) stores the forward computational graph in memory and traverses it backwards, "
            "computing all parameter gradients in a single pass with computational complexity proportional to one forward pass."
        ),
        numerical_example=(
            "Consider a single scalar neuron: y_hat = w · x. Let x = 2.0, target y = 10.0, and current weight w = 3.0.\n"
            "1. Forward Pass: y_hat = 3.0 × 2.0 = 6.0.\n"
            "2. Squared Error Loss: L = 0.5 × (y_hat - y)^2 = 0.5 × (6.0 - 10.0)^2 = 0.5 × (-4.0)^2 = 8.0.\n"
            "3. Backward Pass (Chain Rule):\n"
            "   dL/dy_hat = (y_hat - y) = 6.0 - 10.0 = -4.0.\n"
            "   dy_hat/dw = x = 2.0.\n"
            "   dL/dw = (dL/dy_hat) × (dy_hat/dw) = -4.0 × 2.0 = -8.0.\n"
            "4. Gradient Step (η = 0.1):\n"
            "   w_new = w - η × (dL/dw) = 3.0 - (0.1 × -8.0) = 3.0 + 0.8 = 3.8.\n"
            "5. Verification: New prediction y_hat = 3.8 × 2.0 = 7.6. New loss = 0.5 × (7.6 - 10)^2 = 2.88 (Loss dropped from 8.0 to 2.88!)."
        ),
        code_snippet=(
            "import torch\n\n"
            "# Track gradients explicitly on parameter w:\n"
            "w = torch.tensor([3.0], requires_grad=True)\n"
            "x = torch.tensor([2.0])\n"
            "y = torch.tensor([10.0])\n\n"
            "# Forward pass\n"
            "y_hat = w * x\n"
            "loss = 0.5 * (y_hat - y) ** 2\n\n"
            "# Backward pass (Autograd)\n"
            "loss.backward()\n\n"
            "print(f'Computed gradient dL/dw: {w.grad.item():.4f}')  # Exactly -8.0000\n"
            "with torch.no_grad():\n"
            "    w -= 0.1 * w.grad\n"
            "print(f'Updated weight w: {w.item():.4f}')               # Exactly 3.8000"
        ),
        nexus_citations=[
            LabCitation(
                title="Optimization Algorithms",
                chapter="Chapter 4: First-Order Methods — Gradient Descent and Line Search",
                category="AI_and_Machine_Learning",
                relevance="Mathematical derivations of gradient descent convergence rates and condition numbers.",
            ),
            LabCitation(
                title="Deep Learning with Python, Third Edition",
                chapter="Chapter 2: The Mathematical Building Blocks of Neural Networks — Gradient-Based Optimization",
                category="AI_and_Machine_Learning",
                relevance="Visual intuition for computational graphs, backpropagation, and tensor gradient accumulation.",
            ),
        ],
    ),

    LabConcept(
        id="cross-entropy-kl-divergence",
        title="Shannon Entropy, Cross-Entropy Loss & KL Divergence",
        paradigm="foundations",
        summary="Information theory fundamentals: quantifying uncertainty, pretraining next-token prediction, and bounding policy drift in RLHF.",
        tensor_flow=(
            "Inputs:\n"
            "  Logits z: [Batch, SeqLen, VocabSize] (e.g. Vocab = 128,000)\n"
            "  Target Token IDs: [Batch, SeqLen] (Ground truth integer indices)\n"
            "Operations:\n"
            "  Probabilities P = Softmax(z, dim=-1): [Batch, SeqLen, VocabSize]\n"
            "  NLL Loss = -log(P[target]): Scalar (Negative Log-Likelihood)\n"
            "  KL Divergence Penalty (in DPO/RLHF) = sum(P * log(P / P_ref)): Scalar"
        ),
        formula=r"\mathcal{L}_{\mathrm{CE}} = -\sum_{k=1}^V y_k \ln(\hat{y}_k) = -\ln(\hat{y}_{\mathrm{target}}), \quad D_{\mathrm{KL}}(P \parallel Q) = \sum_{x} P(x) \ln\left(\frac{P(x)}{Q(x)}\right)",
        variables={
            "V": "Vocabulary size (e.g. 128,256 tokens in Llama 3)",
            "y": "True ground-truth distribution (one-hot vector: 1 at target token, 0 elsewhere)",
            "y_hat": "Model output probability distribution produced by Softmax(z)",
            "D_KL": "Kullback-Leibler divergence measuring informational distance between distributions",
            "P, Q": "True distribution P vs predicted/approximate distribution Q",
        },
        math_explanation=(
            "Claude Shannon defined the information content of an event as its surprise: I(x) = -log2 P(x). "
            "Rare events convey high information; predictable events convey near-zero information. "
            "Cross-Entropy measures the average number of bits required to identify a token from a distribution Q when the true distribution is P. "
            "In language modeling, minimizing Cross-Entropy is mathematically identical to Maximum Likelihood Estimation (MLE): "
            "it forces the model to assign maximal probability mass to actual human tokens. "
            "KL Divergence measures the relative entropy or statistical drift between the policy model and the original pre-trained reference model, "
            "preventing alignment fine-tuning from causing catastrophic forgetting."
        ),
        numerical_example=(
            "Suppose the prompt is 'The capital of France is' and target is 'Paris'. Vocab size V = 3 for simplicity.\n"
            "Model logits: z_Paris = 4.0, z_London = 2.0, z_Rome = 1.0.\n"
            "1. Exponentials: exp(4.0) = 54.598, exp(2.0) = 7.389, exp(1.0) = 2.718. Sum = 64.705.\n"
            "2. Softmax Probabilities:\n"
            "   P(Paris) = 54.598 / 64.705 = 0.8438 (84.38%)\n"
            "   P(London) = 7.389 / 64.705 = 0.1142 (11.42%)\n"
            "   P(Rome) = 2.718 / 64.705 = 0.0420 (4.20%)\n"
            "3. Cross-Entropy Loss: L = -ln(P(Paris)) = -ln(0.8438) = 0.1699.\n"
            "4. Contrast with an untrained model predicting P(Paris) = 0.001 (0.1%):\n"
            "   Loss = -ln(0.001) = 6.9077. The gradient magnitude is 40× larger, strongly pushing parameters toward Paris."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n"
            "import torch.nn.functional as F\n\n"
            "# 1 batch, 1 token, vocab of 3 candidates:\n"
            "logits = torch.tensor([[4.0, 2.0, 1.0]])\n"
            "target = torch.tensor([0])  # Index 0 is 'Paris'\n\n"
            "# PyTorch combines LogSoftmax + NLLLoss into CrossEntropyLoss:\n"
            "criterion = nn.CrossEntropyLoss()\n"
            "loss = criterion(logits, target)\n"
            "probs = F.softmax(logits, dim=-1)\n\n"
            "print(f'Token Probabilities: {probs[0].tolist()}')  # [0.8438, 0.1142, 0.0420]\n"
            "print(f'Cross-Entropy Loss:  {loss.item():.4f}')       # Exactly 0.1699"
        ),
        nexus_citations=[
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 5: Pretraining Unlabeled Data — Calculating Training and Validation Loss",
                category="AI_and_Machine_Learning",
                relevance="Detailed walkthrough of Cross-Entropy loss computation across batch sequences and perplexity metrics.",
            ),
            LabCitation(
                title="LLM Evaluation and Alignment, The Foundation",
                chapter="Chapter 4: Preference Optimization and KL Divergence Constraints",
                category="AI_and_Machine_Learning",
                relevance="Formulates KL divergence penalty terms used in DPO and PPO to prevent model collapse.",
            ),
        ],
    ),

    LabConcept(
        id="attention-variance-proof",
        title="Proof: Attention Dot-Product Variance Scales with Dimension",
        paradigm="foundations",
        summary="Mathematical derivation showing why unscaled attention variance equals d_k and requires the 1/sqrt(d_k) factor to prevent gradient saturation.",
        tensor_flow=(
            "Statistical Variables:\n"
            "  q_i ~ N(0, 1) (Query components, i = 1 ... d_k)\n"
            "  k_i ~ N(0, 1) (Key components, i = 1 ... d_k)\n"
            "Unscaled Dot Product:\n"
            "  Z = sum_{i=1}^{d_k} q_i * k_i\n"
            "  E[Z] = 0, Var(Z) = d_k (Variance grows linearly with dimension!)\n"
            "Scaled Dot Product:\n"
            "  Z_scaled = Z / sqrt(d_k)\n"
            "  Var(Z_scaled) = Var(Z) / d_k = d_k / d_k = 1.0 (Unit Variance Restored)"
        ),
        formula=r"\mathrm{Var}\left(\sum_{i=1}^{d_k} q_i k_i\right) = \sum_{i=1}^{d_k} \mathrm{Var}(q_i k_i) = d_k \sigma_q^2 \sigma_k^2 = d_k \implies \mathrm{Var}\left(\frac{q \cdot k}{\sqrt{d_k}}\right) = \frac{d_k}{(\sqrt{d_k})^2} = 1.0",
        variables={
            "q_i, k_i": "Independent zero-mean, unit-variance Gaussian random variables from query and key heads",
            "d_k": "Head projection dimension (typically d_k = 64 or 128)",
            "Var(Z)": "Variance of the unscaled dot product across embedding channels",
            "sqrt(d_k)": "Canonical Vaswani scaling denominator stabilizing the softmax gradient",
        },
        math_explanation=(
            "Let q and k be two random vectors with independent components having zero mean and unit variance. "
            "For each product term z_i = q_i · k_i: E[z_i] = E[q_i] · E[k_i] = 0. "
            "The variance of each term is Var(z_i) = E[z_i^2] - (E[z_i])^2 = E[q_i^2] · E[k_i^2] = 1 · 1 = 1. "
            "Because components are independent, the variance of their sum is the sum of variances: "
            "Var(∑_{i=1}^{d_k} z_i) = ∑_{i=1}^{d_k} Var(z_i) = d_k · 1 = d_k. "
            "For d_k = 128, the standard deviation is sqrt(128) ≈ 11.3. Dot products naturally produce values like +25 and -25. "
            "In Softmax, exp(25) / (exp(25) + exp(-25)) = 0.9999999999999... The softmax saturates, "
            "its derivative s_i(1 - s_i) becomes 0, and backpropagation stalls. "
            "Scaling by 1/sqrt(d_k) divides the standard deviation by sqrt(d_k), forcing the variance to exactly 1.0."
        ),
        numerical_example=(
            "Empirical verification with d_k = 64 across 100,000 random query/key pairs:\n"
            "- Theoretical unscaled variance: 64.0 (StdDev = 8.0).\n"
            "- If dot product = +16, exp(16) = 8,886,110. Softmax assigns ~1.000, killing the gradient.\n"
            "- Scaling by 1/sqrt(64) = 1/8: The scaled dot product is 16/8 = 2.0.\n"
            "- exp(2.0) = 7.389. Softmax produces well-distributed probabilities (e.g. 0.70 vs 0.30) with rich gradients."
        ),
        code_snippet=(
            "import torch\n\n"
            "d_k = 64\n"
            "samples = 100_000\n"
            "q = torch.randn(samples, d_k)\n"
            "k = torch.randn(samples, d_k)\n\n"
            "unscaled_dot = (q * k).sum(dim=-1)\n"
            "scaled_dot = unscaled_dot / (d_k ** 0.5)\n\n"
            "print(f'Theoretical unscaled variance: {d_k:.1f}')\n"
            "print(f'Empirical unscaled variance:   {unscaled_dot.var().item():.3f}')  # ~64.0\n"
            "print(f'Empirical scaled variance:     {scaled_dot.var().item():.3f}')    # ~1.000\n"
            "assert abs(scaled_dot.var().item() - 1.0) < 0.05, 'Scaled variance must equal 1.0'"
        ),
        nexus_citations=[
            LabCitation(
                title="Essential Math for Data Science",
                chapter="Chapter 4: Probability and Statistics — Expectation and Variance of Sums",
                category="Data_Science",
                relevance="Formal proof that variance of a sum of independent random variables equals the sum of variances.",
            ),
            LabCitation(
                title="Transformers in Action",
                chapter="Chapter 2: Inside the Transformer — Scaled Dot-Product Attention Mechanics",
                category="AI_and_Machine_Learning",
                relevance="Walkthrough of the Vaswani et al. proof and softmax gradient degradation analysis.",
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # TIER 2: LANGUAGE & TRANSFORMER ARCHITECTURES
    # ══════════════════════════════════════════════════════════════════════════════
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
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 3: Coding Attention Mechanisms — Self-Attention Step by Step",
                category="AI_and_Machine_Learning",
                relevance="Hands-on Python walkthrough of Query, Key, Value matrix projections and causal attention masks.",
            ),
            LabCitation(
                title="Transformers in Action",
                chapter="Chapter 2: Inside the Transformer — Scaled Dot-Product Attention Mechanics",
                category="AI_and_Machine_Learning",
                relevance="Details causal mask implementation and GPU memory footprints.",
            ),
        ],
    ),

    LabConcept(
        id="multi-head-attention",
        title="Multi-Head Attention (MHA) & KV-Cache Mechanics",
        paradigm="language",
        summary="Splitting embeddings into parallel representation subspaces and caching Key-Value tensors for O(1) autoregressive generation.",
        tensor_flow=(
            "Multi-Head Split:\n"
            "  Input X: [Batch, SeqLen, HiddenDim] (e.g. [1, 1024, 4096])\n"
            "  Projections Q, K, V split across H heads: [Batch, H, SeqLen, d_k] (e.g. H=32, d_k=128)\n"
            "KV Cache (Inference):\n"
            "  Past Tokens Cache: K_past, V_past: [Batch, H, PastLen, d_k]\n"
            "  Concatenate new token: K_cat = [K_past, K_new], V_cat = [V_past, V_new]\n"
            "Multi-Head Concat:\n"
            "  Output = Concat(head_1, ..., head_H) @ W_out: [Batch, SeqLen, HiddenDim]"
        ),
        formula=r"\mathrm{MHA}(Q, K, V) = \mathrm{Concat}(\mathrm{head}_1, \dots, \mathrm{head}_h) W^O, \quad \mathrm{head}_i = \mathrm{Attention}(Q W_i^Q, K W_i^K, V W_i^V)",
        variables={
            "h": "Number of parallel attention heads (e.g. 32 heads in Llama 3 8B)",
            "d_k": "Dimension per head: d_k = HiddenDim / h (e.g. 4096 / 32 = 128)",
            "W_i^Q, W_i^K, W_i^V": "Projection matrices for head i",
            "W^O": "Output projection matrix recombining all head representations back to HiddenDim",
            "K_past, V_past": "In-memory KV cache tensors stored in unified memory / GPU VRAM",
        },
        math_explanation=(
            "Single-head attention forces the model to average over all semantic relationships into one distribution. "
            "Multi-head attention projects Queries, Keys, and Values into h different subspaces, allowing one head to track syntactic agreement (verbs to subjects), "
            "another head to track long-range coreference ('he' -> 'Alexander'), and another to track punctuation. "
            "During inference, text is generated autoregressively one token at a time. Without caching, computing the next token requires recomputing "
            "attention across all N past tokens (O(N^2) complexity). Caching past Keys and Values in VRAM reduces per-step compute to O(N)."
        ),
        numerical_example=(
            "KV Cache Memory Footprint calculation for Llama 3 8B (32 layers, 32 KV heads, d_k = 128, FP16 = 2 bytes per float):\n"
            "Per token memory = 2 (K and V) × 32 layers × 32 heads × 128 dimension × 2 bytes = 524,288 bytes = 0.5 MB / token.\n"
            "- For 2,048 tokens of context: 2,048 × 0.5 MB = 1.0 GB of KV cache VRAM.\n"
            "- For 128,000 tokens of context: 128,000 × 0.5 MB = 64 GB of VRAM just for the KV cache!\n"
            "This explains why modern models use Grouped-Query Attention (GQA) to share KV heads across queries."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class SimpleMultiHeadAttention(nn.Module):\n"
            "    def __init__(self, d_model=512, n_heads=8):\n"
            "        super().__init__()\n"
            "        self.d_k = d_model // n_heads\n"
            "        self.n_heads = n_heads\n"
            "        self.q_proj = nn.Linear(d_model, d_model)\n"
            "        self.k_proj = nn.Linear(d_model, d_model)\n"
            "        self.v_proj = nn.Linear(d_model, d_model)\n"
            "        self.out_proj = nn.Linear(d_model, d_model)\n\n"
            "    def forward(self, x):\n"
            "        B, S, D = x.shape\n"
            "        q = self.q_proj(x).view(B, S, self.n_heads, self.d_k).transpose(1, 2)\n"
            "        k = self.k_proj(x).view(B, S, self.n_heads, self.d_k).transpose(1, 2)\n"
            "        v = self.v_proj(x).view(B, S, self.n_heads, self.d_k).transpose(1, 2)\n"
            "        scores = (q @ k.transpose(-2, -1)) / (self.d_k ** 0.5)\n"
            "        attn = torch.softmax(scores, dim=-1)\n"
            "        out = (attn @ v).transpose(1, 2).contiguous().view(B, S, D)\n"
            "        return self.out_proj(out)\n\n"
            "mha = SimpleMultiHeadAttention(512, 8)\n"
            "x = torch.randn(1, 16, 512)\n"
            "print('MHA Output shape:', mha(x).shape)  # [1, 16, 512]"
        ),
        nexus_citations=[
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 3: Coding Attention Mechanisms — Multi-Head Attention",
                category="AI_and_Machine_Learning",
                relevance="Hands-on breakdown of splitting tensors into multi-head views and efficient batch matrix multiplications.",
            ),
            LabCitation(
                title="LLMs in Production",
                chapter="Chapter 4: Inference Latency and KV Cache Optimization",
                category="AI_and_Machine_Learning",
                relevance="Memory bandwidth limits, KV cache sizing, and vLLM PagedAttention architecture.",
            ),
        ],
    ),

    LabConcept(
        id="rope",
        title="Rotary Position Embeddings (RoPE)",
        paradigm="language",
        summary="Encodes token positions by multiplying 2D slices of query and key vectors by rotation matrices, enabling natural length extrapolation.",
        tensor_flow=(
            "Inputs:\n"
            "  x_m: Query or Key slice at position m: [x_1, x_2] in R^2\n"
            "Rotation Matrix:\n"
            "  R_m = [[cos(m*theta), -sin(m*theta)], [sin(m*theta), cos(m*theta)]]\n"
            "Rotation:\n"
            "  x_rotated = R_m @ x_m: [x_1*cos - x_2*sin, x_1*sin + x_2*cos]\n"
            "Inner Product Property:\n"
            "  <R_m * q, R_n * k> = <q, R_{n-m} * k> (Depends ONLY on relative distance n - m!)"
        ),
        formula=r"R_{\Theta, m}^d = \mathrm{diag}\left(R_{\theta_1, m}, R_{\theta_2, m}, \dots, R_{\theta_{d/2}, m}\right), \quad R_{\theta_i, m} = \begin{pmatrix} \cos(m\theta_i) & -\sin(m\theta_i) \\ \sin(m\theta_i) & \cos(m\theta_i) \end{pmatrix}",
        variables={
            "m, n": "Absolute token positions in the sequence (0, 1, 2, ...)",
            "theta_i": "Base frequency for feature dimension i: theta_i = 10000^(-2(i-1)/d)",
            "R_{m-n}": "Relative rotation matrix encoding the distance between token m and token n",
        },
        math_explanation=(
            "Traditional absolute positional embeddings add a learned vector to the token embedding (x + p_m). "
            "However, self-attention cares about RELATIVE distance ('how far is the verb from the noun?'), not absolute page index. "
            "RoPE rotates adjacent pairs of coordinates in the query and key vectors by an angle proportional to position m. "
            "Because rotating vector q by m·θ and vector k by n·θ causes their inner product to depend strictly on cos((m - n)θ), "
            "the model naturally generalizes to sequences longer than those seen during pre-training."
        ),
        numerical_example=(
            "Let theta = 0.1 rad. Token A at position m = 2 rotates by 0.2 rad. Token B at position n = 5 rotates by 0.5 rad.\n"
            "Their attention dot product directly evaluates cos(0.5 - 0.2) = cos(0.3) = 0.955.\n"
            "If both tokens shift to positions m = 102 and n = 105, the angle difference is still (10.5 - 10.2) = 0.3 rad!\n"
            "The attention score is identical: cos(0.3) = 0.955. Absolute position vanishes; relative distance is preserved."
        ),
        code_snippet=(
            "import torch\n\n"
            "def apply_rotary_emb(x, pos, theta_base=10000.0):\n"
            "    d = x.shape[-1]\n"
            "    freqs = 1.0 / (theta_base ** (torch.arange(0, d, 2).float() / d))\n"
            "    angles = pos * freqs\n"
            "    cos = torch.cos(angles)\n"
            "    sin = torch.sin(angles)\n"
            "    x1, x2 = x[..., 0::2], x[..., 1::2]\n"
            "    return torch.cat([x1 * cos - x2 * sin, x1 * sin + x2 * cos], dim=-1)\n\n"
            "q = torch.randn(1, 64)\n"
            "q_pos1 = apply_rotary_emb(q, pos=1)\n"
            "print('Rotated Query vector norm:', q_pos1.norm().item())  # Norm is preserved!"
        ),
        nexus_citations=[
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 3: Positional Embeddings — Absolute vs. Relative Rotary Encodings",
                category="AI_and_Machine_Learning",
                relevance="Derivation of 2D rotation matrices and complex number representations in modern LLMs.",
            ),
        ],
    ),

    LabConcept(
        id="swiglu",
        title="SwiGLU Feed-Forward Networks & RMSNorm",
        paradigm="language",
        summary="Gated non-linear expansion layers paired with scale-invariant root-mean-square normalization.",
        tensor_flow=(
            "RMSNorm Stage:\n"
            "  rms = sqrt(mean(x^2, dim=-1) + eps): Scalar per token\n"
            "  x_norm = (x / rms) * gamma: [Batch, SeqLen, HiddenDim]\n"
            "SwiGLU FFN Stage:\n"
            "  Gate = x_norm @ W_gate: [Batch, SeqLen, IntermediateDim]\n"
            "  Up   = x_norm @ W_up:   [Batch, SeqLen, IntermediateDim]\n"
            "  Swish = Gate * Sigmoid(Gate): [Batch, SeqLen, IntermediateDim]\n"
            "  Fused = Swish * Up:           [Batch, SeqLen, IntermediateDim]\n"
            "  Down  = Fused @ W_down:       [Batch, SeqLen, HiddenDim]"
        ),
        formula=r"\mathrm{SwiGLU}(x) = \left(\mathrm{Swish}(x W_{\text{gate}}) \otimes x W_{\text{up}}\right) W_{\text{down}}, \quad \mathrm{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{d}\sum_{i=1}^d x_i^2 + \epsilon}} \odot \gamma",
        variables={
            "W_gate": "Gate projection matrix expanding hidden dim to intermediate dim (usually (8/3) * d)",
            "W_up": "Value projection matrix operating in parallel with gate",
            "W_down": "Down projection matrix returning representation back to HiddenDim",
            "gamma": "Learned per-channel scale parameter in RMSNorm",
            "eps": "Small numerical epsilon (1e-6) preventing division by zero",
        },
        math_explanation=(
            "Standard ReLU networks zero out all negative activations, permanently killing gradient flow through those neurons. "
            "SwiGLU (Shazeer, 2020) replaces standard activation with a Gated Linear Unit where one projection acts as a continuous, "
            "differentiable gate controlling how much information from the second projection passes through. "
            "Paired with RMSNorm—which skips LayerNorm's costly mean-centering step and normalizes purely by root-mean-square—this "
            "architecture stabilizes gradient variances and accelerates convergence by 15–20%."
        ),
        numerical_example=(
            "Suppose gate value g = -2.0. In ReLU, max(0, -2.0) = 0 (complete signal blackout, 0 gradient).\n"
            "In Swish: Sigmoid(-2.0) = 0.1192. Swish(-2.0) = -2.0 × 0.1192 = -0.2384.\n"
            "The signal is suppressed, but its slope is non-zero (d/dg Swish(-2.0) = -0.098)!\n"
            "If the optimizer needs to resurrect this feature, the gradient can travel backwards through the gate."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n"
            "import torch.nn.functional as F\n\n"
            "class SwiGLU(nn.Module):\n"
            "    def __init__(self, d_in, d_ff):\n"
            "        super().__init__()\n"
            "        self.w_gate = nn.Linear(d_in, d_ff, bias=False)\n"
            "        self.w_up = nn.Linear(d_in, d_ff, bias=False)\n"
            "        self.w_down = nn.Linear(d_ff, d_in, bias=False)\n\n"
            "    def forward(self, x):\n"
            "        return self.w_down(F.silu(self.w_gate(x)) * self.w_up(x))\n\n"
            "ffn = SwiGLU(4096, 11008)\n"
            "x = torch.randn(1, 4, 4096)\n"
            "print('SwiGLU Output shape:', ffn(x).shape)  # [1, 4, 4096]"
        ),
        nexus_citations=[
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 4: Implementing a Pretrained Model — Gated Linear Units and RMSNorm",
                category="AI_and_Machine_Learning",
                relevance="Details modern Llama-style FFN implementations and layer normalization comparisons.",
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # TIER 3: TRAINING, ALIGNMENT & REINFORCEMENT LEARNING
    # ══════════════════════════════════════════════════════════════════════════════
    LabConcept(
        id="sft-loss-masking",
        title="Supervised Fine-Tuning (SFT) & Prompt Loss Masking",
        paradigm="language",
        summary="Instruction tuning methodology that zeros out loss gradients on user prompts, ensuring model capacity is focused purely on assistant responses.",
        tensor_flow=(
            "Dialogue Sequence:\n"
            "  Tokens: [<|user|>, 'What', 'is', '2+2?', '<|assistant|>, '4', '<|eos|>']\n"
            "  Labels: [ -100,      -100,   -100,  -100,      -100,         '4',  <|eos|> ]\n"
            "Forward Loss:\n"
            "  Logits: [Batch, SeqLen, VocabSize]\n"
            "  Target Loss: CrossEntropyLoss(logits, labels, ignore_index=-100)\n"
            "Outcome:\n"
            "  Gradients calculate ONLY across assistant answer tokens ('4', <|eos|>)"
        ),
        formula=r"\mathcal{L}_{\mathrm{SFT}} = -\frac{1}{\sum_{t} m_t} \sum_{t=1}^T m_t \ln P(x_t \mid x_{<t}), \quad m_t = \begin{cases} 1 & \text{if token } t \in \text{Assistant Completion} \\ 0 & \text{if token } t \in \text{User Prompt} \end{cases}",
        variables={
            "m_t": "Binary loss mask (0 for prompt tokens, 1 for completion tokens)",
            "ignore_index": "Special sentinel value (-100 in PyTorch) skipped during cross-entropy reduction",
            "x_{<t}": "Causal context history available to the model at step t",
        },
        math_explanation=(
            "During pretraining, loss is computed across all tokens because the goal is general text prediction. "
            "During instruction fine-tuning, calculating loss on the user prompt forces the model to memorize user questions. "
            "Setting label tokens in the prompt to -100 (loss masking) directs 100% of the backpropagation gradients into the assistant's answer. "
            "This teaches the model how to respond without degrading its ability to understand diverse user queries."
        ),
        numerical_example=(
            "Consider a prompt of 50 tokens and an answer of 10 tokens (total sequence = 60 tokens).\n"
            "- Without masking: 50 / 60 = 83.3% of the gradient updates penalize prompt wording, causing overfitting.\n"
            "- With loss masking (m_t = 0 for prompt): 100% of the gradient updates optimize the 10 answer tokens.\n"
            "Validation loss drops 3× faster and the model follows instructions reliably."
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "# 1 dialogue sequence of 6 tokens: [Prompt: 3 tokens, Answer: 3 tokens]\n"
            "logits = torch.randn(1, 6, 100, requires_grad=True)\n"
            "# Mask prompt tokens with -100:\n"
            "labels = torch.tensor([[-100, -100, -100, 42, 85, 12]])\n\n"
            "loss_fn = nn.CrossEntropyLoss(ignore_index=-100)\n"
            "loss = loss_fn(logits.view(-1, 100), labels.view(-1))\n"
            "loss.backward()\n\n"
            "print('Loss calculated:', loss.item())\n"
            "print('Prompt token 0 gradient norm:', logits.grad[0, 0].norm().item())  # Exactly 0.0!\n"
            "print('Answer token 3 gradient norm:', logits.grad[0, 3].norm().item())  # Non-zero gradient"
        ),
        nexus_citations=[
            LabCitation(
                title="Build a Large Language Model (From Scratch)",
                chapter="Chapter 6: Fine-Tuning for Instructions — Formatting Instruction Datasets and Masking",
                category="AI_and_Machine_Learning",
                relevance="Hands-on dataset collator implementation applying -100 masks to prompt tokens.",
            ),
        ],
    ),

    LabConcept(
        id="grpo-reasoning",
        title="Group Relative Policy Optimization (GRPO)",
        paradigm="rl",
        summary="Reinforcement learning for mathematical and coding reasoning without a separate critic/value model, powering DeepSeek-R1.",
        tensor_flow=(
            "Group Sampling:\n"
            "  Prompt q -> Generate G candidate solutions {o_1, o_2, ..., o_G} (e.g. G = 8)\n"
            "Rule-Based Verifiers:\n"
            "  Evaluate each solution: r_i = CompilerPass(o_i) + MathExact(o_i)\n"
            "Advantage Normalization:\n"
            "  mean_r = mean(r), std_r = std(r)\n"
            "  Advantage A_i = (r_i - mean_r) / (std_r + eps)\n"
            "Policy Update:\n"
            "  Scale token log-probs by A_i with PPO-style clipping & KL penalty"
        ),
        formula=r"\mathcal{J}_{\mathrm{GRPO}}(\theta) = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^G \min\left( \frac{\pi_\theta(o_i \mid q)}{\pi_{\mathrm{old}}(o_i \mid q)} A_i, \; \mathrm{clip}\left(\frac{\pi_\theta}{\pi_{\mathrm{old}}}, 1-\epsilon, 1+\epsilon\right) A_i \right) - \beta D_{\mathrm{KL}}(\pi_\theta \parallel \pi_{\mathrm{ref}})\right]",
        variables={
            "G": "Group size (number of completions sampled per prompt, typically 8 to 16)",
            "o_i": "Candidate solution i containing Chain-of-Thought reasoning + final answer",
            "r_i": "Deterministic reward score from rule verifier (e.g. 1.0 for passing unit tests, 0.0 for failing)",
            "A_i": "Statistical advantage normalizing how much solution i outperformed the group average",
            "β": "KL penalty coefficient preventing excessive policy drift from reference model",
        },
        math_explanation=(
            "Traditional PPO requires training a separate Value Network (critic) that matches the size of the policy model, "
            "doubling GPU memory requirements and introducing noisy value estimates. "
            "GRPO (Shao et al., DeepSeek 2024) completely removes the critic. Instead, it generates G outputs for each prompt "
            "and uses the group's empirical mean and standard deviation to compute the baseline. "
            "Completions that pass the test suite receive positive advantage; completions that fail receive negative advantage. "
            "This directly trains models to self-correct and reason through long Chain-of-Thought paths."
        ),
        numerical_example=(
            "For a math problem, sample G = 4 answers with rule rewards r = [1.0, 0.0, 1.0, 0.0] (2 correct, 2 wrong).\n"
            "1. Group Mean: (1 + 0 + 1 + 0) / 4 = 0.5.\n"
            "2. Group StdDev: sqrt(((0.5)^2 + (-0.5)^2 + (0.5)^2 + (-0.5)^2) / 4) = 0.5.\n"
            "3. Advantages A_i = (r_i - 0.5) / 0.5:\n"
            "   - Answers 1 & 3 (Correct): A = (1.0 - 0.5) / 0.5 = +1.0 (Tokens reinforced!)\n"
            "   - Answers 2 & 4 (Wrong):   A = (0.0 - 0.5) / 0.5 = -1.0 (Tokens penalized!)\n"
            "Memory saved: Zero critic weights, allowing full 64 GB Mac Studio memory to serve generation."
        ),
        code_snippet=(
            "import torch\n\n"
            "def compute_grpo_advantages(rewards):\n"
            "    # rewards: tensor of shape [G] (e.g. 4 outputs)\n"
            "    mean = rewards.mean()\n"
            "    std = rewards.std() + 1e-8\n"
            "    return (rewards - mean) / std\n\n"
            "rewards = torch.tensor([1.0, 0.0, 1.0, 0.0])\n"
            "advantages = compute_grpo_advantages(rewards)\n"
            "print('Rewards:   ', rewards.tolist())\n"
            "print('Advantages:', [round(a, 3) for a in advantages.tolist()])"
        ),
        nexus_citations=[
            LabCitation(
                title="LLM Evaluation and Alignment, The Foundation",
                chapter="Chapter 5: Reinforcement Learning from Verifiable Rewards — GRPO and PPO",
                category="AI_and_Machine_Learning",
                relevance="Mathematical breakdown of reward normalization, policy gradient clipping, and rule-based verifiers.",
            ),
        ],
    ),

    # ══════════════════════════════════════════════════════════════════════════════
    # TIER 4: MULTIMODAL & GENERATIVE SYSTEMS
    # ══════════════════════════════════════════════════════════════════════════════
    LabConcept(
        id="vision-transformer-vit",
        title="Vision Transformers (ViT) & Patch Projection",
        paradigm="vision",
        summary="Splits 2D images into flat non-overlapping patches, linearly projects them into token embeddings, and processes images as pure sequence transformers.",
        tensor_flow=(
            "Image Input:\n"
            "  I: [Batch, Channels, Height, Width] (e.g. [1, 3, 224, 224])\n"
            "Patch Flattening:\n"
            "  Patch size P = 16 -> Number of patches N = (224/16) * (224/16) = 14 * 14 = 196\n"
            "  Flattened patch shape: [196, 3 * 16 * 16] = [196, 768]\n"
            "Linear Projection:\n"
            "  x_patches = Patches @ W_embed: [Batch, 196, HiddenDim]\n"
            "Token Sequence:\n"
            "  Prepend [CLS] token + add 1D learned position embeddings: [Batch, 197, HiddenDim]\n"
            "Transformer Processing:\n"
            "  Pass through standard self-attention encoder blocks"
        ),
        formula=r"z_0 = \left[ x_{\text{class}}; \; x_p^1 E; \; x_p^2 E; \dots; x_p^N E \right] + E_{\text{pos}}, \quad E \in \mathbb{R}^{(P^2 C) \times D}",
        variables={
            "P": "Spatial resolution of each square image patch (typically 14 or 16 pixels)",
            "N": "Number of patches in the sequence: N = (H · W) / P^2",
            "E": "Learnable patch embedding projection matrix mapping raw pixels to hidden dim D",
            "x_class": "Learnable classification token ([CLS]) aggregating global spatial context",
            "E_pos": "Learnable 1D position embeddings preserving 2D spatial arrangement",
        },
        math_explanation=(
            "Convolutional networks (CNNs) encode hardcoded inductive biases: translation invariance and local receptive fields. "
            "Vision Transformers (Dosovitskiy et al., 2020) prove that with sufficient data, self-attention can learn visual relationships "
            "from scratch without hand-crafted convolutions. "
            "By slicing images into 16x16 pixel grids and treating each patch as a 'word token', standard LLM transformer architectures "
            "can process multimodal image data directly."
        ),
        numerical_example=(
            "For a standard 224×224 RGB image with patch size P = 16:\n"
            "- Height patches = 224 / 16 = 14; Width patches = 224 / 16 = 14.\n"
            "- Total sequence length N = 14 × 14 = 196 image tokens.\n"
            "- Each patch contains 16 × 16 × 3 = 768 raw pixel values.\n"
            "- Linear projection W_embed projects 768 pixels into 768 hidden dimensions.\n"
            "- Adding 1 [CLS] token yields a sequence of 197 tokens—identical to a short text prompt!"
        ),
        code_snippet=(
            "import torch\n"
            "import torch.nn as nn\n\n"
            "class PatchEmbedding(nn.Module):\n"
            "    def __init__(self, in_channels=3, patch_size=16, embed_dim=768):\n"
            "        super().__init__()\n"
            "        # Conv2d with stride=patch_size cleanly slices and projects patches in one pass:\n"
            "        self.proj = nn.Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)\n\n"
            "    def forward(self, x):\n"
            "        # x: [B, 3, 224, 224] -> [B, 768, 14, 14] -> [B, 196, 768]\n"
            "        return self.proj(x).flatten(2).transpose(1, 2)\n\n"
            "patch_layer = PatchEmbedding()\n"
            "img = torch.randn(1, 3, 224, 224)\n"
            "tokens = patch_layer(img)\n"
            "print('Patch Tokens shape:', tokens.shape)  # [1, 196, 768]"
        ),
        nexus_citations=[
            LabCitation(
                title="Deep Learning with Python, Third Edition",
                chapter="Chapter 9: Advanced Computer Vision — Vision Transformers and Attention",
                category="AI_and_Machine_Learning",
                relevance="Comprehensive comparison of Convolutional kernels vs. ViT global self-attention receptive fields.",
            ),
        ],
    ),

    LabConcept(
        id="ddpm-noise-scheduling",
        title="Denoising Diffusion Probabilistic Models (DDPM)",
        paradigm="diffusion",
        summary="Generative modeling via gradual Gaussian noise corruption and learned reverse-time vector field denoising.",
        tensor_flow=(
            "Forward Diffusion Process (Noising):\n"
            "  x_0: Clean Image -> Sample timestep t ~ Uniform(1, T)\n"
            "  Sample noise epsilon ~ N(0, I)\n"
            "  x_t = sqrt(alpha_bar_t) * x_0 + sqrt(1 - alpha_bar_t) * epsilon\n"
            "Reverse Denoising Step:\n"
            "  Model predicts noise: epsilon_pred = UNet(x_t, t)\n"
            "  Loss = MSE(epsilon_pred, epsilon)\n"
            "  Denoise: x_{t-1} = (1 / sqrt(alpha_t)) * (x_t - (beta_t / sqrt(1 - alpha_bar_t)) * epsilon_pred)"
        ),
        formula=r"q(x_t \mid x_0) = \mathcal{N}\left(x_t; \; \sqrt{\bar{\alpha}_t} x_0, \; (1 - \bar{\alpha}_t) \mathbf{I}\right), \quad \mathcal{L}_{\text{simple}} = \mathbb{E}_{t, x_0, \epsilon}\left[ \left\| \epsilon - \epsilon_\theta(x_t, t) \right\|^2 \right]",
        variables={
            "x_0": "Clean original training data sample (e.g. image)",
            "x_t": "Noisy latent sample at diffusion timestep t",
            "beta_t": "Variance schedule value at step t (typically 1e-4 to 0.02)",
            "alpha_bar_t": "Cumulative noise coefficient: product of (1 - beta_s) from s=1 to t",
            "epsilon_theta": "Neural network trained to predict the noise added to sample x_0",
        },
        math_explanation=(
            "Instead of directly generating images in one forward shot (like GANs), diffusion models decompose generation into hundreds of tiny steps. "
            "The forward process gradually destroys structure by adding Gaussian noise according to a schedule beta_t. "
            "By the property of Gaussians, we can jump directly to any timestep t in closed form using alpha_bar_t without stepping through 1...t-1. "
            "The neural network is trained with simple Mean Squared Error to predict the exact noise epsilon injected at step t. "
            "At inference time, starting from pure Gaussian static, the model iteratively subtracts predicted noise to generate pristine images."
        ),
        numerical_example=(
            "Suppose alpha_bar_t = 0.04 at timestep t = 800 (very noisy step):\n"
            "- sqrt(alpha_bar_t) = sqrt(0.04) = 0.2 (only 20% of original signal remains).\n"
            "- sqrt(1 - alpha_bar_t) = sqrt(0.96) = 0.9798 (98% of the tensor is pure Gaussian noise).\n"
            "- The network looks at x_t and predicts the noise epsilon. Training minimizes ||epsilon - epsilon_pred||^2."
        ),
        code_snippet=(
            "import torch\n\n"
            "def forward_diffusion_sample(x_0, t, n_steps=1000):\n"
            "    # Linear beta schedule\n"
            "    betas = torch.linspace(1e-4, 0.02, n_steps)\n"
            "    alphas = 1.0 - betas\n"
            "    alphas_bar = torch.cumprod(alphas, dim=0)\n\n"
            "    sqrt_alpha_bar = alphas_bar[t] ** 0.5\n"
            "    sqrt_one_minus_alpha_bar = (1.0 - alphas_bar[t]) ** 0.5\n"
            "    noise = torch.randn_like(x_0)\n"
            "    return sqrt_alpha_bar * x_0 + sqrt_one_minus_alpha_bar * noise, noise\n\n"
            "img = torch.ones(1, 3, 64, 64)\n"
            "noisy_img, noise = forward_diffusion_sample(img, t=500)\n"
            "print('Noisy image sample shape:', noisy_img.shape)  # [1, 3, 64, 64]"
        ),
        nexus_citations=[
            LabCitation(
                title="Generative AI in Action",
                chapter="Chapter 6: Diffusion Models — Mathematics of Forward and Reverse SDEs",
                category="AI_and_Machine_Learning",
                relevance="Step-by-step mathematical derivation of Gaussian transition kernels and noise schedules.",
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
