import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

BG      = "#0f1117"
BG2     = "#1a1d27"
BG3     = "#22263a"
ACCENT  = "#6c8ef5"
ACCENT2 = "#a78bfa"
SUCCESS = "#34d399"
WARNING = "#fbbf24"
DANGER  = "#f87171"
TEXT    = "#e2e8f0"
TEXT2   = "#94a3b8"
BORDER  = "#2e3347"
FONT    = ("Segoe UI", 10)
FONT_B  = ("Segoe UI", 10, "bold")
FONT_H  = ("Segoe UI", 13, "bold")
FONT_T  = ("Segoe UI", 16, "bold")
FONT_S  = ("Segoe UI", 9)

RISK_COLORS = {
    "Safe":          SUCCESS,
    "Yield Risk":    WARNING,
    "Fatigue Risk":  WARNING,
    "Fracture Risk": DANGER,
    "Buckling Risk": DANGER,
}

RISK_DESCRIPTIONS = {
    "Safe":          "The component can handle this load without risk of failure.",
    "Yield Risk":    "Stress exceeds yield strength — the part will permanently deform.",
    "Fatigue Risk":  "Repeated loading at this stress level will cause cracks over time.",
    "Fracture Risk": "Stress is near ultimate tensile strength — sudden fracture is likely.",
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
        "Increase cross-section to lower stress below 0.85 × Su.",
    ],
    "Buckling Risk": [
        "Reduce column slenderness ratio — shorten unsupported length or increase section.",
        "Add lateral supports to reduce effective length.",
        "Use a higher-E material to increase critical buckling load.",
    ],
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
    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=padx)
    body = tk.Frame(inner, bg=BG2)
    body.pack(fill="x", padx=padx, pady=pady)
    return body

def field_row(parent, label, widget, row, col_offset=0):
    styled_label(parent, label, fg=TEXT2, bg=BG2).grid(
        row=row, column=col_offset, sticky="w", padx=(0, 8), pady=4)
    widget.grid(row=row, column=col_offset + 1, sticky="ew", pady=4)

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

def bind_arrow_keys(entries):
    for i, e in enumerate(entries):
        if i > 0:
            e.bind("<Up>", lambda ev, prev=entries[i - 1]: prev.focus_set())
        if i < len(entries) - 1:
            e.bind("<Down>", lambda ev, nxt=entries[i + 1]: nxt.focus_set())

def warning_box(parent, warnings, suggestions):
    if not warnings and not suggestions:
        return
    box = tk.Frame(parent, bg="#2a1a1a", highlightthickness=1,
                   highlightbackground=DANGER)
    box.pack(fill="x", pady=(6, 0))
    inner = tk.Frame(box, bg="#2a1a1a")
    inner.pack(fill="x", padx=10, pady=8)
    for w in warnings:
        tk.Label(inner, text=f"⚠  {w}", font=FONT_S,
                 fg=WARNING, bg="#2a1a1a", anchor="w",
                 wraplength=700, justify="left").pack(fill="x", pady=(0, 2))
    if suggestions:
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=(4, 4))
        tk.Label(inner, text="Suggested actions:", font=FONT_B,
                 fg=TEXT2, bg="#2a1a1a", anchor="w").pack(fill="x")
        for s in suggestions:
            tk.Label(inner, text=f"  →  {s}", font=FONT_S,
                     fg=TEXT, bg="#2a1a1a", anchor="w",
                     wraplength=700, justify="left").pack(fill="x", pady=(1, 0))


# ── Tooltip ───────────────────────────────────────────────────────────────

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 6
        y = self.widget.winfo_rooty() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        outer = tk.Frame(self.tip, bg=ACCENT, padx=1, pady=1)
        outer.pack()
        tk.Label(outer, text=self.text, font=FONT_S,
                 bg=BG3, fg=TEXT, padx=8, pady=5,
                 justify="left", wraplength=280).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ── Mohr's Circle ─────────────────────────────────────────────────────────

def draw_mohrs_circle(parent, sigma, tau, sy, su):
    R      = np.sqrt((sigma / 2) ** 2 + tau ** 2)
    center = sigma / 2
    s1     = center + R
    s2     = center - R

    # FIX: scale to circle geometry, not Sy/Su lines
    scale = max(abs(center) + R * 1.5, R * 2.0) * 1.3
    scale = max(scale, 1e6)

    def mpa(v): return v / 1e6

    fig = Figure(figsize=(8, 5), dpi=96, facecolor=BG2)
    ax  = fig.add_subplot(111, facecolor=BG3, aspect="equal")
    fig.subplots_adjust(left=0.09, right=0.68, top=0.92, bottom=0.13)

    ax.grid(True, color="#2e3347", linewidth=0.8, linestyle="-", alpha=1.0, zorder=0)
    theta = np.linspace(0, 2 * np.pi, 500)

    # Lighter lineweights
    ax.plot(mpa(center + R * np.cos(theta)), mpa(R * np.sin(theta)),
            color=ACCENT, linewidth=1.4, zorder=3)
    ax.axhline(0, color=TEXT2, linewidth=0.6, zorder=1, alpha=0.4)
    ax.axvline(0, color=TEXT2, linewidth=0.6, zorder=1, alpha=0.4)
    ax.axvline(mpa(sy), color=WARNING, linewidth=1.2, linestyle="--", zorder=2, alpha=0.85)
    ax.axvline(mpa(su), color=DANGER,  linewidth=1.2, linestyle="--", zorder=2, alpha=0.85)
    ax.plot([mpa(center), mpa(sigma)], [0, mpa(tau)],
            color=TEXT2, linewidth=0.8, linestyle=":", zorder=2, alpha=0.5)
    ax.plot([mpa(s2), mpa(s1)], [0, 0], color=TEXT2, linewidth=0.7, zorder=2, alpha=0.35)
    ax.plot([mpa(center), mpa(center)], [0, mpa(R)],
            color=TEXT2, linewidth=0.7, zorder=2, alpha=0.35)

    p_a,      = ax.plot(mpa(sigma),  mpa(tau), "o", color=SUCCESS, markersize=7,  zorder=5)
    p_centre, = ax.plot(mpa(center), 0,        "s", color=ACCENT,  markersize=5,  zorder=5)
    p_s1,     = ax.plot(mpa(s1),     0,        "^", color=WARNING, markersize=6,  zorder=5)
    p_s2,     = ax.plot(mpa(s2),     0,        "v", color=WARNING, markersize=6,  zorder=5)
    p_tmax,   = ax.plot(mpa(center), mpa(R),   "D", color=ACCENT2, markersize=5,  zorder=5)

    from matplotlib.lines import Line2D
    leg_h = [p_a, p_centre, p_s1, p_s2, p_tmax,
             Line2D([0], [0], color=WARNING, linewidth=1.2, linestyle="--"),
             Line2D([0], [0], color=DANGER,  linewidth=1.2, linestyle="--")]
    leg_l = [
        f"A (σ, τ) = ({mpa(sigma):.1f}, {mpa(tau):.1f}) MPa",
        f"Centre = {mpa(center):.1f} MPa",
        f"σ₁ = {mpa(s1):.1f} MPa",
        f"σ₂ = {mpa(s2):.1f} MPa",
        f"τ_max = {mpa(R):.1f} MPa",
        f"Sy = {mpa(sy):.0f} MPa",
        f"Su = {mpa(su):.0f} MPa",
    ]
    ax.legend(leg_h, leg_l, loc="upper left", bbox_to_anchor=(1.02, 1.0),
              fontsize=8, facecolor=BG2, edgecolor=BORDER, labelcolor=TEXT,
              framealpha=1.0, handlelength=1.6, handleheight=1.0,
              handletextpad=0.6, borderpad=0.6, labelspacing=0.45)

    lim = mpa(scale)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim * 0.65, lim * 0.65)
    ax.set_xlabel("Normal Stress σ (MPa)", color=TEXT2, fontsize=9)
    ax.set_ylabel("Shear Stress τ (MPa)",  color=TEXT2, fontsize=9)
    ax.set_title("Mohr's Circle", color=TEXT, fontsize=11, fontweight="bold", pad=10)
    ax.tick_params(colors=TEXT2, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", pady=(4, 0))
    return canvas


# ── Tool Life Curve (always shown) ────────────────────────────────────────

def draw_tool_life_curve(parent, v_base, n, C):
    for w in parent.winfo_children():
        w.destroy()
    speeds = np.linspace(max(1, v_base * 0.3), v_base * 2.0, 300)
    lives  = np.clip(np.array([(C / v) ** (1 / n) for v in speeds]), 0, 10000)

    fig = Figure(figsize=(7, 3.2), dpi=96, facecolor=BG2)
    ax  = fig.add_subplot(111, facecolor=BG3)
    fig.subplots_adjust(left=0.13, right=0.97, top=0.88, bottom=0.18)

    ax.plot(speeds, lives, color=ACCENT2, linewidth=1.6, zorder=3)

    mode_colors = {"Conservative": SUCCESS, "Balanced": ACCENT, "Aggressive": DANGER}
    for label, factor in [("Conservative", 0.8), ("Balanced", 1.0), ("Aggressive", 1.2)]:
        v_pt = v_base * factor
        t_pt = min((C / v_pt) ** (1 / n), 10000)
        ax.axvline(v_pt, color=mode_colors[label], linewidth=1.0,
                   linestyle="--", alpha=0.85, zorder=2)
        ax.plot(v_pt, t_pt, "o", color=mode_colors[label],
                markersize=6, zorder=4, label=f"{label}: {t_pt:.1f} min")

    ax.set_title("Tool Life vs Cutting Speed",
                 color=TEXT, fontsize=9, fontweight="bold", pad=8)
    ax.set_xlabel("Cutting Speed (m/min)", color=TEXT2, fontsize=9)
    ax.set_ylabel("Tool Life (min)",       color=TEXT2, fontsize=9)
    ax.tick_params(colors=TEXT2, labelsize=8)
    ax.grid(True, color=BORDER, linewidth=0.7, linestyle="-", alpha=1.0)
    ax.legend(fontsize=8, facecolor=BG2, edgecolor=BORDER,
              labelcolor=TEXT, framealpha=1.0)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", pady=(4, 0))
    return canvas


# ── Beam Stress Calculator ─────────────────────────────────────────────────

def compute_beam_stresses(section, load_type, L, P_or_w, a, dim1, dim2):
    x = np.linspace(0, L, 500)
    if load_type == "Point Load":
        P     = P_or_w
        b_pos = L - a
        R1    = P * b_pos / L
        V     = np.where(x < a, R1, R1 - P)
        M     = np.where(x < a, R1 * x, R1 * x - P * (x - a))
        M_max = float(np.max(np.abs(M)))
        V_max = float(np.max(np.abs(V)))
        y     = np.where(
            x < a,
            (P * b_pos * x / (6 * L)) * (L ** 2 - b_pos ** 2 - x ** 2),
            (P * a * (L - x) / (6 * L)) * (L ** 2 - a ** 2 - (L - x) ** 2)
        )
    else:
        w     = P_or_w
        R1    = w * L / 2
        V     = R1 - w * x
        M     = R1 * x - (w * x ** 2) / 2
        M_max = float(np.max(np.abs(M)))
        V_max = float(np.max(np.abs(V)))
        y     = (w * x * (L ** 3 - 2 * L * x ** 2 + x ** 3)) / 24

    if section == "Rectangle":
        b, h    = dim1, dim2
        c       = h / 2
        I       = b * h ** 3 / 12
        A       = b * h
        tau_max = 1.5 * V_max / A
    else:
        d       = dim1
        c       = d / 2
        I       = np.pi * d ** 4 / 64
        A       = np.pi * d ** 2 / 4
        tau_max = (4 / 3) * V_max / A

    return M_max * c / I, tau_max, M_max, V_max, x, M, V, y


def draw_beam_plots(parent, x, M, V, y_raw, EI, L, load_type, a=None):
    for w in parent.winfo_children():
        w.destroy()

    y_def = y_raw / EI * 1000
    fig   = Figure(figsize=(8, 8), dpi=96, facecolor=BG2)
    fig.subplots_adjust(left=0.11, right=0.97, top=0.94, bottom=0.07, hspace=0.45)
    x_mm  = x * 1000

    def _style_ax(ax, title, xlabel, ylabel):
        ax.set_facecolor(BG3)
        ax.set_title(title, color=TEXT, fontsize=9, fontweight="bold", pad=6)
        ax.set_xlabel(xlabel, color=TEXT2, fontsize=8)
        ax.set_ylabel(ylabel, color=TEXT2, fontsize=8)
        ax.tick_params(colors=TEXT2, labelsize=7)
        ax.grid(True, color=BORDER, linewidth=0.7, linestyle="-", alpha=1.0)
        ax.axhline(0, color=TEXT2, linewidth=0.6, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)

    ax1 = fig.add_subplot(3, 1, 1)
    ax1.plot(x_mm, V / 1000, color=ACCENT, linewidth=1.6)
    ax1.fill_between(x_mm, V / 1000, 0, alpha=0.2, color=ACCENT)
    _style_ax(ax1, "Shear Force Diagram", "Position (mm)", "V (kN)")

    ax2 = fig.add_subplot(3, 1, 2)
    ax2.plot(x_mm, M / 1000, color=ACCENT2, linewidth=1.6)
    ax2.fill_between(x_mm, M / 1000, 0, alpha=0.2, color=ACCENT2)
    _style_ax(ax2, "Bending Moment Diagram", "Position (mm)", "M (kNm)")

    ax3 = fig.add_subplot(3, 1, 3)
    ax3.plot(x_mm, y_def, color=SUCCESS, linewidth=1.6)
    ax3.fill_between(x_mm, y_def, 0, alpha=0.2, color=SUCCESS)
    ax3.invert_yaxis()
    _style_ax(ax3, "Deflection Curve", "Position (mm)", "δ (mm)")

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", pady=(4, 0))
    return canvas


# ── Main App ───────────────────────────────────────────────────────────────

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
        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=BG3, bordercolor=BORDER,
                        background=ACCENT, lightcolor=ACCENT,
                        darkcolor=ACCENT)

        self._build_header()
        self._build_body()
        self._build_statusbar()

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

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=BG2, height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(sb, textvariable=self.status_var,
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left", padx=12)
        self._progress = ttk.Progressbar(
            sb, orient="horizontal", mode="indeterminate",
            style="Accent.Horizontal.TProgressbar", length=160)
        self._progress.pack(side="right", padx=12, pady=4)

    def set_status(self, msg, busy=False):
        self.status_var.set(msg)
        if busy:
            self._progress.start(12)
        else:
            self._progress.stop()
        self.update_idletasks()

    # ── Module 1 ──────────────────────────────────────────────────────────

    def _build_module1(self):
        scroll = _ScrollFrame(self.tab1)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        inp = card(p, "Material Requirements")
        inp.columnconfigure(1, weight=1)

        # No default values — user must input
        self.m1_yield = styled_entry(inp)
        self.m1_dens  = styled_entry(inp)
        self.m1_elong = styled_entry(inp)

        field_row(inp, "Min Yield Strength (MPa)", self.m1_yield, 0)
        field_row(inp, "Max Density (kg/m³)",      self.m1_dens,  1)
        field_row(inp, "Min Elongation (%)",        self.m1_elong, 2)

        bind_arrow_keys([self.m1_yield, self.m1_dens, self.m1_elong])
        ToolTip(self.m1_yield, "Minimum Yield Strength\nMaterials below this Sy are excluded.\nRange: 0–2500 MPa")
        ToolTip(self.m1_dens,  "Maximum Density\nMaterials above this density are excluded.\nRange: 0–25000 kg/m³")
        ToolTip(self.m1_elong, "Minimum Elongation (A5)\nRange: 0–100%")

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Find Materials", self._run_module1).pack(side="left")

        res = card(p, "Recommended Materials")
        self.m1_result_frame = res

    def _run_module1(self):
        for w in self.m1_result_frame.winfo_children():
            w.destroy()

        try:
            sy = float(self.m1_yield.get())
            ro = float(self.m1_dens.get())
            a5 = float(self.m1_elong.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        if sy <= 0 or sy > 2500:
            messagebox.showerror("Validation Error",
                f"Your input ({sy} MPa) is outside the valid range (0–2500 MPa).")
            return
        if ro <= 0 or ro > 25000:
            messagebox.showerror("Validation Error",
                f"Your input ({ro} kg/m³) is outside the valid range (0–25000 kg/m³).")
            return
        if a5 < 0 or a5 > 100:
            messagebox.showerror("Validation Error",
                f"Your input ({a5}%) is outside the valid range (0–100%).")
            return

        self.set_status("Running Module 1 — K-Means material clustering...", busy=True)

        try:
            results = recommend_materials(sy, ro, a5)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
            self.set_status("Module 1 failed.")
            return

        if not results:
            styled_label(self.m1_result_frame,
                         "No materials match the given requirements.\n"
                         "Try relaxing your constraints.",
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
                       f"A5: {r['Elongation (%)']}%")
            tk.Label(info, text=details, font=FONT_S,
                     fg=TEXT2, bg=BG3, anchor="w").pack(fill="x")
            fc = r["Failure Concern"]
            fc_color = (DANGER if "Fracture" in fc
                        else WARNING if "Fatigue" in fc
                        else TEXT2)
            tk.Label(info, text=f"⚠  {fc}", font=FONT_S,
                     fg=fc_color, bg=BG3, anchor="w").pack(fill="x")

        # Auto-trigger cross-module fills silently
        self._autofill_m2_from_m1(silent=True)
        self._autofill_m3_from_m1(silent=True)

        self.set_status(f"Module 1 complete — {len(results)} materials found. "
                        f"Sy/Su auto-filled in Module 2, grade auto-filled in Module 3.")
        self._update_summary_m1(results)

    def _autofill_m2_from_m1(self, silent=False):
        if not hasattr(self, "m1_last_results") or not self.m1_last_results:
            if not silent:
                messagebox.showwarning("No Data", "Run Module 1 first.")
            return
        r  = self.m1_last_results[0]
        sy = r["Yield Strength (MPa)"] * 1e6
        su = sy * 1.3
        self.m2_sy.delete(0, tk.END)
        self.m2_sy.insert(0, f"{sy:.2e}")
        self.m2_su.delete(0, tk.END)
        self.m2_su.insert(0, f"{su:.2e}")
        if not silent:
            self.set_status(
                f"Module 2 pre-filled — Sy={sy/1e6:.0f} MPa, Su={su/1e6:.0f} MPa "
                f"(Su estimated as 1.3×Sy — adjust if known).")

    def _autofill_m3_from_m1(self, silent=False):
        if not hasattr(self, "m1_last_results") or not self.m1_last_results:
            if not silent:
                messagebox.showwarning("No Data", "Run Module 1 first.")
            return
        r       = self.m1_last_results[0]
        cluster = r.get("Cluster", None)
        grade_map = {0: "M", 1: "H", 2: "L", 3: "M", 4: "M", 5: "M"}
        grade = grade_map.get(cluster, "M")
        self.m3_type.set(grade)
        if not silent:
            self.set_status(
                f"Module 3 pre-filled — Material Grade set to '{grade}' "
                f"based on '{r['Material']}'. Adjust if needed.")

    # ── Module 2 ──────────────────────────────────────────────────────────

    def _build_module2(self):
        scroll = _ScrollFrame(self.tab2)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        # Beam geometry
        beam_card = card(p, "Compute from Beam Geometry  (optional)")
        beam_card.columnconfigure(1, weight=1)
        beam_card.columnconfigure(3, weight=1)

        tk.Label(beam_card,
                 text="Fill this section to auto-compute σ and τ from geometry. "
                      "Leave blank to enter stresses manually below.",
                 font=FONT_S, fg=TEXT2, bg=BG2, wraplength=680, justify="left"
                 ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 6))

        self.b_span    = styled_entry(beam_card)
        self.b_section = styled_combo(beam_card, ["Rectangle", "Circle"])
        self.b_section.bind("<<ComboboxSelected>>", self._on_section_change)
        field_row(beam_card, "Beam Span L (m)",  self.b_span,    1, 0)
        field_row(beam_card, "Cross-Section",     self.b_section, 1, 2)

        self.b_dim1_lbl = tk.StringVar(value="Width b (m)")
        self.b_dim2_lbl = tk.StringVar(value="Height h (m)")
        self.b_dim1 = styled_entry(beam_card)
        self.b_dim2 = styled_entry(beam_card)

        self._dim1_label_widget = tk.Label(beam_card, textvariable=self.b_dim1_lbl,
                                           font=FONT, fg=TEXT2, bg=BG2)
        self._dim1_label_widget.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.b_dim1.grid(row=2, column=1, sticky="ew", pady=4)
        self._dim2_label_widget = tk.Label(beam_card, textvariable=self.b_dim2_lbl,
                                           font=FONT, fg=TEXT2, bg=BG2)
        self._dim2_label_widget.grid(row=2, column=2, sticky="w", padx=(16, 8), pady=4)
        self.b_dim2.grid(row=2, column=3, sticky="ew", pady=4)

        self.b_E = styled_entry(beam_card)
        self.b_I = styled_entry(beam_card)
        self.b_E.insert(0, "200e9")
        tk.Label(beam_card, text="Young's Modulus E (Pa)",
                 font=FONT, fg=TEXT2, bg=BG2).grid(
                 row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        self.b_E.grid(row=3, column=1, sticky="ew", pady=4)
        tk.Label(beam_card, text="Moment of Inertia I (m⁴)  [auto if blank]",
                 font=FONT, fg=TEXT2, bg=BG2).grid(
                 row=3, column=2, sticky="w", padx=(16, 8), pady=4)
        self.b_I.grid(row=3, column=3, sticky="ew", pady=4)

        self.b_loadtype = styled_combo(beam_card, ["Point Load", "UDL"])
        self.b_loadtype.bind("<<ComboboxSelected>>", self._on_loadtype_change)
        tk.Label(beam_card, text="Load Type",
                 font=FONT, fg=TEXT2, bg=BG2).grid(
                 row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        self.b_loadtype.grid(row=4, column=1, sticky="ew", pady=4)

        self.b_mag = styled_entry(beam_card)
        self.b_pos = styled_entry(beam_card)
        self._mag_lbl = tk.StringVar(value="Load P (N)")
        self._pos_lbl = tk.StringVar(value="Position a from left (m)")

        self._mag_label_widget = tk.Label(beam_card, textvariable=self._mag_lbl,
                                          font=FONT, fg=TEXT2, bg=BG2)
        self._mag_label_widget.grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        self.b_mag.grid(row=5, column=1, sticky="ew", pady=4)
        self._pos_label_widget = tk.Label(beam_card, textvariable=self._pos_lbl,
                                          font=FONT, fg=TEXT2, bg=BG2)
        self._pos_label_widget.grid(row=5, column=2, sticky="w", padx=(16, 8), pady=4)
        self.b_pos.grid(row=5, column=3, sticky="ew", pady=4)

        bf2 = tk.Frame(beam_card, bg=BG2)
        bf2.grid(row=6, column=0, columnspan=4, sticky="w", pady=(10, 0))
        action_btn(bf2, "Compute σ and τ", self._compute_beam_stresses,
                   color=SUCCESS).pack(side="left")
        tk.Label(bf2,
                 text="  → fills Normal Stress and Shear Stress fields below automatically",
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left", padx=8)

        ToolTip(self.b_span,  "Beam span — distance between supports (m)")
        ToolTip(self.b_dim1,  "Rectangle: width b (m)\nCircle: diameter d (m)")
        ToolTip(self.b_dim2,  "Rectangle: height h (m)\nNot used for circular sections")
        ToolTip(self.b_E,     "Young's Modulus E (Pa)\nSteel = 200e9, Aluminium = 70e9")
        ToolTip(self.b_I,     "Second Moment of Area I (m⁴)\nLeave blank to auto-compute")
        ToolTip(self.b_mag,   "Load magnitude\nPoint Load: N, UDL: N/m\nPositive = downward")
        ToolTip(self.b_pos,   "Load position from left support (m)\nMust be between 0 and L")

        self.beam_plots_frame = tk.Frame(p, bg=BG)
        self.beam_plots_frame.pack(fill="x", padx=16, pady=(0, 8))

        # Stress inputs — no defaults
        inp = card(p, "Stress Analysis Inputs")
        inp.columnconfigure(1, weight=1)

        self.m2_member = styled_combo(inp, ["beam", "shaft", "column"])
        self.m2_sigma  = styled_entry(inp)
        self.m2_tau    = styled_entry(inp)
        self.m2_sy     = styled_entry(inp)
        self.m2_su     = styled_entry(inp)

        field_row(inp, "Member Type",            self.m2_member, 0, 0)
        field_row(inp, "Normal Stress σ (MPa)",  self.m2_sigma,  1, 0)
        field_row(inp, "Shear Stress τ (MPa)",   self.m2_tau,    2, 0)
        field_row(inp, "Yield Strength Sy (MPa)", self.m2_sy,    3, 0)
        field_row(inp, "UTS Su (MPa)",            self.m2_su,    4, 0)

        bind_arrow_keys([self.m2_sigma, self.m2_tau, self.m2_sy, self.m2_su])
        ToolTip(self.m2_sigma, "Normal Stress σ in MPa\ne.g. 400")
        ToolTip(self.m2_tau,   "Shear Stress τ in MPa\ne.g. 100")
        ToolTip(self.m2_sy,    "Yield Strength in MPa\nAuto-filled from Module 1")
        ToolTip(self.m2_su,    "Ultimate Tensile Strength in MPa\nMust be greater than Sy")

        tk.Label(inp,
                 text="Sy and Su auto-filled when Module 1 is run.",
                 font=FONT_S, fg=ACCENT, bg=BG2).grid(
                 row=5, column=0, columnspan=2, sticky="w", pady=(2, 0))

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Assess Stress", self._run_module2).pack(side="left")

        res = card(p, "Stress Assessment Result")
        self.m2_result_frame = res

        mohr = card(p, "Mohr's Circle")
        self.m2_mohr_frame = mohr

    def _on_section_change(self, event=None):
        if self.b_section.get() == "Rectangle":
            self.b_dim1_lbl.set("Width b (m)")
            self.b_dim2_lbl.set("Height h (m)")
            self._dim2_label_widget.grid()
            self.b_dim2.grid()
        else:
            self.b_dim1_lbl.set("Diameter d (m)")
            self._dim2_label_widget.grid_remove()
            self.b_dim2.grid_remove()

    def _on_loadtype_change(self, event=None):
        if self.b_loadtype.get() == "Point Load":
            self._mag_lbl.set("Load P (N)")
            self._pos_lbl.set("Position a from left (m)")
            self._pos_label_widget.grid()
            self.b_pos.grid()
        else:
            self._mag_lbl.set("Load Intensity w (N/m)")
            self._pos_label_widget.grid_remove()
            self.b_pos.grid_remove()

    def _compute_beam_stresses(self):
        for w in self.beam_plots_frame.winfo_children():
            w.destroy()

        try:
            L = float(self.b_span.get())
            if L <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Beam Input Error", "Enter a valid positive span L (m).")
            return

        section = self.b_section.get()
        try:
            dim1 = float(self.b_dim1.get())
            if dim1 <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Beam Input Error", "Enter a valid cross-section dimension.")
            return

        dim2 = 0.0
        if section == "Rectangle":
            try:
                dim2 = float(self.b_dim2.get())
                if dim2 <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Beam Input Error", "Enter a valid height h (m).")
                return

        try:
            E = float(self.b_E.get())
            if E <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Beam Input Error", "Enter a valid Young's Modulus E (Pa).")
            return

        I_field = self.b_I.get().strip()
        if I_field == "":
            I = (dim1 * dim2 ** 3 / 12) if section == "Rectangle" else (np.pi * dim1 ** 4 / 64)
        else:
            try:
                I = float(I_field)
                if I <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("Beam Input Error", "Enter a valid Moment of Inertia I (m⁴).")
                return

        load_type = self.b_loadtype.get()
        try:
            mag = float(self.b_mag.get())
        except ValueError:
            messagebox.showerror("Beam Input Error", "Enter a valid load magnitude.")
            return

        a = 0.0
        if load_type == "Point Load":
            try:
                a = float(self.b_pos.get())
                if not (0 < a < L):
                    messagebox.showerror("Beam Input Error",
                        f"Load position a must be between 0 and L ({L} m).")
                    return
            except ValueError:
                messagebox.showerror("Beam Input Error", "Enter a valid load position a (m).")
                return

        try:
            sigma, tau, M_max, V_max, x, M, V, y_raw = compute_beam_stresses(
                section, load_type, L, mag, a, dim1, dim2)
        except Exception as ex:
            messagebox.showerror("Computation Error", str(ex))
            return

        EI = E * I
        # Beam tool outputs in Pa — convert to MPa for display fields
        self.m2_sigma.delete(0, tk.END)
        self.m2_sigma.insert(0, f"{sigma/1e6:.4f}")
        self.m2_tau.delete(0, tk.END)
        self.m2_tau.insert(0, f"{tau/1e6:.4f}")
        self.m2_member.set("beam")

        self.set_status(
            f"Beam computed — σ_max = {sigma/1e6:.2f} MPa, "
            f"τ_max = {tau/1e6:.2f} MPa, "
            f"M_max = {M_max/1000:.2f} kNm, V_max = {V_max/1000:.2f} kN")

        outer = tk.Frame(self.beam_plots_frame, bg=BORDER)
        outer.pack(fill="x")
        inner = tk.Frame(outer, bg=BG2)
        inner.pack(fill="x", padx=1, pady=1)
        tk.Label(inner, text="Beam Diagrams — SFD / BMD / Deflection",
                 font=FONT_H, fg=ACCENT, bg=BG2, anchor="w").pack(
                 fill="x", padx=12, pady=(10, 4))
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=12)

        summary_row = tk.Frame(inner, bg=BG2)
        summary_row.pack(fill="x", padx=12, pady=(6, 4))
        for label, val in [
            ("σ_max", f"{sigma/1e6:.3f} MPa"),
            ("τ_max", f"{tau/1e6:.3f} MPa"),
            ("M_max", f"{M_max/1000:.3f} kNm"),
            ("V_max", f"{V_max/1000:.3f} kN"),
        ]:
            col = tk.Frame(summary_row, bg=BG3)
            col.pack(side="left", padx=(0, 8), pady=2)
            tk.Label(col, text=label, font=FONT_S, fg=TEXT2, bg=BG3).pack(padx=10, pady=(4, 0))
            tk.Label(col, text=val,   font=FONT_B, fg=TEXT,  bg=BG3).pack(padx=10, pady=(0, 4))

        plot_container = tk.Frame(inner, bg=BG2)
        plot_container.pack(fill="x", padx=12, pady=(4, 10))
        draw_beam_plots(plot_container, x, M, V, y_raw, EI, L, load_type, a)

    def _run_module2(self):
        for w in self.m2_result_frame.winfo_children():
            w.destroy()
        for w in self.m2_mohr_frame.winfo_children():
            w.destroy()

        try:
            member = self.m2_member.get()
            # Accept MPa, convert to Pa internally
            sigma  = float(self.m2_sigma.get()) * 1e6
            tau    = float(self.m2_tau.get()) * 1e6
            sy     = float(self.m2_sy.get()) * 1e6
            su     = float(self.m2_su.get()) * 1e6
        except ValueError:
            messagebox.showerror("Input Error",
                "Enter valid numbers in MPa (e.g. 400, 100, 350, 600).")
            return

        if sigma < 0:
            messagebox.showerror("Validation Error", "Normal stress σ cannot be negative.")
            return
        if tau < 0:
            messagebox.showerror("Validation Error", "Shear stress τ cannot be negative.")
            return
        if sy <= 0:
            messagebox.showerror("Validation Error", "Yield strength Sy must be greater than 0.")
            return
        if su <= sy:
            messagebox.showerror("Validation Error",
                "UTS (Su) must be greater than Yield Strength (Sy).")
            return

        self.set_status("Running Module 2 — Random Forest stress classification...", busy=True)

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
        sf    = sy / vm if vm > 0 else float("inf")

        # Risk badge
        badge_row = tk.Frame(self.m2_result_frame, bg=BG2)
        badge_row.pack(fill="x", pady=(0, 4))
        tk.Label(badge_row, text=risk, font=("Segoe UI", 14, "bold"),
                 fg=BG, bg=color, padx=16, pady=8).pack(side="left")
        tk.Label(badge_row, text=f"  Model Certainty: {conf}%",
                 font=FONT_B, fg=TEXT2, bg=BG2).pack(side="left", padx=12)
        tk.Label(badge_row, text="(how certain the AI is about this prediction)",
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")

        tk.Label(self.m2_result_frame,
                 text=RISK_DESCRIPTIONS.get(risk, ""),
                 font=FONT_S, fg=TEXT2, bg=BG2, anchor="w").pack(fill="x", pady=(0, 4))

        divider(self.m2_result_frame)

        # Metrics — display in MPa
        metrics = [
            ("Von Mises Stress",  f"{vm/1e6:.2f} MPa"),
            ("Yield Strength",    f"{sy/1e6:.2f} MPa"),
            ("Stress Ratio σ/Sy", f"{ratio:.4f}"),
            ("Member Type",       member.capitalize()),
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

        sf_color = SUCCESS if sf >= 2 else WARNING if sf >= 1 else DANGER
        sf_str   = "∞ (no load applied)" if vm == 0 else f"{sf:.3f}"
        sf_frame = tk.Frame(self.m2_result_frame, bg=BG2)
        sf_frame.pack(fill="x", pady=(8, 0))
        tk.Label(sf_frame, text=f"Safety Factor (Sy/σ_vm): {sf_str}",
                 font=FONT_B, fg=sf_color, bg=BG2).pack(anchor="w")

        # Actionable warnings
        warns = []
        suggs = RISK_SUGGESTIONS.get(risk, [])
        if sf < 1:
            warns.append(f"Safety factor is {sf:.2f} — component will fail under this load.")
        elif sf < 2:
            warns.append(f"Safety factor is {sf:.2f} — below the recommended minimum of 2.0.")
        if risk != "Safe" and hasattr(self, "m1_last_results") and self.m1_last_results:
            top = self.m1_last_results[0]
            warns.append(
                f"Module 1 top result '{top['Material']}' "
                f"(Sy={top['Yield Strength (MPa)']} MPa) was used. "
                f"Consider material #2 or #3 if higher strength is needed.")
        warning_box(self.m2_result_frame, warns, suggs)

        draw_mohrs_circle(self.m2_mohr_frame, sigma, tau, sy, su)
        self.set_status(f"Module 2 complete — {risk} ({conf}% confidence).")
        self._update_summary_m2(result)

    # ── Module 3 ──────────────────────────────────────────────────────────

    def _build_module3(self):
        scroll = _ScrollFrame(self.tab3)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        inp = card(p, "Machining Parameters")
        inp.columnconfigure(1, weight=1)

        # No defaults except tool material and grade (dropdowns start at index 0)
        self.m3_type      = styled_combo(inp, ["L", "M", "H"])
        self.m3_tool_mat  = styled_combo(inp, ["HSS", "Carbide", "Ceramic", "CBN"])
        self.m3_tool_mat.current(1)
        self.m3_air       = styled_entry(inp)
        self.m3_proc      = styled_entry(inp)
        self.m3_rpm       = styled_entry(inp)
        self.m3_torque    = styled_entry(inp)
        self.m3_speed     = styled_entry(inp)
        self.m3_feed      = styled_entry(inp)
        self.m3_depth     = styled_entry(inp)

        field_row(inp, "Workpiece Grade (L/M/H)", self.m3_type,     0)
        field_row(inp, "Tool Material",            self.m3_tool_mat, 1)
        field_row(inp, "Air Temperature (K)",      self.m3_air,      2)
        field_row(inp, "Process Temperature (K)",  self.m3_proc,     3)
        field_row(inp, "Rotational Speed (rpm)",   self.m3_rpm,      4)
        field_row(inp, "Torque (Nm)",              self.m3_torque,   5)
        field_row(inp, "Base Cutting Speed (m/min)", self.m3_speed,  6)
        field_row(inp, "Base Feed Rate (mm/rev)",  self.m3_feed,     7)
        field_row(inp, "Base Depth of Cut (mm)",   self.m3_depth,    8)

        bind_arrow_keys([self.m3_air, self.m3_proc, self.m3_rpm,
                         self.m3_torque, self.m3_speed, self.m3_feed, self.m3_depth])

        ToolTip(self.m3_type,     "Workpiece hardness grade\nL = soft (aluminium, mild steel)\nM = medium\nH = hard (hardened steel, cast iron)\nAuto-filled from Module 1")
        ToolTip(self.m3_tool_mat, "Cutting tool material\nHSS: cheap, slow\nCarbide: standard\nCeramic: fast, brittle\nCBN: hardened steels only")
        ToolTip(self.m3_air,      "Ambient air temperature\nMust be above 273 K (0°C)")
        ToolTip(self.m3_proc,     "Workpiece/process temperature\nMust be greater than air temp")
        ToolTip(self.m3_rpm,      "Spindle rotational speed\nRange: 100–5000 rpm")
        ToolTip(self.m3_torque,   "Cutting torque\nRange: 0–200 Nm")
        ToolTip(self.m3_speed,    "Base cutting speed (m/min)\nAdvisory generates ±20% variants\nRange: 0–500 m/min")
        ToolTip(self.m3_feed,     "Base feed rate (mm/rev)\nRange: 0.01–2.0 mm/rev")
        ToolTip(self.m3_depth,    "Base depth of cut (mm)\nRange: 0.1–20 mm")

        self.m3_tool_desc_var = tk.StringVar()
        self._update_tool_desc()
        self.m3_tool_mat.bind("<<ComboboxSelected>>",
                              lambda e: self._update_tool_desc())
        tk.Label(inp, textvariable=self.m3_tool_desc_var,
                 font=FONT_S, fg=TEXT2, bg=BG2, anchor="w",
                 wraplength=500, justify="left").grid(
                 row=9, column=0, columnspan=2, sticky="w", pady=(0, 4))

        tk.Label(inp,
                 text="Workpiece Grade auto-filled when Module 1 is run.",
                 font=FONT_S, fg=ACCENT, bg=BG2).grid(
                 row=10, column=0, columnspan=2, sticky="w", pady=(0, 4))

        bf = tk.Frame(inp, bg=BG2)
        bf.grid(row=11, column=0, columnspan=2, sticky="w", pady=(8, 0))
        action_btn(bf, "Get Advisory", self._run_module3).pack(side="left")

        res = card(p, "Cutting Condition Advisory")
        self.m3_result_frame = res

        tl_frame = card(p, "Tool Life Curve")
        self.m3_toollife_frame = tl_frame

    def _update_tool_desc(self):
        mat = self.m3_tool_mat.get()
        self.m3_tool_desc_var.set(TOOL_DESCRIPTIONS.get(mat, ""))

    def _run_module3(self):
        for w in self.m3_result_frame.winfo_children():
            w.destroy()
        for w in self.m3_toollife_frame.winfo_children():
            w.destroy()

        try:
            tg        = self.m3_type.get()
            tool_mat  = self.m3_tool_mat.get()
            air       = float(self.m3_air.get())
            proc      = float(self.m3_proc.get())
            rpm       = int(self.m3_rpm.get())
            torq      = float(self.m3_torque.get())
            spd       = float(self.m3_speed.get())
            feed      = float(self.m3_feed.get())
            depth     = float(self.m3_depth.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers.")
            return

        if air <= 273:
            messagebox.showerror("Validation Error", "Air temperature must be above 273 K.")
            return
        if proc <= air:
            messagebox.showerror("Validation Error",
                "Process temperature must be greater than air temperature.")
            return
        if not (100 <= rpm <= 5000):
            messagebox.showerror("Validation Error", "Rotational speed must be 100–5000 rpm.")
            return
        if not (0 < torq <= 200):
            messagebox.showerror("Validation Error", "Torque must be 0–200 Nm.")
            return
        if not (0 < spd <= 500):
            messagebox.showerror("Validation Error", "Cutting speed must be 0–500 m/min.")
            return
        if not (0.01 <= feed <= 2.0):
            messagebox.showerror("Validation Error", "Feed rate must be 0.01–2.0 mm/rev.")
            return
        if not (0.1 <= depth <= 20):
            messagebox.showerror("Validation Error", "Depth of cut must be 0.1–20 mm.")
            return

        self.set_status("Running Module 3 — Taylor tool life + failure classifier...", busy=True)

        try:
            results = get_advisory(tg, air, proc, rpm, torq, spd, feed, depth,
                                   tool_material=tool_mat)
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
            tk.Label(info, text=line1, font=FONT_B, fg=TEXT, bg=BG3, anchor="w").pack(fill="x")

            tl     = r["tool_life (min)"]
            tl_str = ">10,000 min" if tl > 10000 else f"{tl} min"
            fc     = DANGER if r["Failure Risk"] == "Yes" else SUCCESS
            line2  = (f"Tool Life: {tl_str}  |  "
                      f"Failure Risk: {r['Failure Risk']}  |  "
                      f"Confidence: {r['Confidence (%)']}%")
            tk.Label(info, text=line2, font=FONT_S, fg=fc, bg=BG3, anchor="w").pack(fill="x")

            if r["Warnings"] or r["Suggestions"]:
                warning_box(info, r["Warnings"], r["Suggestions"])

        # Always draw tool life curve
        n, C = results[0]["n"], results[0]["C"]
        draw_tool_life_curve(self.m3_toollife_frame, spd, n, C)

        self.set_status("Module 3 complete — advisory generated.")
        self._update_summary_m3(results)

    # ── Summary ───────────────────────────────────────────────────────────

    def _build_summary(self):
        # Export button bar (always visible at top of tab)
        export_bar = tk.Frame(self.tab4, bg=BG2, height=44)
        export_bar.pack(fill="x")
        export_bar.pack_propagate(False)
        tk.Label(export_bar, text="Export this report as a PDF engineering document:",
                 font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left", padx=12)
        action_btn(export_bar, "⬇  Export PDF", self._export_pdf,
                   color=ACCENT2).pack(side="right", padx=12, pady=6)

        scroll = _ScrollFrame(self.tab4)
        scroll.pack(fill="both", expand=True)
        self.sum_inner = scroll.inner
        styled_label(self.sum_inner,
                     "Run all three modules to see the unified summary here.",
                     fg=TEXT2, bg=BG).pack(pady=40)

    def _export_pdf(self):
        m1_done = hasattr(self, "m1_last_results") and self.m1_last_results
        m2_done = hasattr(self, "m2_last_result")
        m3_done = hasattr(self, "m3_last_results") and self.m3_last_results

        if not (m1_done or m2_done or m3_done):
            messagebox.showwarning("Nothing to Export",
                "Run at least one module before exporting.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile="MechAssist_Report.pdf",
            title="Save Engineering Report")
        if not filepath:
            return

        self.set_status("Generating PDF report...", busy=True)

        # Build narrative (same logic as _rebuild_summary)
        lines = []
        if m1_done:
            r = self.m1_last_results[0]
            lines.append(
                f"Material selected: {r['Material']} "
                f"(Sy = {r['Yield Strength (MPa)']} MPa, "
                f"concern: {r['Failure Concern']}).")
        if m2_done:
            r     = self.m2_last_result
            vm    = r["Von Mises Stress (Pa)"]
            sy_pa = float(self.m2_sy.get()) * 1e6 if self.m2_sy.get() else 1
            sf    = sy_pa / vm if vm > 0 else float("inf")
            sf_s  = "inf" if sf == float("inf") else f"{sf:.2f}"
            lines.append(
                f"Stress assessment: {r['Risk Category']} at "
                f"sigma_vm/Sy = {r['Stress Ratio (\u03c3_vm/Sy)']:.3f} "
                f"(Safety Factor = {sf_s}, model certainty {r['Confidence (%)']}%).")
        if m3_done:
            bal = next((r for r in self.m3_last_results
                        if r["Mode"] == "Balanced"), None)
            if bal:
                tl = bal["tool_life (min)"]
                tls = ">10,000 min" if tl > 10000 else f"{tl} min"
                lines.append(
                    f"Machining: {bal.get('tool_material','Carbide')} tool at "
                    f"{bal['speed (m/min)']} m/min — tool life {tls}, "
                    f"machine failure risk: {bal['Failure Risk']}.")

        data = {
            "narrative": "  ".join(lines),
        }

        if m1_done:
            data["m1_results"] = self.m1_last_results
            try:
                data["m1_inputs"] = {
                    "sy": float(self.m1_yield.get()),
                    "ro": float(self.m1_dens.get()),
                    "a5": float(self.m1_elong.get()),
                }
            except Exception:
                pass

        if m2_done:
            r = self.m2_last_result
            data["m2_result"] = r
            try:
                data["m2_inputs"] = {
                    "member":    self.m2_member.get(),
                    "sigma_mpa": float(self.m2_sigma.get()),
                    "tau_mpa":   float(self.m2_tau.get()),
                    "sy_mpa":    float(self.m2_sy.get()),
                    "su_mpa":    float(self.m2_su.get()),
                }
            except Exception:
                pass

        if m3_done:
            data["m3_results"] = self.m3_last_results
            try:
                data["m3_inputs"] = {
                    "grade":    self.m3_type.get(),
                    "tool_mat": self.m3_tool_mat.get(),
                    "air":      float(self.m3_air.get()),
                    "proc":     float(self.m3_proc.get()),
                    "rpm":      int(self.m3_rpm.get()),
                    "torque":   float(self.m3_torque.get()),
                    "speed":    float(self.m3_speed.get()),
                    "feed":     float(self.m3_feed.get()),
                    "depth":    float(self.m3_depth.get()),
                }
            except Exception:
                pass

        try:
            export_report(data, filepath)
            self.set_status(f"PDF exported: {os.path.basename(filepath)}")
            messagebox.showinfo("Export Complete",
                f"Report saved to:\n{filepath}")
        except Exception as ex:
            messagebox.showerror("Export Failed", str(ex))
            self.set_status("PDF export failed.")

    def _update_summary_m1(self, results): self._rebuild_summary()
    def _update_summary_m2(self, result):  self._rebuild_summary()
    def _update_summary_m3(self, results): self._rebuild_summary()

    def _rebuild_summary(self):
        for w in self.sum_inner.winfo_children():
            w.destroy()

        styled_label(self.sum_inner, "Unified Engineering Summary",
                     font=FONT_T, fg=ACCENT, bg=BG).pack(anchor="w", padx=16, pady=(16, 4))
        divider(tk.Frame(self.sum_inner, bg=BG))

        m1_done = hasattr(self, "m1_last_results") and self.m1_last_results
        m2_done = hasattr(self, "m2_last_result")
        m3_done = hasattr(self, "m3_last_results") and self.m3_last_results

        if m1_done or m2_done or m3_done:
            narr = card(self.sum_inner, "Engineering Narrative")
            lines = []

            if m1_done:
                r   = self.m1_last_results[0]
                mat = r["Material"]
                sy  = r["Yield Strength (MPa)"]
                fc  = r["Failure Concern"]
                lines.append(
                    f"Material selected: {mat} (Sy = {sy} MPa, concern: {fc}).")

            if m2_done:
                r     = self.m2_last_result
                risk  = r["Risk Category"]
                ratio = r["Stress Ratio (σ_vm/Sy)"]
                conf  = r["Confidence (%)"]
                vm    = r["Von Mises Stress (Pa)"]
                sy_pa = float(self.m2_sy.get()) * 1e6 if self.m2_sy.get() else 1
                sf    = sy_pa / vm if vm > 0 else float("inf")
                sf_s  = "∞" if sf == float("inf") else f"{sf:.2f}"
                lines.append(
                    f"Stress assessment: {risk} at σ_vm/Sy = {ratio:.3f} "
                    f"(Safety Factor = {sf_s}, model certainty {conf}%).")
                if risk != "Safe":
                    sugg = RISK_SUGGESTIONS.get(risk, [])
                    if sugg:
                        lines.append(f"Recommended action: {sugg[0]}")

            if m3_done:
                bal = next((r for r in self.m3_last_results if r["Mode"] == "Balanced"), None)
                if bal:
                    tl    = bal["tool_life (min)"]
                    tls   = ">10,000 min" if tl > 10000 else f"{tl} min"
                    fisk  = bal["Failure Risk"]
                    tmat  = bal.get("tool_material", "Carbide")
                    lines.append(
                        f"Machining: {tmat} tool at {bal['speed (m/min)']} m/min — "
                        f"tool life {tls}, machine failure risk: {fisk}.")
                    if bal["Suggestions"]:
                        lines.append(f"Machining note: {bal['Suggestions'][0]}")

            full_text = "  ".join(lines) if lines else "Run all three modules for a full narrative."
            tk.Label(narr, text=full_text, font=FONT_S, fg=TEXT,
                     bg=BG2, wraplength=900, justify="left",
                     anchor="w").pack(fill="x")

        if m1_done:
            s = card(self.sum_inner, "Module 1 — Top Material")
            r = self.m1_last_results[0]
            tk.Label(s, text=r["Material"], font=FONT_B, fg=TEXT, bg=BG2).pack(anchor="w")
            tk.Label(s, text=(f"Sy: {r['Yield Strength (MPa)']} MPa  |  "
                              f"ρ: {r['Density (kg/m³)']} kg/m³  |  {r['Failure Concern']}"),
                     font=FONT_S, fg=TEXT2, bg=BG2).pack(anchor="w")

        if m2_done:
            r     = self.m2_last_result
            risk  = r["Risk Category"]
            color = RISK_COLORS.get(risk, TEXT2)
            s     = card(self.sum_inner, "Module 2 — Stress Risk")
            rf    = tk.Frame(s, bg=BG2)
            rf.pack(anchor="w")
            tk.Label(rf, text=risk, font=FONT_B, fg=BG,
                     bg=color, padx=10, pady=4).pack(side="left")
            tk.Label(rf, text=(f"   σ_vm/Sy = {r['Stress Ratio (σ_vm/Sy)']:.4f}  |  "
                               f"Confidence: {r['Confidence (%)']}%"),
                     font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")

        if m3_done:
            s = card(self.sum_inner, "Module 3 — Cutting Conditions")
            mode_colors = {"Conservative": SUCCESS, "Balanced": ACCENT, "Aggressive": DANGER}
            for r in self.m3_last_results:
                color  = mode_colors.get(r["Mode"], TEXT2)
                tl     = r["tool_life (min)"]
                tl_str = ">10,000 min" if tl > 10000 else f"{tl} min"
                row    = tk.Frame(s, bg=BG2)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"{r['Mode']:12}", font=FONT_B,
                         fg=color, bg=BG2).pack(side="left")
                tk.Label(row,
                         text=f"Tool Life: {tl_str}  |  Failure Risk: {r['Failure Risk']}",
                         font=FONT_S, fg=TEXT2, bg=BG2).pack(side="left")


# ── Scroll Frame ───────────────────────────────────────────────────────────

class _ScrollFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self.inner = tk.Frame(self._canvas, bg=BG)
        self.inner.bind("<Configure>",
                        lambda e: self._canvas.configure(
                            scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._canvas.bind("<Enter>", self._bind_scroll)
        self._canvas.bind("<Leave>", self._unbind_scroll)
        self.inner.bind("<Enter>", self._bind_scroll)
        self.inner.bind("<Leave>", self._unbind_scroll)

    def _bind_scroll(self, event=None):
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units"))

    def _unbind_scroll(self, event=None):
        self._canvas.unbind_all("<MouseWheel>")


if __name__ == "__main__":
    app = MechAssist()
    app.mainloop()