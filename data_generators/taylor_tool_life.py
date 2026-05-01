import numpy as np

# ── Tool Material Taylor Constants ─────────────────────────────────────────
# Source: standard machining handbooks (Boothroyd, Kalpakjian)
# Format: (n, C) where v * T^n = C
# C values assume workpiece = medium carbon steel baseline
# Adjusted per workpiece grade (L/M/H) via grade multiplier

TOOL_TAYLOR = {
    'HSS':     (0.125, 70),    # High Speed Steel — slow, cheap
    'Carbide': (0.25,  200),   # Cemented Carbide — industry standard
    'Ceramic': (0.40,  500),   # Ceramic — high speed, brittle
    'CBN':     (0.50,  800),   # Cubic Boron Nitride — hardened steels
}

# Workpiece grade multiplier on C
# H grade = harder material = shorter tool life = lower C
GRADE_MULTIPLIER = {
    'L': 1.20,
    'M': 1.00,
    'H': 0.75,
}

# Upgrade suggestion when tool life is short
TOOL_UPGRADE = {
    'HSS':     'Carbide',
    'Carbide': 'Ceramic',
    'Ceramic': 'CBN',
    'CBN':     None,   # already best
}

TOOL_DESCRIPTIONS = {
    'HSS':     'High Speed Steel — low cost, low speed, general purpose',
    'Carbide': 'Cemented Carbide — industry standard, good speed/life balance',
    'Ceramic': 'Ceramic — high speed, brittle, needs rigid setup',
    'CBN':     'Cubic Boron Nitride — best for hardened steels, premium cost',
}

def get_taylor_constants(tool_material='Carbide', grade='M'):
    n, C_base = TOOL_TAYLOR.get(tool_material, TOOL_TAYLOR['Carbide'])
    mult      = GRADE_MULTIPLIER.get(grade, 1.0)
    C         = round(C_base * mult, 2)
    return n, C

def taylor_tool_life(v, n=0.25, C=200):
    if v <= 0:
        return float('inf')
    T = (C / v) ** (1 / n)
    return round(T, 2)

def generate_cutting_conditions(v_base, feed_base, depth_base, n=0.25, C=200):
    conditions = {
        'Conservative': {
            'speed (m/min)':   round(v_base * 0.8, 2),
            'feed (mm/rev)':   round(feed_base * 0.8, 3),
            'depth (mm)':      round(depth_base * 0.8, 2),
            'tool_life (min)': taylor_tool_life(v_base * 0.8, n, C)
        },
        'Balanced': {
            'speed (m/min)':   round(v_base, 2),
            'feed (mm/rev)':   round(feed_base, 3),
            'depth (mm)':      round(depth_base, 2),
            'tool_life (min)': taylor_tool_life(v_base, n, C)
        },
        'Aggressive': {
            'speed (m/min)':   round(v_base * 1.2, 2),
            'feed (mm/rev)':   round(feed_base * 1.2, 3),
            'depth (mm)':      round(depth_base * 1.2, 2),
            'tool_life (min)': taylor_tool_life(v_base * 1.2, n, C)
        }
    }
    return conditions