import numpy as np

def taylor_tool_life(v, n=0.25, C=200):
    """
    Taylor's extended tool life equation: v * T^n = C
    Solves for T (tool life in minutes) given cutting speed v (m/min)
    Default constants: n=0.25 (HSS tool), C=200 (mild steel)
    """
    T = (C / v) ** (1 / n)
    return round(T, 2)

def generate_cutting_conditions(v_base, feed_base, depth_base):
    """
    Generates 3 cutting condition sets from a base condition.
    Conservative: lower speed, longer tool life
    Balanced: base condition
    Aggressive: higher speed, shorter tool life
    """
    conditions = {
        'Conservative': {
            'speed (m/min)': round(v_base * 0.8, 2),
            'feed (mm/rev)': round(feed_base * 0.8, 3),
            'depth (mm)': round(depth_base * 0.8, 2),
            'tool_life (min)': taylor_tool_life(v_base * 0.8)
        },
        'Balanced': {
            'speed (m/min)': round(v_base, 2),
            'feed (mm/rev)': round(feed_base, 3),
            'depth (mm)': round(depth_base, 2),
            'tool_life (min)': taylor_tool_life(v_base)
        },
        'Aggressive': {
            'speed (m/min)': round(v_base * 1.2, 2),
            'feed (mm/rev)': round(feed_base * 1.2, 3),
            'depth (mm)': round(depth_base * 1.2, 2),
            'tool_life (min)': taylor_tool_life(v_base * 1.2)
        }
    }
    return conditions