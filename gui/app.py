import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys, os, tempfile, threading
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from utils.export_pdf import export_report
from modules.module1_material  import recommend_materials
from modules.module2_stress    import predict_risk
from modules.module3_machining import get_advisory
from data_generators.taylor_tool_life import (
    taylor_tool_life, get_taylor_constants,
    TOOL_DESCRIPTIONS, TOOL_UPGRADE, TOOL_TAYLOR
)
from data_generators.machine_specs import MACHINE_SPECS, GRADE_MACHINE_RECOMMENDATION

import requests as _req

GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

BG      = "#0a0a0a"
BG2     = "#111111"
BG3     = "#1a1a1a"
ACCENT  = "#ffffff"
ACCENT2 = "#cccccc"
SUCCESS = "#b0b0b0"
WARNING = "#888888"
DANGER  = "#555555"
TEXT    = "#e8e8e8"
TEXT2   = "#666666"
BORDER  = "#2a2a2a"

AI_BG      = "#0d1117"
AI_BORDER  = "#1e3a5f"
AI_TEXT    = "#c9d1d9"
AI_ACCENT  = "#388bfd"
AI_REC_BG  = "#0f1923"
AI_REC_FG  = "#58a6ff"
APPLY_BG   = "#0d2137"
APPLY_HOVER= "#1a3a5c"
APPLY_FG   = "#79c0ff"

FONT    = ("Segoe UI", 10)
FONT_B  = ("Segoe UI", 10, "bold")
FONT_H  = ("Segoe UI", 12, "bold")
FONT_T  = ("Segoe UI", 16, "bold")
FONT_S  = ("Segoe UI", 9)
FONT_SB = ("Segoe UI", 9, "bold")
MONO    = ("Consolas", 10)
FONT_M  = ("Consolas", 9)

_PRECISION = [4]
def _p(): return _PRECISION[0]
def _fmt(val, unit=""):
    p = _p(); s = f"{val:.{p}g}"
    return f"{s} {unit}".strip() if unit else s

RISK_COLORS = {
    "Safe":          "#888888",
    "Yield Risk":    "#aaaaaa",
    "Fatigue Risk":  "#aaaaaa",
    "Fracture Risk": "#666666",
    "Buckling Risk": "#666666",
}
RISK_DESCRIPTIONS = {
    "Safe":          "Component handles this load without risk of failure.",
    "Yield Risk":    "Stress exceeds yield strength — part will permanently deform.",
    "Fatigue Risk":  "Repeated loading at this stress level will cause cracks over time.",
    "Fracture Risk": "Stress near ultimate tensile strength — sudden fracture likely.",
    "Buckling Risk": "Compressive load exceeds critical threshold — column will buckle.",
}
RISK_SUGGESTIONS = {
    "Yield Risk":    [
        "Increase cross-section dimensions to reduce stress.",
        "Select a higher-yield material from Module 1.",
        "Redistribute loading to reduce peak stress concentration.",
    ],
    "Fatigue Risk":  [
        "Apply surface treatments (shot peening, case hardening) to improve fatigue resistance.",
        "Reduce cyclic load amplitude or introduce a rest period.",
        "Select a material with higher fatigue limit from Module 1.",
    ],
    "Fracture Risk": [
        "Reduce applied load immediately — fracture is imminent at this stress level.",
        "Select a higher-Su material from Module 1 results.",
        "Increase cross-section to lower stress below 0.85 x Su.",
    ],
    "Buckling Risk": [
        "Reduce column slenderness ratio — shorten unsupported length or increase section.",
        "Add lateral supports to reduce effective length.",
        "Use a higher-E material to increase critical buckling load.",
    ],
}

def fmt_time(minutes):
    if minutes <= 0: return "0 min"
    ms = minutes * 60000
    if ms < 1000: return f"{ms:.1f} ms"
    secs = minutes * 60
    if secs < 90: return f"{secs:.1f} sec"
    if minutes < 90: return f"{minutes:.1f} min"
    hours = minutes / 60
    if hours < 48: return f"{hours:.2f} hr"
    return f"{hours/24:.1f} days"

def fmt_stress_mpa(mpa):
    if abs(mpa) < 0.001: return f"{mpa*1e6:.2f} Pa"
    if abs(mpa) < 1.0:   return f"{mpa*1000:.2f} kPa"
    if abs(mpa) < 1000:  return f"{mpa:.2f} MPa"
    return f"{mpa/1000:.3f} GPa"

def fmt_force(n):
    if abs(n) < 1000: return f"{n:.1f} N"
    if abs(n) < 1e6:  return f"{n/1000:.2f} kN"
    return f"{n/1e6:.3f} MN"

UNIT_SYSTEMS = ["SI  (MPa / kg/m3)", "Imperial  (ksi / lb/ft3)"]

STRESS_UNITS_SI  = ["Pa", "kPa", "MPa", "GPa"]
STRESS_UNITS_IMP = ["psi", "ksi"]
STRESS_TO_MPa = {
    "Pa":1e-6,"kPa":1e-3,"MPa":1.0,"GPa":1e3,
    "psi":6.894757e-3,"ksi":6.894757,
}
MPa_TO_STRESS = {k:1.0/v for k,v in STRESS_TO_MPa.items()}

DENSITY_UNITS_SI  = ["kg/m\u00b3","g/cm\u00b3","g/m\u00b3"]
DENSITY_UNITS_IMP = ["lb/ft\u00b3","lb/in\u00b3"]
DENSITY_TO_KGM3 = {
    "kg/m\u00b3":1.0,"g/cm\u00b3":1000.0,"g/m\u00b3":0.001,
    "lb/ft\u00b3":16.0185,"lb/in\u00b3":27679.9,
}
KGM3_TO_DENSITY = {k:1.0/v for k,v in DENSITY_TO_KGM3.items()}

LENGTH_UNITS_SI  = ["m","cm","mm"]
LENGTH_UNITS_IMP = ["ft","in"]
LENGTH_TO_M  = {"m":1.0,"cm":0.01,"mm":0.001,"ft":0.3048,"in":0.0254}
M_TO_LENGTH  = {k:1.0/v for k,v in LENGTH_TO_M.items()}

FORCE_UNITS_SI  = ["N","kN","MN"]
FORCE_UNITS_IMP = ["lbf","kip"]
FORCE_TO_N  = {"N":1.0,"kN":1e3,"MN":1e6,"lbf":4.44822,"kip":4448.22}
N_TO_FORCE  = {k:1.0/v for k,v in FORCE_TO_N.items()}

TORQUE_UNITS = ["Nm","kNm","lbf.ft","lbf.in"]
TORQUE_TO_NM = {"Nm":1.0,"kNm":1000.0,"lbf.ft":1.35582,"lbf.in":0.112985}
NM_TO_TORQUE = {k:1.0/v for k,v in TORQUE_TO_NM.items()}

SPEED_UNITS   = ["m/min","ft/min","m/s"]
SPEED_TO_MMIN = {"m/min":1.0,"ft/min":0.3048,"m/s":60.0}
MMIN_TO_SPEED = {k:1.0/v for k,v in SPEED_TO_MMIN.items()}

FEED_UNITS    = ["mm/rev","in/rev","um/rev"]
FEED_TO_MMREV = {"mm/rev":1.0,"in/rev":25.4,"um/rev":0.001}
MMREV_TO_FEED = {k:1.0/v for k,v in FEED_TO_MMREV.items()}

RPM_UNITS    = ["rpm","rad/s"]
RPM_TO_RPM   = {"rpm":1.0,"rad/s":60.0/(2*3.14159265)}
RPM_FROM_RPM = {k:1.0/v for k,v in RPM_TO_RPM.items()}

TEMP_UNITS = ["K","C","F"]
def temp_to_K(val, unit):
    if unit=="K": return val
    if unit=="C": return val+273.15
    if unit=="F": return (val-32)*5/9+273.15
    return val

def _stress_label(u): return "ksi" if "ksi" in u else "MPa"
def _density_label(u): return "lb/ft3" if "lb" in u else "kg/m3"
def _to_mpa(v,u): return v*STRESS_TO_MPa["ksi" if "ksi" in u else "MPa"]
def _from_mpa(v,u): return v*MPa_TO_STRESS["ksi" if "ksi" in u else "MPa"]
def _to_kgm3(v,u): return v*DENSITY_TO_KGM3["lb/ft\u00b3" if "lb" in u else "kg/m\u00b3"]
def _from_kgm3(v,u): return v*KGM3_TO_DENSITY["lb/ft\u00b3" if "lb" in u else "kg/m\u00b3"]

RANGES_SI = {
    "m1_sy":  (0,    2500,  "Min Yield Strength"),
    "m1_ro":  (0,    25000, "Max Density"),
    "m1_a5":  (0,    100,   "Min Elongation (%)"),
    "sigma":  (0,    5000,  "Normal Stress"),
    "tau":    (0,    5000,  "Shear Stress"),
    "sy":     (1,    3000,  "Yield Strength Sy"),
    "su":     (1,    4000,  "UTS Su"),
    "sf":     (0.5,  10.0,  "Target Safety Factor"),
}

def stress_units_for(u): return STRESS_UNITS_IMP if "ksi" in u else STRESS_UNITS_SI
def density_units_for(u): return DENSITY_UNITS_IMP if "lb" in u else DENSITY_UNITS_SI
def length_units_for(u): return LENGTH_UNITS_IMP if "ft" in u else LENGTH_UNITS_SI
def force_units_for(u): return FORCE_UNITS_IMP if "lbf" in u else FORCE_UNITS_SI

def _make_stress_tooltip(field_key, unit_source):
    active_unit = unit_source._unit_var.get() if not isinstance(unit_source,str) else ("ksi" if "ksi" in unit_source else "MPa")
    from_mpa = MPa_TO_STRESS.get(active_unit,1.0)
    sl = active_unit
    def cvt(v): return v*from_mpa
    lo_si,hi_si,label = RANGES_SI[field_key]
    lo = cvt(lo_si) if lo_si>0 else 0; hi = cvt(hi_si)
    base = {
        "sigma": (f"Normal stress from bending or axial load.\n  sigma = M*c/I or F/A\n  Typical: {cvt(50):.3g}\u2013{cvt(600):.3g} {sl}\n  Valid: {lo:.3g}\u2013{hi:.3g} {sl}"),
        "tau":   (f"Shear stress from torsion or transverse shear.\n  tau = T*r/J (torsion)\n  Typical: {cvt(10):.3g}\u2013{cvt(300):.3g} {sl}\n  Valid: {lo:.3g}\u2013{hi:.3g} {sl}"),
        "sy":    (f"Yield Strength.\n  Auto-filled from Module 1.\n  Mild steel ~{cvt(250):.3g} | 4140 ~{cvt(655):.3g} | Ti ~{cvt(880):.3g} {sl}\n  Valid: {lo:.3g}\u2013{hi:.3g} {sl}"),
        "su":    (f"Ultimate Tensile Strength.\n  Auto-filled as 1.3 x Sy.\n  Valid: {lo:.3g}\u2013{hi:.3g} {sl}"),
        "m1_sy": (f"Min Yield Strength needed.\n  Frame: {cvt(200):.3g}\u2013{cvt(350):.3g} {sl} | Shaft: {cvt(500):.3g}\u2013{cvt(800):.3g} {sl}\n  Valid: {lo:.3g}\u2013{hi:.3g} {sl}"),
    }
    return base.get(field_key, f"Valid: {lo:.3g}\u2013{hi:.3g} {sl}")

def _make_density_tooltip(unit_source):
    active_unit = unit_source._unit_var.get() if not isinstance(unit_source,str) else ("lb/ft\u00b3" if "lb" in unit_source else "kg/m\u00b3")
    from_kgm3 = KGM3_TO_DENSITY.get(active_unit,1.0)
    dl = active_unit
    def cvt(v): return v*from_kgm3
    lo_si,hi_si,_ = RANGES_SI["m1_ro"]
    return (f"Max density allowed.\n  Steel: ~{cvt(7850):.4g} {dl}\n  Al: ~{cvt(2700):.4g} {dl}\n  Ti: ~{cvt(4500):.4g} {dl}\n  Valid: {cvt(lo_si):.3g}\u2013{cvt(hi_si):.3g} {dl}")

def styled_label(parent, text, font=FONT, fg=TEXT, bg=None, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg or parent["bg"], **kw)

def styled_entry(parent, width=18):
    return tk.Entry(parent, width=width, bg=BG3, fg=TEXT,
                    insertbackground=ACCENT, relief="flat", font=FONT,
                    highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT2)

class UnitEntry(tk.Frame):
    def __init__(self, parent, units, default_unit, to_base, from_base, entry_width=10, **kw):
        super().__init__(parent, bg=BG2, **kw)
        self._units=units; self._to_base=to_base; self._from_base=from_base
        self._unit_var=tk.StringVar(value=default_unit); self._prev_unit=default_unit
        self.entry=tk.Entry(self, width=entry_width, bg=BG3, fg=TEXT,
                            insertbackground=ACCENT, relief="flat", font=FONT,
                            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT2)
        self.entry.pack(side="left", fill="x", expand=True)
        self._unit_btn=ttk.Combobox(self, textvariable=self._unit_var,
                                    values=units, width=6, font=("Segoe UI",9), state="readonly")
        self._unit_btn.pack(side="left", padx=(3,0))
        self._unit_btn.bind("<<ComboboxSelected>>", self._on_unit_change)

    def _on_unit_change(self, event=None):
        new_unit=self._unit_var.get(); raw=self.entry.get().strip()
        if raw:
            try:
                val=float(raw)
                base_val=val*self._to_base.get(self._prev_unit,1.0)
                new_val=base_val*self._from_base.get(new_unit,1.0)
                self.entry.delete(0,tk.END); self.entry.insert(0,f"{new_val:.6g}")
            except ValueError: pass
        self._prev_unit=new_unit

    def get(self): return self.entry.get()
    def get_base(self):
        raw=self.entry.get().strip()
        if not raw: raise ValueError("Empty field")
        return float(raw)*self._to_base.get(self._unit_var.get(),1.0)
    def delete(self,a,b): self.entry.delete(a,b)
    def insert(self,idx,val): self.entry.insert(idx,val)
    def set_from_base(self, base_val):
        unit=self._unit_var.get(); disp=base_val*self._from_base.get(unit,1.0)
        self.entry.delete(0,tk.END); self.entry.insert(0,f"{disp:.6g}")
    def set_units(self, units, default):
        self._units=units; self._unit_btn["values"]=units
        new_unit=default if default in units else units[0]
        raw=self.entry.get().strip()
        if raw:
            try:
                val=float(raw)
                base_val=val*self._to_base.get(self._prev_unit,1.0)
                new_val=base_val*self._from_base.get(new_unit,1.0)
                self.entry.delete(0,tk.END); self.entry.insert(0,f"{new_val:.6g}")
            except (ValueError,TypeError): pass
        self._unit_var.set(new_unit); self._prev_unit=new_unit
    def config(self, **kw):
        if "highlightbackground" in kw or "highlightcolor" in kw: self.entry.config(**kw)
        else: super().config(**kw)
    def bind(self, sequence, func, add=None): self.entry.bind(sequence, func, add)
    def focus_set(self): self.entry.focus_set()

def make_stress_entry(parent, unit_sys, entry_width=10):
    units=stress_units_for(unit_sys); default="ksi" if "ksi" in unit_sys else "MPa"
    return UnitEntry(parent,units,default,STRESS_TO_MPa,MPa_TO_STRESS,entry_width)

def make_density_entry(parent, unit_sys, entry_width=10):
    units=density_units_for(unit_sys); default="lb/ft\u00b3" if "lb" in unit_sys else "kg/m\u00b3"
    return UnitEntry(parent,units,default,DENSITY_TO_KGM3,KGM3_TO_DENSITY,entry_width)

def make_length_entry(parent, unit_sys, entry_width=10):
    units=length_units_for(unit_sys); default="ft" if "ft" in unit_sys else "m"
    return UnitEntry(parent,units,default,LENGTH_TO_M,M_TO_LENGTH,entry_width)

def make_force_entry(parent, unit_sys, entry_width=10):
    units=force_units_for(unit_sys); default="kip" if "lbf" in unit_sys else "N"
    return UnitEntry(parent,units,default,FORCE_TO_N,N_TO_FORCE,entry_width)

def make_torque_entry(parent, entry_width=10):
    return UnitEntry(parent,TORQUE_UNITS,"Nm",TORQUE_TO_NM,NM_TO_TORQUE,entry_width)

def make_speed_entry(parent, entry_width=10):
    return UnitEntry(parent,SPEED_UNITS,"m/min",SPEED_TO_MMIN,MMIN_TO_SPEED,entry_width)

def make_feed_entry(parent, entry_width=10):
    return UnitEntry(parent,FEED_UNITS,"mm/rev",FEED_TO_MMREV,MMREV_TO_FEED,entry_width)

def make_rpm_entry(parent, entry_width=10):
    return UnitEntry(parent,RPM_UNITS,"rpm",RPM_TO_RPM,RPM_FROM_RPM,entry_width)

def styled_combo(parent, values, width=16):
    cb=ttk.Combobox(parent,values=values,width=width,font=FONT,state="readonly"); cb.current(0)
    return cb

def card(parent, title, pady=12, padx=16):
    wrapper=tk.Frame(parent,bg=BG); wrapper.pack(fill="x",padx=12,pady=(0,10))
    tk.Frame(wrapper,bg=ACCENT2,width=2).pack(side="left",fill="y")
    inner=tk.Frame(wrapper,bg=BG2); inner.pack(side="left",fill="x",expand=True)
    tk.Label(inner,text=title,font=FONT_H,fg=TEXT,bg=BG2,anchor="w").pack(fill="x",padx=padx,pady=(10,4))
    tk.Frame(inner,bg=BORDER,height=1).pack(fill="x",padx=padx)
    body=tk.Frame(inner,bg=BG2); body.pack(fill="x",padx=padx,pady=pady)
    return body

def field_row(parent, label, widget, row, col_offset=0):
    tk.Label(parent,text=label,font=FONT,fg=TEXT2,bg=BG2).grid(
        row=row,column=col_offset,sticky="w",padx=(0,12),pady=5)
    widget.grid(row=row,column=col_offset+1,sticky="ew",pady=5)

def action_btn(parent, text, cmd, color=None):
    btn=tk.Button(parent,text=text,command=cmd,bg=BG3,fg=TEXT,font=FONT_B,
                  relief="flat",cursor="hand2",padx=20,pady=8,
                  highlightthickness=1,highlightbackground=ACCENT2,
                  activebackground=BORDER,activeforeground=TEXT)
    btn.bind("<Enter>",lambda e:btn.config(bg=BORDER))
    btn.bind("<Leave>",lambda e:btn.config(bg=BG3))
    return btn

def divider(parent):
    tk.Frame(parent,bg=BORDER,height=1).pack(fill="x",pady=6)

def bind_arrow_keys(entries):
    for i,e in enumerate(entries):
        if i>0: e.bind("<Up>",lambda ev,p=entries[i-1]:p.focus_set())
        if i<len(entries)-1: e.bind("<Down>",lambda ev,n=entries[i+1]:n.focus_set())

def warning_box(parent, warnings, suggestions):
    if not warnings and not suggestions: return
    WBG="#0f0f0f"
    box=tk.Frame(parent,bg=WBG,highlightthickness=1,highlightbackground="#2a2a2a")
    box.pack(fill="x",pady=(8,0))
    inner=tk.Frame(box,bg=WBG); inner.pack(fill="x",padx=12,pady=8)
    for w in warnings:
        tk.Label(inner,text=f"!  {w}",font=FONT_S,fg=TEXT2,bg=WBG,
                 anchor="w",wraplength=800,justify="left").pack(fill="x",pady=(0,3))
    if suggestions:
        tk.Frame(inner,bg="#2a2a2a",height=1).pack(fill="x",pady=(4,4))
        tk.Label(inner,text="Actions:",font=FONT_SB,fg=TEXT2,bg=WBG,anchor="w").pack(fill="x")
        for s in suggestions:
            tk.Label(inner,text=f"  ->  {s}",font=FONT_S,fg=TEXT,bg=WBG,
                     anchor="w",wraplength=800,justify="left").pack(fill="x",pady=(2,0))

class ToolTip:
    def __init__(self, widget, text_or_fn):
        self.widget=widget; self._text_or_fn=text_or_fn; self.tip=None
        widget.bind("<Enter>",self.show); widget.bind("<Leave>",self.hide)
    @property
    def text(self):
        t=self._text_or_fn; return t() if callable(t) else t
    def show(self, event=None):
        if self.tip: return
        x=self.widget.winfo_rootx()+self.widget.winfo_width()+8
        y=self.widget.winfo_rooty()
        self.tip=tk.Toplevel(self.widget); self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        outer=tk.Frame(self.tip,bg=BORDER,padx=1,pady=1); outer.pack()
        inner=tk.Frame(outer,bg=BG3); inner.pack()
        tk.Frame(inner,bg=ACCENT2,height=1).pack(fill="x")
        tk.Label(inner,text=self.text,font=FONT_S,bg=BG3,fg=TEXT,
                 padx=12,pady=8,justify="left",wraplength=340).pack()
    def hide(self, event=None):
        if self.tip: self.tip.destroy(); self.tip=None

# ── Shaft torsion computation ──────────────────────────────────────────────
def compute_shaft_torsion(T_Nm, d_m, L_m=None, P_N=None):
    tau = 16*T_Nm / (np.pi * d_m**3)
    sigma = 0.0
    if L_m and P_N and L_m > 0 and P_N > 0:
        M = P_N * L_m / 4
        sigma = 32*M / (np.pi * d_m**3)
    return sigma/1e6, tau/1e6

# ── M1 required-Sy computation ─────────────────────────────────────────────
def compute_required_sy(member, load_type, load_val, span_m, dim1_m, dim2_m, section, sf):
    if member in ("beam", "plate"):
        L=span_m; P=load_val
        if load_type=="Point Load":
            M_max=P*L/4; V_max=P/2
        else:
            M_max=P*L**2/8; V_max=P*L/2
        if section=="Rectangle":
            b,h=dim1_m,dim2_m; c=h/2; I=b*h**3/12; A=b*h; tau_max=1.5*V_max/A
        else:
            d=dim1_m; c=d/2; I=np.pi*d**4/64; A=np.pi*d**2/4; tau_max=(4/3)*V_max/A
        sigma=M_max*c/I
    elif member=="column":
        if section=="Rectangle": A=dim1_m*dim2_m
        else: A=np.pi*dim1_m**2/4
        sigma=load_val/A; tau_max=0.0
    elif member=="shaft":
        T=load_val; d=dim1_m
        tau_max=16*T/(np.pi*d**3); sigma=0.0
    else:
        sigma=0.0; tau_max=0.0
    sigma_vm=np.sqrt(sigma**2+3*tau_max**2)
    return sigma/1e6, tau_max/1e6, sigma_vm/1e6, sigma_vm/1e6*sf

# ── M3 auto-compute ────────────────────────────────────────────────────────
def compute_suggested_m3_inputs(m1_results, m2_result=None, m2_inputs=None):
    if not m1_results: return None
    top=m1_results[0]; sy_mpa=top["Yield Strength (MPa)"]
    if sy_mpa<400: grade="L"
    elif sy_mpa<800: grade="M"
    else: grade="H"
    n_taylor=0.25; C_taylor=200.0
    from data_generators.taylor_tool_life import GRADE_MULTIPLIER
    gm=GRADE_MULTIPLIER.get(grade,1.0); C_eff=C_taylor*gm
    speed_mmin=round(C_eff/(60.0**n_taylor),1); speed_mmin=max(10.0,min(speed_mmin,300.0))
    D_mm=50.0
    if m2_inputs:
        try:
            sigma_mpa=m2_inputs.get("sigma_mpa",200.0); sf_target=m2_inputs.get("sf_target",2.0)
            if sigma_mpa>0 and sy_mpa>0:
                D_mm=max(20.0,min(150.0,50.0*(sy_mpa/(sigma_mpa*sf_target+1))**0.3))
        except Exception: D_mm=50.0
    rpm=round((speed_mmin*1000)/(3.14159*D_mm)); rpm=max(100,min(5000,rpm))
    feed_map={"L":0.25,"M":0.15,"H":0.10}; depth_map={"L":3.0,"M":2.0,"H":1.0}
    feed_mmrev=feed_map[grade]; depth_mm=depth_map[grade]
    kc_map={"L":1200,"M":1800,"H":2500}; kc=kc_map[grade]
    Fc_N=kc*depth_mm*feed_mmrev; torque_nm=round(Fc_N*(D_mm/2)/1000,1)
    torque_nm=max(1.0,min(200.0,torque_nm))
    return {"grade":grade,"speed_mmin":speed_mmin,"rpm":rpm,"torque_nm":torque_nm,
            "feed_mmrev":feed_mmrev,"depth_mm":depth_mm,"D_mm":D_mm}

# ── Suggestion Engine ──────────────────────────────────────────────────────
def _compute_tool_life(speed, feed, depth, n, C, tool_mat, grade):
    from data_generators.taylor_tool_life import GRADE_MULTIPLIER
    gm=GRADE_MULTIPLIER.get(grade,1.0); C_eff=C*gm
    if speed<=0: return float("inf")
    return (C_eff/speed)**(1/n)

def _smart_fallback_suggestion(ctx):
    t=ctx.get("type","")
    if t=="machining":
        tl=ctx["tool_life"]; tool=ctx["tool_mat"]; spd=ctx["speed"]
        feed=ctx["feed"]; depth=ctx["depth"]; grade=ctx["grade"]
        n=ctx["n"]; C=ctx["C"]; changes=[]; text_parts=[]; recovery=""
        if tl<15:
            new_spd=round(spd*0.80,1)
            new_tl_spd=_compute_tool_life(new_spd,feed,depth,n,C,tool,grade)
            gain_spd=new_tl_spd-tl; new_feed=round(feed*0.80,3)
            upgrade_tool=TOOL_UPGRADE.get(tool); upgrade_txt=""
            if upgrade_tool and upgrade_tool in TOOL_TAYLOR:
                n2,C2=TOOL_TAYLOR[upgrade_tool]
                new_tl_up=_compute_tool_life(spd,feed,depth,n2,C2,tool,grade)
                upgrade_txt=f"Upgrading to {upgrade_tool} gives {fmt_time(new_tl_up)} (+{fmt_time(new_tl_up-tl)})."
            text_parts.append(
                f"Tool life critically short ({fmt_time(tl)}). "
                f"Reducing speed {spd} -> {new_spd} m/min adds {fmt_time(gain_spd)} "
                f"(new: {fmt_time(new_tl_spd)}). Reducing feed {feed} -> {new_feed} mm/rev also helps. "+upgrade_txt)
            changes=[
                {"field_key":"m3_speed","label":f"Speed: {spd} -> {new_spd} m/min","new_val":str(new_spd)},
                {"field_key":"m3_feed","label":f"Feed: {feed} -> {new_feed} mm/rev","new_val":str(new_feed)},
            ]
            pct=(gain_spd/tl*100) if tl>0 else 0
            recovery=f"Speed reduction -> {fmt_time(tl)} -> {fmt_time(new_tl_spd)} (+{pct:.0f}%)"
        elif tl>10000:
            new_spd=round(spd*1.30,1)
            new_tl=_compute_tool_life(new_spd,feed,depth,n,C,tool,grade)
            prod=(new_spd/spd-1)*100
            text_parts.append(f"Tool life too long ({fmt_time(tl)}) — too conservative. Increase speed {spd} -> {new_spd} m/min: {fmt_time(new_tl)} life (+{prod:.0f}% MRR).")
            changes=[{"field_key":"m3_speed","label":f"Speed: {spd} -> {new_spd} m/min","new_val":str(new_spd)}]
            recovery=f"Speed increase -> {fmt_time(new_tl)} tool life, +{prod:.0f}% MRR."
        elif tl>1000:
            new_spd=round(spd*1.15,1)
            new_tl=_compute_tool_life(new_spd,feed,depth,n,C,tool,grade)
            text_parts.append(f"Tool life good ({fmt_time(tl)}) but room to push. Try {new_spd} m/min for {fmt_time(new_tl)} — faster cycle.")
            changes=[{"field_key":"m3_speed","label":f"Speed: {spd} -> {new_spd} m/min","new_val":str(new_spd)}]
            recovery=f"+15% speed -> {fmt_time(new_tl)} tool life, faster cycle."
        else:
            text_parts.append(f"Balanced setup. Tool life {fmt_time(tl)} optimal. Speed {spd} m/min well-calibrated for {tool} on grade {grade}.")
            recovery="No changes needed."
        return {"text":text_parts[0] if text_parts else "Setup looks reasonable.","changes":changes,"recovery_text":recovery}

    if t=="stress":
        risk=ctx["risk"]; sf=ctx["sf"]; vm=ctx["vm_mpa"]
        sy=ctx["sy_mpa"]; sf_target=ctx.get("sf_target",2.0); changes=[]; recovery=""
        if risk=="Safe" and sf>=3:
            saving=(1-sf_target/sf)*100
            text=f"Component over-designed (SF={sf:.2f}). Cross-section could shrink ~{saving:.0f}% and still meet SF {sf_target:.1f}."
            recovery=f"Reducing section by {saving:.0f}% -> SF ~ {sf_target:.1f}."
        elif risk=="Fatigue Risk":
            limit=sy*0.45; needed=vm/0.45
            text=f"sigma_vm = {fmt_stress_mpa(vm)} is {vm/sy*100:.1f}% of Sy. Keep sigma_vm < 0.45xSy = {fmt_stress_mpa(limit)}. Need Sy >= {fmt_stress_mpa(needed)}."
            recovery=f"Sy >= {fmt_stress_mpa(needed)} keeps fatigue ratio below 0.45."
        elif risk in ("Yield Risk","Fracture Risk"):
            pct=(vm/sy-1)*100; new_sy=vm*sf_target
            suggested_sf=min(round(sf_target+1.0,1),5.0)
            text=f"Stress exceeds yield by {fmt_stress_mpa(vm-sy)}. Need section +{pct:.0f}% or Sy >= {fmt_stress_mpa(new_sy)}. Suggest increasing SF target to {suggested_sf:.1f}."
            recovery=f"Section +{pct:.0f}% OR Sy >= {fmt_stress_mpa(new_sy)} -> SF={sf_target:.1f}."
            changes=[{"field_key":"m2_sf_target","label":f"SF Target -> {suggested_sf:.1f}","new_val":str(suggested_sf)}]
        elif risk=="Buckling Risk":
            text="Buckling risk. Reduce slenderness or add lateral bracing. Increase SF target to 3.0."
            recovery="Midpoint brace halves effective length -> 4x buckling load."
            changes=[{"field_key":"m2_sf_target","label":"SF Target -> 3.0","new_val":"3.0"}]
        else:
            text=f"Component safe (SF={sf:.2f}). No immediate action."; recovery="No changes needed."
        return {"text":text,"changes":changes,"recovery_text":recovery}

    if t=="material":
        fc=ctx["failure_concern"]; sy=ctx["sy"]; mat=ctx["material"]
        if "Fracture" in fc:
            text=f"Fracture-prone material (Sy={fmt_stress_mpa(sy)}). Apply minimum SF=3.0. Avoid sharp corners."
            recovery="SF=3.0 + generous fillets -> fracture risk controlled."
            changes=[{"field_key":"m2_sf_target","label":"SF Target -> 3.0","new_val":"3.0"}]
        elif "Fatigue" in fc:
            text=f"Fatigue-prone material. Keep sigma_vm < 0.45xSy = {fmt_stress_mpa(sy*0.45)}. Surface finish Ra < 0.8 um."
            recovery=f"sigma_vm < {fmt_stress_mpa(sy*0.45)} -> infinite fatigue life estimate."
            changes=[{"field_key":"m2_sf_target","label":"SF Target -> 2.5","new_val":"2.5"}]
        else:
            text=f"{mat} suitable. Verify Sy={fmt_stress_mpa(sy)} meets SF."; recovery="Review SF."; changes=[]
        return {"text":text,"changes":changes,"recovery_text":recovery}

    return {"text":"Review design inputs against application requirements.","changes":[],"recovery_text":""}

def _groq_suggest(prompt, api_key, callback):
    def _run():
        try:
            resp=_req.post(GROQ_URL,
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                json={"model":GROQ_MODEL,"messages":[{"role":"user","content":prompt}],
                      "max_tokens":250,"temperature":0.3},timeout=15)
            if resp.status_code==200:
                text=resp.json()["choices"][0]["message"]["content"].strip()
                callback(text if text else None)
            else: callback(None)
        except Exception: callback(None)
    threading.Thread(target=_run,daemon=True).start()

def get_ai_suggestion(ctx, api_key, callback):
    fallback=_smart_fallback_suggestion(ctx); t=ctx.get("type","")
    if not api_key or not api_key.strip() or api_key.strip()=="APIKEYHERE":
        callback(fallback); return
    if t=="stress":
        prompt=(f"Mechanical engineering advisor. A {ctx.get('member','component')} classified as '{ctx['risk']}' with "
                f"Von Mises {ctx['vm_mpa']:.1f} MPa, Sy {ctx['sy_mpa']:.1f} MPa, SF {ctx['sf']:.3f} (target {ctx.get('sf_target',2.0):.1f}). "
                f"ONE specific actionable recommendation, 2-3 sentences, numbers. No preamble.")
    elif t=="machining":
        prompt=(f"Machining process advisor. Grade: {ctx['grade']}, Tool: {ctx['tool_mat']}, "
                f"speed {ctx['speed']} m/min, feed {ctx['feed']} mm/rev, depth {ctx['depth']} mm, tool life {fmt_time(ctx['tool_life'])}. "
                f"ONE specific improvement, 2-3 sentences, numbers. No preamble.")
    elif t=="material":
        prompt=(f"Materials selection advisor. Top: {ctx['material']} (Sy={ctx['sy']} MPa, density={ctx['density']} kg/m3, "
                f"elong={ctx['elongation']}%, concern={ctx['failure_concern']}). ONE design consideration, 2-3 sentences. No preamble.")
    else: callback(fallback); return
    def _cb(text):
        if text: result=dict(fallback); result["text"]=text; callback(result)
        else: callback(fallback)
    _groq_suggest(prompt,api_key.strip(),_cb)

class SmartSuggestionCard(tk.Frame):
    def __init__(self, parent, app_ref, **kw):
        super().__init__(parent,bg=AI_BG,highlightthickness=1,highlightbackground=AI_BORDER,**kw)
        self._app=app_ref; self._show_idle()

    def _show_idle(self):
        tk.Label(self,text="Run module to generate suggestion.",font=FONT_S,fg=AI_REC_FG,bg=AI_BG,anchor="w",wraplength=860).pack(fill="x",padx=14,pady=10)

    def _hdr(self):
        for w in self.winfo_children(): w.destroy()
        hdr=tk.Frame(self,bg=AI_BG); hdr.pack(fill="x",padx=14,pady=(10,0))
        tk.Label(hdr,text="\u25cf",font=("Segoe UI",8),fg=AI_ACCENT,bg=AI_BG).pack(side="left")
        tk.Label(hdr,text="  AI Suggestion",font=FONT_SB,fg=AI_ACCENT,bg=AI_BG).pack(side="left")
        tk.Frame(self,bg=AI_BORDER,height=1).pack(fill="x",padx=14,pady=(6,0))

    def show_loading(self):
        self._hdr()
        tk.Label(self,text="Generating suggestion\u2026",font=FONT_S,fg=AI_REC_FG,bg=AI_BG,anchor="w",wraplength=860).pack(fill="x",padx=14,pady=(6,10))

    def show_result(self, result):
        self._hdr()
        text=result.get("text",""); changes=result.get("changes",[]); recovery=result.get("recovery_text","")
        tk.Label(self,text=text,font=FONT_S,fg=AI_TEXT,bg=AI_BG,wraplength=900,justify="left",anchor="w").pack(fill="x",padx=14,pady=(8,6))
        if recovery and recovery not in ("No changes needed.",""):
            rec_f=tk.Frame(self,bg=AI_REC_BG,highlightthickness=1,highlightbackground=AI_BORDER)
            rec_f.pack(fill="x",padx=14,pady=(0,8))
            tk.Label(rec_f,text=f"  \u2191  {recovery}",font=FONT_S,fg=AI_REC_FG,bg=AI_REC_BG,anchor="w",wraplength=900,justify="left").pack(fill="x",padx=10,pady=6)
        if changes:
            tk.Frame(self,bg=AI_BORDER,height=1).pack(fill="x",padx=14,pady=(0,6))
            btn_row=tk.Frame(self,bg=AI_BG); btn_row.pack(fill="x",padx=14,pady=(0,10))
            tk.Label(btn_row,text="Apply:",font=FONT_SB,fg=AI_REC_FG,bg=AI_BG).pack(side="left",padx=(0,10))
            for ch in changes:
                lbl=ch["label"]; new_val=ch["new_val"]; fkey=ch["field_key"]
                btn=tk.Button(btn_row,text=f"\u2197  {lbl}",font=FONT_SB,fg=APPLY_FG,bg=APPLY_BG,relief="flat",cursor="hand2",
                              padx=14,pady=5,highlightthickness=1,highlightbackground=AI_BORDER,
                              activebackground=APPLY_HOVER,activeforeground=APPLY_FG,
                              command=lambda f=fkey,v=new_val:self._apply(f,v))
                btn.bind("<Enter>",lambda e,b=btn:b.config(bg=APPLY_HOVER))
                btn.bind("<Leave>",lambda e,b=btn:b.config(bg=APPLY_BG))
                btn.pack(side="left",padx=(0,8))
        else:
            tk.Frame(self,bg=AI_BG,height=6).pack()

    def _apply(self, field_key, new_val):
        self._app._apply_suggestion_change(field_key,new_val)

def draw_mohrs_circle(parent, sigma, tau, sy, su):
    R=np.sqrt((sigma/2)**2+tau**2); center=sigma/2; s1,s2=center+R,center-R
    mpa=lambda v:v/1e6
    circle_extent=max(abs(center)+R*1.5,R*2.0)*1.3
    if R>0 and circle_extent<sy*0.05: scale=max(circle_extent*4.0,R*6.0)
    else: scale=max(circle_extent,sy*0.12)
    scale=max(scale,1e6)
    fig=Figure(figsize=(8,5),dpi=96,facecolor=BG2)
    ax=fig.add_subplot(111,facecolor=BG3,aspect="equal")
    fig.subplots_adjust(left=0.09,right=0.68,top=0.92,bottom=0.13)
    ax.grid(True,color=BORDER,linewidth=0.8,zorder=0)
    theta=np.linspace(0,2*np.pi,500)
    ax.plot(mpa(center+R*np.cos(theta)),mpa(R*np.sin(theta)),color=TEXT,linewidth=1.4,zorder=3)
    ax.axhline(0,color=TEXT2,linewidth=0.6,alpha=0.4); ax.axvline(0,color=TEXT2,linewidth=0.6,alpha=0.4)
    ax.axvline(mpa(sy),color="#aaaaaa",linewidth=1.2,linestyle="--",zorder=2,alpha=0.85)
    ax.axvline(mpa(su),color="#666666",linewidth=1.2,linestyle="--",zorder=2,alpha=0.85)
    ax.plot([mpa(center),mpa(sigma)],[0,mpa(tau)],color=TEXT2,linewidth=0.8,linestyle=":",alpha=0.5)
    from matplotlib.lines import Line2D
    p_a, =ax.plot(mpa(sigma),mpa(tau),"o",color="#e0e0e0",markersize=7,zorder=5)
    p_c, =ax.plot(mpa(center),0,"s",color=TEXT,markersize=5,zorder=5)
    p_s1,=ax.plot(mpa(s1),0,"^",color="#aaaaaa",markersize=6,zorder=5)
    p_s2,=ax.plot(mpa(s2),0,"v",color="#aaaaaa",markersize=6,zorder=5)
    p_tm,=ax.plot(mpa(center),mpa(R),"D",color=ACCENT2,markersize=5,zorder=5)
    prec=4
    ax.legend([p_a,p_c,p_s1,p_s2,p_tm,
               Line2D([0],[0],color="#aaaaaa",linewidth=1.2,linestyle="--"),
               Line2D([0],[0],color="#666666",linewidth=1.2,linestyle="--")],
              [f"A ({mpa(sigma):.{prec}g}, {mpa(tau):.{prec}g}) MPa",
               f"Centre = {mpa(center):.{prec}g} MPa",f"s1 = {mpa(s1):.{prec}g} MPa",
               f"s2 = {mpa(s2):.{prec}g} MPa",f"t_max = {mpa(R):.{prec}g} MPa",
               f"Sy = {mpa(sy):.0f} MPa",f"Su = {mpa(su):.0f} MPa"],
              loc="upper left",bbox_to_anchor=(1.02,1.0),fontsize=8,
              facecolor=BG2,edgecolor=BORDER,labelcolor=TEXT,framealpha=1.0,
              handlelength=1.6,handleheight=1.0,handletextpad=0.6,borderpad=0.6,labelspacing=0.45)
    lim=mpa(scale); ax.set_xlim(-lim,lim); ax.set_ylim(-lim*0.65,lim*0.65)
    ax.set_xlabel("Normal Stress (MPa)",color=TEXT2,fontsize=9)
    ax.set_ylabel("Shear Stress (MPa)",color=TEXT2,fontsize=9)
    ax.set_title("Mohr's Circle",color=TEXT,fontsize=11,fontweight="bold",pad=10)
    ax.tick_params(colors=TEXT2,labelsize=8)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    canvas=FigureCanvasTkAgg(fig,master=parent)
    canvas.draw(); canvas.get_tk_widget().pack(fill="x",pady=(4,0))
    return canvas

def render_mohrs_circle_to_png(sigma, tau, sy, su, path):
    R=np.sqrt((sigma/2)**2+tau**2); center=sigma/2; s1,s2=center+R,center-R
    scale=max(abs(center)+R*1.5,R*2.0)*1.3; scale=max(scale,1e6); mpa=lambda v:v/1e6
    fig,ax=plt.subplots(figsize=(8,5),facecolor="white")
    ax.set_facecolor("#f8f9fa"); ax.set_aspect("equal")
    fig.subplots_adjust(left=0.09,right=0.68,top=0.92,bottom=0.13)
    theta=np.linspace(0,2*np.pi,500)
    ax.grid(True,color="#dee2e6",linewidth=0.8,zorder=0)
    ax.plot(mpa(center+R*np.cos(theta)),mpa(R*np.sin(theta)),color="#222222",linewidth=1.6,zorder=3)
    ax.axhline(0,color="#6c757d",linewidth=0.6,alpha=0.5); ax.axvline(0,color="#6c757d",linewidth=0.6,alpha=0.5)
    ax.axvline(mpa(sy),color="#555555",linewidth=1.2,linestyle="--",alpha=0.9,label=f"Sy = {mpa(sy):.0f} MPa")
    ax.axvline(mpa(su),color="#222222",linewidth=1.2,linestyle="--",alpha=0.9,label=f"Su = {mpa(su):.0f} MPa")
    ax.plot(mpa(sigma),mpa(tau),"o",color="#111111",markersize=7,zorder=5,label=f"A ({mpa(sigma):.1f}, {mpa(tau):.1f}) MPa")
    ax.plot(mpa(center),0,"s",color="#333333",markersize=5,zorder=5,label=f"Centre = {mpa(center):.1f} MPa")
    ax.plot(mpa(s1),0,"^",color="#555555",markersize=6,zorder=5,label=f"s1 = {mpa(s1):.1f} MPa")
    ax.plot(mpa(s2),0,"v",color="#555555",markersize=6,zorder=5,label=f"s2 = {mpa(s2):.1f} MPa")
    ax.plot(mpa(center),mpa(R),"D",color="#777777",markersize=5,zorder=5,label=f"t_max = {mpa(R):.1f} MPa")
    lim=mpa(scale); ax.set_xlim(-lim,lim); ax.set_ylim(-lim*0.65,lim*0.65)
    ax.set_xlabel("Normal Stress (MPa)",fontsize=9); ax.set_ylabel("Shear Stress (MPa)",fontsize=9)
    ax.set_title("Mohr's Circle",fontsize=11,fontweight="bold")
    ax.legend(loc="upper left",bbox_to_anchor=(1.02,1.0),fontsize=8,framealpha=1.0)
    fig.savefig(path,dpi=120,bbox_inches="tight",facecolor="white"); plt.close(fig)

def draw_tool_life_curve(parent, v_base, n, C):
    for w in parent.winfo_children(): w.destroy()
    speeds=np.linspace(max(1,v_base*0.3),v_base*2.0,300)
    lives=np.clip([(C/v)**(1/n) for v in speeds],0,10000)
    fig=Figure(figsize=(7,3.2),dpi=96,facecolor=BG2)
    ax=fig.add_subplot(111,facecolor=BG3)
    fig.subplots_adjust(left=0.13,right=0.97,top=0.88,bottom=0.18)
    ax.plot(speeds,lives,color=ACCENT2,linewidth=1.6,zorder=3)
    mc={"Conservative":"#cccccc","Balanced":"#999999","Aggressive":"#555555"}
    for label,fac in [("Conservative",0.8),("Balanced",1.0),("Aggressive",1.2)]:
        v_pt=v_base*fac; t_pt=min((C/v_pt)**(1/n),10000)
        ax.axvline(v_pt,color=mc[label],linewidth=1.0,linestyle="--",alpha=0.85,zorder=2)
        ax.plot(v_pt,t_pt,"o",color=mc[label],markersize=6,zorder=4,label=f"{label}: {fmt_time(t_pt)}")
    ax.set_title("Tool Life vs Cutting Speed",color=TEXT,fontsize=9,fontweight="bold",pad=8)
    ax.set_xlabel("Cutting Speed (m/min)",color=TEXT2,fontsize=9)
    ax.set_ylabel("Tool Life (min)",color=TEXT2,fontsize=9)
    ax.tick_params(colors=TEXT2,labelsize=8); ax.grid(True,color=BORDER,linewidth=0.7,alpha=1.0)
    ax.legend(fontsize=8,facecolor=BG2,edgecolor=BORDER,labelcolor=TEXT,framealpha=1.0)
    for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    canvas=FigureCanvasTkAgg(fig,master=parent)
    canvas.draw(); canvas.get_tk_widget().pack(fill="x",pady=(4,0))
    return canvas

def render_tool_life_curve_to_png(v_base, n, C, path):
    speeds=np.linspace(max(1,v_base*0.3),v_base*2.0,300)
    lives=np.clip([(C/v)**(1/n) for v in speeds],0,10000)
    fig,ax=plt.subplots(figsize=(7,3.5),facecolor="white"); ax.set_facecolor("#f8f9fa")
    fig.subplots_adjust(left=0.13,right=0.97,top=0.88,bottom=0.18)
    ax.plot(speeds,lives,color="#333333",linewidth=1.8,zorder=3)
    mc={"Conservative":"#777777","Balanced":"#444444","Aggressive":"#111111"}
    for label,fac in [("Conservative",0.8),("Balanced",1.0),("Aggressive",1.2)]:
        v_pt=v_base*fac; t_pt=min((C/v_pt)**(1/n),10000)
        ax.axvline(v_pt,color=mc[label],linewidth=1.0,linestyle="--",alpha=0.9)
        ax.plot(v_pt,t_pt,"o",color=mc[label],markersize=7,zorder=4,label=f"{label}: {fmt_time(t_pt)}")
    ax.set_title("Tool Life vs Cutting Speed",fontsize=10,fontweight="bold")
    ax.set_xlabel("Cutting Speed (m/min)",fontsize=9); ax.set_ylabel("Tool Life (min)",fontsize=9)
    ax.grid(True,color="#dee2e6",linewidth=0.7,alpha=1.0); ax.legend(fontsize=8,framealpha=1.0)
    fig.savefig(path,dpi=120,bbox_inches="tight",facecolor="white"); plt.close(fig)

def compute_beam_stresses(section, load_type, L, P_or_w, a, dim1, dim2):
    x=np.linspace(0,L,500)
    if load_type=="Point Load":
        P=P_or_w; b_pos=L-a; R1=P*b_pos/L
        V=np.where(x<a,R1,R1-P); M=np.where(x<a,R1*x,R1*x-P*(x-a))
        M_max=float(np.max(np.abs(M))); V_max=float(np.max(np.abs(V)))
        y=np.where(x<a,(P*b_pos*x/(6*L))*(L**2-b_pos**2-x**2),(P*a*(L-x)/(6*L))*(L**2-a**2-(L-x)**2))
    else:
        w=P_or_w; R1=w*L/2; V=R1-w*x; M=R1*x-(w*x**2)/2
        M_max=float(np.max(np.abs(M))); V_max=float(np.max(np.abs(V)))
        y=(w*x*(L**3-2*L*x**2+x**3))/24
    if section=="Rectangle":
        b,h=dim1,dim2; c=h/2; I=b*h**3/12; A=b*h; tau_max=1.5*V_max/A
    else:
        d=dim1; c=d/2; I=np.pi*d**4/64; A=np.pi*d**2/4; tau_max=(4/3)*V_max/A
    return M_max*c/I,tau_max,M_max,V_max,x,M,V,y

def draw_beam_plots(parent, x, M, V, y_raw, EI, L, load_type, a=None):
    for w in parent.winfo_children(): w.destroy()
    y_def=y_raw/EI*1000; x_mm=x*1000
    fig=Figure(figsize=(8,8),dpi=96,facecolor=BG2)
    fig.subplots_adjust(left=0.11,right=0.97,top=0.94,bottom=0.07,hspace=0.45)
    def _ax(ax,title,xl,yl):
        ax.set_facecolor(BG3); ax.set_title(title,color=TEXT,fontsize=9,fontweight="bold",pad=6)
        ax.set_xlabel(xl,color=TEXT2,fontsize=8); ax.set_ylabel(yl,color=TEXT2,fontsize=8)
        ax.tick_params(colors=TEXT2,labelsize=7); ax.grid(True,color=BORDER,linewidth=0.7,alpha=1.0)
        ax.axhline(0,color=TEXT2,linewidth=0.6,alpha=0.5)
        for sp in ax.spines.values(): sp.set_edgecolor(BORDER)
    ax1=fig.add_subplot(3,1,1); ax1.plot(x_mm,V/1000,color=TEXT,linewidth=1.6)
    ax1.fill_between(x_mm,V/1000,0,alpha=0.15,color=TEXT); _ax(ax1,"Shear Force Diagram","Position (mm)","V (kN)")
    ax2=fig.add_subplot(3,1,2); ax2.plot(x_mm,M/1000,color=ACCENT2,linewidth=1.6)
    ax2.fill_between(x_mm,M/1000,0,alpha=0.15,color=ACCENT2); _ax(ax2,"Bending Moment Diagram","Position (mm)","M (kNm)")
    ax3=fig.add_subplot(3,1,3); ax3.plot(x_mm,y_def,color="#888888",linewidth=1.6)
    ax3.fill_between(x_mm,y_def,0,alpha=0.15,color="#888888"); ax3.invert_yaxis()
    _ax(ax3,"Deflection Curve","Position (mm)","d (mm)")
    canvas=FigureCanvasTkAgg(fig,master=parent)
    canvas.draw(); canvas.get_tk_widget().pack(fill="x",pady=(4,0))
    return canvas

class PDFMetaDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent); self.title("PDF Export \u2014 Report Details")
        self.configure(bg=BG2); self.resizable(False,False); self.grab_set(); self.result=None
        tk.Label(self,text="Report Details",font=FONT_H,fg=TEXT,bg=BG2).pack(padx=24,pady=(18,2),anchor="w")
        tk.Label(self,text="These fields appear in the PDF header and title block.",font=FONT_S,fg=TEXT2,bg=BG2).pack(padx=24,pady=(0,10),anchor="w")
        form=tk.Frame(self,bg=BG2); form.pack(padx=24,pady=(0,10),fill="x"); form.columnconfigure(1,weight=1)
        self._fields={}
        rows=[("project_name","Project Name","MechAssist Engineering Analysis"),
              ("engineer","Engineer Name","Monjyeeman Dutta"),
              ("institution","Institution","Jorhat Engineering College"),
              ("company","Company / Client",""),("revision","Revision","Rev 1.0"),("notes","Notes (optional)","")]
        for i,(key,label,default) in enumerate(rows):
            tk.Label(form,text=label+":",font=FONT_S,fg=TEXT2,bg=BG2,anchor="w").grid(row=i,column=0,sticky="w",padx=(0,12),pady=4)
            e=styled_entry(form,width=38)
            if default: e.insert(0,default)
            e.grid(row=i,column=1,sticky="ew",pady=4); self._fields[key]=e
        btn_row=tk.Frame(self,bg=BG2); btn_row.pack(padx=24,pady=(0,18),anchor="e")
        tk.Button(btn_row,text="Cancel",command=self.destroy,bg=BG3,fg=TEXT2,font=FONT,relief="flat",padx=16,pady=6).pack(side="left",padx=(0,8))
        action_btn(btn_row,"Export PDF",self._confirm).pack(side="left")
    def _confirm(self):
        self.result={k:e.get().strip() for k,e in self._fields.items()}; self.destroy()

class LogPanel(tk.Frame):
    MAX_ENTRIES=200
    def __init__(self, parent, **kw):
        super().__init__(parent,bg="#090909",**kw)
        self._entries=[]; self._visible=False
        hdr=tk.Frame(self,bg="#090909"); hdr.pack(fill="x",padx=10,pady=(4,0))
        tk.Label(hdr,text="Activity Log",font=FONT_SB,fg=TEXT,bg="#090909").pack(side="left")
        tk.Button(hdr,text="Clear",font=("Segoe UI",8),fg=TEXT2,bg="#090909",relief="flat",cursor="hand2",
                  activebackground=BG3,activeforeground=TEXT,command=self._clear).pack(side="right")
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x",padx=10,pady=(4,0))
        txt_f=tk.Frame(self,bg="#090909"); txt_f.pack(fill="both",expand=True,padx=10,pady=(4,6))
        sb=ttk.Scrollbar(txt_f,orient="vertical")
        self._txt=tk.Text(txt_f,height=8,bg="#090909",fg=TEXT2,font=("Consolas",9),relief="flat",wrap="word",
                          state="disabled",yscrollcommand=sb.set,selectbackground=BG3,insertbackground=ACCENT)
        sb.config(command=self._txt.yview)
        self._txt.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._txt.tag_config("ts",foreground=TEXT2); self._txt.tag_config("info",foreground=TEXT)
        self._txt.tag_config("busy",foreground="#888888"); self._txt.tag_config("success",foreground=ACCENT2)
        self._txt.tag_config("error",foreground="#555555"); self._txt.tag_config("ready",foreground=TEXT)
    def log(self, msg, busy=False):
        from datetime import datetime; ts=datetime.now().strftime("%H:%M:%S")
        self._entries.append((ts,msg))
        if len(self._entries)>self.MAX_ENTRIES: self._entries.pop(0)
        ml=msg.lower()
        tag=("error" if "failed" in ml or "error" in ml else
             "success" if "complete" in ml or "exported" in ml or "found" in ml else
             "busy" if busy or "running" in ml or "generating" in ml else
             "ready" if "ready" in ml else "info")
        self._txt.config(state="normal")
        self._txt.insert("end",f"  {ts}  ","ts"); self._txt.insert("end",f"{msg}\n",tag)
        self._txt.see("end"); self._txt.config(state="disabled")
    def _clear(self):
        self._entries.clear(); self._txt.config(state="normal"); self._txt.delete("1.0","end"); self._txt.config(state="disabled")
    def toggle(self):
        self._visible=not self._visible
        if self._visible:
            self.pack(fill="x",side="bottom",before=self.master.winfo_children()[-1] if self.master.winfo_children() else None)
        else: self.pack_forget()
        return self._visible

class MechAssist(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MechAssist \u2014Engineering Decision Support")
        self.geometry("1100x820"); self.minsize(900,700)
        self.configure(bg=BG); self.resizable(True,True)
        self._mohr_png=None; self._toollife_png=None
        self._unit_var=tk.StringVar(value=UNIT_SYSTEMS[0])
        self._api_key_var=tk.StringVar(value="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")
        self._m1_ai_card=self._m2_ai_card=self._m3_ai_card=None
        self._prec_var=tk.StringVar(value="4 sig.fig")
        self._prec_var.trace_add("write",self._on_prec_change)
        self._m1_override_open=False
        style=ttk.Style(self); style.theme_use("clam")
        style.configure("TCombobox",fieldbackground=BG3,background=BG3,foreground=TEXT,selectbackground=BORDER,selectforeground=TEXT,borderwidth=0)
        style.map("TCombobox",fieldbackground=[("readonly",BG3)],foreground=[("readonly",TEXT)])
        style.configure("TNotebook",background=BG,borderwidth=0)
        style.configure("TNotebook.Tab",background=BG2,foreground=TEXT2,font=("Segoe UI",10),padding=(16,8))
        style.map("TNotebook.Tab",background=[("selected",BG3)],foreground=[("selected",TEXT)])
        self._log_panel=LogPanel(self)
        self._build_header(); self._build_body(); self._build_statusbar()

    def _apply_suggestion_change(self, field_key, new_val):
        widget_map={
            "m3_speed":self.m3_speed,"m3_feed":self.m3_feed,"m3_depth":self.m3_depth,
            "m2_sigma":self.m2_sigma,"m2_tau":self.m2_tau,"m2_sy":self.m2_sy,
            "m2_su":self.m2_su,"m2_sf_target":self.m2_sf_target,
            "m1_yield":getattr(self,"m1_yield",None),
        }
        widget=widget_map.get(field_key)
        if widget:
            widget.delete(0,tk.END); widget.insert(0,new_val)
            if hasattr(widget,"entry"):
                widget.entry.config(highlightbackground=AI_ACCENT,highlightcolor=AI_ACCENT)
                self.after(2000,lambda w=widget:w.entry.config(highlightbackground=BORDER,highlightcolor=ACCENT2))
            else:
                widget.config(highlightbackground=AI_ACCENT,highlightcolor=AI_ACCENT)
                self.after(2000,lambda w=widget:w.config(highlightbackground=BORDER,highlightcolor=ACCENT2))
            self.set_status(f"Applied: {field_key} = {new_val}  (re-run module to update)")

    def _build_header(self):
        hdr=tk.Frame(self,bg=BG2,height=54); hdr.pack(fill="x"); hdr.pack_propagate(False)
        logo_f=tk.Frame(hdr,bg=BG2); logo_f.pack(side="left",padx=(20,0))
        tk.Label(logo_f,text="MechAssist",font=("Segoe UI",16,"bold"),fg=TEXT,bg=BG2).pack(side="left")
        tk.Label(logo_f,text="  /",font=("Segoe UI",16),fg=TEXT2,bg=BG2).pack(side="left")
        tk.Label(logo_f,text="  engineering decision support",font=("Segoe UI",10),fg=TEXT2,bg=BG2).pack(side="left")
        self._status_badge_var=tk.StringVar(value="READY")
        self._status_badge_lbl=tk.Label(hdr,textvariable=self._status_badge_var,font=("Segoe UI",9,"bold"),fg=BG2,bg=ACCENT2,padx=10,pady=3)
        self._status_badge_lbl.pack(side="right",padx=(0,20))
        self._imp_btn=tk.Button(hdr,text="Imperial",font=("Segoe UI",9),bg=BG3,fg=TEXT2,relief="flat",cursor="hand2",padx=10,pady=4,bd=0,
                                activebackground=BORDER,activeforeground=TEXT,command=lambda:self._set_unit("Imperial  (ksi / lb/ft3)"))
        self._imp_btn.pack(side="right",padx=(0,4))
        self._si_btn=tk.Button(hdr,text="SI",font=("Segoe UI",9,"bold"),bg=BG3,fg=TEXT,relief="flat",cursor="hand2",padx=10,pady=4,bd=0,
                               highlightthickness=1,highlightbackground=ACCENT2,activebackground=BORDER,activeforeground=TEXT,
                               command=lambda:self._set_unit("SI  (MPa / kg/m3)"))
        self._si_btn.pack(side="right",padx=(0,2))
        tk.Label(hdr,text="Units :",font=("Segoe UI",9),fg=TEXT2,bg=BG2).pack(side="right",padx=(0,6))
        tk.Frame(hdr,bg=BORDER,width=1).pack(side="right",fill="y",padx=(6,6),pady=8)
        prec_cb=ttk.Combobox(hdr,textvariable=self._prec_var,values=["2 sig.fig","3 sig.fig","4 sig.fig","5 sig.fig","6 sig.fig"],
                             width=8,font=("Segoe UI",9),state="readonly")
        prec_cb.pack(side="right",padx=(0,2))
        tk.Label(hdr,text="Precision :",font=("Segoe UI",9),fg=TEXT2,bg=BG2).pack(side="right",padx=(0,4))
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x")

    def _set_unit(self, unit_str):
        self._unit_var.set(unit_str); is_si="MPa" in unit_str
        self._si_btn.config(highlightthickness=1 if is_si else 0,highlightbackground=ACCENT2,
                            fg=TEXT if is_si else TEXT2,font=("Segoe UI",9,"bold") if is_si else ("Segoe UI",9))
        self._imp_btn.config(highlightthickness=1 if not is_si else 0,highlightbackground=ACCENT2,
                             fg=TEXT if not is_si else TEXT2,font=("Segoe UI",9,"bold") if not is_si else ("Segoe UI",9))
        self._refresh_unit_labels()

    def _refresh_unit_labels(self):
        su=self._unit_var.get(); is_imp="ksi" in su
        sl=_stress_label(su); dl=_density_label(su)
        for attr,val in [("_m1_yield_lbl",f"Min Yield Strength"),
                         ("_m1_dens_lbl",f"Max Density [optional]"),
                         ("_m2_sigma_lbl",f"Normal Stress"),
                         ("_m2_tau_lbl",f"Shear Stress"),
                         ("_m2_sy_lbl",f"Yield Strength"),
                         ("_m2_su_lbl",f"UTS")]:
            if hasattr(self,attr): getattr(self,attr).set(val)
        stress_units=STRESS_UNITS_IMP if is_imp else STRESS_UNITS_SI
        den_units=DENSITY_UNITS_IMP if is_imp else DENSITY_UNITS_SI
        def_stress="ksi" if is_imp else "MPa"
        def_den="lb/ft\u00b3" if is_imp else "kg/m\u00b3"
        if hasattr(self,"m1_yield") and isinstance(self.m1_yield,UnitEntry):
            self.m1_yield.set_units(stress_units,def_stress)
        if hasattr(self,"m1_dens") and isinstance(self.m1_dens,UnitEntry):
            self.m1_dens.set_units(den_units,def_den)
        for attr in ("m2_sigma","m2_tau","m2_sy","m2_su"):
            if hasattr(self,attr) and isinstance(getattr(self,attr),UnitEntry):
                getattr(self,attr).set_units(stress_units,def_stress)

    def _on_prec_change(self, *args):
        try: p=int(self._prec_var.get().split()[0]); _PRECISION[0]=p
        except (ValueError,IndexError): pass

    def _build_body(self):
        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True,pady=(8,0))
        nb=ttk.Notebook(body); nb.pack(fill="both",expand=True,padx=8,pady=4)
        self.tab1=tk.Frame(nb,bg=BG); self.tab2=tk.Frame(nb,bg=BG)
        self.tab3=tk.Frame(nb,bg=BG); self.tab4=tk.Frame(nb,bg=BG)
        nb.add(self.tab1,text="  Material Selection  "); nb.add(self.tab2,text="  Stress Assessment  ")
        nb.add(self.tab3,text="  Machinability  ");      nb.add(self.tab4,text="  Summary  ")
        self._build_module1(); self._build_module2(); self._build_module3(); self._build_summary()

    def _build_statusbar(self):
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x",side="bottom")
        self._log_panel.pack(fill="x",side="bottom"); self._log_panel.pack_forget()
        sb=tk.Frame(self,bg="#090909",height=26); sb.pack(fill="x",side="bottom"); sb.pack_propagate(False)
        tk.Label(sb,text=">",font=("Segoe UI",12),fg=TEXT2,bg="#090909").pack(side="left",padx=(12,5))
        self.status_var=tk.StringVar(value="MechAssist v1.0  Ready")
        tk.Label(sb,textvariable=self.status_var,font=("Segoe UI",9),fg=TEXT2,bg="#090909").pack(side="left")
        self._log_btn_var=tk.StringVar(value="Log ^")
        log_btn=tk.Button(sb,textvariable=self._log_btn_var,font=("Segoe UI",8),fg=TEXT2,bg="#090909",
                          relief="flat",cursor="hand2",activebackground=BG3,activeforeground=TEXT,command=self._toggle_log)
        log_btn.pack(side="right",padx=(0,12))

    def set_status(self, msg, busy=False):
        self.status_var.set(msg)
        if busy: self._status_badge_var.set("BUSY"); self._status_badge_lbl.config(bg="#444444",fg=TEXT)
        else: self._status_badge_var.set("READY"); self._status_badge_lbl.config(bg=ACCENT2,fg=BG2)
        if hasattr(self,"_log_panel"): self._log_panel.log(msg,busy)
        self.update_idletasks()

    def _toggle_log(self):
        visible=self._log_panel.toggle(); self._log_btn_var.set("Log v" if visible else "Log ^")

    @property
    def _us(self): return self._unit_var.get()

    def _read_stress(self, entry):
        if isinstance(entry,UnitEntry): return entry.get_base()
        return _to_mpa(float(entry.get()),self._us)

    def _read_density(self, entry):
        if isinstance(entry,UnitEntry): return entry.get_base()
        return _to_kgm3(float(entry.get()),self._us)

    def _write_stress_mpa(self, entry, mpa_val):
        if isinstance(entry,UnitEntry): entry.set_from_base(mpa_val)
        else: entry.delete(0,tk.END); entry.insert(0,f"{_from_mpa(mpa_val,self._us):.4g}")

    def _validate_stress(self, val_mpa, key):
        lo,hi,label=RANGES_SI[key]
        if not (lo<=val_mpa<=hi):
            su=self._us; sl=_stress_label(su)
            lo_d=_from_mpa(lo,su); hi_d=_from_mpa(hi,su); disp=_from_mpa(val_mpa,su)
            messagebox.showerror("Validation Error",f"{label}: {disp:.4g} {sl} is outside valid range ({lo_d:.4g}\u2013{hi_d:.4g} {sl}).")
            return False
        return True

    def _validate_density(self, val_kgm3):
        lo,hi,label=RANGES_SI["m1_ro"]
        if not (lo<=val_kgm3<=hi):
            su=self._us; dl=_density_label(su)
            lo_d=_from_kgm3(lo,su); hi_d=_from_kgm3(hi,su); disp=_from_kgm3(val_kgm3,su)
            messagebox.showerror("Validation Error",f"{label}: {disp:.4g} {dl} is outside valid range ({lo_d:.4g}\u2013{hi_d:.4g} {dl}).")
            return False
        return True

    # ── Module 1 ──────────────────────────────────────────────────────────
    def _build_module1(self):
        scroll=_ScrollFrame(self.tab1); scroll.pack(fill="both",expand=True)
        p=scroll.inner
        inp=card(p,"Application Requirements"); inp.columnconfigure(1,weight=1); inp.columnconfigure(3,weight=1)

        self.m1_member=styled_combo(inp,["beam","shaft","column","plate"],width=12)
        self.m1_member.bind("<<ComboboxSelected>>",self._on_m1_member_change)
        tk.Label(inp,text="Member Type",font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=0,sticky="w",padx=(0,12),pady=5)
        self.m1_member.grid(row=0,column=1,sticky="ew",pady=5)
        self.m1_sf=styled_entry(inp,width=10); self.m1_sf.insert(0,"2.0")
        tk.Label(inp,text="Target Safety Factor",font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=2,sticky="w",padx=(16,12),pady=5)
        self.m1_sf.grid(row=0,column=3,sticky="ew",pady=5)

        self._m1_load_lbl=tk.StringVar(value="Applied Load")
        tk.Label(inp,textvariable=self._m1_load_lbl,font=FONT,fg=TEXT2,bg=BG2).grid(row=1,column=0,sticky="w",padx=(0,12),pady=5)
        self.m1_load=make_force_entry(inp,self._us,entry_width=10)
        self.m1_load.grid(row=1,column=1,sticky="ew",pady=5)
        self._m1_loadtype_label=tk.Label(inp,text="Load Type",font=FONT,fg=TEXT2,bg=BG2)
        self._m1_loadtype_label.grid(row=1,column=2,sticky="w",padx=(16,12),pady=5)
        self.m1_loadtype=styled_combo(inp,["Point Load","UDL"],width=12)
        self.m1_loadtype.grid(row=1,column=3,sticky="ew",pady=5)

        self._m1_span_lbl=tk.StringVar(value="Span / Length")
        tk.Label(inp,textvariable=self._m1_span_lbl,font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=0,sticky="w",padx=(0,12),pady=5)
        self.m1_span=make_length_entry(inp,self._us,entry_width=10)
        self.m1_span.grid(row=2,column=1,sticky="ew",pady=5)
        self.m1_section=styled_combo(inp,["Rectangle","Circle"],width=12)
        self.m1_section.bind("<<ComboboxSelected>>",self._on_m1_section_change)
        tk.Label(inp,text="Cross-Section",font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=2,sticky="w",padx=(16,12),pady=5)
        self.m1_section.grid(row=2,column=3,sticky="ew",pady=5)

        self._m1_dim1_lbl=tk.StringVar(value="Width")
        tk.Label(inp,textvariable=self._m1_dim1_lbl,font=FONT,fg=TEXT2,bg=BG2).grid(row=3,column=0,sticky="w",padx=(0,12),pady=5)
        self.m1_dim1=make_length_entry(inp,self._us,entry_width=10)
        self.m1_dim1.grid(row=3,column=1,sticky="ew",pady=5)
        self._m1_dim2_lbl=tk.StringVar(value="Height")
        self._m1_dim2_lw=tk.Label(inp,textvariable=self._m1_dim2_lbl,font=FONT,fg=TEXT2,bg=BG2)
        self._m1_dim2_lw.grid(row=3,column=2,sticky="w",padx=(16,12),pady=5)
        self.m1_dim2=make_length_entry(inp,self._us,entry_width=10)
        self.m1_dim2.grid(row=3,column=3,sticky="ew",pady=5)

        self._m1_dens_lbl=tk.StringVar(value=f"Max Density [optional]")
        tk.Label(inp,textvariable=self._m1_dens_lbl,font=FONT,fg=TEXT2,bg=BG2).grid(row=4,column=0,sticky="w",padx=(0,12),pady=5)
        self.m1_dens=make_density_entry(inp,self._us,entry_width=10)
        self.m1_dens.grid(row=4,column=1,sticky="ew",pady=5)
        tk.Label(inp,text="Leave blank = no density constraint",font=FONT_S,fg=TEXT2,bg=BG2).grid(row=4,column=2,columnspan=2,sticky="w",padx=(16,0))

        ToolTip(self.m1_member,"beam/plate: bending+shear (simply supported)\nshaft: torsion  tau=16T/(pi*d^3)\ncolumn: axial  sigma=F/A")
        ToolTip(self.m1_sf,"Safety factor: Required Sy = sigma_vm x SF\nStatic: 1.5-2.0 | Dynamic: 2.0-3.0 | Impact: 3.0-5.0")
        ToolTip(self.m1_load,"beam/plate/column: load in N\nshaft: torque in Nm")
        ToolTip(self.m1_span,"beam/plate: span between supports\nshaft: shaft length (optional)\ncolumn: effective length")
        ToolTip(self.m1_dim1,"Rectangle: width\nCircle/shaft: diameter")
        ToolTip(self.m1_dim2,"Rectangle: height h")
        ToolTip(self.m1_dens,lambda:_make_density_tooltip(self.m1_dens))

        ovr_f=tk.Frame(inp,bg=BG2); ovr_f.grid(row=5,column=0,columnspan=4,sticky="w",pady=(8,0))
        self._m1_ovr_btn=tk.Button(ovr_f,text="+ Manual Override  (enter Sy / density / elongation directly)",
                                   font=FONT_S,fg=TEXT2,bg=BG2,relief="flat",cursor="hand2",
                                   activebackground=BG2,activeforeground=TEXT,command=self._toggle_m1_override)
        self._m1_ovr_btn.pack(side="left")

        self._m1_ovr_frame=tk.Frame(inp,bg=BG2)
        self._m1_ovr_frame.grid(row=6,column=0,columnspan=4,sticky="ew",pady=(4,0))
        self._m1_ovr_frame.grid_remove()
        self._m1_ovr_frame.columnconfigure(1,weight=1)

        self._m1_yield_lbl=tk.StringVar(value=f"Min Yield Strength ({_stress_label(self._us)})")
        tk.Label(self._m1_ovr_frame,textvariable=self._m1_yield_lbl,font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=0,sticky="w",padx=(0,12),pady=4)
        self.m1_yield=make_stress_entry(self._m1_ovr_frame,self._us,entry_width=10)
        self.m1_yield.grid(row=0,column=1,sticky="ew",pady=4)
        tk.Label(self._m1_ovr_frame,text="Min Elongation (%)",font=FONT,fg=TEXT2,bg=BG2).grid(row=1,column=0,sticky="w",padx=(0,12),pady=4)
        self.m1_elong=styled_entry(self._m1_ovr_frame,width=10)
        self.m1_elong.grid(row=1,column=1,sticky="ew",pady=4)
        tk.Label(self._m1_ovr_frame,text="Override: filters applied directly. Leave blank to skip that filter.",
                 font=FONT_S,fg=TEXT2,bg=BG2,justify="left").grid(row=2,column=0,columnspan=2,sticky="w",pady=(2,4))

        ToolTip(self.m1_yield,lambda:_make_stress_tooltip("m1_sy",self.m1_yield))
        ToolTip(self.m1_elong,"Minimum elongation (ductility).\n  Safety-critical: 15-25%\n  General: 10-15%\n  Springs/tools: 2-8%\n  Valid: 0-100%")

        bf=tk.Frame(inp,bg=BG2); bf.grid(row=7,column=0,columnspan=4,sticky="w",pady=(10,0))
        action_btn(bf,"Find Materials",self._run_module1).pack(side="left")

        self.m1_result_frame=card(p,"Recommended Materials")
        _ai_body_m1=card(p,"AI / Suggestion")
        self._m1_ai_card=SmartSuggestionCard(_ai_body_m1,self)
        self._m1_ai_card.pack(fill="x")

        self._on_m1_member_change()
        self._on_m1_section_change()

    def _toggle_m1_override(self):
        self._m1_override_open=not self._m1_override_open
        if self._m1_override_open:
            self._m1_ovr_frame.grid(); self._m1_ovr_btn.config(text="- Manual Override")
        else:
            self._m1_ovr_frame.grid_remove(); self._m1_ovr_btn.config(text="+ Manual Override  (enter Sy / density / elongation directly)")

    def _on_m1_member_change(self, event=None):
        m=self.m1_member.get()
        if m=="shaft":
            self._m1_load_lbl.set("Applied Torque")
            self._m1_span_lbl.set("Shaft Length  [optional]")
            self.m1_load.set_units(TORQUE_UNITS,"Nm")
            self._m1_loadtype_label.grid_remove(); self.m1_loadtype.grid_remove()
            self.m1_section.set("Circle"); self.m1_section.config(state="disabled")
            self._on_m1_section_change()
        elif m=="column":
            self._m1_load_lbl.set("Axial Load")
            self._m1_span_lbl.set("Effective Length")
            self.m1_load.set_units(force_units_for(self._us),"kip" if "ksi" in self._us else "N")
            self._m1_loadtype_label.grid_remove(); self.m1_loadtype.grid_remove()
            self.m1_section.config(state="readonly")
        else:
            # beam and plate: same bending+shear formulas, both show load type
            self._m1_load_lbl.set("Applied Load")
            self._m1_span_lbl.set("Span / Length")
            self.m1_load.set_units(force_units_for(self._us),"kip" if "ksi" in self._us else "N")
            self._m1_loadtype_label.grid(); self.m1_loadtype.grid()
            self.m1_section.config(state="readonly")

    def _on_m1_section_change(self, event=None):
        if self.m1_section.get()=="Rectangle":
            self._m1_dim1_lbl.set("Width"); self._m1_dim2_lbl.set("Height")
            self._m1_dim2_lw.grid(); self.m1_dim2.grid()
        else:
            self._m1_dim1_lbl.set("Diameter")
            self._m1_dim2_lw.grid_remove(); self.m1_dim2.grid_remove()

    def _run_module1(self):
        for w in self.m1_result_frame.winfo_children(): w.destroy()
        self._m1_ai_card.show_loading()

        if self._m1_override_open:
            try:
                sy_raw=self.m1_yield.get().strip()
                dens_raw=self.m1_dens.get().strip()
                elong_raw=self.m1_elong.get().strip()
                req_sy_mpa=self._read_stress(self.m1_yield) if sy_raw else 0.0
                ro=self._read_density(self.m1_dens) if dens_raw else 25000.0
                a5=float(elong_raw) if elong_raw else 0.0
            except ValueError:
                messagebox.showerror("Input Error","Enter valid numbers in override fields."); return
        else:
            member=self.m1_member.get()
            try:
                sf=float(self.m1_sf.get())
                if sf<=0: raise ValueError
            except ValueError:
                messagebox.showerror("Input Error","Target Safety Factor must be > 0."); return
            try:
                load_val=self.m1_load.get_base()
                if load_val<=0: raise ValueError
            except (ValueError,AttributeError):
                messagebox.showerror("Input Error","Enter a valid positive load / torque."); return
            try:
                span_raw=self.m1_span.get().strip()
                span_m=self.m1_span.get_base() if span_raw else None
            except Exception: span_m=None
            try:
                dim1_m=self.m1_dim1.get_base()
                if dim1_m<=0: raise ValueError
            except ValueError:
                messagebox.showerror("Input Error","Enter a valid dimension."); return
            dim2_m=0.0; section=self.m1_section.get()
            if section=="Rectangle":
                try:
                    dim2_m=self.m1_dim2.get_base()
                    if dim2_m<=0: raise ValueError
                except ValueError:
                    messagebox.showerror("Input Error","Enter a valid height."); return
            load_type=self.m1_loadtype.get() if member not in ("shaft","column") else "Point Load"
            span_use=span_m if span_m else dim1_m*10
            try:
                _,_,_,req_sy_mpa=compute_required_sy(member,load_type,load_val,span_use,dim1_m,dim2_m,section,sf)
            except Exception as ex:
                messagebox.showerror("Computation Error",str(ex)); return
            dens_raw=self.m1_dens.get().strip()
            try: ro=self._read_density(self.m1_dens) if dens_raw else 25000.0
            except Exception: ro=25000.0
            a5=0.0

        self.set_status("Running Module 1 \u2014 K-Means Material Clustering...",busy=True)
        try: results=recommend_materials(req_sy_mpa,ro,a5)
        except Exception as ex:
            messagebox.showerror("Error",str(ex)); self.set_status("Module 1 Failed."); return

        if not results:
            styled_label(self.m1_result_frame,"No materials match. Try relaxing constraints or lowering safety factor.",fg=TEXT2).pack(anchor="w")
            self.set_status("No Results Found."); return

        self.m1_last_results=results
        rank_colors=[TEXT,ACCENT2,"#888888"]
        for i,r in enumerate(results):
            color=rank_colors[i%3]
            row=tk.Frame(self.m1_result_frame,bg=BG3); row.pack(fill="x",pady=(0,8))
            tk.Label(row,text=f"  #{i+1}  ",font=FONT_B,fg=BG2,bg=color,width=4).pack(side="left")
            info=tk.Frame(row,bg=BG3); info.pack(side="left",fill="x",expand=True,padx=10,pady=6)
            tk.Label(info,text=r["Material"],font=FONT_B,fg=TEXT,bg=BG3,anchor="w").pack(fill="x")
            fc=r["Failure Concern"]
            fc_col="#888888" if "Creep" in fc else "#777777" if "Fatigue" in fc else "#555555"
            tk.Label(info,text=f"  \u26a0  {fc}",font=FONT_S,fg=fc_col,bg=BG3,anchor="w").pack(fill="x",pady=(1,0))

        self._autofill_m2_from_m1(silent=True)
        self._autofill_m3_from_m1(silent=True)
        self.set_status(f"Module 1 Complete \u2014 {len(results)} Materials Found.")
        self._update_summary_m1(results)
        top=results[0]
        ctx={"type":"material","material":top["Material"],"sy":top["Yield Strength (MPa)"],
             "density":top["Density (kg/m\u00b3)"],"elongation":top["Elongation (%)"],"failure_concern":top["Failure Concern"]}
        get_ai_suggestion(ctx,self._api_key_var.get(),lambda r:self.after(0,lambda:self._m1_ai_card.show_result(r)))

    def _autofill_m2_from_m1(self, silent=False):
        if not hasattr(self,"m1_last_results") or not self.m1_last_results:
            if not silent: messagebox.showwarning("No Data","Run Module 1 first.")
            return
        # FIX 1: sync M2 member type from M1 so correct geometry tool is shown
        m1_mem = self.m1_member.get()
        self.m2_member.set(m1_mem)
        self._on_m2_member_change()

        r=self.m1_last_results[0]; sy_mpa=r["Yield Strength (MPa)"]; su_mpa=round(sy_mpa*1.3,1)
        self._write_stress_mpa(self.m2_sy,sy_mpa); self._write_stress_mpa(self.m2_su,su_mpa)
        e_pa=r.get("E (Pa)",None)
        if e_pa and hasattr(self,"b_E"):
            self.b_E.delete(0,tk.END); self.b_E.insert(0,f"{e_pa:.6g}")
        if not silent:
            sl=_stress_label(self._us); e_gpa=r.get("E (GPa)",None)
            e_msg=f", E={e_gpa:.1f} GPa auto-filled to Beam Tool" if e_gpa else ""
            self.set_status(f"M2 Pre-Filled \u2014 Sy={_from_mpa(sy_mpa,self._us):.{_p()}g} {sl}, Su={_from_mpa(su_mpa,self._us):.{_p()}g} {sl}{e_msg}.")

    def _autofill_m3_from_m1(self, silent=False):
        if not hasattr(self, "m1_last_results") or not self.m1_last_results:
            if not silent: messagebox.showwarning("No Data", "Run Module 1 first.")
            return
        r = self.m1_last_results[0]
        grade_map = {0:"M", 1:"H", 2:"L", 3:"M", 4:"M", 5:"M"}
        grade = grade_map.get(r.get("Cluster"), "M"); self.m3_type.set(grade)

        m2_inputs = None
        if hasattr(self, "m2_last_result"):
            try:
                m2_inputs = {
                    "sigma_mpa": self._read_stress(self.m2_sigma),
                    "sf_target": getattr(self, "m2_last_sf_target", 2.0),
                }
            except Exception:
                pass

        sugg = compute_suggested_m3_inputs(self.m1_last_results, m2_inputs=m2_inputs)
        if not sugg:
            if not silent: self.set_status(f"M3 Pre-Filled \u2014 Grade '{grade}' from '{r['Material']}'.")
            return

        cat   = self._m3_machine_cat.get()
        model = self._m3_machine_model.get()
        specs = MACHINE_SPECS.get(cat, {}).get(model)

        if specs:
            raw_speed  = sugg["speed_mmin"]
            cap_speed  = min(raw_speed, specs["max_speed_mmin"])
            D_mm       = sugg.get("D_mm", specs.get("typical_dia_mm", 50))
            cap_rpm    = round((cap_speed * 1000) / (3.14159 * D_mm))
            cap_rpm    = max(specs["min_rpm"], min(cap_rpm, specs["max_rpm"]))
            cap_torque = min(sugg["torque_nm"], specs["max_torque_nm"])
        else:
            cap_speed  = sugg["speed_mmin"]
            cap_rpm    = sugg["rpm"]
            cap_torque = sugg["torque_nm"]

        try: self.m3_speed.set_from_base(cap_speed)
        except Exception: pass
        try: self.m3_feed.set_from_base(sugg["feed_mmrev"])
        except Exception: pass
        try: self.m3_depth.set_from_base(sugg["depth_mm"] / 1000.0)
        except Exception: pass
        try: self.m3_rpm.set_from_base(cap_rpm)
        except Exception: pass
        try: self.m3_torque.set_from_base(cap_torque)
        except Exception: pass

        if not silent:
            machine_info = f" [{model}]" if specs else ""
            self.set_status(
                f"M3 Auto-filled{machine_info} \u2014 "
                f"Grade={sugg['grade']}, Speed={cap_speed} m/min, "
                f"RPM={cap_rpm}, Feed={sugg['feed_mmrev']} mm/rev, "
                f"Depth={sugg['depth_mm']} mm, Torque={cap_torque} Nm"
            )

    # ── Module 2 ──────────────────────────────────────────────────────────
    def _build_module2(self):
        scroll=_ScrollFrame(self.tab2); scroll.pack(fill="both",expand=True)
        p=scroll.inner

        mem_sel=card(p,"Member Type"); mem_sel.columnconfigure(1,weight=1)
        self.m2_member=styled_combo(mem_sel,["beam","shaft","column","plate"],width=14)
        self.m2_member.bind("<<ComboboxSelected>>",self._on_m2_member_change)
        tk.Label(mem_sel,text="Member Type",font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=0,sticky="w",padx=(0,12),pady=5)
        self.m2_member.grid(row=0,column=1,sticky="w",pady=5)
        tk.Label(mem_sel,text="Geometry tool below changes based on member type. Skip if you already have stress values.",
                 font=FONT_S,fg=TEXT2,bg=BG2,wraplength=700,justify="left").grid(row=1,column=0,columnspan=2,sticky="w",pady=(0,4))

        # FIX 4: plate note label — shown when member=plate
        self._m2_plate_note_var = tk.StringVar(value="")
        self._m2_plate_note_lbl = tk.Label(
            mem_sel, textvariable=self._m2_plate_note_var,
            font=FONT_S, fg=AI_REC_FG, bg=BG2, anchor="w", wraplength=700, justify="left"
        )
        self._m2_plate_note_lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0,2))

        self._beam_tool_wrapper=tk.Frame(p,bg=BG); self._beam_tool_wrapper.pack(fill="x")

        # FIX 4: dynamic title for beam tool card (beam vs plate)
        self._beam_card_title_var = tk.StringVar(value="Compute from Beam Geometry  (optional \u2014 auto-fills stress fields below)")
        beam_outer = tk.Frame(self._beam_tool_wrapper, bg=BG)
        beam_outer.pack(fill="x", padx=12, pady=(0,10))
        tk.Frame(beam_outer, bg=ACCENT2, width=2).pack(side="left", fill="y")
        beam_inner = tk.Frame(beam_outer, bg=BG2); beam_inner.pack(side="left", fill="x", expand=True)
        tk.Label(beam_inner, textvariable=self._beam_card_title_var, font=FONT_H, fg=TEXT, bg=BG2, anchor="w").pack(fill="x", padx=16, pady=(10,4))
        tk.Frame(beam_inner, bg=BORDER, height=1).pack(fill="x", padx=16)
        beam_card = tk.Frame(beam_inner, bg=BG2); beam_card.pack(fill="x", padx=16, pady=12)
        beam_card.columnconfigure(1, weight=1); beam_card.columnconfigure(3, weight=1)

        self.b_span=make_length_entry(beam_card,self._us,entry_width=8)
        self.b_section=styled_combo(beam_card,["Rectangle","Circle"])
        self.b_section.bind("<<ComboboxSelected>>",self._on_section_change)
        tk.Label(beam_card,text="Beam Span",font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=0,sticky="w",padx=(0,8),pady=5)
        self.b_span.grid(row=0,column=1,sticky="ew",pady=5)
        tk.Label(beam_card,text="Cross-Section",font=FONT,fg=TEXT2,bg=BG2).grid(row=0,column=2,sticky="w",padx=(16,8),pady=5)
        self.b_section.grid(row=0,column=3,sticky="ew",pady=5)

        self.b_dim1_lbl=tk.StringVar(value="Width"); self.b_dim2_lbl=tk.StringVar(value="Height")
        self.b_dim1=make_length_entry(beam_card,self._us,entry_width=8)
        self.b_dim2=make_length_entry(beam_card,self._us,entry_width=8)
        self._dim1_lw=tk.Label(beam_card,textvariable=self.b_dim1_lbl,font=FONT,fg=TEXT2,bg=BG2)
        self._dim1_lw.grid(row=1,column=0,sticky="w",padx=(0,8),pady=4)
        self.b_dim1.grid(row=1,column=1,sticky="ew",pady=4)
        self._dim2_lw=tk.Label(beam_card,textvariable=self.b_dim2_lbl,font=FONT,fg=TEXT2,bg=BG2)
        self._dim2_lw.grid(row=1,column=2,sticky="w",padx=(16,8),pady=4)
        self.b_dim2.grid(row=1,column=3,sticky="ew",pady=4)

        self.b_E=styled_entry(beam_card); self.b_E.insert(0,"200e9")
        self.b_I=styled_entry(beam_card)
        tk.Label(beam_card,text="Young's Modulus",font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=0,sticky="w",padx=(0,8),pady=4)
        self.b_E.grid(row=2,column=1,sticky="ew",pady=4)
        tk.Label(beam_card,text="Moment of Inertia [auto if blank]",font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=2,sticky="w",padx=(16,8),pady=4)
        self.b_I.grid(row=2,column=3,sticky="ew",pady=4)

        self.b_loadtype=styled_combo(beam_card,["Point Load","UDL"])
        self.b_loadtype.bind("<<ComboboxSelected>>",self._on_loadtype_change)
        tk.Label(beam_card,text="Load Type",font=FONT,fg=TEXT2,bg=BG2).grid(row=3,column=0,sticky="w",padx=(0,8),pady=4)
        self.b_loadtype.grid(row=3,column=1,sticky="ew",pady=4)

        self.b_mag=make_force_entry(beam_card,self._us,entry_width=8)
        self.b_pos=make_length_entry(beam_card,self._us,entry_width=8)
        self._mag_lbl=tk.StringVar(value="Load"); self._pos_lbl=tk.StringVar(value="Position a from left")
        self._mag_lw=tk.Label(beam_card,textvariable=self._mag_lbl,font=FONT,fg=TEXT2,bg=BG2)
        self._mag_lw.grid(row=4,column=0,sticky="w",padx=(0,8),pady=4)
        self.b_mag.grid(row=4,column=1,sticky="ew",pady=4)
        self._pos_lw=tk.Label(beam_card,textvariable=self._pos_lbl,font=FONT,fg=TEXT2,bg=BG2)
        self._pos_lw.grid(row=4,column=2,sticky="w",padx=(16,8),pady=4)
        self.b_pos.grid(row=4,column=3,sticky="ew",pady=4)

        bf2=tk.Frame(beam_card,bg=BG2); bf2.grid(row=5,column=0,columnspan=4,sticky="w",pady=(10,0))
        action_btn(bf2,"Compute Normal Stress and Shear Stress",self._compute_beam_stresses).pack(side="left")
        tk.Label(bf2,text="[ Auto-fills stress fields below ]",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left",padx=8)

        ToolTip(self.b_span,"Span between supports\ne.g. 2.0 m")
        ToolTip(self.b_dim1,"Rectangle: Width\nCircle: diameter")
        ToolTip(self.b_dim2,"Rectangle: Height")
        ToolTip(self.b_E,"Young's Modulus\nSteel=200e9 | Al=70e9 | Ti=110e9")
        ToolTip(self.b_I,"Second Moment of Area\nLeave blank \u2014 auto-computed from dims")
        ToolTip(self.b_mag,"Point Load: total force\nUDL: force per unit length (N/m)")
        ToolTip(self.b_pos,"Distance from left support to point load\nMust be strictly between 0 and L")

        self.beam_plots_frame=tk.Frame(p,bg=BG); self.beam_plots_frame.pack(fill="x",padx=16,pady=(0,8))

        self._shaft_tool_wrapper=tk.Frame(p,bg=BG)
        shaft_card=card(self._shaft_tool_wrapper,"Shaft Torsion Tool  (optional \u2014 auto-fills stress fields below)")
        shaft_card.columnconfigure(1,weight=1); shaft_card.columnconfigure(3,weight=1)

        tk.Label(shaft_card,text="Enter torque and diameter to compute torsional shear. "
                 "Optionally add transverse load and length for combined bending + torsion.",
                 font=FONT_S,fg=TEXT2,bg=BG2,wraplength=700,justify="left").grid(row=0,column=0,columnspan=4,sticky="w",pady=(0,6))

        self.s_torque=make_torque_entry(shaft_card,entry_width=8)
        self.s_diam=make_length_entry(shaft_card,self._us,entry_width=8)
        tk.Label(shaft_card,text="Applied Torque",font=FONT,fg=TEXT2,bg=BG2).grid(row=1,column=0,sticky="w",padx=(0,8),pady=5)
        self.s_torque.grid(row=1,column=1,sticky="ew",pady=5)
        tk.Label(shaft_card,text="Shaft Diameter",font=FONT,fg=TEXT2,bg=BG2).grid(row=1,column=2,sticky="w",padx=(16,8),pady=5)
        self.s_diam.grid(row=1,column=3,sticky="ew",pady=5)

        self.s_load=make_force_entry(shaft_card,self._us,entry_width=8)
        self.s_len=make_length_entry(shaft_card,self._us,entry_width=8)
        tk.Label(shaft_card,text="Transverse Load [optional]",font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=0,sticky="w",padx=(0,8),pady=4)
        self.s_load.grid(row=2,column=1,sticky="ew",pady=4)
        tk.Label(shaft_card,text="Shaft Length [optional]",font=FONT,fg=TEXT2,bg=BG2).grid(row=2,column=2,sticky="w",padx=(16,8),pady=4)
        self.s_len.grid(row=2,column=3,sticky="ew",pady=4)

        bfs=tk.Frame(shaft_card,bg=BG2); bfs.grid(row=3,column=0,columnspan=4,sticky="w",pady=(10,0))
        action_btn(bfs,"Compute Shear Stress and Normal Stress",self._compute_shaft_stresses).pack(side="left")
        tk.Label(bfs,text="  -> auto-fills stress fields below",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left",padx=8)

        ToolTip(self.s_torque,"Applied torque on shaft\ne.g. 150 Nm")
        ToolTip(self.s_diam,"Shaft outer diameter\ne.g. 50 mm")
        ToolTip(self.s_load,"Transverse load (gear/belt force)\nLeave blank for torsion only")
        ToolTip(self.s_len,"Shaft length between bearings\nUsed for bending if transverse load given")

        # FIX 3: column info wrapper — shown when member=column
        self._column_tool_wrapper = tk.Frame(p, bg=BG)
        col_card = card(self._column_tool_wrapper, "Column — Axial Stress")
        tk.Label(col_card,
                 text="For columns, enter normal stress (sigma = F/A) directly in the Stress Analysis Inputs below.\n"
                      "No geometry tool needed — Beam/Shaft geometry tools do not apply to axial-only members.\n"
                      "If buckling is a concern, reduce effective length or increase cross-section area.",
                 font=FONT_S, fg=TEXT2, bg=BG2, wraplength=700, justify="left").pack(fill="x")

        inp=card(p,"Stress Analysis Inputs"); inp.columnconfigure(1,weight=1)
        self._m2_sigma_lbl=tk.StringVar(value=f"Normal Stress")
        self._m2_tau_lbl=tk.StringVar(value=f"Shear Stress")
        self._m2_sy_lbl=tk.StringVar(value=f"Yield Strength")
        self._m2_su_lbl=tk.StringVar(value=f"Ultimate Tensile Strength")
        self.m2_sf_target=styled_entry(inp); self.m2_sf_target.insert(0,"2.0")
        for i,(lvar,attr) in enumerate([(self._m2_sigma_lbl,"m2_sigma"),(self._m2_tau_lbl,"m2_tau"),
                                        (self._m2_sy_lbl,"m2_sy"),(self._m2_su_lbl,"m2_su")]):
            tk.Label(inp,textvariable=lvar,font=FONT,fg=TEXT2,bg=BG2).grid(row=i,column=0,sticky="w",padx=(0,12),pady=5)
            entry=make_stress_entry(inp,self._us,entry_width=10)
            entry.grid(row=i,column=1,sticky="ew",pady=5); setattr(self,attr,entry)
        field_row(inp,"Target Safety Factor",self.m2_sf_target,4)
        bind_arrow_keys([self.m2_sigma,self.m2_tau,self.m2_sy,self.m2_su,self.m2_sf_target])
        ToolTip(self.m2_sigma,lambda:_make_stress_tooltip("sigma",self.m2_sigma))
        ToolTip(self.m2_tau,lambda:_make_stress_tooltip("tau",self.m2_tau))
        ToolTip(self.m2_sy,lambda:_make_stress_tooltip("sy",self.m2_sy))
        ToolTip(self.m2_su,lambda:_make_stress_tooltip("su",self.m2_su))
        ToolTip(self.m2_sf_target,
                "Design decision \u2014 not measured.\n"
                "  Static, well-known load: 1.5\u20132.0\n  Dynamic/fatigue: 2.0\u20133.0\n"
                "  Impact/uncertainty: 3.0\u20135.0\n  ASME pressure vessels: >= 3.5")
        tk.Label(inp,text="Sy and Su auto-filled when Module 1 is run.",font=FONT_S,fg=TEXT2,bg=BG2).grid(row=5,column=0,columnspan=2,sticky="w",pady=(2,0))
        bf=tk.Frame(inp,bg=BG2); bf.grid(row=6,column=0,columnspan=2,sticky="w",pady=(8,0))
        action_btn(bf,"Assess Stress",self._run_module2).pack(side="left")

        self.m2_result_frame=card(p,"Stress Assessment Result")
        self.m2_mohr_frame=card(p,"Mohr's Circle")
        _ai_body_m2=card(p,"AI / Suggestion")
        self._m2_ai_card=SmartSuggestionCard(_ai_body_m2,self); self._m2_ai_card.pack(fill="x")

        self._on_m2_member_change()

    # FIX 2 + FIX 3: full member change handler with plate and column cases
    def _on_m2_member_change(self, event=None):
        m = self.m2_member.get()
        # hide all geometry tool wrappers first
        self._beam_tool_wrapper.pack_forget()
        self._shaft_tool_wrapper.pack_forget()
        self._column_tool_wrapper.pack_forget()

        if m == "shaft":
            self._shaft_tool_wrapper.pack(fill="x", before=self.beam_plots_frame)
            self._m2_plate_note_var.set("")

        elif m == "column":
            # FIX 3: show column info card, hide beam and shaft tools
            self._column_tool_wrapper.pack(fill="x", before=self.beam_plots_frame)
            self._m2_plate_note_var.set("")

        elif m == "plate":
            # FIX 4: plate uses beam bending formulas — show beam tool with note
            self._beam_tool_wrapper.pack(fill="x", before=self.beam_plots_frame)
            self._beam_card_title_var.set(
                "Compute from Plate Geometry  (plate treated as flat beam — simply supported, bending + shear)")
            self._m2_plate_note_var.set(
                "Plate selected: using simply-supported flat-beam bending formulas (M\u00b7c/I, 1.5\u00b7V/A). "
                "Enter plate width as b and thickness as h.")

        else:
            # beam
            self._beam_tool_wrapper.pack(fill="x", before=self.beam_plots_frame)
            self._beam_card_title_var.set(
                "Compute from Beam Geometry  (optional \u2014 auto-fills stress fields below)")
            self._m2_plate_note_var.set("")

    def _on_section_change(self, event=None):
        if self.b_section.get()=="Rectangle":
            self.b_dim1_lbl.set("Width"); self.b_dim2_lbl.set("Height")
            self._dim2_lw.grid(); self.b_dim2.grid()
        else:
            self.b_dim1_lbl.set("Diameter")
            self._dim2_lw.grid_remove(); self.b_dim2.grid_remove()

    def _on_loadtype_change(self, event=None):
        if self.b_loadtype.get()=="Point Load":
            self._mag_lbl.set("Load P"); self._pos_lbl.set("Position a from left")
            self._pos_lw.grid(); self.b_pos.grid()
        else:
            self._mag_lbl.set("Load Intensity w")
            self._pos_lw.grid_remove(); self.b_pos.grid_remove()

    def _compute_shaft_stresses(self):
        try:
            T=self.s_torque.get_base()
            if T<=0: raise ValueError
        except (ValueError,AttributeError):
            messagebox.showerror("Shaft Input Error","Enter a valid positive torque."); return
        try:
            d=self.s_diam.get_base()
            if d<=0: raise ValueError
        except (ValueError,AttributeError):
            messagebox.showerror("Shaft Input Error","Enter a valid shaft diameter."); return
        L_m=None; P_N=None
        try:
            if self.s_len.get().strip(): L_m=self.s_len.get_base()
        except Exception: pass
        try:
            if self.s_load.get().strip(): P_N=self.s_load.get_base()
        except Exception: pass
        sigma_mpa,tau_mpa=compute_shaft_torsion(T,d,L_m,P_N)
        self._write_stress_mpa(self.m2_sigma,sigma_mpa)
        self._write_stress_mpa(self.m2_tau,tau_mpa)
        # shaft tool always sets shaft — correct, no change needed
        self.m2_member.set("shaft")
        self._on_m2_member_change()
        sl=_stress_label(self._us)
        self.set_status(f"Shaft: tau={_from_mpa(tau_mpa,self._us):.4g} {sl}, sigma_bending={_from_mpa(sigma_mpa,self._us):.4g} {sl}, d={d*1000:.1f} mm, T={T:.1f} Nm")

    def _compute_beam_stresses(self):
        for w in self.beam_plots_frame.winfo_children(): w.destroy()
        try:
            L=self.b_span.get_base()
            if L<=0: raise ValueError
        except (ValueError,AttributeError):
            messagebox.showerror("Beam Input Error","Enter a valid positive span L."); return
        section=self.b_section.get()
        try:
            dim1=self.b_dim1.get_base()
            if dim1<=0: raise ValueError
        except (ValueError,AttributeError):
            messagebox.showerror("Beam Input Error","Enter a valid dimension."); return
        dim2=0.0
        if section=="Rectangle":
            try:
                dim2=self.b_dim2.get_base()
                if dim2<=0: raise ValueError
            except (ValueError,AttributeError):
                messagebox.showerror("Beam Input Error","Enter a valid height."); return
        try:
            E=float(self.b_E.get())
            if E<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Beam Input Error","Enter a valid Young's Modulus E (Pa)."); return
        I_field=self.b_I.get().strip()
        if I_field=="":
            I=(dim1*dim2**3/12) if section=="Rectangle" else (np.pi*dim1**4/64)
        else:
            try:
                I=float(I_field)
                if I<=0: raise ValueError
            except ValueError:
                messagebox.showerror("Beam Input Error","Enter a valid I (m4)."); return
        load_type=self.b_loadtype.get()
        try: mag=self.b_mag.get_base()
        except (ValueError,AttributeError):
            messagebox.showerror("Beam Input Error","Enter a valid load magnitude."); return
        a=0.0
        if load_type=="Point Load":
            try:
                a=self.b_pos.get_base()
                if not (0<a<L):
                    messagebox.showerror("Beam Input Error",f"Load position must be between 0 and L ({L:.4g} m)."); return
            except (ValueError,AttributeError):
                messagebox.showerror("Beam Input Error","Enter a valid position a."); return
        try:
            sigma,tau,M_max,V_max,x,M,V,y_raw=compute_beam_stresses(section,load_type,L,mag,a,dim1,dim2)
        except Exception as ex:
            messagebox.showerror("Computation Error",str(ex)); return
        EI=E*I
        self._write_stress_mpa(self.m2_sigma,sigma/1e6)
        self._write_stress_mpa(self.m2_tau,tau/1e6)

        # FIX 2: don't hardcode "beam" — preserve plate if that's what's selected
        current_member = self.m2_member.get()
        if current_member not in ("beam", "plate"):
            self.m2_member.set("beam")
            self._on_m2_member_change()

        sl=_stress_label(self._us)
        member_label = "Plate" if self.m2_member.get() == "plate" else "Beam"
        self.set_status(f"{member_label}: s_max={_from_mpa(sigma/1e6,self._us):.4g} {sl}, t_max={_from_mpa(tau/1e6,self._us):.4g} {sl}, M_max={fmt_force(M_max)}m, V_max={fmt_force(V_max)}")
        outer=tk.Frame(self.beam_plots_frame,bg=BORDER); outer.pack(fill="x")
        inner=tk.Frame(outer,bg=BG2); inner.pack(fill="x",padx=1,pady=1)
        diag_title = "Plate Diagrams \u2014 SFD / BMD / Deflection" if self.m2_member.get() == "plate" else "Beam Diagrams \u2014 SFD / BMD / Deflection"
        tk.Label(inner,text=diag_title,font=FONT_H,fg=TEXT,bg=BG2,anchor="w").pack(fill="x",padx=12,pady=(10,4))
        tk.Frame(inner,bg=BORDER,height=1).pack(fill="x",padx=12)
        sr=tk.Frame(inner,bg=BG2); sr.pack(fill="x",padx=12,pady=(6,4))
        for lbl,val in [("s_max",f"{fmt_stress_mpa(_from_mpa(sigma/1e6,self._us))}"),
                        ("t_max",f"{fmt_stress_mpa(_from_mpa(tau/1e6,self._us))}"),
                        ("M_max",f"{fmt_force(M_max)}m"),("V_max",f"{fmt_force(V_max)}")]:
            col=tk.Frame(sr,bg=BG3); col.pack(side="left",padx=(0,8),pady=2)
            tk.Label(col,text=lbl,font=FONT_S,fg=TEXT2,bg=BG3).pack(padx=10,pady=(4,0))
            tk.Label(col,text=val,font=FONT_B,fg=TEXT,bg=BG3).pack(padx=10,pady=(0,4))
        pc=tk.Frame(inner,bg=BG2); pc.pack(fill="x",padx=12,pady=(4,10))
        draw_beam_plots(pc,x,M,V,y_raw,EI,L,load_type,a)

    def _run_module2(self):
        for w in self.m2_result_frame.winfo_children(): w.destroy()
        for w in self.m2_mohr_frame.winfo_children(): w.destroy()
        self._m2_ai_card.show_loading()
        try:
            member=self.m2_member.get()
            sigma=self._read_stress(self.m2_sigma)*1e6
            tau=self._read_stress(self.m2_tau)*1e6
            sy=self._read_stress(self.m2_sy)*1e6
            su=self._read_stress(self.m2_su)*1e6
        except ValueError:
            messagebox.showerror("Input Error","Enter valid numbers in all stress fields."); return
        try:
            sf_target=float(self.m2_sf_target.get())
            if sf_target<=0: raise ValueError
        except ValueError:
            messagebox.showerror("Input Error","Target Safety Factor must be > 0."); return
        if not self._validate_stress(sigma/1e6,"sigma"): return
        if not self._validate_stress(tau/1e6,"tau"): return
        if not self._validate_stress(sy/1e6,"sy"): return
        if not self._validate_stress(su/1e6,"su"): return
        lo,hi,_=RANGES_SI["sf"]
        if not (lo<=sf_target<=hi):
            messagebox.showerror("Validation Error",f"Target SF {sf_target} outside valid range ({lo}\u2013{hi})."); return
        if su<=sy:
            messagebox.showerror("Validation Error","Su must be greater than Sy."); return
        self.set_status("Running Module 2 \u2014 Random Forest Stress Classification...",busy=True)
        try: result=predict_risk(member,sigma,tau,sy,su)
        except Exception as ex:
            messagebox.showerror("Error",str(ex)); self.set_status("Module 2 Failed."); return
        self.m2_last_result=result; self.m2_last_sf_target=sf_target
        risk=result["Risk Category"]; color=RISK_COLORS.get(risk,TEXT2)
        conf=result["Confidence (%)"]; vm=result["Von Mises Stress (Pa)"]
        ratio=result["Stress Ratio (\u03c3_vm/Sy)"]
        sf=sy/vm if vm>0 else float("inf"); sf_pass=sf>=sf_target; allow_vm=sy/sf_target
        sf_label="SF Check: PASS" if sf_pass else "SF Check: FAIL"
        sf_color="#666666" if sf_pass else "#333333"
        sl=_stress_label(self._us)
        br=tk.Frame(self.m2_result_frame,bg=BG2); br.pack(fill="x",pady=(0,4))
        tk.Label(br,text=risk,font=("Segoe UI",13,"bold"),fg=BG2,bg=color,padx=16,pady=8).pack(side="left")
        tk.Label(br,text=f"  Certainty: {conf}%",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left",padx=12)
        tk.Label(br,text=sf_label,font=("Segoe UI",11,"bold"),fg=TEXT,bg=sf_color,padx=12,pady=8).pack(side="left",padx=(16,0))
        sf_str="inf" if vm==0 else f"{sf:.{_p()}g}"
        tk.Label(br,text=f"  SF={sf_str}  /  target {sf_target:.1f}",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left",padx=6)
        tk.Label(self.m2_result_frame,text=RISK_DESCRIPTIONS.get(risk,""),font=FONT_S,fg=TEXT2,bg=BG2,anchor="w").pack(fill="x",pady=(0,4))
        divider(self.m2_result_frame)
        p2=_p()
        vm_disp=fmt_stress_mpa(_from_mpa(vm/1e6,self._us))
        sy_disp=fmt_stress_mpa(_from_mpa(sy/1e6,self._us))
        allow_disp=fmt_stress_mpa(_from_mpa(allow_vm/1e6,self._us))
        # FIX: display "Plate" not "Plate" aliased as "Beam" in member label
        member_display = member.capitalize()
        metrics=[("s_vm",vm_disp),("Yield Sy",sy_disp),("s_vm / Sy",f"{ratio:.{p2}g}"),("Allowable s_vm",allow_disp),("Member",member_display)]
        mg=tk.Frame(self.m2_result_frame,bg=BG2); mg.pack(fill="x")
        for i,(lbl,val) in enumerate(metrics):
            col=tk.Frame(mg,bg=BG3); col.grid(row=0,column=i,padx=(0,8),pady=4,sticky="ew")
            mg.columnconfigure(i,weight=1)
            tk.Label(col,text=lbl,font=FONT_S,fg=TEXT2,bg=BG3,anchor="w").pack(fill="x",padx=8,pady=(6,0))
            tk.Label(col,text=val,font=FONT_B,fg=TEXT,bg=BG3,anchor="w").pack(fill="x",padx=8,pady=(0,6))
        sf_c=TEXT if sf>=2 else TEXT2 if sf>=1 else "#555555"
        sf_f=tk.Frame(self.m2_result_frame,bg=BG2); sf_f.pack(fill="x",pady=(8,0))
        tk.Label(sf_f,text=f"Safety Factor (Sy / s_vm): {sf_str}  |  target {sf_target:.{_p()}g}",font=FONT_B,fg=sf_c,bg=BG2).pack(anchor="w")
        if not sf_pass:
            deficit=fmt_stress_mpa(_from_mpa((vm-allow_vm)/1e6,self._us))
            tk.Label(sf_f,text=f"[!] s_vm exceeds allowable by {deficit} (allowable = Sy/SF_target = {allow_disp})",font=FONT_S,fg=TEXT2,bg=BG2,anchor="w").pack(fill="x",pady=(2,0))
        else:
            margin=fmt_stress_mpa(_from_mpa((allow_vm-vm)/1e6,self._us))
            tk.Label(sf_f,text=f"s_vm is {margin} below allowable \u2014 margin satisfied.",font=FONT_S,fg=TEXT2,bg=BG2,anchor="w").pack(fill="x",pady=(2,0))
        warns=[]; suggs=RISK_SUGGESTIONS.get(risk,[])
        if sf<1: warns.append(f"SF={sf:.2f} \u2014 component will fail under this load.")
        elif sf<sf_target: warns.append(f"SF={sf:.2f} \u2014 below target of {sf_target:.1f}.")
        if risk!="Safe" and hasattr(self,"m1_last_results") and self.m1_last_results:
            top=self.m1_last_results[0]
            warns.append(f"M1 top: '{top['Material']}' (Sy={fmt_stress_mpa(top['Yield Strength (MPa)'])}). Consider #2 or #3 for higher strength.")
        warning_box(self.m2_result_frame,warns,suggs)
        draw_mohrs_circle(self.m2_mohr_frame,sigma,tau,sy,su)
        try:
            tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False); tmp.close()
            self._mohr_png=tmp.name
            render_mohrs_circle_to_png(sigma,tau,sy,su,self._mohr_png)
        except Exception: self._mohr_png=None
        self.set_status(f"Module 2 Complete \u2014 {risk} | {sf_label}")
        self._update_summary_m2(result)
        if hasattr(self,"m1_last_results") and self.m1_last_results:
            m2_inputs={"sigma_mpa":sigma/1e6,"sf_target":sf_target}
            sugg=compute_suggested_m3_inputs(self.m1_last_results,m2_inputs=m2_inputs)
            if sugg:
                cat   = self._m3_machine_cat.get()
                model = self._m3_machine_model.get()
                specs = MACHINE_SPECS.get(cat, {}).get(model)
                if specs:
                    cap_speed  = min(sugg["speed_mmin"], specs["max_speed_mmin"])
                    D_mm       = sugg.get("D_mm", specs.get("typical_dia_mm", 50))
                    cap_rpm    = round((cap_speed * 1000) / (3.14159 * D_mm))
                    cap_rpm    = max(specs["min_rpm"], min(cap_rpm, specs["max_rpm"]))
                    cap_torque = min(sugg["torque_nm"], specs["max_torque_nm"])
                else:
                    cap_speed  = sugg["speed_mmin"]
                    cap_rpm    = sugg["rpm"]
                    cap_torque = sugg["torque_nm"]
                try: self.m3_speed.set_from_base(cap_speed)
                except Exception: pass
                try: self.m3_feed.set_from_base(sugg["feed_mmrev"])
                except Exception: pass
                try: self.m3_depth.set_from_base(sugg["depth_mm"]/1000.0)
                except Exception: pass
                try: self.m3_rpm.set_from_base(cap_rpm)
                except Exception: pass
                try: self.m3_torque.set_from_base(cap_torque)
                except Exception: pass
        ctx={"type":"stress","risk":risk,"member":member,"vm_mpa":vm/1e6,"sy_mpa":sy/1e6,"sf":sf,"sf_target":sf_target}
        get_ai_suggestion(ctx,self._api_key_var.get(),lambda r:self.after(0,lambda:self._m2_ai_card.show_result(r)))

    # ── Module 3 ──────────────────────────────────────────────────────────
    def _build_module3(self):
        scroll = _ScrollFrame(self.tab3); scroll.pack(fill="both", expand=True)
        p = scroll.inner

        mach_card = card(p, "Machine Tool")
        mach_card.columnconfigure(1, weight=1); mach_card.columnconfigure(3, weight=1)

        categories = list(MACHINE_SPECS.keys())
        self._m3_machine_cat = styled_combo(mach_card, categories, width=22)
        self._m3_machine_cat.bind("<<ComboboxSelected>>", self._on_machine_category_change)
        tk.Label(mach_card, text="Machine Category", font=FONT, fg=TEXT2, bg=BG2).grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=5)
        self._m3_machine_cat.grid(row=0, column=1, sticky="ew", pady=5)

        first_cat    = categories[0]
        first_models = list(MACHINE_SPECS[first_cat].keys())
        self._m3_machine_model = styled_combo(mach_card, first_models, width=22)
        self._m3_machine_model.bind("<<ComboboxSelected>>", self._on_machine_model_change)
        tk.Label(mach_card, text="Machine Model", font=FONT, fg=TEXT2, bg=BG2).grid(
            row=0, column=2, sticky="w", padx=(16, 12), pady=5)
        self._m3_machine_model.grid(row=0, column=3, sticky="ew", pady=5)

        self._m3_spec_var = tk.StringVar(value="Select a machine model to see specifications.")
        tk.Label(mach_card, textvariable=self._m3_spec_var, font=FONT_S, fg=TEXT2, bg=BG2,
                 anchor="w", wraplength=900, justify="left").grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 2))

        ToolTip(self._m3_machine_cat,
                "Machine category.\nAffects: speed cap, RPM cap, torque cap, workpiece size check.")
        ToolTip(self._m3_machine_model,
                "Specific machine model.\nSpecs auto-cap M3 inputs to machine limits when M1 is run.")

        self._on_machine_model_change()

        inp = card(p, "Machining Parameters"); inp.columnconfigure(1, weight=1)
        self.m3_type     = styled_combo(inp, ["L", "M", "H"])
        self.m3_tool_mat = styled_combo(inp, ["HSS", "Carbide", "Ceramic", "CBN"])
        self.m3_tool_mat.current(1)
        self.m3_air   = UnitEntry(inp, TEMP_UNITS, "K", {"K":1,"C":1,"F":1}, {"K":1,"C":1,"F":1}, entry_width=8)
        self.m3_proc  = UnitEntry(inp, TEMP_UNITS, "K", {"K":1,"C":1,"F":1}, {"K":1,"C":1,"F":1}, entry_width=8)
        self.m3_rpm   = make_rpm_entry(inp,   entry_width=8)
        self.m3_torque= make_torque_entry(inp, entry_width=8)
        self.m3_speed = make_speed_entry(inp,  entry_width=8)
        self.m3_feed  = make_feed_entry(inp,   entry_width=8)
        self.m3_depth = UnitEntry(inp, ["mm","cm","m","in"], "mm",
                                  {"mm":0.001,"cm":0.01,"m":1.0,"in":0.0254},
                                  {"mm":1000.0,"cm":100.0,"m":1.0,"in":39.3701}, entry_width=8)
        field_row(inp, "Workpiece Grade (Low/Medium/High)", self.m3_type,      0)
        field_row(inp, "Tool Material",           self.m3_tool_mat,   1)
        field_row(inp, "Air Temperature",         self.m3_air,        2)
        field_row(inp, "Process Temperature",     self.m3_proc,       3)
        field_row(inp, "Rotational Speed",        self.m3_rpm,        4)
        field_row(inp, "Cutting Torque",          self.m3_torque,     5)
        field_row(inp, "Base Cutting Speed",      self.m3_speed,      6)
        field_row(inp, "Base Feed Rate",          self.m3_feed,       7)
        field_row(inp, "Base Depth of Cut",       self.m3_depth,      8)
        bind_arrow_keys([self.m3_air, self.m3_proc, self.m3_rpm, self.m3_torque,
                         self.m3_speed, self.m3_feed, self.m3_depth])

        ToolTip(self.m3_type,
                "Workpiece hardness grade (auto-filled from M1).\n"
                "  L=soft: Al, mild steel\n  M=medium: alloy steel, stainless\n"
                "  H=hard: hardened steel, Inconel")
        ToolTip(self.m3_tool_mat,
                "Cutting tool material.\n  HSS: v < 30 m/min\n"
                "  Carbide: 80\u2013200 m/min\n  Ceramic: > 200 m/min\n  CBN: hardened steels")
        ToolTip(self.m3_air,
                "Ambient temperature.\n  20C=293K | 25C=298K\n  Must be > 273 K")
        ToolTip(self.m3_proc,
                "Cutting zone temperature.\n  HSS: 350\u2013500K | Carbide: 500\u2013700K | Ceramic: 700\u20131000K\n"
                "  Use 450K if unknown. Must be > air temp.")
        ToolTip(self.m3_rpm,
                "Spindle speed.\nAuto-capped to selected machine max RPM.\n  Valid: 100\u20135000 rpm")
        ToolTip(self.m3_torque,
                "Cutting torque.\nAuto-capped to machine max torque.\n  Valid: 0\u2013200 Nm")
        ToolTip(self.m3_speed,
                "Base cutting speed.\nAuto-capped to machine max speed.\n"
                "  Advisory gives 0.8x/1.0x/1.2x modes.\n  Valid: 0\u2013500 m/min")
        ToolTip(self.m3_feed,
                "Feed per revolution (auto-computed from M1).\n"
                "  Roughing: 0.2\u20130.5 | Finishing: 0.05\u20130.15 mm/rev\n  Valid: 0.01\u20132.0 mm/rev")
        ToolTip(self.m3_depth,
                "Depth of cut (auto-computed from M1).\n"
                "  Roughing: 2\u20135mm | Finishing: 0.1\u20130.5mm\n  Valid: 0.1\u201320 mm")

        self.m3_tool_desc_var = tk.StringVar(); self._update_tool_desc()
        self.m3_tool_mat.bind("<<ComboboxSelected>>", lambda e: self._update_tool_desc())
        tk.Label(inp, textvariable=self.m3_tool_desc_var, font=FONT_S, fg=TEXT2, bg=BG2,
                 anchor="w", wraplength=500, justify="left").grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(0, 4))
        tk.Label(inp,
                 text="Speed / RPM / Feed / Depth auto-computed (capped to machine limits) when Module 1 is run.",
                 font=FONT_S, fg=AI_REC_FG, bg=BG2).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(0, 4))

        bf = tk.Frame(inp, bg=BG2); bf.grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Get Advisory", self._run_module3).pack(side="left")

        self.m3_result_frame   = card(p, "Cutting Condition Advisory")
        self.m3_toollife_frame = card(p, "Tool Life Curve")
        _ai_body_m3 = card(p, "AI / Suggestion")
        self._m3_ai_card = SmartSuggestionCard(_ai_body_m3, self)
        self._m3_ai_card.pack(fill="x")

    def _on_machine_category_change(self, event=None):
        cat = self._m3_machine_cat.get()
        models = list(MACHINE_SPECS.get(cat, {}).keys())
        self._m3_machine_model["values"] = models
        if models:
            self._m3_machine_model.current(0)
        self._on_machine_model_change()

    def _on_machine_model_change(self, event=None):
        cat   = self._m3_machine_cat.get()
        model = self._m3_machine_model.get()
        specs = MACHINE_SPECS.get(cat, {}).get(model)
        if not specs:
            self._m3_spec_var.set("No spec data.")
            return
        dia_key   = "swing_mm" if "swing_mm" in specs else "table_mm"
        dia_val   = specs.get(dia_key, "—")
        dia_label = f"Swing: {dia_val} mm" if "swing_mm" in specs else f"Table: {dia_val} mm"
        spec_str  = (
            f"Max RPM: {specs['max_rpm']}  |  "
            f"Max Torque: {specs['max_torque_nm']} Nm  |  "
            f"Power: {specs['power_kw']} kW  |  "
            f"Max Speed: {specs['max_speed_mmin']} m/min  |  "
            f"Max Dia: {specs['max_workpiece_dia_mm']} mm  |  "
            f"{dia_label}"
        )
        self._m3_spec_var.set(spec_str)
        self._autofill_m3_from_machine(specs)

    def _autofill_m3_from_machine(self, specs):
        if not hasattr(self, "m1_last_results") or not self.m1_last_results:
            return
        m2_inputs = None
        if hasattr(self, "m2_last_result"):
            try:
                m2_inputs = {
                    "sigma_mpa": self._read_stress(self.m2_sigma),
                    "sf_target": getattr(self, "m2_last_sf_target", 2.0),
                }
            except Exception:
                pass
        sugg = compute_suggested_m3_inputs(self.m1_last_results, m2_inputs=m2_inputs)
        if not sugg:
            return
        raw_speed  = sugg["speed_mmin"]
        cap_speed  = min(raw_speed, specs["max_speed_mmin"])
        D_mm       = sugg.get("D_mm", specs.get("typical_dia_mm", 50))
        cap_rpm    = round((cap_speed * 1000) / (3.14159 * D_mm))
        cap_rpm    = max(specs["min_rpm"], min(cap_rpm, specs["max_rpm"]))
        cap_torque = min(sugg["torque_nm"], specs["max_torque_nm"])
        try: self.m3_speed.set_from_base(cap_speed)
        except Exception: pass
        try: self.m3_rpm.set_from_base(cap_rpm)
        except Exception: pass
        try: self.m3_torque.set_from_base(cap_torque)
        except Exception: pass
        try: self.m3_feed.set_from_base(sugg["feed_mmrev"])
        except Exception: pass
        try: self.m3_depth.set_from_base(sugg["depth_mm"] / 1000.0)
        except Exception: pass

    def _update_tool_desc(self):
        self.m3_tool_desc_var.set(TOOL_DESCRIPTIONS.get(self.m3_tool_mat.get(),""))

    def _run_module3(self):
        for w in self.m3_result_frame.winfo_children():   w.destroy()
        for w in self.m3_toollife_frame.winfo_children(): w.destroy()
        self._m3_ai_card.show_loading()

        try:
            tg    = self.m3_type.get(); tool_mat = self.m3_tool_mat.get()
            air   = temp_to_K(float(self.m3_air.get()),  self.m3_air._unit_var.get())
            proc  = temp_to_K(float(self.m3_proc.get()), self.m3_proc._unit_var.get())
            rpm   = int(self.m3_rpm.get_base()); torq = self.m3_torque.get_base()
            spd   = self.m3_speed.get_base();    feed = self.m3_feed.get_base()
            depth = self.m3_depth.get_base() * 1000.0
        except ValueError:
            messagebox.showerror("Input Error", "Enter valid numbers in all fields."); return

        if air  <= 273: messagebox.showerror("Validation Error", "Air temperature must be > 273 K."); return
        if proc <= air: messagebox.showerror("Validation Error", "Process temperature must be > air temperature."); return
        if not (100 <= rpm  <= 5000): messagebox.showerror("Validation Error", "RPM must be 100\u20135000."); return
        if not (0   <  torq <= 200):  messagebox.showerror("Validation Error", "Torque must be 0\u2013200 Nm."); return
        if not (0   <  spd  <= 500):  messagebox.showerror("Validation Error", "Cutting speed must be 0\u2013500 m/min."); return
        if not (0.01<= feed <= 2.0):  messagebox.showerror("Validation Error", "Feed rate must be 0.01\u20132.0 mm/rev."); return
        if not (0.1 <= depth<= 20):   messagebox.showerror("Validation Error", "Depth of cut must be 0.1\u201320 mm."); return

        cat   = self._m3_machine_cat.get()
        model = self._m3_machine_model.get()
        specs = MACHINE_SPECS.get(cat, {}).get(model)
        machine_warnings = []

        if specs:
            if spd > specs["max_speed_mmin"]:
                machine_warnings.append(
                    f"Speed {spd} m/min exceeds {model} max ({specs['max_speed_mmin']} m/min). "
                    f"Reduce speed or select a higher-capacity machine.")
            if torq > specs["max_torque_nm"]:
                machine_warnings.append(
                    f"Torque {torq:.1f} Nm exceeds {model} max ({specs['max_torque_nm']} Nm). "
                    f"Reduce depth/feed or select a larger machine.")
            if rpm > specs["max_rpm"]:
                machine_warnings.append(
                    f"RPM {rpm} exceeds {model} max ({specs['max_rpm']} rpm). "
                    f"Reduce cutting speed or increase workpiece diameter.")
            if hasattr(self, "m1_last_results") and self.m1_last_results:
                sugg_chk = compute_suggested_m3_inputs(self.m1_last_results)
                if sugg_chk:
                    D_mm = sugg_chk.get("D_mm", specs.get("typical_dia_mm", 50))
                    if D_mm > specs["max_workpiece_dia_mm"]:
                        machine_warnings.append(
                            f"Estimated workpiece dia {D_mm:.0f} mm exceeds {model} capacity "
                            f"({specs['max_workpiece_dia_mm']} mm). Select a larger machine.")
            recommended_cats = GRADE_MACHINE_RECOMMENDATION.get(tg, [])
            if cat not in recommended_cats:
                machine_warnings.append(
                    f"Grade {tg} material on {cat}: may lack rigidity. "
                    f"Recommended: {', '.join(recommended_cats)}.")

        self.set_status("Running Module 3 \u2014 Taylor Tool Life + Failure Classifier...", busy=True)
        try:
            results = get_advisory(tg, air, proc, rpm, torq, spd, feed, depth, tool_material=tool_mat)
        except Exception as ex:
            messagebox.showerror("Error", str(ex)); self.set_status("Module 3 Failed."); return
        self.m3_last_results = results

        if machine_warnings:
            warning_box(self.m3_result_frame, machine_warnings, [])

        mc = {"Conservative": "#cccccc", "Balanced": "#999999", "Aggressive": "#555555"}
        for r in results:
            mode = r["Mode"]; color = mc.get(mode, TEXT2)
            row  = tk.Frame(self.m3_result_frame, bg=BG3); row.pack(fill="x", pady=(0,8))
            tk.Label(row, text=f"  {mode}  ", font=FONT_B, fg=BG2, bg=color).pack(side="left")
            info = tk.Frame(row, bg=BG3); info.pack(side="left", fill="x", expand=True, padx=10, pady=6)
            tk.Label(info,
                     text=f"Speed: {r['speed (m/min)']} m/min  |  Feed: {r['feed (mm/rev)']} mm/rev  |  Depth: {r['depth (mm)']} mm",
                     font=FONT_B, fg=TEXT, bg=BG3, anchor="w").pack(fill="x")
            tl   = r["tool_life (min)"]; tl_str = fmt_time(tl)
            fc   = "#555555" if r["Failure Risk"] == "Yes" else TEXT2
            tk.Label(info,
                     text=f"Tool Life: {tl_str}  |  Failure Risk: {r['Failure Risk']}  |  Confidence: {r['Confidence (%)']:.1f}%",
                     font=FONT_S, fg=fc, bg=BG3, anchor="w").pack(fill="x")
            if r["Warnings"] or r["Suggestions"]:
                warning_box(info, r["Warnings"], r["Suggestions"])

        if specs:
            mf = tk.Frame(self.m3_result_frame, bg=BG2); mf.pack(fill="x", pady=(4,0))
            tk.Label(mf,
                     text=f"Machine: {model}  |  Max RPM: {specs['max_rpm']}  |  "
                          f"Max Speed: {specs['max_speed_mmin']} m/min  |  "
                          f"Max Torque: {specs['max_torque_nm']} Nm",
                     font=FONT_S, fg=TEXT2, bg=BG2, anchor="w").pack(fill="x")

        n_val = results[0]["n"]; C_val = results[0]["C"]
        draw_tool_life_curve(self.m3_toollife_frame, spd, n_val, C_val)
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False); tmp.close()
            self._toollife_png = tmp.name
            render_tool_life_curve_to_png(spd, n_val, C_val, self._toollife_png)
        except Exception: self._toollife_png = None

        self.set_status("Module 3 Complete \u2014 Advisory Generated.")
        self._update_summary_m3(results)
        bal = next((r for r in results if r["Mode"] == "Balanced"), results[0])
        ctx = {
            "type": "machining", "grade": tg, "tool_mat": tool_mat,
            "speed": bal["speed (m/min)"], "feed": bal["feed (mm/rev)"],
            "depth": bal["depth (mm)"],    "tool_life": bal["tool_life (min)"],
            "n": n_val, "C": C_val,
        }
        get_ai_suggestion(ctx, self._api_key_var.get(),
                          lambda r: self.after(0, lambda: self._m3_ai_card.show_result(r)))

    # ── Summary ───────────────────────────────────────────────────────────
    def _build_summary(self):
        export_bar=tk.Frame(self.tab4,bg="#0a0a0a",height=40)
        export_bar.pack(fill="x"); export_bar.pack_propagate(False)
        tk.Label(export_bar,text="Export Engineering Report as PDF",font=FONT_S,fg=TEXT2,bg="#0a0a0a").pack(side="left",padx=14)
        action_btn(export_bar,"Export PDF",self._export_pdf).pack(side="right",padx=14,pady=6)
        scroll=_ScrollFrame(self.tab4); scroll.pack(fill="both",expand=True)
        self.sum_inner=scroll.inner
        styled_label(self.sum_inner,"Run all three modules to see the unified summary here.",fg=TEXT2,bg=BG).pack(pady=40)

    def _export_pdf(self):
        m1_done=hasattr(self,"m1_last_results") and self.m1_last_results
        m2_done=hasattr(self,"m2_last_result")
        m3_done=hasattr(self,"m3_last_results") and self.m3_last_results
        if not (m1_done or m2_done or m3_done):
            messagebox.showwarning("Nothing to Export","Run at least one module before exporting."); return
        tb_project=getattr(self._tb_project,"get",lambda:"")() if hasattr(self,"_tb_project") else ""
        tb_engineer=getattr(self._tb_engineer,"get",lambda:"")() if hasattr(self,"_tb_engineer") else ""
        tb_institution=getattr(self._tb_institution,"get",lambda:"")() if hasattr(self,"_tb_institution") else ""
        tb_revision=getattr(self._tb_revision,"get",lambda:"")() if hasattr(self,"_tb_revision") else ""
        key_filled=all([tb_project.strip(),tb_engineer.strip(),tb_institution.strip(),tb_revision.strip()])
        if key_filled:
            meta={"project_name":tb_project,"engineer":tb_engineer,"institution":tb_institution,"company":"","revision":tb_revision,"notes":""}
        else:
            dlg=PDFMetaDialog(self); self.wait_window(dlg)
            if dlg.result is None: return
            meta=dlg.result
            if hasattr(self,"_tb_project") and meta.get("project_name"): self._tb_project.set(meta["project_name"])
            if hasattr(self,"_tb_engineer") and meta.get("engineer"): self._tb_engineer.set(meta["engineer"])
            if hasattr(self,"_tb_institution") and meta.get("institution"): self._tb_institution.set(meta["institution"])
            if hasattr(self,"_tb_revision") and meta.get("revision"): self._tb_revision.set(meta["revision"])
        init_name=(meta.get("project_name","MechAssist_Report").replace(" ","_").replace("/","-"))+".pdf"
        filepath=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF files","*.pdf")],initialfile=init_name,title="Save Engineering Report")
        if not filepath: return
        self.set_status("Generating PDF Report...",busy=True)
        lines=[]
        if m1_done:
            r=self.m1_last_results[0]
            lines.append(f"Material selected: {r['Material']} (Sy={fmt_stress_mpa(r['Yield Strength (MPa)'])}, concern: {r['Failure Concern']}).")
        if m2_done:
            r=self.m2_last_result; vm=r["Von Mises Stress (Pa)"]
            sy_pa=self._read_stress(self.m2_sy)*1e6 if self.m2_sy.get() else 1
            sf=sy_pa/vm if vm>0 else float("inf"); sf_s="inf" if sf==float("inf") else f"{sf:.2f}"
            sf_target=getattr(self,"m2_last_sf_target",2.0); sf_check="PASS" if sf>=sf_target else "FAIL"
            lines.append(f"Stress: {r['Risk Category']} at sigma_vm/Sy={r['Stress Ratio (\u03c3_vm/Sy)']:.3f} (SF={sf_s}, target={sf_target:.1f}, {sf_check}, certainty {r['Confidence (%)']:.1f}%).")
        if m3_done:
            bal=next((r for r in self.m3_last_results if r["Mode"]=="Balanced"),None)
            if bal:
                tl=bal["tool_life (min)"]
                lines.append(f"Machining: {bal.get('tool_material','Carbide')} at {bal['speed (m/min)']} m/min \u2014 tool life {fmt_time(tl)}, failure risk: {bal['Failure Risk']}.")
        data={"narrative":"  ".join(lines),"meta":meta}
        if m1_done:
            data["m1_results"]=self.m1_last_results
            try:
                data["m1_inputs"]={
                    "sy":float(self.m1_yield.get()) if self._m1_override_open and self.m1_yield.get().strip() else 0,
                    "ro":float(self.m1_dens.get()) if self.m1_dens.get().strip() else 0,
                    "a5":float(self.m1_elong.get()) if self._m1_override_open and self.m1_elong.get().strip() else 0,
                    "sy_mpa":self._read_stress(self.m1_yield) if self._m1_override_open and self.m1_yield.get().strip() else 0,
                    "ro_kgm3":self._read_density(self.m1_dens) if self.m1_dens.get().strip() else 0,
                    "unit_sys":self._us,
                }
            except Exception: pass
        if m2_done:
            data["m2_result"]=self.m2_last_result
            try:
                data["m2_inputs"]={"member":self.m2_member.get(),
                    "sigma_mpa":self._read_stress(self.m2_sigma),"tau_mpa":self._read_stress(self.m2_tau),
                    "sy_mpa":self._read_stress(self.m2_sy),"su_mpa":self._read_stress(self.m2_su),
                    "sf_target":getattr(self,"m2_last_sf_target",2.0)}
            except Exception: pass
            if self._mohr_png and os.path.exists(self._mohr_png): data["mohr_png"]=self._mohr_png
        if m3_done:
            data["m3_results"]=self.m3_last_results
            try:
                data["m3_inputs"]={"grade":self.m3_type.get(),"tool_mat":self.m3_tool_mat.get(),
                    "air":float(self.m3_air.get()),"proc":float(self.m3_proc.get()),
                    "rpm":int(self.m3_rpm.get_base()),"torque":self.m3_torque.get_base(),
                    "speed":self.m3_speed.get_base(),"feed":self.m3_feed.get_base(),
                    "depth":self.m3_depth.get_base()*1000.0}
            except Exception: pass
            if self._toollife_png and os.path.exists(self._toollife_png): data["toollife_png"]=self._toollife_png
        try:
            export_report(data,filepath)
            self.set_status(f"PDF Exported: {os.path.basename(filepath)}")
            messagebox.showinfo("Export Complete",f"Report saved to:\n{filepath}")
        except Exception as ex:
            messagebox.showerror("Export Failed",str(ex)); self.set_status("PDF Export Failed.")

    def _update_summary_m1(self,results): self._rebuild_summary()
    def _update_summary_m2(self,result):  self._rebuild_summary()
    def _update_summary_m3(self,results): self._rebuild_summary()

    def _rebuild_summary(self):
        for w in self.sum_inner.winfo_children(): w.destroy()
        from datetime import datetime
        m1_done=hasattr(self,"m1_last_results") and self.m1_last_results
        m2_done=hasattr(self,"m2_last_result")
        m3_done=hasattr(self,"m3_last_results") and self.m3_last_results
        sl=_stress_label(self._us); dl=_density_label(self._us)

        tb=card(self.sum_inner,"Engineering Report \u2014 Title Block")
        tb.columnconfigure(1,weight=1); tb.columnconfigure(3,weight=1)
        now=datetime.now().strftime("%Y-%m-%d  %H:%M")
        if not hasattr(self,"_tb_project"):
            self._tb_project=tk.StringVar(value="MechAssist Engineering Analysis")
            self._tb_engineer=tk.StringVar(value="Monjyeeman Dutta")
            self._tb_institution=tk.StringVar(value="Jorhat Engineering College")
            self._tb_revision=tk.StringVar(value="Rev 1.0")
        ent_kw=dict(bg=BG3,fg=TEXT,insertbackground=ACCENT,relief="flat",font=FONT,highlightthickness=1,highlightbackground=BORDER,highlightcolor=ACCENT2)
        for row_i,(label,var,width) in enumerate([("Project",self._tb_project,30),("Engineer",self._tb_engineer,30),("Institution",self._tb_institution,30),("Revision",self._tb_revision,12)]):
            col=(row_i%2)*2; r=row_i//2
            tk.Label(tb,text=label+":",font=FONT_S,fg=TEXT2,bg=BG2).grid(row=r,column=col,sticky="w",padx=(0,6),pady=3)
            tk.Entry(tb,textvariable=var,width=width,**ent_kw).grid(row=r,column=col+1,sticky="ew",padx=(0,16),pady=3)
        tk.Label(tb,text=f"Date: {now}   |   Tool: MechAssist v1.0",font=FONT_S,fg=TEXT2,bg=BG2).grid(row=2,column=0,columnspan=4,sticky="w",pady=(4,0))

        if m1_done:
            dr=card(self.sum_inner,"2. Design Requirements"); dr.columnconfigure(1,weight=1)
            reqs=[("Member Type",self.m1_member.get().capitalize())]
            if m2_done: reqs+=[("Target Safety Factor",str(getattr(self,"m2_last_sf_target",2.0)))]
            for j,(k,v) in enumerate(reqs):
                tk.Label(dr,text=k+":",font=FONT_S,fg=TEXT2,bg=BG2).grid(row=j,column=0,sticky="w",padx=(0,8),pady=2)
                tk.Label(dr,text=v,font=FONT_B,fg=TEXT,bg=BG2).grid(row=j,column=1,sticky="w",pady=2)

        if m1_done:
            cm=card(self.sum_inner,"3. Candidate Materials")
            hdr_cols=["Rank","Material",f"Sy ({sl})",f"Density ({dl})","Elong (%)","Failure Concern"]
            hdr_widths=[5,30,10,14,9,22]
            hdr_row=tk.Frame(cm,bg=BG3); hdr_row.pack(fill="x",pady=(0,2))
            for ct,w in zip(hdr_cols,hdr_widths):
                tk.Label(hdr_row,text=ct,font=FONT_B,fg=TEXT,bg=BG3,anchor="w",width=w).pack(side="left",padx=4,pady=4)
            for i,r in enumerate(self.m1_last_results):
                dr_row=tk.Frame(cm,bg=BG2 if i%2==0 else BG3); dr_row.pack(fill="x",pady=1)
                sy_d=_from_mpa(r["Yield Strength (MPa)"],self._us)
                ro_d=_from_kgm3(r["Density (kg/m\u00b3)"],self._us)
                rank_c=[TEXT,ACCENT2,"#888888"][i%3]
                vals=[(f"#{i+1}",rank_c),(r["Material"],TEXT),(f"{sy_d:.4g}",TEXT),(f"{ro_d:.4g}",TEXT),(str(r["Elongation (%)"]),TEXT),(r["Failure Concern"],TEXT2)]
                for (val,fg),w in zip(vals,hdr_widths):
                    tk.Label(dr_row,text=val,font=FONT_S,fg=fg,bg=dr_row["bg"],anchor="w",width=w).pack(side="left",padx=4,pady=3)

        if m1_done:
            sr=card(self.sum_inner,"4. Selection Rationale"); top=self.m1_last_results[0]
            sy_d=_from_mpa(top["Yield Strength (MPa)"],self._us)
            tk.Label(sr,text=f"Top material '{top['Material']}' selected: highest Sy ({sy_d:.4g} {sl}) meeting computed load requirement. Primary concern: {top['Failure Concern']}. Su estimated as 1.3 x Sy.",
                     font=FONT_S,fg=TEXT,bg=BG2,wraplength=900,justify="left").pack(fill="x")

        if m1_done:
            fm=card(self.sum_inner,"5. Failure Mode Analysis")
            fma={"Fracture":"Brittle fracture under overload. Avoid stress concentrations. Use SF >= 3.0.",
                 "Fatigue":"Cyclic crack growth. Limit sigma_vm < 0.45 x Sy. Surface finish Ra < 0.8 um.",
                 "Creep":"Time-dependent deformation at high temperature. T_operating < 0.4 x T_melting."}
            for r in self.m1_last_results:
                fc=r["Failure Concern"]
                key="Fracture" if "Fracture" in fc else "Fatigue" if "Fatigue" in fc else "Creep"
                rf=tk.Frame(fm,bg=BG3); rf.pack(fill="x",pady=(0,6))
                tk.Label(rf,text=f"  {r['Material']}  ",font=FONT_B,fg=BG2,bg=TEXT2).pack(side="left")
                df=tk.Frame(rf,bg=BG3); df.pack(side="left",padx=10,pady=4,fill="x",expand=True)
                tk.Label(df,text=fc,font=FONT_B,fg=TEXT2,bg=BG3,anchor="w").pack(fill="x")
                tk.Label(df,text=fma.get(key,""),font=FONT_S,fg=TEXT2,bg=BG3,anchor="w",wraplength=750,justify="left").pack(fill="x")

        if m2_done:
            sa=card(self.sum_inner,"6. Stress Analysis Summary")
            r=self.m2_last_result; risk=r["Risk Category"]; color=RISK_COLORS.get(risk,TEXT2)
            conf=r["Confidence (%)"]; ratio=r["Stress Ratio (\u03c3_vm/Sy)"]
            vm=r["Von Mises Stress (Pa)"]
            sy_pa=self._read_stress(self.m2_sy)*1e6 if self.m2_sy.get() else 1
            sf=sy_pa/vm if vm>0 else float("inf"); sf_s="inf" if sf==float("inf") else f"{sf:.3f}"
            sf_t=getattr(self,"m2_last_sf_target",2.0)
            sf_check="PASS" if sf>=sf_t else "FAIL"; sf_clr="#666666" if sf_check=="PASS" else "#333333"
            vm_d=fmt_stress_mpa(_from_mpa(vm/1e6,self._us)); allow_d=fmt_stress_mpa(_from_mpa(sy_pa/sf_t/1e6,self._us))
            br=tk.Frame(sa,bg=BG2); br.pack(fill="x",pady=(0,6))
            tk.Label(br,text=risk,font=FONT_B,fg=BG2,bg=color,padx=10,pady=4).pack(side="left")
            tk.Label(br,text=f"  SF Check: {sf_check}",font=FONT_B,fg=TEXT,bg=sf_clr,padx=10,pady=4).pack(side="left",padx=8)
            tk.Label(br,text=f"   Certainty: {conf:.1f}%  |  s_vm/Sy: {ratio:.4f}  |  SF: {sf_s}  |  Target: {sf_t:.1f}",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left")
            tk.Label(sa,text=f"s_vm: {vm_d}  |  Allowable (Sy/SF_target): {allow_d}  |  Sy: {fmt_stress_mpa(_from_mpa(sy_pa/1e6,self._us))}",font=FONT_S,fg=TEXT2,bg=BG2,anchor="w").pack(fill="x")
            if risk!="Safe":
                sugg=RISK_SUGGESTIONS.get(risk,[])
                if sugg: tk.Label(sa,text=f"-> {sugg[0]}",font=FONT_S,fg=TEXT2,bg=BG2,anchor="w",wraplength=900).pack(fill="x",pady=(4,0))

        if m3_done:
            mf=card(self.sum_inner,"7. Manufacturability")
            bal=next((r for r in self.m3_last_results if r["Mode"]=="Balanced"),None)
            if bal:
                tl=bal["tool_life (min)"]; tmat=bal.get("tool_material",self.m3_tool_mat.get()); fisk=bal["Failure Risk"]
                mr=tk.Frame(mf,bg=BG2); mr.pack(fill="x",pady=(0,6))
                for lbl,val,clr in [("Tool",tmat,TEXT),("Grade",self.m3_type.get(),TEXT),("Tool Life (Balanced)",fmt_time(tl),TEXT),("Failure Risk",fisk,TEXT2 if fisk=="Yes" else TEXT)]:
                    col=tk.Frame(mr,bg=BG3); col.pack(side="left",padx=(0,8))
                    tk.Label(col,text=lbl,font=FONT_S,fg=TEXT2,bg=BG3).pack(padx=8,pady=(4,0))
                    tk.Label(col,text=val,font=FONT_B,fg=clr,bg=BG3).pack(padx=8,pady=(0,4))
                mc={"Conservative":"#cccccc","Balanced":"#999999","Aggressive":"#555555"}
                for r in self.m3_last_results:
                    tl_r=r["tool_life (min)"]
                    rm=tk.Frame(mf,bg=BG2); rm.pack(fill="x",pady=2)
                    tk.Label(rm,text=f"{r['Mode']:12}",font=FONT_B,fg=mc.get(r["Mode"],TEXT2),bg=BG2).pack(side="left")
                    tk.Label(rm,text=f"Speed: {r['speed (m/min)']} m/min  |  Feed: {r['feed (mm/rev)']} mm/rev  |  Depth: {r['depth (mm)']} mm  |  Tool Life: {fmt_time(tl_r)}  |  Failure Risk: {r['Failure Risk']}",font=FONT_S,fg=TEXT2,bg=BG2).pack(side="left")

        if m1_done or m2_done or m3_done:
            cl=card(self.sum_inner,"8. Conclusion & Next Steps"); lines=[]
            if m1_done:
                top=self.m1_last_results[0]
                lines.append(f"Selected: {top['Material']} (Sy={fmt_stress_mpa(top['Yield Strength (MPa)'])}, concern: {top['Failure Concern']}).")
            if m2_done:
                r=self.m2_last_result; vm=r["Von Mises Stress (Pa)"]
                sy_pa=self._read_stress(self.m2_sy)*1e6 if self.m2_sy.get() else 1
                sf=sy_pa/vm if vm>0 else float("inf"); sf_s="inf" if sf==float("inf") else f"{sf:.3f}"
                sf_t=getattr(self,"m2_last_sf_target",2.0); sfck="PASS" if sf>=sf_t else "FAIL"
                lines.append(f"Stress: {r['Risk Category']}, SF={sf_s} (SF Check vs {sf_t:.1f}: {sfck}).")
                if r["Risk Category"]!="Safe":
                    sugg=RISK_SUGGESTIONS.get(r["Risk Category"],[])
                    if sugg: lines.append(f"Action: {sugg[0]}")
            if m3_done:
                bal=next((r for r in self.m3_last_results if r["Mode"]=="Balanced"),None)
                if bal:
                    tl=bal["tool_life (min)"]
                    lines.append(f"Machining: {bal.get('tool_material',self.m3_tool_mat.get())} at {bal['speed (m/min)']} m/min \u2014 life {fmt_time(tl)}.")
            lines.append("Verify all results with a qualified engineer before implementation.")
            for line in lines:
                tk.Label(cl,text=f"  ->  {line}",font=FONT_S,fg=TEXT,bg=BG2,wraplength=900,justify="left",anchor="w").pack(fill="x",pady=1)

        if not (m1_done or m2_done or m3_done):
            styled_label(self.sum_inner,"Run all three modules to see the unified summary here.",fg=TEXT2,bg=BG).pack(pady=40)


class _ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent,bg=BG)
        self._canvas=tk.Canvas(self,bg=BG,highlightthickness=0)
        sb=ttk.Scrollbar(self,orient="vertical",command=self._canvas.yview)
        self.inner=tk.Frame(self._canvas,bg=BG)
        self.inner.bind("<Configure>",lambda e:self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0,0),window=self.inner,anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left",fill="both",expand=True); sb.pack(side="right",fill="y")
        self._canvas.bind("<Enter>",self._bind_scroll); self._canvas.bind("<Leave>",self._unbind_scroll)
        self.inner.bind("<Enter>",self._bind_scroll); self.inner.bind("<Leave>",self._unbind_scroll)
    def _bind_scroll(self,event=None):
        self._canvas.bind_all("<MouseWheel>",lambda e:self._canvas.yview_scroll(-1*(e.delta//120),"units"))
    def _unbind_scroll(self,event=None):
        self._canvas.unbind_all("<MouseWheel>")


if __name__=="__main__":
    app=MechAssist()
    app.mainloop()