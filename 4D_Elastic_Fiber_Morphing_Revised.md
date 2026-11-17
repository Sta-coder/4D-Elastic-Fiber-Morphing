# Four-Dimensional Elastic Fiber Morphing and Spatiotemporal Disintegration: A Revised Methodology

**Keywords:** 4D projection, tesseract, fiber morphing, elastic network, phase-field erosion, Cinema 4D scripting, perceptual projection

---

## Abstract

We present a revised framework for spatiotemporal "4D fiber morphing" based on a four-dimensional hypercube (tesseract) model. Building on an initial experimental pipeline, we retain the core four-stage architecture combining 4D rotation, elastic deformation, dual-phase propagation, and temporal "erosion," while systematically correcting mathematical and implementation inconsistencies in the original formulation. Specifically, we re-derive the $4 \times 4$ rotation matrices to form a valid $SO(4)$ operator—composing six independent planar rotations ($XY, XZ, XW, YZ, YW, ZW$) rather than a five-angle shorthand—and clarify perspective projection (division by the shifted fourth coordinate $w'$) with explicit near-plane singularity clamping ($|w'| \ge \varepsilon$). We distinguish the sinusoidal envelope $\sin(\pi t)$ as a geometric kinematic amplitude profile (zero at $t=0,1$, maximum at $t=0.5$) rather than a physical stiffness law, and formulate a decoupled Hookean spring network across the 16 vertices and 32 edges of the tesseract. Furthermore, we reconcile implementation differences between the Maxon Cinema 4D (C4D) Python Generator script—which explicitly outputs B-Spline geometry via `return spline` and encodes four-channel `RGBA` vertex data—and the standalone Google Colab verification script, clarifying how shader-level threshold classification ($E = w_{\text{norm}} + \text{noise}$) pairs with downstream `PolyFX` segment detachment for topological breakup.

---

## 1. Introduction

Four-dimensional (4D) hyper-projection and fiber morphing involves interpreting a higher-dimensional geometric manifold and visualizing its structure through successive spatial projections and physical deformations. In this framework, the base 4D manifold is a regular tesseract (4-cube), discretized as a network of elastic filaments. The architecture operates across four coupled stages:

1. **4D Orthonormal Rotation:** Applying a true six-plane $SO(4)$ rotation to the tesseract in $\mathbb{R}^4$.
2. **Perspective Hyper-Projection:** Projecting rotated 4D coordinates into 3D space while preventing near-plane division singularities.
3. **Elastic Deformation & Dual-Phase Propagation:** Deforming fiber trajectories using a decoupled Hookean spring model and sinusoidal kinematic envelope, driven by localized spatial fields and global temporal progression.
4. **Spatiotemporal Erosion & Fragmentation:** Evaluating a thresholded scalar erosion field $E$ to drive thermal shader emission seams and downstream geometric detachment.

Early prototypes of this pipeline contained mathematical shortcuts—such as an incomplete five-angle rotation matrix, asymmetric coordinate scaling during rotation, conflation of geometric sine envelopes with physical Hookean stiffness, and ambiguity between vertex color thresholding and topological mesh deletion. This revised methodology establishes a mathematically consistent, reproducible formulation across both Cinema 4D / Redshift and standalone Python (NumPy/Matplotlib) environments.

---

## 2. Related Work

* **4D Geometry & $SO(4)$ Rotations:** A regular tesseract consists of 16 vertices and 32 edges, with four orthogonal edges meeting at each vertex. Unlike 3D rotations ($SO(3)$, 3 degrees of freedom), the 4D rotation group $SO(4)$ is a 6-dimensional Lie group requiring six independent planar rotation angles corresponding to the coordinate planes $(X,Y), (X,Z), (X,W), (Y,Z), (Y,W), (Z,W)$.
* **Elastic Networks & 4D Printing:** Mass-spring networks are standard tools for simulating deformable filaments in computer graphics, while programmable shape-morphing materials (4D printing) study how fiber-reinforced polymers deform and degrade over time under thermal or chemical stimuli.
* **Procedural Shading & Cinema 4D Architecture:** Cinema 4D's Python Generator evaluates procedural geometry inside `main()` and returns a `c4d.BaseObject` (such as a `c4d.Ospline`). Multi-channel vertex data is stored via `c4d.VertexColorTag` (supporting four `RGBA` channels per vertex) and read inside Redshift via `RS Color User Data` nodes, while physical segment detachment is executed downstream using MoGraph `PolyFX` modifiers.

---

## 3. Corrected Mathematical Methods

### 3.1 True $SO(4)$ Six-Plane Rotation
To preserve Euclidean edge lengths and prevent non-rigid shearing in $\mathbb{R}^4$, any 4D rotation matrix $\mathbf{R}$ must belong to the special orthogonal group $SO(4)$, satisfying $\mathbf{R}^T \mathbf{R} = \mathbf{I}$ and $\det(\mathbf{R}) = +1$. Rather than constructing a single heuristic matrix, we compose six independent planar Givens rotations:

$$\mathbf{R}_{XY}(\alpha) = \begin{bmatrix} \cos\alpha & -\sin\alpha & 0 & 0 \\ \sin\alpha & \cos\alpha & 0 & 0 \\ 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 1 \end{bmatrix}$$

Analogous $4 \times 4$ planar rotation matrices $\mathbf{R}_{XZ}(\beta)$, $\mathbf{R}_{XW}(\gamma)$, $\mathbf{R}_{YZ}(\delta)$, $\mathbf{R}_{YW}(\epsilon)$, and $\mathbf{R}_{ZW}(\zeta)$ rotate their respective coordinate pairs while leaving the remaining two axes invariant. The total orthonormal transformation is:

$$\mathbf{R}_{\text{total}} = \mathbf{R}_{ZW}(\zeta)\,\mathbf{R}_{YW}(\epsilon)\,\mathbf{R}_{YZ}(\delta)\,\mathbf{R}_{XW}(\gamma)\,\mathbf{R}_{XZ}(\beta)\,\mathbf{R}_{XY}(\alpha)$$

### 3.2 Singularity-Safe Perspective Projection ($\mathbb{R}^4 \to \mathbb{R}^3$)
Given a rotated 4D point $\mathbf{v}' = [x', y', z', w']^T = \mathbf{R}_{\text{total}}\mathbf{v}$, we translate along the fourth dimension by a camera offset $w_{\text{offset}} > \sqrt{4}\,(s/2)$ so that the tesseract remains strictly in front of the 4D projection hyperplane:

$$w_{\text{shifted}} = w' + w_{\text{offset}}$$

To prevent numerical explosion near the projection singularity ($w_{\text{shifted}} \to 0$), we enforce a near-plane threshold $\varepsilon = 10^{-3}$. Any point with $|w_{\text{shifted}}| < \varepsilon$ is skipped or clamped; otherwise, its 3D perspective coordinates are:

$$\mathbf{p}_{3D} = \left( \frac{x'}{w_{\text{shifted}}},\; \frac{y'}{w_{\text{shifted}}},\; \frac{z'}{w_{\text{shifted}}} \right)$$

### 3.3 Tesseract Discretization & Decoupled Hookean Spring Model
For a centered tesseract of side length $s$, the 16 vertices are located at $(\pm s/2, \pm s/2, \pm s/2, \pm s/2)$, connected by 32 edges between vertex pairs differing in exactly one coordinate. Each edge $(i, j)$ is uniformly sampled in 4D with $N$ points ($t_k = k/(N-1)$ for $k = 0, \dots, N-1$) prior to rotation and projection.

We strictly separate **physical material stiffness** from **geometric morphing envelopes**:
1. **Hookean Elastic Network (Physical):** Each projected edge acts as a linear spring with rest length $L_0$ and stiffness constant $k$. The restoring force and elastic potential energy are:
   $$\mathbf{F}_{ij} = -k\left(\|\mathbf{p}_i - \mathbf{p}_j\| - L_0\right)\frac{\mathbf{p}_i - \mathbf{p}_j}{\|\mathbf{p}_i - \mathbf{p}_j\|}, \qquad E_{\text{spring}} = \frac{1}{2}k\left(\|\mathbf{p}_i - \mathbf{p}_j\| - L_0\right)^2$$
2. **Sinusoidal Kinematic Envelope (Geometric):** The function $\sin(\pi t)$ for normalized time $t \in [0, 1]$ acts as a smooth temporal amplitude envelope ($0$ at $t=0,1$; maximum $1$ at $t=0.5$) scaling radial arc perturbations $\mathbf{u}(s, t) = A\sin(\pi t)\sin(\pi s)\hat{\mathbf{n}}$ without altering physical stiffness $k$.

### 3.4 Two-Tier Spatiotemporal Erosion & Disintegration
To model progressive breakdown across the $W$-axis, each sampled point evaluates a normalized scalar erosion field:

$$E(x, y, z, w) = w_{\text{norm}} + \eta_{\text{proc}}(x, y, z)$$

where $w_{\text{norm}} \in [0, 1]$ is the normalized fourth coordinate and $\eta_{\text{proc}} \in [0, 0.5]$ is bounded procedural noise. Rather than conflating shader coloring with topological deletion, we define two explicit tiers:
* **Tier 1 — Shader Threshold Classification:** Points with $E < 0.48$ remain solid (`Opacity = 1.0`). Points inside the narrow 4% boundary $0.48 \le E \le 0.52$ trigger a high-intensity **Redshift Emission** spike (the thermal ignition seam). Points with $E > 0.52$ are assigned `Opacity = 0.0`.
* **Tier 2 — Topological Detachment (`PolyFX` / Segment Filtering):** In standalone Python verification, points exceeding the cutoff ($E > 0.52$) are pruned from rendered segments. Inside Cinema 4D, routing the same scalar field into a MoGraph **PolyFX** modifier (with `Scale = -1` and radial falloff) physically detaches and scatters spline segments along the burning boundary.

---

## 4. Cinema 4D vs. Google Colab Implementation Alignment

| System Component | Cinema 4D Python Generator (`c4d_4d_fiber_engine.py`) | Google Colab Sandbox (`test_4d_so4_engine.py`) |
| :--- | :--- | :--- |
| **Execution Context** | Native **Python Generator** object; builds `c4d.Ospline` with 32 segments and terminates with `return spline`. | Standalone NumPy / Matplotlib 3D verification script. |
| **$SO(4)$ Rotation** | Composes 6 planar $4 \times 4$ rotation matrices without asymmetric coordinate scaling. | Composes identical 6 planar $4 \times 4$ matrices; logs $\|\mathbf{R}^T\mathbf{R} - \mathbf{I}\|$ and $\det(\mathbf{R})$. |
| **Sampling Resolution** | Configurable User Data integer $N$ (`pts_per_strand`, standardized to `30`). | Standardized to `pts_per_edge = 30` for 1:1 vertex correspondence. |
| **Vertex Data & Output** | Writes 4-channel `RGBA` data into `c4d.VertexColorTag` (`R`: Opacity cutoff, `G`: Ignition seam, `B`: Erosion $E$) for Redshift + `PolyFX`. | Plots solid (`#00e5ff`) and ignition (`#ff5500`) points while pruning $E > 0.52$, printing Hookean energy (J). |

---

## 5. Experimental Validation Protocol

To empirically benchmark the revised system, we define five controlled computational experiments:
1. **Orthonormality & Topology Baseline:** Verify $\|\mathbf{R}^T\mathbf{R} - \mathbf{I}\|_F < 10^{-12}$, $\det(\mathbf{R}) = 1.0$, and exact connectivity of 16 vertices and 32 edges at $t = 0$.
2. **Six-Plane Rotation Sweep:** Sweep each angle $(\alpha, \beta, \gamma, \delta, \epsilon, \zeta) \in [0, 2\pi]$ independently while verifying near-plane stability ($|w_{\text{shifted}}| \ge \varepsilon$).
3. **Hookean Energy vs. Kinematic Envelope Ablation:** Compare total spring energy $E_{\text{spring}}$ with and without the sinusoidal arc perturbation $A\sin(\pi t)\sin(\pi s)$ to verify that endpoints remain pinned while midpoint strain peaks cleanly at $t = 0.5$.
4. **Erosion Threshold Monotonicity Sweep:** Sweep the cutoff threshold across $[0.0, 1.0]$ and verify monotonic transition from 100% solid vertices to 100% eroded vertices, tracking ignition seam point counts in the $4\%$ transition band.
5. **Cross-Environment Parity Test:** Export 3D vertex coordinates from the Cinema 4D Python Generator and compute mean Euclidean distance against the Colab NumPy output under identical parameters (target error $< 10^{-5}$).

---

## 6. Limitations and Future Work

* **Empirical Calibration:** Current spring stiffness ($k$) and noise scale parameters are normalized for visual and numerical stability rather than calibrated to physical polymer laboratory data.
* **Dynamic Time-Stepping:** Replacing static energy evaluation with a symplectic Verlet or implicit Euler integrator would allow inertial wave propagation across the 32 fibers during rapid $SO(4)$ rotations.
* **GPU Acceleration:** Porting the 6-plane matrix transformations and erosion field evaluations to C++ or GPU compute shaders would enable real-time simulation of dense multi-thousand-strand bundles.

---

## References

1. Coxeter, H. S. M. *Regular Polytopes*. Dover Publications, 1973. (Foundational geometry of the 4-cube / tesseract: 16 vertices, 32 edges, 24 faces, 8 cells).
2. Hanson, A. J. *Visualizing Quaternions*. Morgan Kaufmann, 2006. (Structure of $SO(4)$, planar rotations, and 4D-to-3D perspective projection).
3. Baraff, D., & Witkin, A. "Large Steps in Cloth Simulation." *ACM SIGGRAPH*, 1998. (Hookean spring-mass energy formulations).
4. Maxon Computer GmbH. *Cinema 4D Python SDK & Redshift Documentation* (VertexColorTag `RGBA` architecture and `PolyFX` falloff modifiers).
