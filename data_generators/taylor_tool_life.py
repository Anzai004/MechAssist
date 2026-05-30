import numpy as np

TOOL_TAYLOR = {
    'HSS':     (0.125, 70),
    'Carbide': (0.25,  200),
    'Ceramic': (0.40,  500),
    'CBN':     (0.50,  800),
}

GRADE_MULTIPLIER = {
    'L': 1.20,
    'M': 1.00,
    'H': 0.75,
}

TOOL_UPGRADE = {
    'HSS':     'Carbide',
    'Carbide': 'Ceramic',
    'Ceramic': 'CBN',
    'CBN':     None,
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
    v_aggressive = min(v_base * 1.2, 500)   #Hard cap since no tool survives >500 m/min on HSS/Carbide
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
            'speed (m/min)':   round(v_aggressive, 2),
            'feed (mm/rev)':   round(feed_base * 1.2, 3),
            'depth (mm)':      round(depth_base * 1.2, 2),
            'tool_life (min)': taylor_tool_life(v_aggressive, n, C)
        }
    }
    return conditions