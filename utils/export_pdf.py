"""
MechAssist — PDF Export (Upgrade 9)
Generates a structured engineering report from all three module results.
Usage: called from gui/app.py via export_report(data, filepath)
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
import os

# ── Colour palette (matches app dark theme, adapted for white paper) ───────
C_ACCENT  = colors.HexColor("#3b5bd6")   # blue
C_ACCENT2 = colors.HexColor("#6d4fc4")   # purple
C_SUCCESS = colors.HexColor("#1a9e6e")   # green
C_WARNING = colors.HexColor("#c47d00")   # amber
C_DANGER  = colors.HexColor("#c0392b")   # red
C_DARK    = colors.HexColor("#1a1d27")   # near-black
C_MID     = colors.HexColor("#4a5568")   # slate
C_LIGHT   = colors.HexColor("#e2e8f0")   # pale
C_WHITE   = colors.white
C_RULE    = colors.HexColor("#cbd5e0")

RISK_COLORS = {
    "Safe":          C_SUCCESS,
    "Yield Risk":    C_WARNING,
    "Fatigue Risk":  C_WARNING,
    "Fracture Risk": C_DANGER,
    "Buckling Risk": C_DANGER,
}

# ── Styles ─────────────────────────────────────────────────────────────────

def _make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle", fontSize=22, leading=28,
            textColor=C_DARK, fontName="Helvetica-Bold",
            alignment=TA_LEFT, spaceAfter=4),
        "subtitle": ParagraphStyle(
            "ReportSub", fontSize=10, leading=14,
            textColor=C_MID, fontName="Helvetica",
            alignment=TA_LEFT, spaceAfter=2),
        "section": ParagraphStyle(
            "Section", fontSize=13, leading=17,
            textColor=C_ACCENT, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=4),
        "subsection": ParagraphStyle(
            "Subsection", fontSize=10, leading=14,
            textColor=C_DARK, fontName="Helvetica-Bold",
            spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle(
            "Body", fontSize=9, leading=13,
            textColor=C_MID, fontName="Helvetica",
            spaceAfter=3),
        "body_dark": ParagraphStyle(
            "BodyDark", fontSize=9, leading=13,
            textColor=C_DARK, fontName="Helvetica",
            spaceAfter=3),
        "warning": ParagraphStyle(
            "Warning", fontSize=8.5, leading=12,
            textColor=C_WARNING, fontName="Helvetica",
            spaceAfter=2),
        "danger": ParagraphStyle(
            "Danger", fontSize=8.5, leading=12,
            textColor=C_DANGER, fontName="Helvetica",
            spaceAfter=2),
        "success": ParagraphStyle(
            "Success", fontSize=8.5, leading=12,
            textColor=C_SUCCESS, fontName="Helvetica",
            spaceAfter=2),
        "footer": ParagraphStyle(
            "Footer", fontSize=7.5, leading=10,
            textColor=C_MID, fontName="Helvetica",
            alignment=TA_CENTER),
        "metric_label": ParagraphStyle(
            "MetricLabel", fontSize=7.5, leading=10,
            textColor=C_MID, fontName="Helvetica"),
        "metric_value": ParagraphStyle(
            "MetricValue", fontSize=10, leading=13,
            textColor=C_DARK, fontName="Helvetica-Bold"),
    }


def _rule(story):
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=C_RULE, spaceAfter=6, spaceBefore=2))


def _section(story, title, styles):
    story.append(Paragraph(title, styles["section"]))
    _rule(story)


def _kv_table(data, styles, col_widths=None):
    """Two-column key-value table."""
    w = col_widths or [55*mm, 105*mm]
    rows = []
    for k, v in data:
        rows.append([
            Paragraph(k, styles["metric_label"]),
            Paragraph(str(v), styles["metric_value"]),
        ])
    t = Table(rows, colWidths=w)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f7f8fa")),
        ("BACKGROUND", (1, 0), (1, -1), C_WHITE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#f7f8fa"), C_WHITE]),
        ("BOX",      (0, 0), (-1, -1), 0.4, C_RULE),
        ("INNERGRID",(0, 0), (-1, -1), 0.4, C_RULE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("VALIGN",   (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _risk_badge_table(risk, styles):
    color = RISK_COLORS.get(risk, C_MID)
    badge = Table([[Paragraph(f"  {risk}  ", ParagraphStyle(
        "Badge", fontSize=11, fontName="Helvetica-Bold",
        textColor=C_WHITE, leading=16))]],
        colWidths=[50*mm])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    return badge


def _m3_conditions_table(results, styles):
    mode_colors = {
        "Conservative": C_SUCCESS,
        "Balanced":     C_ACCENT,
        "Aggressive":   C_DANGER,
    }
    header = ["Mode", "Speed (m/min)", "Feed (mm/rev)",
              "Depth (mm)", "Tool Life (min)", "Failure Risk"]
    rows = [header]
    for r in results:
        tl = r.get("tool_life (min)", 0)
        tl_str = ">10,000" if tl > 10000 else str(tl)
        rows.append([
            r["Mode"],
            str(r.get("speed (m/min)", "-")),
            str(r.get("feed (mm/rev)", "-")),
            str(r.get("depth (mm)", "-")),
            tl_str,
            r.get("Failure Risk", "-"),
        ])

    col_w = [30*mm, 28*mm, 28*mm, 24*mm, 28*mm, 24*mm]
    t = Table(rows, colWidths=col_w)
    style_cmds = [
        ("BACKGROUND",   (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("BOX",          (0, 0), (-1, -1), 0.4, C_RULE),
        ("INNERGRID",    (0, 0), (-1, -1), 0.4, C_RULE),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f7f8fa"), C_WHITE]),
    ]
    for i, r in enumerate(results, start=1):
        mc = mode_colors.get(r["Mode"], C_MID)
        style_cmds.append(("TEXTCOLOR", (0, i), (0, i), mc))
        style_cmds.append(("FONTNAME",  (0, i), (0, i), "Helvetica-Bold"))
        fr = r.get("Failure Risk", "No")
        fr_color = C_DANGER if fr == "Yes" else C_SUCCESS
        style_cmds.append(("TEXTCOLOR", (5, i), (5, i), fr_color))
    t.setStyle(TableStyle(style_cmds))
    return t


# ── Header / Footer callbacks ───────────────────────────────────────────────

def _make_header_footer(timestamp, project="MechAssist Engineering Report"):
    def on_page(canvas, doc):
        canvas.saveState()
        W, H = A4
        # Header bar
        canvas.setFillColor(C_DARK)
        canvas.rect(15*mm, H - 18*mm, W - 30*mm, 10*mm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(20*mm, H - 12.5*mm, "⚙  MechAssist")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(48*mm, H - 12.5*mm, project)
        canvas.drawRightString(W - 20*mm, H - 12.5*mm,
                               f"Generated: {timestamp}")
        # Footer
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(C_MID)
        canvas.drawCentredString(W / 2, 10*mm,
            f"MechAssist v1.0  |  Monjyeeman Dutta  |  Page {doc.page}")
        canvas.setStrokeColor(C_RULE)
        canvas.setLineWidth(0.4)
        canvas.line(15*mm, 14*mm, W - 15*mm, 14*mm)
        canvas.restoreState()
    return on_page


# ── Main export function ────────────────────────────────────────────────────

def export_report(data: dict, filepath: str):
    """
    data keys (all optional — sections skipped if key absent):
      m1_results    : list of dicts from recommend_materials()
      m1_inputs     : dict {sy, ro, a5}
      m2_result     : dict from predict_risk()
      m2_inputs     : dict {member, sigma_mpa, tau_mpa, sy_mpa, su_mpa}
      m3_results    : list of dicts from get_advisory()
      m3_inputs     : dict {grade, tool_mat, air, proc, rpm, torque,
                            speed, feed, depth}
      narrative     : str  (pipeline narrative paragraph)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M")
    styles    = _make_styles()
    story     = []

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=22*mm,  bottomMargin=20*mm,
    )

    # ── Cover block ───────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Engineering Decision Report", styles["title"]))
    story.append(Paragraph(
        f"Generated by MechAssist v1.0  &nbsp;|&nbsp;  {timestamp}",
        styles["subtitle"]))
    story.append(Paragraph(
        "Monjyeeman Dutta  &nbsp;|&nbsp;  Jorhat Engineering College",
        styles["subtitle"]))
    story.append(Spacer(1, 4*mm))
    _rule(story)
    story.append(Spacer(1, 2*mm))

    # ── Narrative ────────────────────────────────────────────────────────
    if data.get("narrative"):
        _section(story, "1. Engineering Narrative", styles)
        story.append(Paragraph(data["narrative"], styles["body_dark"]))
        story.append(Spacer(1, 3*mm))

    # ── Module 1 ─────────────────────────────────────────────────────────
    if data.get("m1_results"):
        _section(story, "2. Material Selection — Module 1", styles)

        if data.get("m1_inputs"):
            inp = data["m1_inputs"]
            story.append(Paragraph("Design Requirements", styles["subsection"]))
            story.append(_kv_table([
                ("Min Yield Strength", f"{inp.get('sy', '-')} MPa"),
                ("Max Density",        f"{inp.get('ro', '-')} kg/m\u00b3"),
                ("Min Elongation",     f"{inp.get('a5', '-')} %"),
            ], styles))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Candidate Materials", styles["subsection"]))
        header = ["Rank", "Material", "Sy (MPa)", "Density (kg/m\u00b3)",
                  "Elongation (%)", "Failure Concern"]
        rows   = [header]
        for i, r in enumerate(data["m1_results"], 1):
            rows.append([
                f"#{i}",
                r["Material"],
                str(r["Yield Strength (MPa)"]),
                str(r["Density (kg/m\u00b3)"]),
                str(r["Elongation (%)"]),
                r["Failure Concern"],
            ])
        col_w = [12*mm, 50*mm, 22*mm, 30*mm, 26*mm, 30*mm]
        t = Table(rows, colWidths=col_w)
        fc_colors_map = {}
        for i, r in enumerate(data["m1_results"], 1):
            fc = r["Failure Concern"]
            fc_colors_map[i] = (C_DANGER if "Fracture" in fc
                                else C_WARNING if "Fatigue" in fc
                                else C_MID)
        t.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), C_DARK),
            ("TEXTCOLOR",    (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("BOX",          (0, 0), (-1, -1), 0.4, C_RULE),
            ("INNERGRID",    (0, 0), (-1, -1), 0.4, C_RULE),
            ("LEFTPADDING",  (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("ALIGN",        (2, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f7f8fa"), C_WHITE]),
            *[("TEXTCOLOR", (5, i), (5, i), fc_colors_map[i])
              for i in range(1, len(data["m1_results"]) + 1)],
        ]))
        story.append(t)

        top = data["m1_results"][0]
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("Selection Rationale", styles["subsection"]))
        story.append(Paragraph(
            f"Top-ranked material <b>{top['Material']}</b> selected based on highest "
            f"yield strength ({top['Yield Strength (MPa)']} MPa) within density and "
            f"elongation constraints. Primary failure concern: {top['Failure Concern']}. "
            f"Materials ranked by descending Sy, ascending density.",
            styles["body"]))
        story.append(Spacer(1, 3*mm))

    # ── Module 2 ─────────────────────────────────────────────────────────
    if data.get("m2_result"):
        _section(story, "3. Stress Assessment — Module 2", styles)
        r    = data["m2_result"]
        risk = r["Risk Category"]
        vm   = r["Von Mises Stress (Pa)"]
        conf = r["Confidence (%)"]
        ratio= r["Stress Ratio (σ_vm/Sy)"]

        inp = data.get("m2_inputs", {})
        sy_pa = inp.get("sy_mpa", 1) * 1e6
        sf = sy_pa / vm if vm > 0 else float("inf")
        sf_s = "∞" if sf == float("inf") else f"{sf:.3f}"

        if inp:
            story.append(Paragraph("Analysis Inputs", styles["subsection"]))
            story.append(_kv_table([
                ("Member Type",        inp.get("member", "-").capitalize()),
                ("Normal Stress σ",    f"{inp.get('sigma_mpa', '-')} MPa"),
                ("Shear Stress τ",     f"{inp.get('tau_mpa', '-')} MPa"),
                ("Yield Strength Sy",  f"{inp.get('sy_mpa', '-')} MPa"),
                ("UTS Su",             f"{inp.get('su_mpa', '-')} MPa"),
            ], styles))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Assessment Result", styles["subsection"]))
        badge = _risk_badge_table(risk, styles)

        sf_color = C_SUCCESS if sf >= 2 else C_WARNING if sf >= 1 else C_DANGER
        metrics_table = Table([
            [badge,
             _kv_table([
                 ("Von Mises Stress σ<sub rise=2 size=6>vm</sub>",
                  f"{vm/1e6:.2f} MPa"),
                 ("Stress Ratio σ<sub rise=2 size=6>vm</sub>/Sy",
                  f"{ratio:.4f}"),
                 ("Safety Factor Sy/σ<sub rise=2 size=6>vm</sub>",
                  sf_s),
                 ("Model Certainty", f"{conf}%"),
             ], styles, col_widths=[45*mm, 55*mm])]
            ],
            colWidths=[55*mm, 105*mm]
        )
        metrics_table.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        story.append(metrics_table)

        if risk != "Safe":
            story.append(Spacer(1, 3*mm))
            story.append(Paragraph("⚠  Risk Interpretation", styles["subsection"]))
            descs = {
                "Yield Risk":    "Stress exceeds yield strength — permanent deformation expected.",
                "Fatigue Risk":  "Repeated loading at this stress level will initiate cracks.",
                "Fracture Risk": "Stress near UTS — sudden fracture imminent.",
                "Buckling Risk": "Compressive load exceeds critical threshold — column will buckle.",
            }
            story.append(Paragraph(descs.get(risk, ""), styles["warning"]))

        story.append(Spacer(1, 3*mm))

    # ── Module 3 ─────────────────────────────────────────────────────────
    if data.get("m3_results"):
        _section(story, "4. Machinability Advisory — Module 3", styles)

        inp = data.get("m3_inputs", {})
        if inp:
            story.append(Paragraph("Machining Parameters", styles["subsection"]))
            story.append(_kv_table([
                ("Workpiece Grade",    inp.get("grade", "-")),
                ("Tool Material",      inp.get("tool_mat", "-")),
                ("Air Temperature",    f"{inp.get('air', '-')} K"),
                ("Process Temperature",f"{inp.get('proc', '-')} K"),
                ("Rotational Speed",   f"{inp.get('rpm', '-')} rpm"),
                ("Torque",             f"{inp.get('torque', '-')} Nm"),
                ("Base Cutting Speed", f"{inp.get('speed', '-')} m/min"),
                ("Base Feed Rate",     f"{inp.get('feed', '-')} mm/rev"),
                ("Base Depth of Cut",  f"{inp.get('depth', '-')} mm"),
            ], styles))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Cutting Condition Advisory", styles["subsection"]))
        story.append(_m3_conditions_table(data["m3_results"], styles))

        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("Warnings & Recommendations", styles["subsection"]))
        any_warn = False
        for r in data["m3_results"]:
            for w in r.get("Warnings", []):
                story.append(Paragraph(f"[{r['Mode']}]  ⚠  {w}", styles["warning"]))
                any_warn = True
            for s in r.get("Suggestions", []):
                story.append(Paragraph(f"  →  {s}", styles["body"]))
        if not any_warn:
            story.append(Paragraph("No warnings — all cutting conditions nominal.",
                                   styles["success"]))

        story.append(Spacer(1, 3*mm))

    # ── Disclaimer ────────────────────────────────────────────────────────
    _rule(story)
    story.append(Paragraph(
        "Disclaimer: This report is generated by an AI-assisted decision support tool. "
        "All results should be verified by a qualified mechanical engineer before "
        "implementation. MechAssist does not replace professional engineering judgment.",
        styles["footer"]))

    doc.build(story, onFirstPage=_make_header_footer(timestamp),
              onLaterPages=_make_header_footer(timestamp))
    return filepath