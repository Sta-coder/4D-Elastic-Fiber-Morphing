import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# 1. SIMULATION PARAMETERS (Aligned with Revised Methodology)
# ==============================================================================
side_length = 2.0        # Regular tesseract edge length (vertices at +/- 1.0)
pts_per_edge = 30        # Uniform sampling resolution N per edge
w_offset = 3.2           # Camera/4D offset along W to prevent near-plane singularity
t_morph = 0.50           # Normalized time t in [0, 1] (Envelope peaks at t = 0.5)
amplitude = 0.18         # Geometric kinematic perturbation amplitude A
spring_k = 1.5           # Hookean spring stiffness constant k
erosion_threshold = 0.52 # Structural cutoff threshold on field E
ignition_band = 0.04     # Narrow 4% thermal emission band [0.48, 0.52]

# Six independent rotation angles (in radians) for SO(4) coordinate planes
angles_so4 = {
    'xy': 0.35,
    'xz': 0.25,
    'xw': 0.75,
    'yz': 0.20,
    'yw': 0.45,
    'zw': 0.60
}

# ==============================================================================
# 2. TRUE SO(4) SIX-PLANE ROTATION MATRIX & PERSPECTIVE PROJECTION
# ==============================================================================
def planar_rotation_4d(i, j, theta):
    """Constructs a 4x4 orthonormal rotation matrix in coordinate plane (i, j)."""
    R = np.eye(4)
    c, s = np.cos(theta), np.sin(theta)
    R[i, i] = c
    R[i, j] = -s
    R[j, i] = s
    R[j, j] = c
    return R

def build_so4_matrix(angles):
    """Composes all 6 planar rotations: R = R_zw * R_yw * R_yz * R_xw * R_xz * R_xy."""
    R_xy = planar_rotation_4d(0, 1, angles['xy'])
    R_xz = planar_rotation_4d(0, 2, angles['xz'])
    R_xw = planar_rotation_4d(0, 3, angles['xw'])
    R_yz = planar_rotation_4d(1, 2, angles['yz'])
    R_yw = planar_rotation_4d(1, 3, angles['yw'])
    R_zw = planar_rotation_4d(2, 3, angles['zw'])
    return R_zw @ R_yw @ R_yz @ R_xw @ R_xz @ R_xy

def project_4d_to_3d(v4d, w_cam_offset, eps=1e-3):
    """Perspective projection (x'/w', y'/w', z'/w') with near-plane singularity check."""
    x, y, z, w = v4d
    w_shifted = w + w_cam_offset
    if abs(w_shifted) < eps:
        return None, w_shifted
    return np.array([x / w_shifted, y / w_shifted, z / w_shifted]), w_shifted

# ==============================================================================
# 3. TESSERACT TOPOLOGY (16 VERTICES, 32 EDGES) & ELASTIC DIAGNOSTICS
# ==============================================================================
half = side_length / 2.0
vertices_4d = np.array([
    [sx * half, sy * half, sz * half, sw * half]
    for sx in (-1.0, 1.0)
    for sy in (-1.0, 1.0)
    for sz in (-1.0, 1.0)
    for sw in (-1.0, 1.0)
])

# Connect vertices differing in exactly one coordinate
edges = []
for i in range(16):
    for j in range(i + 1, 16):
        if np.sum(np.abs(vertices_4d[i] - vertices_4d[j]) > 1e-6) == 1:
            edges.append((i, j))

R_total = build_so4_matrix(angles_so4)

# Verify SO(4) orthonormality: R^T * R = I and det(R) = +1
ortho_error = np.linalg.norm(R_total.T @ R_total - np.eye(4))
det_r = np.linalg.det(R_total)

# Project base vertices to compute Hookean spring energy across the 32 edges
proj_verts = {}
for idx, v in enumerate(vertices_4d):
    v_rot = R_total @ v
    p3, _ = project_4d_to_3d(v_rot, w_offset)
    if p3 is not None:
        proj_verts[idx] = p3

# Compute rest length L0 from unrotated projected edge length
v0_unrot, _ = project_4d_to_3d(vertices_4d[edges[0][0]], w_offset)
v1_unrot, _ = project_4d_to_3d(vertices_4d[edges[0][1]], w_offset)
L0 = np.linalg.norm(v0_unrot - v1_unrot)

total_spring_energy = 0.0
max_spring_force = 0.0
for (i, j) in edges:
    if i in proj_verts and j in proj_verts:
        dist = np.linalg.norm(proj_verts[i] - proj_verts[j])
        stretch = dist - L0
        total_spring_energy += 0.5 * spring_k * (stretch ** 2)
        max_spring_force = max(max_spring_force, abs(-spring_k * stretch))

# ==============================================================================
# 4. FIBER SAMPLING, SINUSOIDAL ENVELOPE & EROSION FIELD EVALUATION
# ==============================================================================
fig = plt.figure(figsize=(10, 8), facecolor='#0b0f19')
ax = fig.add_subplot(111, projection='3d', facecolor='#0b0f19')

kinematic_envelope = np.sin(np.pi * t_morph)  # Geometric midpoint bump at t = 0.5
solid_pts, ignition_pts, removed_pts = 0, 0, 0
np.random.seed(42)  # Deterministic noise for reproducible verification

for s_idx, (i, j) in enumerate(edges):
    va, vb = vertices_4d[i], vertices_4d[j]
    strand_coords = []
    strand_colors = []

    for k in range(pts_per_edge):
        s = k / float(pts_per_edge - 1)
        p4d = va + s * (vb - va)
        p4d_rot = R_total @ p4d

        p3d, w_val = project_4d_to_3d(p4d_rot, w_offset)
        if p3d is None:
            continue

        # Geometric sinusoidal envelope along the fiber arc (0 at endpoints)
        arc_profile = np.sin(np.pi * s)
        radial_dir = p3d / (np.linalg.norm(p3d) + 1e-6)
        p3d_morphed = p3d + radial_dir * (amplitude * kinematic_envelope * arc_profile)

        # Normalized erosion field E = w_norm + proc_noise in [0, 1]
        w_norm = (p4d_rot[3] + half) / side_length
        proc_noise = 0.25 * (np.sin(p3d_morphed[0] * 6.0) * np.cos(p3d_morphed[1] * 6.0) + 1.0)
        E_field = w_norm + proc_noise

        # Topological removal (simulating C4D PolyFX cutoff) vs Shader Ignition
        if E_field > erosion_threshold:
            removed_pts += 1
            continue
        elif (erosion_threshold - ignition_band) <= E_field <= erosion_threshold:
            ignition_pts += 1
            color = '#ff5500'  # Thermal Ignition Seam
        else:
            solid_pts += 1
            color = '#00e5ff'  # Intact Elastic Fiber

        strand_coords.append(p3d_morphed)
        strand_colors.append(color)

    if len(strand_coords) > 1:
        pts_arr = np.array(strand_coords)
        ax.scatter(pts_arr[:, 0], pts_arr[:, 1], pts_arr[:, 2], c=strand_colors, s=14, alpha=0.95)
        ax.plot(pts_arr[:, 0], pts_arr[:, 1], pts_arr[:, 2], color='#00e5ff', alpha=0.25, linewidth=1.0)

ax.set_title("Revised SO(4) Tesseract Fiber Morphing & Erosion Diagnostics", color='white', pad=15)
ax.axis('off')
plt.tight_layout()
plt.show()

# ==============================================================================
# 5. PRINT MATHEMATICAL & PHYSICAL DIAGNOSTICS
# ==============================================================================
print("=== SO(4) MATRIX VERIFICATION ===")
print(f"Orthonormality Error ||R^T R - I||: {ortho_error:.2e}")
print(f"Determinant det(R):                 {det_r:.6f}")
print("\n=== HOOKEAN SPRING NETWORK DIAGNOSTICS ===")
print(f"Rest Length (L0):                   {L0:.4f}")
print(f"Total Elastic Potential Energy:     {total_spring_energy:.4f} J")
print(f"Peak Edge Spring Force:             {max_spring_force:.4f} N")
print("\n=== SPATIOTEMPORAL EROSION COUNTS ===")
print(f"Solid Fiber Vertices (E < 0.48):    {solid_pts}")
print(f"Ignition Seam (0.48 <= E <= 0.52):  {ignition_pts}")
print(f"Removed by PolyFX Cutoff (E > 0.52):{removed_pts}")
