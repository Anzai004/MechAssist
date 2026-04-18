import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# ── Path Setup ─────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from modules.module1_material import recommend_materials
from modules.module2_stress import predict_risk
from modules.module3_machining import get_advisory

# ── Theme ──────────────────────────────────────────────────────────────────
BG         = "#0f1117"
BG2        = "#1a1d27"
BG3        = "#22263a"
ACCENT     = "#6c8ef5"
ACCENT2    = "#a78bfa"
SUCCESS    = "#34d399"
WARNING    = "#fbbf24"
DANGER     = "#f87171"
TEXT       = "#e2e8f0"
TEXT2      = "#94a3b8"
BORDER     = "#2e3347"
FONT       = ("Segoe UI", 10)
FONT_B     = ("Segoe UI", 10, "bold")
FONT_H     = ("Segoe UI", 13, "bold")
FONT_T     = ("Segoe UI", 16, "bold")
FONT_S     = ("Segoe UI", 9)

RISK_COLORS = {
    "Safe":          SUCCESS,
    "Yield Risk":    WARNING,
    "Fatigue Risk":  WARNING,
    "Fracture Risk": DANGER,
    "Buckling Risk": DANGER,
}

# ── Helpers ────────────────────────────────────────────────────────────────
def styled_label(parent, text, font=FONT, fg=TEXT, bg=None, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg,
                    bg=bg or parent["bg"], **kw)

def styled_entry(parent, width=18):
    e = tk.Entry(parent, width=width, bg=BG3, fg=TEXT,
                 insertbackground=TEXT, relief="flat",
                 font=FONT, highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACCENT)
    return e

def styled_combo(parent, values, width=16):
    cb = ttk.Combobox(parent, values=values, width=width,
                      font=FONT, state="readonly")
    cb.current(0)
    return cb

def card(parent, title, pady=10, padx=12):
    outer = tk.Frame(parent, bg=BORDER, bd=0)
    outer.pack(fill="x", padx=16, pady=(0, 12))
    inner = tk.Frame(outer, bg=BG2, bd=0)
    inner.pack(fill="x", padx=1, pady=1)
    tk.Label(inner, text=title, font=FONT_H, fg=ACCENT,
             bg=BG2, anchor="w").pack(fill="x", padx=padx, pady=(pady, 4))
    sep = tk.Frame(inner, bg=BORDER, height=1)
    sep.pack(fill="x", padx=padx)
    body = tk.Frame(inner, bg=BG2)
    body.pack(fill="x", padx=padx, pady=pady)
    return body

def field_row(parent, label, widget, row, col_offset=0):
    styled_label(parent, label, fg=TEXT2, bg=BG2).grid(
        row=row, column=col_offset, sticky="w", padx=(0, 8), pady=4)
    widget.grid(row=row, column=col_offset+1, sticky="w", pady=4)

def action_btn(parent, text, cmd, color=ACCENT):
    btn = tk.Button(parent, text=text, command=cmd,
                    bg=color, fg=BG, font=FONT_B,
                    relief="flat", cursor="hand2",
                    padx=20, pady=8,
                    activebackground=ACCENT2,
                    activeforeground=BG)
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT2))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn

def divider(parent):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=8)

# ── App ────────────────────────────────────────────────────────────────────
class MechAssist(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MechAssist — Engineering Decision Support")
        self.geometry("1100x820")
        self.minsize(900, 700)
        self.configure(bg=BG)
        self.resizable(True, True)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=BG3, background=BG3,
                        foreground=TEXT, selectbackground=ACCENT,
                        selectforeground=BG, borderwidth=0)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG3)],
                  foreground=[("readonly", TEXT)])

        self._build_header()
        self._build_body()
        self._build_statusbar()

    # ── Header ─────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=BG2, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  MechAssist", font=("Segoe UI", 17, "bold"),
                 fg=ACCENT, bg=BG2).pack(side="left", padx=20)
        tk.Label(hdr, text="Engineering Decision Support System",
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")
        tk.Label(hdr, text="v1.0",
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="right", padx=20)

    # ── Body ───────────────────────────────────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, pady=(8, 0))

        nb = ttk.Notebook(body)
        style = ttk.Style()
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG2, foreground=TEXT2,
                        font=FONT_B, padding=(16, 8))
        style.map("TNotebook.Tab",
                  background=[("selected", BG3)],
                  foreground=[("selected", ACCENT)])
        nb.pack(fill="both", expand=True, padx=8, pady=4)

        self.tab1 = tk.Frame(nb, bg=BG)
        self.tab2 = tk.Frame(nb, bg=BG)
        self.tab3 = tk.Frame(nb, bg=BG)
        self.tab4 = tk.Frame(nb, bg=BG)

        nb.add(self.tab1, text="  Module 1 — Material Selection  ")
        nb.add(self.tab2, text="  Module 2 — Stress Assessment  ")
        nb.add(self.tab3, text="  Module 3 — Machinability  ")
        nb.add(self.tab4, text="  Summary  ")

        self._build_module1()
        self._build_module2()
        self._build_module3()
        self._build_summary()

    # ── Status Bar ─────────────────────────────────────────────────────────
    def _build_statusbar(self):
        sb = tk.Frame(self, bg=BG2, height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self.status_var,
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left", padx=12)

    def set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    # ── Module 1 ───────────────────────────────────────────────────────────
    def _build_module1(self):
        scroll = _ScrollFrame(self.tab1)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        inp = card(p, "Material Requirements")
        inp.columnconfigure(1, weight=1)

        self.m1_yield = styled_entry(inp)
        self.m1_dens  = styled_entry(inp)
        self.m1_elong = styled_entry(inp)
        self.m1_yield.insert(0, "300")
        self.m1_dens.insert(0, "8000")
        self.m1_elong.insert(0, "10")

        field_row(inp, "Min Yield Strength (MPa)", self.m1_yield, 0)
        field_row(inp, "Max Density (kg/m³)",      self.m1_dens,  1)
        field_row(inp, "Min Elongation (%)",        self.m1_elong, 2)

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Find Materials", self._run_module1).pack(side="left")

        res = card(p, "Recommended Materials")
        self.m1_result_frame = res

    def _run_module1(self):
        try:
            sy = float(self.m1_yield.get())
            ro = float(self.m1_dens.get())
            a5 = float(self.m1_elong.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        if sy <= 0 or sy > 2500:
            messagebox.showerror("Validation Error",
                "Yield strength must be between 0 and 2500 MPa.")
            return
        if ro <= 0 or ro > 25000:
            messagebox.showerror("Validation Error",
                "Density must be between 0 and 25000 kg/m³.")
            return
        if a5 < 0 or a5 > 100:
            messagebox.showerror("Validation Error",
                "Elongation must be between 0 and 100%.")
            return

        self.set_status("Running Module 1 — K-Means material clustering...")
        for w in self.m1_result_frame.winfo_children():
            w.destroy()

        try:
            results = recommend_materials(sy, ro, a5)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
            self.set_status("Module 1 failed.")
            return

        if not results:
            styled_label(self.m1_result_frame,
                         "No materials match the given requirements.\n"
                         "Try relaxing your constraints (lower Sy, higher ρ, or lower A5).",
                         fg=DANGER).pack(anchor="w")
            self.set_status("No results found.")
            return

        self.m1_last_results = results
        for i, r in enumerate(results):
            color = [ACCENT, ACCENT2, SUCCESS][i % 3]
            row = tk.Frame(self.m1_result_frame, bg=BG3)
            row.pack(fill="x", pady=(0, 8))
            tk.Label(row, text=f"  #{i+1}  ", font=FONT_B,
                     fg=BG, bg=color, width=4).pack(side="left")
            info = tk.Frame(row, bg=BG3)
            info.pack(side="left", fill="x", expand=True, padx=10, pady=6)
            tk.Label(info, text=r["Material"], font=FONT_B,
                     fg=TEXT, bg=BG3, anchor="w").pack(fill="x")
            details = (f"Sy: {r['Yield Strength (MPa)']} MPa  |  "
                       f"ρ: {r['Density (kg/m³)']} kg/m³  |  "
                       f"A5: {r['Elongation (%)']}%  |  "
                       f"Cluster: {r['Cluster']}")
            tk.Label(info, text=details, font=FONT_S,
                     fg=TEXT2, bg=BG3, anchor="w").pack(fill="x")
            fc = r["Failure Concern"]
            fc_color = (DANGER if "Fracture" in fc
                        else WARNING if "Fatigue" in fc
                        else TEXT2)
            tk.Label(info, text=f"⚠  {fc}", font=FONT_S,
                     fg=fc_color, bg=BG3, anchor="w").pack(fill="x")

        self.set_status(f"Module 1 complete — {len(results)} materials found.")
        self._update_summary_m1(results)

    # ── Module 2 ───────────────────────────────────────────────────────────
    def _build_module2(self):
        scroll = _ScrollFrame(self.tab2)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        inp = card(p, "Stress Analysis Inputs")
        inp.columnconfigure(1, weight=1)

        self.m2_member = styled_combo(inp, ["beam", "shaft", "column"])
        self.m2_sigma  = styled_entry(inp)
        self.m2_tau    = styled_entry(inp)
        self.m2_sy     = styled_entry(inp)
        self.m2_su     = styled_entry(inp)
        self.m2_sigma.insert(0, "400e6")
        self.m2_tau.insert(0, "100e6")
        self.m2_sy.insert(0, "350e6")
        self.m2_su.insert(0, "600e6")

        field_row(inp, "Member Type",            self.m2_member, 0, 0)
        field_row(inp, "Normal Stress σ (Pa)",   self.m2_sigma,  1, 0)
        field_row(inp, "Shear Stress τ (Pa)",    self.m2_tau,    2, 0)
        field_row(inp, "Yield Strength Sy (Pa)", self.m2_sy,     3, 0)
        field_row(inp, "UTS Su (Pa)",            self.m2_su,     4, 0)

        tk.Label(inp, text="Tip: Enter values in Pa  e.g. 400e6 = 400 MPa",
                 font=FONT_S, fg=TEXT2, bg=BG2).grid(
                 row=5, column=0, columnspan=2, sticky="w", pady=(2, 0))

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Assess Stress", self._run_module2).pack(side="left")

        res = card(p, "Stress Assessment Result")
        self.m2_result_frame = res

    def _run_module2(self):
        try:
            member = self.m2_member.get()
            sigma  = float(self.m2_sigma.get())
            tau    = float(self.m2_tau.get())
            sy     = float(self.m2_sy.get())
            su     = float(self.m2_su.get())
        except ValueError:
            messagebox.showerror("Input Error",
                "Please enter valid numbers. Use scientific notation e.g. 400e6")
            return

        if sigma < 0:
            messagebox.showerror("Validation Error",
                "Normal stress σ cannot be negative. Enter the magnitude.")
            return
        if tau < 0:
            messagebox.showerror("Validation Error",
                "Shear stress τ cannot be negative. Enter the magnitude.")
            return
        if sy <= 0:
            messagebox.showerror("Validation Error",
                "Yield strength Sy must be greater than 0.")
            return
        if su <= sy:
            messagebox.showerror("Validation Error",
                "UTS (Su) must be greater than Yield Strength (Sy).\n"
                "A material always fractures above its yield point.")
            return

        self.set_status("Running Module 2 — Random Forest stress classification...")
        for w in self.m2_result_frame.winfo_children():
            w.destroy()

        try:
            result = predict_risk(member, sigma, tau, sy, su)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
            self.set_status("Module 2 failed.")
            return

        self.m2_last_result = result
        risk  = result["Risk Category"]
        color = RISK_COLORS.get(risk, TEXT2)
        conf  = result["Confidence (%)"]
        vm    = result["Von Mises Stress (Pa)"]
        ratio = result["Stress Ratio (σ_vm/Sy)"]

        badge_row = tk.Frame(self.m2_result_frame, bg=BG2)
        badge_row.pack(fill="x", pady=(0, 8))
        tk.Label(badge_row, text=risk, font=("Segoe UI", 14, "bold"),
                 fg=BG, bg=color, padx=16, pady=8).pack(side="left")
        tk.Label(badge_row, text=f"  Confidence: {conf}%",
                 font=FONT_B, fg=TEXT2, bg=BG2).pack(side="left", padx=12)

        divider(self.m2_result_frame)

        metrics = [
            ("Von Mises Stress", f"{vm:,.0f} Pa"),
            ("Yield Strength",   f"{sy:,.0f} Pa"),
            ("Stress Ratio σ/Sy", f"{ratio:.4f}"),
            ("Member Type",      member.capitalize()),
        ]
        mg = tk.Frame(self.m2_result_frame, bg=BG2)
        mg.pack(fill="x")
        for i, (label, val) in enumerate(metrics):
            col = tk.Frame(mg, bg=BG3)
            col.grid(row=0, column=i, padx=(0, 8), pady=4, sticky="ew")
            mg.columnconfigure(i, weight=1)
            tk.Label(col, text=label, font=FONT_S, fg=TEXT2,
                     bg=BG3, anchor="w").pack(fill="x", padx=8, pady=(6, 0))
            tk.Label(col, text=val, font=FONT_B, fg=TEXT,
                     bg=BG3, anchor="w").pack(fill="x", padx=8, pady=(0, 6))

        # Safety Factor
        sf = sy / vm if vm > 0 else float('inf')
        sf_color = SUCCESS if sf >= 2 else WARNING if sf >= 1 else DANGER
        sf_frame = tk.Frame(self.m2_result_frame, bg=BG2)
        sf_frame.pack(fill="x", pady=(8, 0))
        tk.Label(sf_frame, text=f"Safety Factor (Sy/σ_vm): {sf:.3f}",
                 font=FONT_B, fg=sf_color, bg=BG2).pack(anchor="w")

        self.set_status(f"Module 2 complete — {risk} ({conf}% confidence).")
        self._update_summary_m2(result)

    # ── Module 3 ───────────────────────────────────────────────────────────
    def _build_module3(self):
        scroll = _ScrollFrame(self.tab3)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        inp = card(p, "Machining Parameters")
        inp.columnconfigure(1, weight=1)

        self.m3_type   = styled_combo(inp, ["L", "M", "H"])
        self.m3_air    = styled_entry(inp)
        self.m3_proc   = styled_entry(inp)
        self.m3_rpm    = styled_entry(inp)
        self.m3_torque = styled_entry(inp)
        self.m3_speed  = styled_entry(inp)
        self.m3_feed   = styled_entry(inp)
        self.m3_depth  = styled_entry(inp)

        self.m3_air.insert(0, "300.0")
        self.m3_proc.insert(0, "310.0")
        self.m3_rpm.insert(0, "1500")
        self.m3_torque.insert(0, "40.0")
        self.m3_speed.insert(0, "150.0")
        self.m3_feed.insert(0, "0.2")
        self.m3_depth.insert(0, "2.0")

        field_row(inp, "Material Grade (L/M/H)",     self.m3_type,   0)
        field_row(inp, "Air Temperature (K)",         self.m3_air,    1)
        field_row(inp, "Process Temperature (K)",     self.m3_proc,   2)
        field_row(inp, "Rotational Speed (rpm)",      self.m3_rpm,    3)
        field_row(inp, "Torque (Nm)",                 self.m3_torque, 4)
        field_row(inp, "Base Cutting Speed (m/min)",  self.m3_speed,  5)
        field_row(inp, "Base Feed Rate (mm/rev)",     self.m3_feed,   6)
        field_row(inp, "Base Depth of Cut (mm)",      self.m3_depth,  7)

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Get Advisory", self._run_module3).pack(side="left")

        res = card(p, "Cutting Condition Advisory")
        self.m3_result_frame = res

    def _run_module3(self):
        try:
            tg    = self.m3_type.get()
            air   = float(self.m3_air.get())
            proc  = float(self.m3_proc.get())
            rpm   = int(self.m3_rpm.get())
            torq  = float(self.m3_torque.get())
            spd   = float(self.m3_speed.get())
            feed  = float(self.m3_feed.get())
            depth = float(self.m3_depth.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        if air <= 273:
            messagebox.showerror("Validation Error",
                "Air temperature must be above 273 K (0°C).")
            return
        if proc <= air:
            messagebox.showerror("Validation Error",
                "Process temperature must be greater than air temperature.\n"
                "The workpiece is always hotter than ambient during machining.")
            return
        if not (100 <= rpm <= 5000):
            messagebox.showerror("Validation Error",
                "Rotational speed must be between 100 and 5000 rpm.")
            return
        if not (0 < torq <= 200):
            messagebox.showerror("Validation Error",
                "Torque must be between 0 and 200 Nm.")
            return
        if not (0 < spd <= 500):
            messagebox.showerror("Validation Error",
                "Cutting speed must be between 0 and 500 m/min.")
            return
        if not (0.01 <= feed <= 2.0):
            messagebox.showerror("Validation Error",
                "Feed rate must be between 0.01 and 2.0 mm/rev.")
            return
        if not (0.1 <= depth <= 20):
            messagebox.showerror("Validation Error",
                "Depth of cut must be between 0.1 and 20 mm.")
            return

        self.set_status("Running Module 3 — Taylor tool life + failure classifier...")
        for w in self.m3_result_frame.winfo_children():
            w.destroy()

        try:
            results = get_advisory(tg, air, proc, rpm, torq, spd, feed, depth)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
            self.set_status("Module 3 failed.")
            return

        self.m3_last_results = results
        mode_colors = {"Conservative": SUCCESS, "Balanced": ACCENT, "Aggressive": DANGER}

        for r in results:
            mode  = r["Mode"]
            color = mode_colors.get(mode, TEXT2)
            row   = tk.Frame(self.m3_result_frame, bg=BG3)
            row.pack(fill="x", pady=(0, 8))

            tk.Label(row, text=f"  {mode}  ", font=FONT_B,
                     fg=BG, bg=color).pack(side="left")
            info = tk.Frame(row, bg=BG3)
            info.pack(side="left", fill="x", expand=True, padx=10, pady=6)

            line1 = (f"Speed: {r['speed (m/min)']} m/min  |  "
                     f"Feed: {r['feed (mm/rev)']} mm/rev  |  "
                     f"Depth: {r['depth (mm)']} mm")
            tk.Label(info, text=line1, font=FONT_B, fg=TEXT,
                     bg=BG3, anchor="w").pack(fill="x")

            tl = r['tool_life (min)']
            tl_str = ">10,000 min" if tl > 10000 else f"{tl} min"
            fail_color = DANGER if r["Failure Risk"] == "Yes" else SUCCESS
            line2 = (f"Tool Life: {tl_str}  |  "
                     f"Failure Risk: {r['Failure Risk']}  |  "
                     f"Confidence: {r['Confidence (%)']}%")
            tk.Label(info, text=line2, font=FONT_S, fg=fail_color,
                     bg=BG3, anchor="w").pack(fill="x")

        self.set_status("Module 3 complete — advisory generated.")
        self._update_summary_m3(results)

    # ── Summary Tab ────────────────────────────────────────────────────────
    def _build_summary(self):
        scroll = _ScrollFrame(self.tab4)
        scroll.pack(fill="both", expand=True)
        self.sum_inner = scroll.inner
        styled_label(self.sum_inner,
                     "Run all three modules to see the unified summary here.",
                     fg=TEXT2, bg=BG).pack(pady=40)

    def _update_summary_m1(self, results):
        self._rebuild_summary()

    def _update_summary_m2(self, result):
        self._rebuild_summary()

    def _update_summary_m3(self, results):
        self._rebuild_summary()

    def _rebuild_summary(self):
        for w in self.sum_inner.winfo_children():
            w.destroy()

        styled_label(self.sum_inner, "Unified Engineering Summary",
                     font=FONT_T, fg=ACCENT, bg=BG).pack(anchor="w", padx=16, pady=(16, 4))
        divider(tk.Frame(self.sum_inner, bg=BG))

        if hasattr(self, "m1_last_results") and self.m1_last_results:
            s = card(self.sum_inner, "Module 1 — Top Material")
            r = self.m1_last_results[0]
            tk.Label(s, text=r["Material"], font=FONT_B,
                     fg=TEXT, bg=BG2).pack(anchor="w")
            tk.Label(s,
                     text=f"Sy: {r['Yield Strength (MPa)']} MPa  |  "
                          f"ρ: {r['Density (kg/m³)']} kg/m³  |  {r['Failure Concern']}",
                     font=FONT_S, fg=TEXT2, bg=BG2).pack(anchor="w")

        if hasattr(self, "m2_last_result"):
            r     = self.m2_last_result
            risk  = r["Risk Category"]
            color = RISK_COLORS.get(risk, TEXT2)
            s     = card(self.sum_inner, "Module 2 — Stress Risk")
            rf    = tk.Frame(s, bg=BG2)
            rf.pack(anchor="w")
            tk.Label(rf, text=risk, font=FONT_B, fg=BG,
                     bg=color, padx=10, pady=4).pack(side="left")
            tk.Label(rf,
                     text=f"   σ_vm/Sy = {r['Stress Ratio (σ_vm/Sy)']:.4f}  |  "
                          f"Confidence: {r['Confidence (%)']}%",
                     font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")

        if hasattr(self, "m3_last_results") and self.m3_last_results:
            s = card(self.sum_inner, "Module 3 — Recommended Cutting Conditions")
            mode_colors = {"Conservative": SUCCESS, "Balanced": ACCENT, "Aggressive": DANGER}
            for r in self.m3_last_results:
                color  = mode_colors.get(r["Mode"], TEXT2)
                tl     = r['tool_life (min)']
                tl_str = ">10,000 min" if tl > 10000 else f"{tl} min"
                row = tk.Frame(s, bg=BG2)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{r['Mode']:12}", font=FONT_B,
                         fg=color, bg=BG2).pack(side="left")
                tk.Label(row,
                         text=f"Tool Life: {tl_str}  |  Failure Risk: {r['Failure Risk']}",
                         font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")


# ── Scrollable Frame Helper ────────────────────────────────────────────────
class _ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.inner = tk.Frame(canvas, bg=BG)
        self.inner.bind("<Configure>",
                        lambda e: canvas.configure(
                            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))


# ── Entry Point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = MechAssist()
    app.mainloop()