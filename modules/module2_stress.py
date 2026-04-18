import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'module2', 'stress_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'rf_module2.pkl')
ENCODER_PATH = os.path.join(BASE_DIR, 'models', 'encoder_module2.pkl')

# ── Train & Save ───────────────────────────────────────────────────────────
def train():
    df = pd.read_csv(DATA_PATH)

    # Encode member_type as numeric
    df['member_type_enc'] = df['member_type'].map({'beam': 0, 'shaft': 1, 'column': 2})

    features = ['member_type_enc', 'sigma', 'tau', 'sigma_vm', 'Sy', 'Su']
    X = df[features]
    y = df['label']

    # Encode labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(X, y_enc, test_size=0.2, random_state=42)

    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    os.makedirs(os.path.join(BASE_DIR, 'models'), exist_ok=True)
    joblib.dump(rf, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)

    return rf, le

# ── Predict ────────────────────────────────────────────────────────────────
def predict_risk(member_type, sigma, tau, Sy, Su):
    rf = joblib.load(MODEL_PATH)
    le = joblib.load(ENCODER_PATH)

    member_map = {'beam': 0, 'shaft': 1, 'column': 2}
    sigma_vm = np.sqrt(sigma**2 + 3 * tau**2)

    X = pd.DataFrame([{
        'member_type_enc': member_map[member_type],
        'sigma': sigma,
        'tau': tau,
        'sigma_vm': sigma_vm,
        'Sy': Sy,
        'Su': Su
    }])

    pred_enc = rf.predict(X)[0]
    pred_proba = rf.predict_proba(X)[0]
    label = le.inverse_transform([pred_enc])[0]
    confidence = round(max(pred_proba) * 100, 2)

    return {
        'Risk Category': label,
        'Confidence (%)': confidence,
        'Von Mises Stress (Pa)': round(sigma_vm, 2),
        'Yield Strength (Pa)': Sy,
        'Stress Ratio (σ_vm/Sy)': round(sigma_vm / Sy, 4)
    }
    
# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    train()