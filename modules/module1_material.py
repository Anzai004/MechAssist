import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH   = os.path.join(BASE_DIR, 'data', 'module1', 'Material Selection', 'Data.csv')
KMEANS_PATH = os.path.join(BASE_DIR, 'models', 'kmeans_module1.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'models', 'scaler_module1.pkl')

FEATURES = ['Su', 'Sy', 'E', 'G', 'mu', 'Ro', 'A5']

# ── Load & Preprocess ──────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv(DATA_PATH)
    df['Sy'] = pd.to_numeric(df['Sy'], errors='coerce')
    df = df.drop(columns=['HV', 'pH', 'ID', 'Std', 'Heat treatment'])
    df['A5'] = df['A5'].fillna(df['A5'].median())
    df['Sy'] = df['Sy'].fillna(df['Sy'].median())
    return df

# ── Train & Save ───────────────────────────────────────────────────────────
def train(df):
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(df[FEATURES])
    km       = KMeans(n_clusters=6, random_state=42, n_init=10)
    km.fit(X_scaled)
    os.makedirs('models', exist_ok=True)
    joblib.dump(km, KMEANS_PATH)
    joblib.dump(scaler, SCALER_PATH)
    return km, scaler

# ── Load Saved Models ──────────────────────────────────────────────────────
def load_models():
    km     = joblib.load(KMEANS_PATH)
    scaler = joblib.load(SCALER_PATH)
    return km, scaler

def get_elbow_data(k_range=range(1, 11)):
    df = load_data()
    km, scaler = load_models()
    X_scaled = scaler.transform(df[FEATURES])
    inertias = []
    for k in k_range:
        m = KMeans(n_clusters=k, random_state=42, n_init=10)
        m.fit(X_scaled)
        inertias.append(m.inertia_)
    return list(k_range), inertias

# ── Failure Concern ────────────────────────────────────────────────────────
def get_failure_concern(bhn, sy=None):
    if pd.isna(bhn):
        if sy is None:                return "Unknown"
        elif sy > 600:                return "Fracture Risk"
        elif sy > 300:                return "Fatigue Risk"
        else:                         return "Creep Risk"
    elif bhn > 300:                   return "Fracture Risk"
    elif bhn > 200:                   return "Fatigue Risk"
    else:                             return "Creep Risk"

# ── E fallback map by failure concern / Sy range (GPa) ────────────────────
# Used when the dataset row has NaN for E.
# Approximate values sourced from Machinery's Handbook & ASM.
def _estimate_E_gpa(row) -> float:
    """Return approximate Young's modulus in GPa from dataset row."""
    e_raw = row.get('E', None)
    try:
        e = float(e_raw)
        if e > 0:
            # Data.csv stores E in MPa (same units as Sy/Su)
            # If E > 10000 it's in MPa → convert to GPa
            return round(e / 1000.0, 1) if e > 10000 else round(e, 1)
    except (TypeError, ValueError):
        pass
    # Fallback: estimate from density + Sy (very rough)
    sy  = float(row.get('Sy', 250))
    ro  = float(row.get('Ro', 7850))
    if ro < 3000:    return 70.0   # aluminium-class
    if ro < 5000:    return 110.0  # titanium-class
    if sy > 1200:    return 210.0  # high-alloy steel
    if sy > 600:     return 200.0  # alloy steel
    return 190.0                   # mild / low-alloy steel

# ── Recommend ──────────────────────────────────────────────────────────────
def recommend_materials(min_yield, max_density, min_elongation, n=3):
    df = load_data()
    km, scaler = load_models()
    X_scaled   = scaler.transform(df[FEATURES])
    df['Cluster'] = km.labels_

    filtered = df[
        (df['Sy'] >= min_yield)      &
        (df['Ro'] <= max_density)    &
        (df['A5'] >= min_elongation)
    ].copy()

    if filtered.empty:
        return []

    filtered = filtered.sort_values(by=['Sy', 'Ro'], ascending=[False, True])
    top      = filtered.head(n)

    results = []
    for _, row in top.iterrows():
        e_gpa = _estimate_E_gpa(row)
        results.append({
            'Material':             row['Material'],
            'Yield Strength (MPa)': row['Sy'],
            'Density (kg/m\u00b3)': row['Ro'],
            'Elongation (%)':       row['A5'],
            'E (GPa)':              e_gpa,            # ← NEW
            'E (Pa)':               e_gpa * 1e9,      # ← NEW  ready for beam tool
            'Cluster':              int(row['Cluster']),
            'Failure Concern':      get_failure_concern(row['Bhn'], row['Sy'])
        })
    return results