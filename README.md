# 4D Elastic Fiber Morphing & Spatiotemporal Disintegration

[![Python 3.10+](https://shields.io)](https://python.org)
[![Cinema 4D](https://shields.io)](https://maxon.net)
[![License: MIT](https://shields.io)](LICENSE)[![DOI](https://zenodo.org/badge/1461271194.svg)](https://doi.org/10.5281/zenodo.24309319)

A computational graphics and physics framework that projects **6-plane SO(4) four-dimensional tesseract rotations** into **3D Hookean elastic fiber networks**, complete with **sinusoidal kinematic envelopes** and **threshold-driven spatiotemporal erosion** for Maxon Cinema 4D, Redshift, and Python.

---

## 💡 Overview (The Elevator Pitch)

Imagine trying to explain a 3D cube to a flat, 2D stick-figure living on a piece of paper—you could only show them its shadow as it spins. In this project, we project a **4D hypercube (tesseract)** into our 3D world.

Instead of rendering rigid, weightless wireframes, this engine models the 16 vertices and 32 edges of the tesseract as a **network of elastic physical fibers**. As the 4D topology undergoes orthonormal SO(4) rotations across six planes, the system computes Hookean spring tension, applies a smooth midpoint kinematic swell (\(\sin(\pi t)\)), and progressively disintegrates the fibers along a glowing thermal emission boundary.

---

## 🌍 Real-World Impact & Applications

* **Computer Graphics & VFX:** Automates complex higher-dimensional morphs and threshold-driven disintegration effects in Cinema 4D and Redshift using deterministic math rather than manual keyframing.
* **Physics & Mathematics Education:** Gives abstract 4D geometry physical mass, Hookean spring energy diagnostics, and color-coded stress zones—making invisible 4D rotations intuitive.
* **4D Printing & Smart Materials:** Offers a digital verification sandbox for modeling how dense smart-fiber networks stretch, relax under strain, and degrade across thermal thresholds.

---

## 🧮 Core Mathematical Upgrades (Revised Methodology)

1. **True SO(4) Six-Plane Orthonormal Rotation:** Composes six independent planar rotation matrices (\(R_{XY}, R_{XZ}, R_{XW}, R_{YZ}, R_{YW}, R_{ZW}\)) to guarantee \(R^T R = I\) and \(\det(R) = +1\), preserving exact 4D edge lengths without asymmetric scaling distortion.
2. **Singularity-Safe Perspective Projection:** Maps rotated 4D points (x', y', z', w') to 3D via (x'/w', y'/w', z'/w') using a W-camera offset and near-plane threshold (|w'| ≥ ε) to prevent division-by-zero explosions.
3. **Decoupled Elastic Physics & Kinematic Envelope:** Separates physical Hookean spring energy \(E_{\text{spring}} = \frac{1}{2}k(\Vert{}\mathbf{p}_i - \mathbf{p}_j\Vert{} - L_0)^2\) from the geometric midpoint perturbation envelope \(\sin(\pi t)\).
4. **Two-Tier Spatiotemporal Erosion:** Evaluates \(E = w_{\text{norm}} + \text{noise}\) to drive both **Redshift shader classification** (triggering a glowing emission seam in the narrow 0.48 ≤ E ≤ 0.52 band) and **topological segment removal** (E > 0.52 via Cinema 4D `PolyFX`).

---

## 📂 Repository Structure

```text
4D-Elastic-Fiber-Morphing/
├── README.md                                  # Project overview, math summary, and quick start
├── LICENSE                                    # MIT open-source license
├── paper/
│   └── 4D_Elastic_Fiber_Morphing_Revised.md   # Full revised academic methodology & proofs
├── c4d_plugin/
│   └── c4d_4d_fiber_engine.py                 # Cinema 4D Python Generator script (return spline)
└── colab_sandbox/
    └── test_4d_so4_engine.py                  # Standalone NumPy/Matplotlib SO(4) verification script
```

---

## 🚀 Quick Start

### 1. Verify the Math in Google Colab (No Cinema 4D Required)
Open [Google Colab](https://google.com), create a new notebook, paste the contents of `colab_sandbox/test_4d_so4_engine.py` into a code cell, and run it to verify $SO(4)$ orthonormality ($\|R^T R - I\| \approx 0$), Hookean potential energy (Joules), and 3D fiber erosion plots.

### 2. Run Inside Cinema 4D + Redshift
1. Create a **Python Generator** (`Create > Extensions > Python Generator`).
2. Paste `c4d_plugin/c4d_4d_fiber_engine.py` into the code editor and click **Execute** (outputs a B-Spline object via `return spline` with auto-generated User Data sliders).
3. Attach a **Redshift Object Tag** (Curves mode) and route the generated `VertexColorTag` into an **RS Color User Data** node to drive Opacity cutouts and glowing Emission tips, paired with a **PolyFX** modifier for physical fragment scatter.

---

## 👤 Author
**B.Sc. Computer Science University Student** — Computational Physics, Procedural Geometry, and Computer Graphics.
