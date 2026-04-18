import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'module1', 'Material Selection', 'Data.csv')
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
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[FEATURES])
    km = KMeans(n_clusters=6, random_state=42, n_init=10)
    km.fit(X_scaled)
    os.makedirs('models', exist_ok=True)
    joblib.dump(km, KMEANS_PATH)
    joblib.dump(scaler, SCALER_PATH)
    return km, scaler

# ── Load Saved Models ──────────────────────────────────────────────────────
def load_models():
    km = joblib.load(KMEANS_PATH)
    scaler = joblib.load(SCALER_PATH)
    return km, scaler

# ── Failure Concern ────────────────────────────────────────────────────────
def get_failure_concern(bhn):
    if pd.isna(bhn):
        return "Unknown"
    elif bhn > 300:
        return "Fracture Risk"
    elif bhn > 200:
        return "Fatigue Risk"
    else:
        return "Creep Risk"

# ── Recommend ──────────────────────────────────────────────────────────────
def recommend_materials(min_yield, max_density, min_elongation, n=3):
    df = load_data()
    km, scaler = load_models()
    X_scaled = scaler.transform(df[FEATURES])
    df['Cluster'] = km.labels_

    filtered = df[
        (df['Sy'] >= min_yield) &
        (df['Ro'] <= max_density) &
        (df['A5'] >= min_elongation)
    ].copy()

    if filtered.empty:
        return []

    filtered = filtered.sort_values(by=['Sy', 'Ro'], ascending=[False, True])
    top = filtered.head(n)

    results = []
    for _, row in top.iterrows():
        results.append({
            'Material': row['Material'],
            'Yield Strength (MPa)': row['Sy'],
            'Density (kg/m³)': row['Ro'],
            'Elongation (%)': row['A5'],
            'Cluster': int(row['Cluster']),
            'Failure Concern': get_failure_concern(row['Bhn'])
        })
    return results