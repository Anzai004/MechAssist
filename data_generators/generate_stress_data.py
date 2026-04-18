import numpy as np
import pandas as pd
import os

np.random.seed(42)
N = 30000  # total samples

# ── BEAM: Bending + Transverse Shear ──────────────────────────────────────
def generate_beam_samples(n):
    # Geometry
    b = np.random.uniform(0.02, 0.2, n)       # width (m)
    h = np.random.uniform(0.05, 0.4, n)       # height (m)
    L = np.random.uniform(0.5, 5.0, n)        # length (m)

    # Loading
    M = np.random.uniform(1e3, 1e6, n)        # bending moment (Nm)
    V = np.random.uniform(1e2, 1e5, n)        # shear force (N)

    # Material
    Sy = np.random.uniform(200e6, 1500e6, n)  # yield strength (Pa)
    Su = Sy * np.random.uniform(1.2, 2.0, n)  # UTS (Pa)

    # Stress calculations
    I = (b * h**3) / 12                       # second moment of area
    y = h / 2                                 # distance to outer fibre
    sigma = (M * y) / I                       # bending stress (Pa)
    tau = (1.5 * V) / (b * h)                # shear stress (Pa)

    # Von Mises stress
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)

    return sigma, tau, sigma_vm, Sy, Su, ['beam'] * n

# ── SHAFT: Bending + Torsion ───────────────────────────────────────────────
def generate_shaft_samples(n):
    # Geometry
    d = np.random.uniform(0.02, 0.2, n)       # diameter (m)

    # Loading
    M = np.random.uniform(1e3, 1e6, n)        # bending moment (Nm)
    T = np.random.uniform(1e3, 1e6, n)        # torque (Nm)

    # Material
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)

    # Stress calculations
    r = d / 2
    I = np.pi * r**4 / 4                      # second moment of area
    J = np.pi * r**4 / 2                      # polar moment of area
    sigma = (M * r) / I                       # bending stress (Pa)
    tau = (T * r) / J                         # torsional shear stress (Pa)

    # Von Mises stress
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)

    return sigma, tau, sigma_vm, Sy, Su, ['shaft'] * n

# ── COLUMN: Euler Buckling ─────────────────────────────────────────────────
def generate_column_samples(n):
    # Geometry
    b = np.random.uniform(0.02, 0.2, n)       # width (m)
    h = np.random.uniform(0.02, 0.2, n)       # height (m)
    L = np.random.uniform(0.5, 5.0, n)        # length (m)

    # Loading
    P = np.random.uniform(1e3, 1e7, n)        # axial load (N)

    # Material
    E = np.random.uniform(70e9, 210e9, n)     # Young's modulus (Pa)
    Sy = np.random.uniform(200e6, 1500e6, n)
    Su = Sy * np.random.uniform(1.2, 2.0, n)

    # Stress calculations
    A = b * h                                  # cross sectional area
    I = (b * h**3) / 12                       # second moment of area
    sigma = P / A                             # axial stress (Pa)

    # Euler critical load (pinned-pinned)
    P_cr = (np.pi**2 * E * I) / (L**2)

    sigma_vm = sigma                           # no shear for pure axial
    tau = np.zeros(n)

    return sigma, tau, sigma_vm, Sy, Su, P, P_cr, ['column'] * n

# ── LABELLING ──────────────────────────────────────────────────────────────
def label_sample(sigma_vm, Sy, Su, member_type, P=None, P_cr=None):
    labels = []
    for i in range(len(sigma_vm)):
        if member_type[i] == 'column' and P is not None and P_cr is not None:
            if P[i] >= P_cr[i]:
                labels.append('Buckling Risk')
            elif sigma_vm[i] >= Sy[i]:
                labels.append('Yield Risk')
            elif sigma_vm[i] >= 0.5 * Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= 0.4 * Sy[i]:
                labels.append('Fatigue Risk')
            else:
                labels.append('Safe')
        else:
            if sigma_vm[i] >= Sy[i]:
                labels.append('Yield Risk')
            elif sigma_vm[i] >= 0.4 * Su[i]:
                labels.append('Fracture Risk')
            elif sigma_vm[i] >= 0.3 * Sy[i]:
                labels.append('Fatigue Risk')
            else:
                labels.append('Safe')
    return labels

# ── MAIN ───────────────────────────────────────────────────────────────────
def generate():
    n_each = N // 3

    # Beams
    s1, t1, vm1, sy1, su1, mt1 = generate_beam_samples(n_each)
    labels1 = label_sample(vm1, sy1, su1, mt1)

    # Shafts
    s2, t2, vm2, sy2, su2, mt2 = generate_shaft_samples(n_each)
    labels2 = label_sample(vm2, sy2, su2, mt2)

    # Columns
    s3, t3, vm3, sy3, su3, p3, pcr3, mt3 = generate_column_samples(n_each)
    labels3 = label_sample(vm3, sy3, su3, mt3, P=p3, P_cr=pcr3)

    df = pd.DataFrame({
        'member_type': mt1 + mt2 + mt3,
        'sigma': np.concatenate([s1, s2, s3]),
        'tau': np.concatenate([t1, t2, t3]),
        'sigma_vm': np.concatenate([vm1, vm2, vm3]),
        'Sy': np.concatenate([sy1, sy2, sy3]),
        'Su': np.concatenate([su1, su2, su3]),
        'label': labels1 + labels2 + labels3
    })

    os.makedirs('data/module2', exist_ok=True)
    df.to_csv('data/module2/stress_data.csv', index=False)
    print(f"Generated {len(df)} samples")
    print(df['label'].value_counts())

generate()