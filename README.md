# MechAssist

**Engineering Decision Support System**  
AI/ML-powered desktop app for mechanical engineers and engineering students.  
Built as Portfolio Project P2 — Batch 2028, Jorhat Engineering College.

---

## Overview

MechAssist combines three ML modules into a single pipeline: material selection, stress assessment, and machinability advisory. Each module feeds into the next via auto-fill, producing a unified engineering summary and exportable PDF report.

---

## Features

### Module 1 — Material Selection
- K-Means clustering (k=6) on 1,552 real materials
- Filters by minimum yield strength, maximum density, minimum elongation
- Returns top 3 candidates ranked by Sy (descending) and ρ (ascending)
- Failure concern classification (Fracture / Fatigue / Creep) via Brinell hardness or Sy fallback
- Auto-fills Sy and Su into Module 2, material grade into Module 3

### Module 2 — Stress Assessment
- Random Forest Classifier trained on 44,900 synthetic samples
- 5 risk classes: Safe, Yield Risk, Fatigue Risk, Fracture Risk, Buckling Risk
- Von Mises stress, stress ratio, safety factor
- Mohr's Circle visualization (dynamic scale)
- Optional beam geometry tool: computes σ and τ from span, section, and load
- Shear Force Diagram, Bending Moment Diagram, Deflection Curve

### Module 3 — Machinability Advisory
- Random Forest Classifier on AI4I 2020 Predictive Maintenance Dataset (10,000 rows)
- Taylor tool life equation with real constants per tool material (HSS / Carbide / Ceramic / CBN)
- Three cutting modes: Conservative (−20%), Balanced (base), Aggressive (+20%)
- Workpiece grade multiplier (L / M / H) on Taylor C constant
- Tool life curve always shown
- Warnings and upgrade suggestions when tool life is short or failure risk detected

### Summary & Export
- Unified engineering narrative across all three modules
- Structured module cards with risk badges
- PDF export: full engineering report (A4, industry-style layout)

---

## Tech Stack

| Layer | Tools |
|---|---|
| Language | Python 3.14 |
| ML | scikit-learn (K-Means, Random Forest) |
| Data | pandas, NumPy |
| GUI | Tkinter (dark theme) |
| Plots | Matplotlib (TkAgg backend) |
| PDF | ReportLab |
| Models | joblib |

---

## Project Structure

```
MechAssist/
├── data/
│   ├── module1/Material Selection/Data.csv   # 1,552 materials
│   ├── module2/stress_data.csv               # 44,900 synthetic samples
│   └── module3/ai4i2020.csv                  # 10,000 rows, UCI dataset
├── data_generators/
│   ├── generate_stress_data.py               # Module 2 synthetic data
│   └── taylor_tool_life.py                   # Taylor constants + conditions
├── gui/
│   └── app.py                                # Main Tkinter application
├── models/
│   ├── kmeans_module1.pkl
│   ├── scaler_module1.pkl
│   ├── rf_module2.pkl
│   ├── encoder_module2.pkl
│   └── rf_module3_clf.pkl
├── modules/
│   ├── module1_material.py
│   ├── module2_stress.py
│   └── module3_machining.py
├── utils/
│   └── export_pdf.py                         # PDF report generator
├── notebook/                                 # Exploratory notebooks
├── main.py
└── LICENSE
```

---

## Setup

```bash
# Clone
git clone https://github.com/Anzai004/MechAssist.git
cd MechAssist

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install scikit-learn pandas numpy matplotlib joblib reportlab

# Run
python gui/app.py
```

> **Note:** Pre-trained model files are included in `models/`. No retraining needed to run.

---

## Retraining Models

```bash
# Module 1 (K-Means)
python modules/module1_material.py

# Module 2 (Random Forest — generate data first)
python data_generators/generate_stress_data.py
python modules/module2_stress.py

# Module 3 (Random Forest)
python modules/module3_machining.py
```

---

## Datasets

| Module | Dataset | Source |
|---|---|---|
| Module 1 | Material Selection Data (1,552 rows) | CES EduPack / public materials DB |
| Module 2 | Synthetic stress data (44,900 rows) | Generated — `generate_stress_data.py` |
| Module 3 | AI4I 2020 Predictive Maintenance | [UCI ML Repository](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) |

---

## Taylor Tool Life Constants

| Tool Material | n | C (base, M-grade) |
|---|---|---|
| HSS | 0.125 | 70 m/min |
| Carbide | 0.25 | 200 m/min |
| Ceramic | 0.40 | 500 m/min |
| CBN | 0.50 | 800 m/min |

Grade multipliers: L = ×1.20, M = ×1.00, H = ×0.75  
Source: Boothroyd & Knight, *Fundamentals of Machining and Machine Tools*; Kalpakjian.

---

## Known Limitations

- Su in Module 1 → Module 2 auto-fill estimated as 1.3 × Sy — verify if exact value known
- Beam tool: simply supported beam only; point load and UDL only
- Aggressive cutting speed not capped at 500 m/min validator limit when base speed is high
- Module 3 failure classifier uses fixed tool wear estimate (108) — does not update with actual wear data

---

## Roadmap

- [ ] Upgrade 11 — Retrain RF models with n_estimators=200
- [ ] Module 1 redesign: component-description input → required Sy computed internally
- [ ] Factor of Safety as design input (back-calculate allowable σ_vm)
- [ ] Industry-standard Summary tab (ASTM/ASME format)
- [ ] Accept MPa directly for all stress inputs

---

## Author

**Monjyeeman Dutta**  
B.Tech Mechanical Engineering, Jorhat Engineering College (Batch 2028)  
AI/ML Minor, Jorhat Engineering College
GitHub: [@Anzai004](https://github.com/Anzai004)

---

## License

MIT License — see [LICENSE](LICENSE)