"""
machine_specs.py — Machine tool database for MechAssist Module 3.
Covers India-relevant (HMT, Kirloskar, ACE, BFW, Batliboi) and
international (Haas, Mazak, DMG Mori, Okuma) machines.

Dict structure:
  MACHINE_SPECS[category][model] = {
      max_rpm, min_rpm, max_torque_nm, power_kw,
      max_speed_mmin, max_workpiece_dia_mm, max_workpiece_len_mm,
      typical_dia_mm, swing_mm (lathes) / table_mm (mills),
      ops: list of compatible operation types
  }

'ops' used for soft-warning if user selects wrong machine type.
"""

MACHINE_SPECS = {

    # ── LATHE ──────────────────────────────────────────────────────────────
    "Lathe": {

        "HMT NH26": {
            "max_rpm": 1800, "min_rpm": 36,
            "max_torque_nm": 800,  "power_kw": 7.5,
            "max_speed_mmin": 120,
            "max_workpiece_dia_mm": 260, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 50,  "swing_mm": 260,
            "ops": ["turning", "facing", "boring", "threading", "knurling"],
        },

        "HMT NH40": {
            "max_rpm": 1200, "min_rpm": 28,
            "max_torque_nm": 1200, "power_kw": 11.0,
            "max_speed_mmin": 150,
            "max_workpiece_dia_mm": 400, "max_workpiece_len_mm": 2000,
            "typical_dia_mm": 80,  "swing_mm": 400,
            "ops": ["turning", "facing", "boring", "threading", "knurling"],
        },

        "Kirloskar Turnmaster 35": {
            "max_rpm": 1600, "min_rpm": 32,
            "max_torque_nm": 900,  "power_kw": 7.5,
            "max_speed_mmin": 120,
            "max_workpiece_dia_mm": 350, "max_workpiece_len_mm": 1500,
            "typical_dia_mm": 60,  "swing_mm": 350,
            "ops": ["turning", "facing", "boring", "threading"],
        },

        "ACE Jobber XL": {
            "max_rpm": 3000, "min_rpm": 50,
            "max_torque_nm": 600,  "power_kw": 7.5,
            "max_speed_mmin": 200,
            "max_workpiece_dia_mm": 300, "max_workpiece_len_mm": 750,
            "typical_dia_mm": 50,  "swing_mm": 300,
            "ops": ["turning", "facing", "boring", "threading"],
        },

        "Batliboi Excel 165": {
            "max_rpm": 1400, "min_rpm": 28,
            "max_torque_nm": 750,  "power_kw": 5.5,
            "max_speed_mmin": 100,
            "max_workpiece_dia_mm": 165, "max_workpiece_len_mm": 750,
            "typical_dia_mm": 40,  "swing_mm": 165,
            "ops": ["turning", "facing", "boring", "threading"],
        },

        "Haas ST-10": {
            "max_rpm": 6000, "min_rpm": 25,
            "max_torque_nm": 203,  "power_kw": 11.2,
            "max_speed_mmin": 300,
            "max_workpiece_dia_mm": 330, "max_workpiece_len_mm": 394,
            "typical_dia_mm": 50,  "swing_mm": 330,
            "ops": ["turning", "facing", "boring", "threading", "grooving"],
        },

        "Haas ST-30": {
            "max_rpm": 4000, "min_rpm": 20,
            "max_torque_nm": 678,  "power_kw": 22.4,
            "max_speed_mmin": 400,
            "max_workpiece_dia_mm": 660, "max_workpiece_len_mm": 762,
            "typical_dia_mm": 100, "swing_mm": 660,
            "ops": ["turning", "facing", "boring", "threading", "grooving"],
        },

        "Mazak QTN 200": {
            "max_rpm": 5000, "min_rpm": 20,
            "max_torque_nm": 430,  "power_kw": 18.5,
            "max_speed_mmin": 350,
            "max_workpiece_dia_mm": 450, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 75,  "swing_mm": 450,
            "ops": ["turning", "facing", "boring", "threading", "grooving"],
        },

        "DMG Mori CTX 310": {
            "max_rpm": 5000, "min_rpm": 15,
            "max_torque_nm": 490,  "power_kw": 16.0,
            "max_speed_mmin": 350,
            "max_workpiece_dia_mm": 400, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 70,  "swing_mm": 400,
            "ops": ["turning", "facing", "boring", "threading", "grooving"],
        },

        "Okuma LB3000 EX": {
            "max_rpm": 5000, "min_rpm": 15,
            "max_torque_nm": 500,  "power_kw": 18.5,
            "max_speed_mmin": 380,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 1500,
            "typical_dia_mm": 80,  "swing_mm": 500,
            "ops": ["turning", "facing", "boring", "threading", "grooving"],
        },
    },

    # ── VERTICAL MILLING MACHINE ───────────────────────────────────────────
    "Vertical Milling Machine": {

        "HMT FN2V": {
            "max_rpm": 2240, "min_rpm": 35,
            "max_torque_nm": 250,  "power_kw": 3.7,
            "max_speed_mmin": 120,
            "max_workpiece_dia_mm": 300, "max_workpiece_len_mm": 700,
            "typical_dia_mm": 25,  "table_mm": 900,
            "ops": ["face milling", "end milling", "slot milling", "drilling"],
        },

        "Kirloskar FV-1": {
            "max_rpm": 1800, "min_rpm": 60,
            "max_torque_nm": 200,  "power_kw": 3.7,
            "max_speed_mmin": 100,
            "max_workpiece_dia_mm": 250, "max_workpiece_len_mm": 600,
            "typical_dia_mm": 20,  "table_mm": 800,
            "ops": ["face milling", "end milling", "slot milling", "drilling"],
        },

        "ACE V-Centre 400": {
            "max_rpm": 4000, "min_rpm": 50,
            "max_torque_nm": 180,  "power_kw": 7.5,
            "max_speed_mmin": 200,
            "max_workpiece_dia_mm": 400, "max_workpiece_len_mm": 800,
            "typical_dia_mm": 30,  "table_mm": 900,
            "ops": ["face milling", "end milling", "slot milling", "drilling", "boring"],
        },

        "BFW Millpak 1": {
            "max_rpm": 3000, "min_rpm": 40,
            "max_torque_nm": 220,  "power_kw": 5.5,
            "max_speed_mmin": 150,
            "max_workpiece_dia_mm": 350, "max_workpiece_len_mm": 750,
            "typical_dia_mm": 25,  "table_mm": 850,
            "ops": ["face milling", "end milling", "slot milling", "drilling"],
        },

        "Haas VF-2": {
            "max_rpm": 8100, "min_rpm": 20,
            "max_torque_nm": 122,  "power_kw": 22.4,
            "max_speed_mmin": 400,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 40,  "table_mm": 1016,
            "ops": ["face milling", "end milling", "slot milling", "drilling", "boring", "tapping"],
        },

        "Haas VF-4": {
            "max_rpm": 8100, "min_rpm": 20,
            "max_torque_nm": 122,  "power_kw": 22.4,
            "max_speed_mmin": 400,
            "max_workpiece_dia_mm": 800, "max_workpiece_len_mm": 1500,
            "typical_dia_mm": 60,  "table_mm": 1524,
            "ops": ["face milling", "end milling", "slot milling", "drilling", "boring", "tapping"],
        },
    },

    # ── HORIZONTAL MILLING MACHINE ─────────────────────────────────────────
    "Horizontal Milling Machine": {

        "HMT FH400": {
            "max_rpm": 1800, "min_rpm": 28,
            "max_torque_nm": 400,  "power_kw": 5.5,
            "max_speed_mmin": 100,
            "max_workpiece_dia_mm": 400, "max_workpiece_len_mm": 1200,
            "typical_dia_mm": 60,  "table_mm": 1200,
            "ops": ["slab milling", "side milling", "gang milling", "straddle milling"],
        },

        "Batliboi H-Mill 500": {
            "max_rpm": 1600, "min_rpm": 25,
            "max_torque_nm": 500,  "power_kw": 7.5,
            "max_speed_mmin": 120,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 1500,
            "typical_dia_mm": 75,  "table_mm": 1400,
            "ops": ["slab milling", "side milling", "gang milling"],
        },

        "Mazak HCN-5000": {
            "max_rpm": 15000, "min_rpm": 20,
            "max_torque_nm": 200,  "power_kw": 30.0,
            "max_speed_mmin": 500,
            "max_workpiece_dia_mm": 630, "max_workpiece_len_mm": 2000,
            "typical_dia_mm": 80,  "table_mm": 2000,
            "ops": ["face milling", "slab milling", "side milling", "boring", "drilling", "tapping"],
        },
    },

    # ── CNC MACHINING CENTRE ───────────────────────────────────────────────
    "CNC Machining Centre": {

        "ACE FX-5": {
            "max_rpm": 8000, "min_rpm": 20,
            "max_torque_nm": 150,  "power_kw": 11.0,
            "max_speed_mmin": 350,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 40,  "table_mm": 900,
            "ops": ["face milling", "end milling", "drilling", "boring", "tapping", "reaming"],
        },

        "BFW ORION V-40": {
            "max_rpm": 8000, "min_rpm": 20,
            "max_torque_nm": 190,  "power_kw": 15.0,
            "max_speed_mmin": 400,
            "max_workpiece_dia_mm": 600, "max_workpiece_len_mm": 1200,
            "typical_dia_mm": 50,  "table_mm": 1000,
            "ops": ["face milling", "end milling", "drilling", "boring", "tapping", "reaming"],
        },

        "Haas VF-3 (CNC)": {
            "max_rpm": 8100, "min_rpm": 20,
            "max_torque_nm": 122,  "power_kw": 22.4,
            "max_speed_mmin": 400,
            "max_workpiece_dia_mm": 600, "max_workpiece_len_mm": 1200,
            "typical_dia_mm": 50,  "table_mm": 1118,
            "ops": ["face milling", "end milling", "drilling", "boring", "tapping", "reaming"],
        },

        "Mazak VARIAXIS i-500": {
            "max_rpm": 12000, "min_rpm": 10,
            "max_torque_nm": 119,  "power_kw": 22.0,
            "max_speed_mmin": 500,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 500,
            "typical_dia_mm": 50,  "table_mm": 500,
            "ops": ["5-axis milling", "end milling", "drilling", "boring", "tapping"],
        },

        "DMG Mori DMU 50": {
            "max_rpm": 14000, "min_rpm": 10,
            "max_torque_nm": 120,  "power_kw": 25.0,
            "max_speed_mmin": 500,
            "max_workpiece_dia_mm": 500, "max_workpiece_len_mm": 500,
            "typical_dia_mm": 50,  "table_mm": 630,
            "ops": ["5-axis milling", "end milling", "drilling", "boring", "tapping", "reaming"],
        },

        "Okuma MB-5000H": {
            "max_rpm": 15000, "min_rpm": 10,
            "max_torque_nm": 210,  "power_kw": 30.0,
            "max_speed_mmin": 500,
            "max_workpiece_dia_mm": 700, "max_workpiece_len_mm": 1400,
            "typical_dia_mm": 60,  "table_mm": 1400,
            "ops": ["face milling", "end milling", "drilling", "boring", "tapping", "reaming"],
        },
    },

    # ── DRILL PRESS ────────────────────────────────────────────────────────
    "Drill Press": {

        "HMT Radial Drill RD-40": {
            "max_rpm": 2000, "min_rpm": 25,
            "max_torque_nm": 350,  "power_kw": 3.7,
            "max_speed_mmin": 80,
            "max_workpiece_dia_mm": 400, "max_workpiece_len_mm": 1500,
            "typical_dia_mm": 25,  "table_mm": 600,
            "ops": ["drilling", "reaming", "tapping", "counterboring", "countersinking"],
        },

        "Kirloskar Pillar Drill PD-25": {
            "max_rpm": 2800, "min_rpm": 56,
            "max_torque_nm": 120,  "power_kw": 1.5,
            "max_speed_mmin": 60,
            "max_workpiece_dia_mm": 250, "max_workpiece_len_mm": 600,
            "typical_dia_mm": 15,  "table_mm": 400,
            "ops": ["drilling", "reaming", "tapping", "counterboring"],
        },

        "Batliboi Radial Drill BD-50": {
            "max_rpm": 1600, "min_rpm": 20,
            "max_torque_nm": 500,  "power_kw": 5.5,
            "max_speed_mmin": 100,
            "max_workpiece_dia_mm": 600, "max_workpiece_len_mm": 2000,
            "typical_dia_mm": 30,  "table_mm": 700,
            "ops": ["drilling", "reaming", "tapping", "boring", "counterboring"],
        },

        "Generic Bench Drill Press": {
            "max_rpm": 3000, "min_rpm": 200,
            "max_torque_nm": 50,   "power_kw": 0.75,
            "max_speed_mmin": 40,
            "max_workpiece_dia_mm": 150, "max_workpiece_len_mm": 400,
            "typical_dia_mm": 10,  "table_mm": 300,
            "ops": ["drilling", "countersinking"],
        },
    },

    # ── GRINDING MACHINE ───────────────────────────────────────────────────
    "Grinding Machine": {

        "HMT G-13 Surface Grinder": {
            "max_rpm": 3000, "min_rpm": 1500,
            "max_torque_nm": 30,   "power_kw": 2.2,
            "max_speed_mmin": 35,
            "max_workpiece_dia_mm": 300, "max_workpiece_len_mm": 600,
            "typical_dia_mm": 50,  "table_mm": 600,
            "ops": ["surface grinding", "face grinding"],
        },

        "HMT G-17 Cylindrical Grinder": {
            "max_rpm": 500, "min_rpm": 60,
            "max_torque_nm": 60,   "power_kw": 3.7,
            "max_speed_mmin": 30,
            "max_workpiece_dia_mm": 200, "max_workpiece_len_mm": 750,
            "typical_dia_mm": 50,  "table_mm": 750,
            "ops": ["cylindrical grinding", "plunge grinding", "traverse grinding"],
        },

        "Kirloskar KSG-200 Surface Grinder": {
            "max_rpm": 2800, "min_rpm": 1400,
            "max_torque_nm": 25,   "power_kw": 2.2,
            "max_speed_mmin": 30,
            "max_workpiece_dia_mm": 250, "max_workpiece_len_mm": 500,
            "typical_dia_mm": 50,  "table_mm": 500,
            "ops": ["surface grinding", "face grinding"],
        },

        "Okuma GA-26N Cylindrical Grinder": {
            "max_rpm": 400,  "min_rpm": 40,
            "max_torque_nm": 120,  "power_kw": 11.0,
            "max_speed_mmin": 45,
            "max_workpiece_dia_mm": 320, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 80,  "table_mm": 1000,
            "ops": ["cylindrical grinding", "plunge grinding", "traverse grinding", "taper grinding"],
        },

        "Studer S33 CNC Grinder": {
            "max_rpm": 1000, "min_rpm": 20,
            "max_torque_nm": 100,  "power_kw": 7.5,
            "max_speed_mmin": 45,
            "max_workpiece_dia_mm": 175, "max_workpiece_len_mm": 1000,
            "typical_dia_mm": 50,  "table_mm": 1000,
            "ops": ["cylindrical grinding", "internal grinding", "plunge grinding", "traverse grinding"],
        },
    },
}

# ── Category → compatible operation types ──────────────────────────────────
# Used for soft warning if mismatch detected.
CATEGORY_OPS = {
    "Lathe":                    ["turning", "facing", "boring", "threading", "knurling", "grooving", "parting"],
    "Vertical Milling Machine": ["face milling", "end milling", "slot milling", "drilling", "boring", "tapping"],
    "Horizontal Milling Machine": ["slab milling", "side milling", "gang milling", "straddle milling", "face milling"],
    "CNC Machining Centre":     ["face milling", "end milling", "drilling", "boring", "tapping", "reaming", "5-axis milling"],
    "Drill Press":              ["drilling", "reaming", "tapping", "counterboring", "countersinking", "boring"],
    "Grinding Machine":         ["surface grinding", "cylindrical grinding", "face grinding", "plunge grinding", "traverse grinding", "internal grinding", "taper grinding"],
}

# Material hardness grade → recommended minimum machine category
GRADE_MACHINE_RECOMMENDATION = {
    "L": ["Lathe", "Vertical Milling Machine", "Horizontal Milling Machine", "Drill Press", "CNC Machining Centre", "Grinding Machine"],
    "M": ["Lathe", "Vertical Milling Machine", "CNC Machining Centre", "Grinding Machine"],
    "H": ["CNC Machining Centre", "Grinding Machine"],
}