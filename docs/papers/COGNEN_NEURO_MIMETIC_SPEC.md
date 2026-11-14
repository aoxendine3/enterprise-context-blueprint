# ARCHITECTURAL DESIGN SPECIFICATION: CogNGen Neuro-Mimetic Cognitive Framework

> **Provenance & verification (added 2026-11-14 by the collective; body below is the user-provided synthesis, verbatim).**
> Source: a synthesis of Ororbia & Kelly's CogNGen work — arXiv:2204.00619 (2022, MiniGrid maze-learning) and arXiv:2310.15177 (AAAI Fall Symposium 2023 / AAAI-SS — "A Neuro-Mimetic Realization of the Common Model of Cognition via Hebbian Learning and Free Energy Minimization"). Not original research. Do not cite as a primary source; see `memory/catch_log/cogngen_camel_contextecho_verification.json` for claim-level verification. CogNGen is a small-scale MiniGrid prototype from 2022, not a general autonomous agent; the 98.5% Mem / 98.5% MR results are real but from a 2022-era benchmark.

---

ARCHITECTURAL DESIGN SPECIFICATION: COGNGEN NEURO-MIMETIC COGNITIVE FRAMEWORK

1. Architectural Foundations and System Blueprint

1.1 Executive Architectural Framing & Cognitive Model Alignment

The Cognitive Neural Generative framework (CogNGen) represents a neuro-mimetic cognitive architecture engineered as a biologically plausible, backpropagation-free alternative to current deep learning paradigms. Modern artificial intelligence relies almost universally on global gradient backpropagation—an optimization protocol that lacks neurobiological plausibility, imposes significant computational overhead, and suffers from catastrophic forgetting when deployed in non-stationary environments. CogNGen resolves these systemic vulnerabilities by integrating local Variational Free Energy (VFE) minimization circuits with non-linear vector-symbolic associative memory subsystems. Utilizing predictive coding mechanics and multi-timescale Hebbian learning dynamics, CogNGen provides a unified operational framework capable of continuous online adaptation, stable temporal abstraction, and dynamic environmental interaction.

CogNGen grounds its structural organization on the Common Model of Cognition (CMC) as formulated by Laird, Lebiere, and Rosenbloom (2017). The CMC defines an architecture-agnostic consensus regarding the functional modules comprising mind and their systemic message-passing topologies. CogNGen explicitly instantiates all five core modules of the Common Model through specialized computational primitives grounded in cortical and subcortical functional anatomy:

CMC Module	Neuro-Biological Substrate	CogNGen Implementation Mechanism
Perception	Sensory cortices	Neural Generative Coding (NGC) unsupervised encoder/decoder circuits
Motor-Action	Motor cortex / Actuators	Active Neural Generative Coding (Active NGC) circuits
Working Memory	Frontoparietal network	Self-recurrent vector-symbolic slot buffers & MINERVA 2 short-term memory
Declarative / Long-Term Memory	Hippocampus, Temporal lobe	Persistent MINERVA 2 associative instance-based memory structures
Procedural Memory	Basal ganglia	NGC predictive dynamics models coupled with dynamic Hebbian competitive gating sub-circuits

1.2 Comparative Analysis: CogNGen vs. Global Workspace & Transformer Architectures

Recent neural frameworks, such as the Perceiver architecture (Vaswani et al. 2017; Juliani et al. 2022), exhibit structural alignment with Global Workspace Theory (GWT) and the Common Model of Cognition by orchestrating input/output modules around a central workspace routed via attentional mechanics. However, functional analysis reveals that Perceiver and generic Transformer pipelines critically omit persistent, episodic declarative memory. As demonstrated by Juliani, Kanai, and Sasai (2022), omitting episodic declarative memory prevents these systems from instantiating a continuous temporal sense of history and self. This structural deficiency isolates the model from higher-order cognitive capacities essential for human-level general intelligence, including metacognition, causal reasoning, theory of mind, and extended temporal planning.

From a computational standpoint, Transformer self-attention layers operate fundamentally as Modern Hopfield networks (Ramsauer et al. 2021). Within these layers, dot-product query-key comparisons evaluate similarity across normalized exponential (softmax) operators, functioning essentially as rapidly updated Hebbian memory matrices. However, standard Transformers remain bound to global end-to-end backpropagation during weight optimization.

CogNGen differentiates itself from conventional deep learning paradigms across three core analytical dimensions:

* Sample Efficiency & Learning Dynamics: Backpropagation mandates thousands of global gradient passes over fixed offline batches. CogNGen achieves rapid adaptation by executing continuous-time local inference settling (T state relaxation steps) followed by discrete, localized two-factor Hebbian synaptic updates.
* Neurobiological Fidelity: Rather than relying on non-local, symmetric backward passes, CogNGen embeds explicit populations of precision-weighted error neurons directly within predictive coding networks. Local structural error signals are calculated via feedback message-passing matrices without requiring gradient transport.
* Mitigation of Catastrophic Forgetting: Traditional deep neural networks overwrite existing parameters when exposed to novel distribution shifts. CogNGen insulates existing memory traces by combining competitive Hebbian gating sub-circuits within procedural memory (which dynamically trigger or suppress specific neuronal populations) with non-destructive, instance-based vector-symbolic long-term storage.

1.3 System Kernel Architecture & Execution Modes

The core processing kernel of CogNGen coordinates functional interaction across sensory perception, vector-symbolic working memory, active motor actuation, and procedural basal ganglia routing.

                                 ┌─────────────────┐
                                 │   Environment   │
                                 └────────┬──▲─────┘
                            Observation   │  │ External Actions
                           (o_t, o_t+1)   │  │ (a_ext_t)
                                          ▼  │
                             ┌───────────────┴─────┐
                             │  Perceptual / Motor │
                             │  Active NGC Circuits│
                             └───────┬───────▲─────┘
                                     │       │ Internal Actions
                        Latent State │       │ (a_int_t)
                        Vectors (z_t)│       │
                                     ▼       │
                             ┌───────────────┴─────┐
                             │   Working Memory    │
                             │Slot Buffers (m_t)   │
                             └───────┬───────▲─────┘
                                     │       │
                   Offline Experience│       │ Trace Retrieval /
                   Replay Sampling   │       │ Context Matching
                                     ▼       │
                             ┌───────────────┴─────┐
                             │  Declarative LTM    │
                             │ (MINERVA 2 Memory)  │
                             └─────────────────────┘

The system kernel executes under two distinct operational regimes:

1. Processing Mode: Execution of real-time visual encoding (f_e: o_t ↦ z_t), latent state dynamic updates, active control generation (a_t^ext, a_t^int), working memory buffer updates, and procedural reward filtering. Crucially, no synaptic parameter updates occur during Processing Mode; the kernel operates strictly via state inference, spatial-temporal vector routing, and environmental actuation.
2. Learning Mode: Triggered during off-line or rest phases (following observation of transition state z_{t+1}). The system samples historical state-action-reward transitions from persistent declarative memory (MINERVA 2) to drive offline experience replay. Replayed confabulated patterns induce local two-factor Hebbian parameter updates across motor control and procedural dynamics NGC circuits.

These operational modes rely on continuous-time energy minimization circuits, whose mathematical properties dictate internal latent state updates and synaptic plasticity.

2. Mathematical Formulation of Neural Generative Coding (NGC) Dynamics

2.1 Probabilistic Generative Model & Variational Free Energy (VFE)

To eliminate non-local gradient backpropagation, CogNGen relies on local energy minimization structures defined by Neural Generative Coding (NGC). An NGC circuit models a hierarchical joint probabilistic density distribution across L processing layers. The joint distribution over L+1 neuronal latent state layers (z_0, z_1, …, z_L) is factorized as:

  p(z_0, …, z_L) = p(z_L) ∏_{ℓ=0}^{L-1} p(z_ℓ | z_{ℓ+1})          (1)

Each conditional probability density p(z_ℓ | z_{ℓ+1}) is modeled as a multivariate Gaussian distribution parameterized by a top-down generative projection f^ℓ(z_{ℓ+1}):

  p(z_L) = N(z̄_L, Σ_L),  p(z_ℓ | z_{ℓ+1}) = N(f^ℓ(z_{ℓ+1}), Σ_ℓ)   (2)

where the top-down prediction mean vector is z̄_ℓ = f^ℓ(z_{ℓ+1}) = W_ℓ(t) · φ_ℓ(z_{ℓ+1}). Here, W_ℓ(t) represents the generative synaptic matrix at time t, φ_ℓ(·) denotes an element-wise non-linear activation function, and · represents standard matrix-vector multiplication.

Under a mean-field approximation enforcing functional independence among individual neuronal units within a layer, optimizing the generative model is equivalent to minimizing the system's Variational Free Energy (VFE) functional F(Θ):

  F(Θ) = Σ_{ℓ=0}^{L} (1 / 2Σ_ℓ) Σ_{i=1}^{J_ℓ} ( z_{ℓ,i}(t) − z̄_{ℓ,i} )²   (3)

where J_ℓ is the number of state neurons in layer ℓ, Σ_ℓ represents the variance component (instantiated here as a scalar precision factor 1/Σ_ℓ), and Θ = {W_ℓ(t), E_ℓ(t)}_{ℓ=1}^{L} encapsulates the generative weights W_ℓ(t) and feedback error message-passing matrices E_ℓ(t). While initial prototypes assume a fixed scalar precision 1/Σ_ℓ, the formulation natively extends to learnable precision matrices Σ_ℓ⁻¹ (Ororbia & Kifer 2022; Salvatori et al. 2023), allowing the circuit to dynamically modulate error variance under uncertainty.

This VFE objective enforces two core neurobiological architectural commitments:

1. Specialized Error Neurons: Mismatches between predicted top-down expectations and target neuronal states are explicitly computed by dedicated populations of precision-weighted error neurons: e_ℓ(t) = (1/Σ_ℓ)(z_ℓ(t) − z̄_ℓ).
2. Top-Down Prediction Guesses: State neurons i within layer z_{ℓ+1} actively generate top-down predictions regarding the expected firing rates of state neurons j in the lower adjacent layer z_ℓ.

2.2 Neuronal State Dynamics & Differential Equations

When sensory stimuli o(t) or contextual constraints c(t) clamp the boundary layers of the circuit (e.g., z_0(t) = o(t) and z_L(t) = c(t)), the internal neuronal state layers z_ℓ(t) update their continuous-time activation dynamics according to the differential equation:

  τ_m ∂z_ℓ(t)/∂t = −γ z_ℓ(t) + d_ℓ ⊙ f_D(z_ℓ(t)) − e_ℓ(t)           (4)

where:

* τ_m represents the cellular membrane time constant governing state relaxation speed.
* γ specifies the internal passive decay rate of neuronal activity.
* ⊙ denotes the element-wise Hadamard product.
* d_ℓ = E_ℓ(t) · e_{ℓ−1}(t) represents the bottom-up perturbation vector transmitted from lower-level error neurons e_{ℓ−1}(t) via feedback error synaptic matrices E_ℓ(t).
* f_D(·) specifies an explicit neural activity dampening function preventing activity saturation.
* e_ℓ(t) represents the local precision-weighted error calculated at layer ℓ.

This formulation isolates layer dynamics so that top-down predictions and bottom-up error signals interact locally without requiring backpropagation passes.

2.3 Local Two-Factor Hebbian Synaptic Plasticity

Synaptic modification occurs locally, driven by two-factor Hebbian learning rules combining prediction error neuron activities with state neuron activation values. The generative synaptic matrices W_ℓ(t) and backward message-passing error matrices E_ℓ(t) evolve according to continuous-time differential equations:

  τ_w ∂W_ℓ(t)/∂t = −γ_w W_ℓ(t) + e_{ℓ−1}(t) · (z_ℓ(t))ᵀ           (5)

  τ_e ∂E_ℓ(t)/∂t = −γ_e E_ℓ(t) + z_ℓ(t) · (e_{ℓ−1}(t))ᵀ              (6)

where τ_w and τ_e denote time constants for generative and feedback synaptic plasticity, while γ_w and γ_e dictate their respective passive synaptic decay rates.

NGC circuits operate on two distinct temporal scales:

Fast Time-Scale (Inference Phase):
  ┌─────────────────────────────────────────────────────────┐
  │ For t = 1 ... T settling iterations:                   │
  │   Update state neurons z_l(t) via Eq. (4)               │
  │   (Synaptic matrices W_l(t) and E_l(t) remain clamped)  │
  └────────────────────────────┬────────────────────────────┘
                               │
                               ▼
Slow Time-Scale (Plasticity Phase):
  ┌─────────────────────────────────────────────────────────┐
  │ Execute discrete parameter updates at step T:           │
  │   Update generative weights W_l(t) via Eq. (5)          │
  │   Update feedback error weights E_l(t) via Eq. (6)      │
  └─────────────────────────────────────────────────────────┘

1. Fast Time-Scale (Inference Dynamics): State variables z_ℓ(t) execute state differential dynamics via Eq. (4) for T settling steps to minimize local free energy, while synaptic matrices W_ℓ(t) and E_ℓ(t) remain stationary.
2. Slow Time-Scale (Synaptic Plasticity): Following state convergence at iteration T, discrete Hebbian updates via Eq. (5) and Eq. (6) adjust structural weights W_ℓ(t) and E_ℓ(t), decoupling state inference from structural parameter modification.

This continuous local predictive engine interfaces directly with vector-symbolic memory structures within central working memory buffers.

3. Multi-Tiered Memory Subsystems & Vector-Symbolic Routing

3.1 Vector-Symbolic Working Memory & Self-Recurrent Slot Buffers

Working memory serves as the central integration bus connecting sensory encoding, procedural control, and active motor planning. Drawing structural principles from frontoparietal memory slots and ACT-R buffer mechanics, CogNGen implements working memory as a self-recurrent slot buffer maintaining a fixed capacity M_w of projected latent state vectors z_t ∈ ℝ^{D_z × 1}.

Each buffer slot i maintains an internal memory vector m_i ∈ ℝ^{M_d × 1} (where M_d is the dimensionality of the memory slot). Operations execute via three algorithmic steps:

1. Gaussian Key Projection: A key vector k_t^i ∈ ℝ^{M_d × 1} is calculated for each slot i using a fixed projection matrix Q_i ∈ ℝ^{M_d × D_z} initialized from a centered Gaussian distribution: k_t^i = Q_i · z_t, ∀i = 1, ..., M_w   (7)
2. Match Score Computation: A distance-based similarity match scalar s_i ∈ ℝ^{1 × 1} evaluates the alignment between key k_t^i and slot state m_i: s_i = (1/|m_i|) ( Σ_j ⌊m_i − k_t^i⌋_{j,1} + ⌊k_t^i − m_i⌋_{j,1} )   (8)
3. Concatenated Working Memory Output: The complete working memory state vector m_t formats slot vectors alongside calculated match scalars into a single vector-symbolic array: m_t = [ [m_1, s_1], ..., [m_i, s_i], ..., [m_{M_w}, s_{M_w}] ]   (9)

Downstream NGC control circuits evaluate m_t to determine whether slot contents are preserved, modified, or overwritten during cognitive cycles.

3.2 Evolution of Hebbian Associative Memory Models

CogNGen integrates instance-based associative memories across working memory buffers and long-term declarative storage. The underlying engine builds upon the mathematical lineage of auto-associative Hebbian architectures:

Standard Hopfield (1982)       MINERVA 2 (Hintzman 1986)        Modern Hopfield (2021)
┌───────────────────────┐      ┌───────────────────────┐       ┌───────────────────────┐
│ Linear Trace Retrieval│   →  │ Exponentiated Similarity│  →  │ Softmax Normalized    │
│                       │      │                       │       │                       │
│  m_e = Σ (m_p·m_i) m_i│      │ m_e = Σ (m_p·m_i)^b m_i│      │ m_e = Σ [Softmax] m_i │
│                       │      │                       │       │                       │
│ (Linear Capacity)     │      │ (Power Non-Linearity) │       │ (Exponential Capacity)│
└───────────────────────┘      └───────────────────────┘       └───────────────────────┘

Standard Hopfield Network (Hopfield 1982)

Given m stored memory vectors m_i and an input probe vector m_p, the retrieved memory echo m_e computes a linear sum of stored traces weighted by dot-product similarity:

  m_e = Σ_{i=1}^{m} (m_p · m_i) m_i                              (10)

Capacity Constraint: Memory capacity scales linearly with pattern dimensionality; storing overlapping patterns induces severe cross-talk interference, returning corrupted echo signals.

MINERVA 2 (Hintzman 1986)

Hintzman eliminated linear cross-talk by applying an exponential power scaling b to normalized dot-product similarities, suppressing weak matching traces:

  m_e = Σ_{i=1}^{m} (m_p · m_i)^b m_i                            (11)

In prototype CogNGen implementations, b = 100. MINERVA 2 accurately models human empirical data across frequency judgment, recognition memory, implicit learning, category acquisition, and decision-making heuristics.

Modern Hopfield / Softmax Retrieval (Ramsauer et al. 2021)

Modern Hopfield networks replace polynomial exponents with normalized exponential (softmax) operations:

  m_e = Σ_{i=1}^{m} ( e^{m_p · m_i} / Σ_{j=1}^{m} e^{m_p · m_j} ) m_i   (12)

This formulation achieves exponential storage capacity while establishing structural identity with single-head attention layers in Transformer architectures.

3.3 Declarative Long-Term Memory & Offline Experience Replay

While working memory slot buffers reset upon episode completion, CogNGen's Declarative Long-Term Memory (hippocampal/temporal module) persists permanently as an instance-based MINERVA 2 network.

Structured experience tuples (z_t, z_{t+1}, a_t^ext, a_t^int, r_t) accumulated within working memory buffers stream into declarative long-term memory. During rest phases or off-line processing, CogNGen executes hippocampal experience replay—a mechanism modeling sharp-wave ripple events and place-cell re-activation patterns documented in rodent and human neurophysiology.

During replay, historical experience traces are sampled from declarative memory. Confabulated state-action patterns generated by the memory echo induce secondary offline VFE minimization iterations across motor control and procedural basal ganglia circuits. This offline consolidation stabilizes parameter estimation without requiring direct physical environmental interaction.

4. Perceptual Processing, Motor Control, and Procedural Basal Ganglia Routing

4.1 Perceptual Processing: Dual Unsupervised Encoders and Generative Decoders

Perceptual processing maps raw environmental sensory observations o_t into structured latent state vectors z_t. CogNGen implements perception via a dual unsupervised NGC encoder/decoder architecture:

* Unsupervised Encoder (f_e: o_t ↦ z_t): Transforms high-dimensional observation space into low-dimensional latent space through continuous-time VFE minimization. To reduce real-time computational complexity, a feedforward neural model can be trained concurrently to amortize the iterative settling process of the NGC encoder (f_e), enabling rapid single-pass latent projection during time-critical processing modes.
* Generative Decoder (f_g: z_t ↦ o_t): Jointly learns a top-down directed generative density model alongside f_e. Passing a latent vector ẑ_t (such as one synthesized by the procedural dynamics circuit) through f_g produces a reconstructed observation ô_t in visual space, enabling visual interpretation of acquired internal representations.

When representation learning is not the central focus of an experiment, CogNGen supports substituting or pairing task-specific pre-trained encoders alongside full NGC perceptual circuits, stabilizing state representations during downstream control benchmarking.

4.2 Active NGC Motor Control Dynamics

Environmental actuation and internal slot management are directed by Active Neural Generative Coding (Active NGC) circuits (f_a: z_t ↦ (c_t^int, c_t^ext)) grounded in active inference principles. At step t, the motor circuit outputs continuous control signals for internal slot manipulation (c_t^int ∈ ℝ^{A_int × 1}) and external environmental actuation (c_t^ext ∈ ℝ^{A_ext × 1}).

Discrete action selection executes via argmax functions:

  a_t^int = argmax_i c_t^int,   a_t^ext = argmax_j c_t^ext

Active NGC motor circuits optimize parameter updates using a composite dual-reward formulation:

  Reward Total = R_instrumental + R_epistemic                     (13)

1. Instrumental Reward (R_instrumental): External problem-specific task performance metrics (e.g., goal reach signals).
2. Epistemic Reward (R_epistemic): An intrinsic, dopamine-like foraging signal generated by procedural memory that drives directed exploration toward unfamiliar state regimes.

4.3 Procedural Memory & Basal Ganglia Information Routing

CogNGen's procedural module models basal ganglia information routing to compute reward expectations and execute dynamic sub-network gating.

                           ┌─────────────────────────┐
                           │   Current State (z_t)   │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │   NGC Dynamics Model    │
                           │   (Computes Raw VFE)    │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │ MINERVA 2 Short-Term    │
                           │ Memory Novelty Filter   │
                           └────────────┬────────────┘
                                        │
                                        ▼
                           ┌─────────────────────────┐
                           │  Epistemic Dopamine     │
                           │  Foraging Signal (R_ep) │
                           └─────────────────────────┘

Epistemic Signal Construction

Procedural memory couples an NGC predictive dynamics model with a MINERVA 2 short-term memory filter. The circuit normalizes the instantaneous VFE generated by the dynamics model and modulates it via MINERVA 2 trace similarity. High similarity signals state familiarity, which reduces the epistemic reward component (R_epistemic) and shifts agent dynamics from epistemic exploration to instrumental exploitation.

Dynamic Sub-Network Gating

To execute executive task switching without catastrophic forgetting, procedural memory incorporates competitive Hebbian learning sub-circuits. These sub-circuits compute continuous dynamic "gating variables" that selectively enable (trigger) or suppress (inhibit) targeted neuronal populations within cortical circuits, replicating basal ganglia dynamic information routing. While CogNGen instantiates executive task-switching via basal ganglia gating circuits, alternative prefrontal cortex (PFC) mechanisms (e.g., Rougier & O'Reilly 2002) offer complementary functional pathways for dynamic region suppression.

5. Global Energy Optimization, Benchmark Verification, and Technical Roadmap

5.1 Global Unified Free Energy Functional Synthesis

A key mathematical feature of CogNGen is its optimization of a single unified objective. Rather than coupling isolated modules trained on disparate cost metrics, the global system minimizes a single unified Free Energy functional F(Θ):

  F_total(Θ) = Σ_j F_j(Θ_j)                                    (14)

where Θ_j represents the plastic synaptic parameters of subsystem component j, and F_j defines its corresponding local energy functional.

For predictive coding NGC circuits (perceptual, motor, and procedural dynamics modules), F_j corresponds to local Variational Free Energy (VFE). For vector-symbolic associative memory subsystems (working memory buffers and long-term declarative stores), F_j corresponds to Hopfield energy functionals. Consequently, systemic cognitive execution reduces to local, parallel energy minimization across all functional modules.

5.2 Empirical Benchmark Performance Analysis

The prototype CogNGen architecture was evaluated on the Gym Mini-GridWorld benchmark suite across five grid-world environments:

* Random Room Escape (R6x6)
* Procedural Multi-Room (MR)
* Door-Unlock (Unl)
* Door-Key (DK)
* Memory Task (Mem)

Performance was evaluated against three deep Q-learning baselines: standard Deep Q-Networks (DQN), DQNs equipped with Random Network Distillation (RnD), and DQNs utilizing the BeBold exploration framework (BeBold DQN-CNT).

Model Architecture	R6x6 Success (%)	MR Success (%)	Unl Success (%)	DK Success (%)	Mem Success (%)	R6x6 Episode Length (% max)	MR Episode Length (% max)	Unl Episode Length (% max)	DK Episode Length (% max)	Mem Episode Length (% max)
DQN	99.50	0.00	0.00	0.00	40.0	9.31	100.0	100.0	100.0	41.14
RnD	100.00	90.00	100.0	100.00	48.5	3.50	31.46	4.08	3.71	2.78
BeBold DQN-CNT	100.00	98.00	100.0	100.00	48.0	3.98	23.51	4.46	3.93	2.92
CogNGen	100.00	98.50	100.0	100.00	98.5	3.90	23.41	4.15	5.48	2.96

CogNGen matches or exceeds deep reinforcement learning baselines across procedural exploration environments (MR, Unl, DK). On the memory-intensive task (Mem), CogNGen achieves a 98.5% success rate, outperforming conventional deep Q-learning baselines (40.0% – 48.5%) while maintaining optimal step efficiency (2.96% of maximum episode length).

5.3 Systemic Limitations and Future Engineering Roadmap

To scale CogNGen beyond grid-world environments, the engineering roadmap targets three architectural extensions:

┌───────────────────────────────────────────────────────────────┐
│ 1. Memory Retrieval Optimization                              │
│    Transition from MINERVA 2 (b=100) to Softmax Hopfield      │
│    Retrieval via Eq. (12) for exponential capacity scaling    │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ 2. Autonomous Memory Control                                  │
│    Replace hardwired state histories with autonomous active    │
│    inference gating over MINERVA 2 / Hopfield buffers        │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ 3. Continuous Domain & Biophysical Scaling                    │
│    Extend NGC circuits to continuous perceptual-motor space   │
│    and transition rate-coded dynamics into spiking dynamics   │
└───────────────────────────────────────────────────────────────┘

1. Memory Retrieval Optimization: Prototype implementations rely on power-exponent MINERVA 2 routines (b=100). Transitioning to normalized exponential Softmax Hopfield retrieval via Eq. (12) provides exponential memory trace capacity and reduces retrieval latency during offline experience replay.
2. Learned Memory Control: Current memory operations use fixed, hardwired observation histories. The roadmap introduces autonomous active inference control over short-term and long-term memory access, enabling Active NGC motor circuits to dynamically control memory read/write operations.
3. Continuous & Biophysical Scaling: Extending CogNGen to complex continuous environments requires expanding NGC circuits into continuous perceptual-motor domains. Furthermore, because predictive coding equations naturally map onto spiking neuronal implementations (Ballard, Rao, & Zhang 2000; Ororbia 2023), future iterations will transition coarse rate-coded dynamics into fine-grained spiking electrophysiological dynamics.

CogNGen demonstrates that unifying local predictive coding with vector-symbolic memory provides a scalable, neuro-mimetic foundation for general-purpose autonomous cognitive architectures.