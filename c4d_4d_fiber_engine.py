import c4d
import math

def setup_user_data(op):
    """Creates interactive sliders in the C4D Attribute Manager if they do not exist."""
    if len(op.GetUserDataContainer()) > 0:
        return

    controls = [
        ("W-Camera Offset (d)", 1.5, 10.0, 0.1, 3.2),
        ("SO(4) Rotation Speed", 0.0, 5.0, 0.05, 1.0),
        ("Morph Progress (t)", 0.0, 1.0, 0.01, 0.5),
        ("Kinematic Amplitude (A)", 0.0, 50.0, 0.5, 12.0),
        ("Spring Stiffness (k)", 0.1, 10.0, 0.1, 1.5),
        ("Erosion Cutoff Threshold", 0.0, 1.5, 0.01, 0.52)
    ]

    for name, min_val, max_val, step, default_val in controls:
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
        bc[c4d.DESC_NAME] = name
        bc[c4d.DESC_MIN] = min_val
        bc[c4d.DESC_MAX] = max_val
        bc[c4d.DESC_STEP] = step
        bc[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER
        element = op.AddUserData(bc)
        op[element] = default_val

    c4d.EventAdd()

def planar_rotation_4d(i, j, theta):
    """Constructs a 4x4 orthonormal rotation matrix in coordinate plane (i, j)."""
    R = [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ]
    c, s = math.cos(theta), math.sin(theta)
    R[i][i] = c
    R[i][j] = -s
    R[j][i] = s
    R[j][j] = c
    return R

def mat_mul_4x4(A, B):
    """Multiplies two 4x4 matrices A and B."""
    result = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            result[i][j] = sum(A[i][k] * B[k][j] for k in range(4))
    return result

def build_so4_matrix(xy, xz, xw, yz, yw, zw):
    """Composes all 6 independent planar rotations: R = R_zw * R_yw * R_yz * R_xw * R_xz * R_xy."""
    R = planar_rotation_4d(0, 1, xy)
    R = mat_mul_4x4(planar_rotation_4d(0, 2, xz), R)
    R = mat_mul_4x4(planar_rotation_4d(0, 3, xw), R)
    R = mat_mul_4x4(planar_rotation_4d(1, 2, yz), R)
    R = mat_mul_4x4(planar_rotation_4d(1, 3, yw), R)
    R = mat_mul_4x4(planar_rotation_4d(2, 3, zw), R)
    return R

def multiply_matrix_vector_4d(M, v):
    """Multiplies a 4x4 orthonormal matrix M by a 4D vector [x, y, z, w]."""
    return [
        sum(M[i][j] * v[j] for j in range(4))
        for i in range(4)
    ]

def project_4d_to_3d(v4d, w_offset, scale=150.0, eps=1e-3):
    """
    Perspective projection (x'/w', y'/w', z'/w') with W-camera offset
    and near-plane singularity protection (|w'| >= eps).
    """
    x, y, z, w = v4d
    w_shifted = w + w_offset
    if abs(w_shifted) < eps:
        w_shifted = eps if w_shifted >= 0.0 else -eps
    factor = scale / w_shifted
    return c4d.Vector(x * factor, y * factor, z * factor), w_shifted

def main():
    setup_user_data(op)

    # Read UI Sliders safely
    w_offset    = op[c4d.ID_USERDATA, 1] if op[c4d.ID_USERDATA, 1] is not None else 3.2
    rot_speed   = op[c4d.ID_USERDATA, 2] if op[c4d.ID_USERDATA, 2] is not None else 1.0
    t_morph     = op[c4d.ID_USERDATA, 3] if op[c4d.ID_USERDATA, 3] is not None else 0.5
    amplitude   = op[c4d.ID_USERDATA, 4] if op[c4d.ID_USERDATA, 4] is not None else 12.0
    spring_k    = op[c4d.ID_USERDATA, 5] if op[c4d.ID_USERDATA, 5] is not None else 1.5
    e_cutoff    = op[c4d.ID_USERDATA, 6] if op[c4d.ID_USERDATA, 6] is not None else 0.52

    doc = c4d.documents.GetActiveDocument()
    frame = doc.GetTime().GetFrame(doc.GetFps())
    t_rot = frame * 0.03 * rot_speed

    # 1. Construct Regular Tesseract (16 Vertices, 32 Edges, side_length = 2.0)
    side_length = 2.0
    half = side_length / 2.0
    vertices_4d = [
        [sx * half, sy * half, sz * half, sw * half]
        for sx in (-1.0, 1.0)
        for sy in (-1.0, 1.0)
        for sz in (-1.0, 1.0)
        for sw in (-1.0, 1.0)
    ]

    edges = []
    for i in range(16):
        for j in range(i + 1, 16):
            diffs = sum(1 for k in range(4) if abs(vertices_4d[i][k] - vertices_4d[j][k]) > 1e-6)
            if diffs == 1:
                edges.append((i, j))

    # 2. Build Full 6-Plane Orthonormal SO(4) Rotation Matrix
    R_so4 = build_so4_matrix(
        xy=t_rot * 0.35,
        xz=t_rot * 0.25,
        xw=t_rot * 0.75,
        yz=t_rot * 0.20,
        yw=t_rot * 0.45,
        zw=t_rot * 0.60
    )

    # 3. Compute Hookean Spring Elastic Energy Across Projected Vertices
    proj_verts = []
    for v in vertices_4d:
        v_rot = multiply_matrix_vector_4d(R_so4, v)
        p3, _ = project_4d_to_3d(v_rot, w_offset)
        proj_verts.append(p3)

    v0_unrot, _ = project_4d_to_3d(vertices_4d[edges[0][0]], w_offset)
    v1_unrot, _ = project_4d_to_3d(vertices_4d[edges[0][1]], w_offset)
    L0 = (v0_unrot - v1_unrot).GetLength()

    total_spring_energy = 0.0
    for (i, j) in edges:
        dist = (proj_verts[i] - proj_verts[j]).GetLength()
        stretch = dist - L0
        total_spring_energy += 0.5 * spring_k * (stretch * stretch)

    # 4. Sample Fibers, Apply Kinematic Envelope sin(pi * t), & Evaluate Erosion Field
    num_strands = len(edges)
    pts_per_strand = 30  # Standardized N = 30 matching Colab script
    total_pts = num_strands * pts_per_strand

    kinematic_envelope = math.sin(math.pi * t_morph)
    ignition_band = 0.04

    points_3d = []
    vertex_colors = []

    for s_idx, (i1, i2) in enumerate(edges):
        va = vertices_4d[i1]
        vb = vertices_4d[i2]

        for p_idx in range(pts_per_strand):
            s = p_idx / float(pts_per_strand - 1)
            p4d = [va[k] + s * (vb[k] - va[k]) for k in range(4)]
            p4d_rot = multiply_matrix_vector_4d(R_so4, p4d)

            p3d, _ = project_4d_to_3d(p4d_rot, w_offset)

            # Geometric sinusoidal envelope along fiber arc (0 at endpoints)
            arc_profile = math.sin(math.pi * s)
            p_len = p3d.GetLength()
            radial_dir = p3d / p_len if p_len > 1e-6 else c4d.Vector(0.0, 1.0, 0.0)
            final_pos = p3d + radial_dir * (amplitude * kinematic_envelope * arc_profile)
            points_3d.append(final_pos)

            # Normalized erosion field E = w_norm + proc_noise
            w_norm = (p4d_rot[3] + half) / side_length
            proc_noise = 0.25 * (math.sin(final_pos.x * 0.05) * math.cos(final_pos.y * 0.05) + 1.0)
            E_field = w_norm + proc_noise

            # Encode RGBA channels for Redshift & PolyFX:
            # R = Opacity / PolyFX Mask (0.0 if E > cutoff else 1.0)
            # G = Thermal Ignition Seam (1.0 in [cutoff - 0.04, cutoff] else 0.0)
            # B = Normalized Elastic Energy Strain Indicator
            # A = 1.0
            cutoff_mask = 0.0 if E_field > e_cutoff else 1.0
            ignition_mask = 1.0 if ((e_cutoff - ignition_band) <= E_field <= e_cutoff) else 0.0
            strain_norm = min(total_spring_energy / 50000.0, 1.0)

            vertex_colors.append(c4d.Vector4d(cutoff_mask, ignition_mask, strain_norm, 1.0))

    # 5. Build Output B-Spline Object & Attach VertexColorTag
    spline = c4d.BaseObject(c4d.Ospline)
    spline.ResizeObject(total_pts, num_strands)
    spline.SetAllPoints(points_3d)
    spline[c4d.SPLINEOBJECT_TYPE] = c4d.SPLINEOBJECT_TYPE_B_SPLINE

    for s in range(num_strands):
        spline.SetSegment(s, pts_per_strand, Closed=False)

    vc_tag = spline.GetTag(c4d.Tvertexcolor)
    if vc_tag is None:
        vc_tag = c4d.VertexColorTag(total_pts)
        vc_tag.SetPerPointMode(True)
        spline.InsertTag(vc_tag)

    data_handle = vc_tag.GetDataAddressW()
    for idx, col in enumerate(vertex_colors):
        c4d.VertexColorTag.SetPoint(data_handle, None, None, idx, col)

    spline.Message(c4d.MSG_UPDATE)
    return spline
