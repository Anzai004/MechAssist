import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_generators.taylor_tool_life import (
    taylor_tool_life, generate_cutting_conditions,
    get_taylor_constants, TOOL_UPGRADE, TOOL_DESCRIPTIONS
)

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'module3', 'ai4i2020.csv')
CLF_PATH  = os.path.join(BASE_DIR, 'models', 'rf_module3_clf.pkl')

FEATURES = ['Type', 'Air temperature [K]', 'Process temperature [K]',
            'Rotational speed [rpm]', 'Torque [Nm]', 'TWF', 'HDF',
            'PWF', 'OSF', 'cutting_power', 'temp_delta']

# Tool life thresholds for warnings
TOOL_LIFE_CRITICAL = 5    # min — suggest upgrade
TOOL_LIFE_WARNING  = 15   # min — caution


def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.drop(columns=['UDI', 'Product ID', 'RNF'])
    df['Type'] = df['Type'].map({'L': 0, 'M': 1, 'H': 2})
    df['cutting_power'] = df['Torque [Nm]'] * (df['Rotational speed [rpm]'] * 2 * np.pi / 60)
    df['temp_delta']    = df['Process temperature [K]'] - df['Air temperature [K]']
    return df


def train():
    df = load_data()
    X  = df[FEATURES]
    y  = df['Machine failure']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)
    rf = RandomForestClassifier(
        n_estimators=100, class_weight='balanced', random_state=42)
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred,
          target_names=['No Failure', 'Failure']))
    os.makedirs(os.path.join(BASE_DIR, 'models'), exist_ok=True)
    joblib.dump(rf, CLF_PATH)
    return rf


def predict_failure(type_grade, air_temp, process_temp, rpm, torque,
                    twf, hdf, pwf, osf):
    rf            = joblib.load(CLF_PATH)
    cutting_power = torque * (rpm * 2 * np.pi / 60)
    temp_delta    = process_temp - air_temp
    type_map      = {'L': 0, 'M': 1, 'H': 2}
    X = pd.DataFrame([{
        'Type':                       type_map[type_grade],
        'Air temperature [K]':        air_temp,
        'Process temperature [K]':    process_temp,
        'Rotational speed [rpm]':     rpm,
        'Torque [Nm]':                torque,
        'TWF':                        twf,
        'HDF':                        hdf,
        'PWF':                        pwf,
        'OSF':                        osf,
        'cutting_power':              cutting_power,
        'temp_delta':                 temp_delta
    }])
    pred  = rf.predict(X)[0]
    proba = rf.predict_proba(X)[0]
    return {
        'Failure Risk':    'Yes' if pred == 1 else 'No',
        'Confidence (%)':  round(max(proba) * 100, 2)
    }


def get_advisory(type_grade, air_temp, process_temp, rpm, torque,
                 v_base, feed_base, depth_base,
                 tool_material='Carbide'):
    """
    Returns list of dicts, one per mode (Conservative/Balanced/Aggressive).
    Each dict includes tool life, failure risk, warnings, and suggestions.
    tool_material: 'HSS' | 'Carbide' | 'Ceramic' | 'CBN'
    type_grade   : 'L' | 'M' | 'H'  (workpiece hardness)
    """
    n, C       = get_taylor_constants(tool_material, type_grade)
    conditions = generate_cutting_conditions(v_base, feed_base, depth_base, n, C)
    results    = []

    cutting_power = torque * (rpm * 2 * np.pi / 60)
    temp_delta    = process_temp - air_temp
    tool_wear_est = 108

    twf = int(tool_wear_est > 200 and 3.8 <= torque <= 9)
    hdf = int(temp_delta < 8.6)
    pwf = int(cutting_power < 3500 or cutting_power > 9000)
    osf = int(torque * tool_wear_est > 11000)

    for mode, params in conditions.items():
        failure = predict_failure(
            type_grade, air_temp, process_temp,
            rpm, torque, twf, hdf, pwf, osf
        )

        tl = params['tool_life (min)']

        # Build warnings and suggestions
        warnings    = []
        suggestions = []

        if tl < TOOL_LIFE_CRITICAL:
            warnings.append(f"Tool life critically short ({tl} min).")
            upgrade = TOOL_UPGRADE.get(tool_material)
            if upgrade:
                suggestions.append(
                    f"Switch to {upgrade} tooling — "
                    f"expect {TOOL_DESCRIPTIONS[upgrade].split('—')[1].strip()}.")
            else:
                suggestions.append(
                    "Already using best available tool material. "
                    "Reduce cutting speed or depth of cut.")
        elif tl < TOOL_LIFE_WARNING:
            warnings.append(f"Tool life is short ({tl} min) — frequent tool changes needed.")
            upgrade = TOOL_UPGRADE.get(tool_material)
            if upgrade:
                suggestions.append(f"Consider upgrading to {upgrade} for longer tool life.")

        if failure['Failure Risk'] == 'Yes':
            warnings.append("Machine failure risk detected.")
            suggestions.append(
                "Reduce cutting speed or torque. "
                "Check spindle load and coolant flow.")

        if cutting_power > 9000:
            warnings.append(f"Cutting power high ({cutting_power:.0f} W).")
            suggestions.append("Reduce depth of cut or feed rate to lower power demand.")

        if temp_delta < 8.6:
            warnings.append("Low process-to-air temperature delta — possible coolant issue.")
            suggestions.append("Check coolant flow. Inadequate cooling accelerates tool wear.")

        results.append({
            'Mode':           mode,
            **params,
            'Failure Risk':   failure['Failure Risk'],
            'Confidence (%)': failure['Confidence (%)'],
            'Warnings':       warnings,
            'Suggestions':    suggestions,
            'tool_material':  tool_material,
            'n':              n,
            'C':              C,
        })

    return results