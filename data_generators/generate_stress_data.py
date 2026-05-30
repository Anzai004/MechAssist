"""
MechAssist — Stress Data Generator
44,900+ samples across 5 risk classes and 3 member types.
Shaft samples are torsion-dominant (tau >> sigma).
"""
import numpy as np
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, '..', 'data', 'module2', 'stress_data.csv')

rng = np.random.default_rng(42)

def von_mises(sigma, tau):
    return np.sqrt(sigma**2 + 3*tau**2)

rows = []

# 1. BEAM samples (bending dominant)
n = 9000
Sy  = rng.uniform(100e6, 1400e6, n)
Su  = Sy * rng.uniform(1.2, 1.6, n)
sigma = rng.uniform(0, 1.6*Sy)
tau   = rng.uniform(0, 0.4*Sy)
vm    = von_mises(sigma, tau)
ratio = vm / Sy
for i in range(n):
    r = ratio[i]
    if r < 0.6:   lbl = "Safe"
    elif r < 0.9: lbl = "Fatigue Risk" if rng.random()<0.5 else "Yield Risk"
    elif r < 1.1: lbl = "Yield Risk"
    else:         lbl = "Fracture Risk"
    rows.append({"member_type":"beam","sigma":sigma[i],"tau":tau[i],"sigma_vm":vm[i],"Sy":Sy[i],"Su":Su[i],"label":lbl})

# 2. COLUMN samples (axial, buckling-prone)
n = 9000
Sy  = rng.uniform(100e6, 1400e6, n)
Su  = Sy * rng.uniform(1.2, 1.6, n)
sigma = rng.uniform(0, 1.8*Sy)
tau   = rng.uniform(0, 0.2*Sy)
vm    = von_mises(sigma, tau)
ratio = vm / Sy
for i in range(n):
    r = ratio[i]
    if sigma[i] > 0.6*Sy[i] and rng.random()<0.55: lbl = "Buckling Risk"
    elif r < 0.6:   lbl = "Safe"
    elif r < 0.9:   lbl = "Yield Risk"
    elif r < 1.1:   lbl = "Yield Risk"
    else:           lbl = "Fracture Risk"
    rows.append({"member_type":"column","sigma":sigma[i],"tau":tau[i],"sigma_vm":vm[i],"Sy":Sy[i],"Su":Su[i],"label":lbl})

# 3. SHAFT samples (torsion dominant)
n = 12000
Sy  = rng.uniform(150e6, 1400e6, n)
Su  = Sy * rng.uniform(1.2, 1.6, n)
tau   = rng.uniform(0, 1.2*Sy)    # torsional shear — dominant
sigma = rng.uniform(0, 0.4*Sy)    # bending — secondary
vm    = von_mises(sigma, tau)
ratio = vm / Sy
for i in range(n):
    r = ratio[i]
    if r < 0.6:   lbl = "Safe"
    elif r < 0.9: lbl = "Fatigue Risk" if rng.random()<0.55 else "Yield Risk"
    elif r < 1.1: lbl = "Yield Risk"
    else:         lbl = "Fracture Risk"
    rows.append({"member_type":"shaft","sigma":sigma[i],"tau":tau[i],"sigma_vm":vm[i],"Sy":Sy[i],"Su":Su[i],"label":lbl})

# 4. Extra buckling (column)
n = 3000
Sy    = rng.uniform(200e6, 900e6, n)
Su    = Sy * rng.uniform(1.2, 1.6, n)
sigma = rng.uniform(0.55*Sy, 1.8*Sy)
tau   = rng.uniform(0, 0.15*Sy)
vm    = von_mises(sigma, tau)
for i in range(n):
    rows.append({"member_type":"column","sigma":sigma[i],"tau":tau[i],"sigma_vm":vm[i],"Sy":Sy[i],"Su":Su[i],"label":"Buckling Risk"})

# 5. Safe oversampling (all types)
n_each = 1000
for member in ["beam","shaft","column"]:
    Sy    = rng.uniform(150e6, 1200e6, n_each)
    Su    = Sy * rng.uniform(1.2, 1.6, n_each)
    sigma = rng.uniform(0, 0.45*Sy)
    tau   = rng.uniform(0, 0.25*Sy)
    vm    = von_mises(sigma, tau)
    for i in range(n_each):
        rows.append({"member_type":member,"sigma":sigma[i],"tau":tau[i],"sigma_vm":vm[i],"Sy":Sy[i],"Su":Su[i],"label":"Safe"})

df = pd.DataFrame(rows).sample(frac=1, random_state=42).reset_index(drop=True)
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"Generated {len(df)} samples")
print(df["label"].value_counts())
print(df["member_type"].value_counts())