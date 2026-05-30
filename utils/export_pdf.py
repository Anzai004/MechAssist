"""
MechAssist — PDF Export
Generates a structured A4 engineering report.
Called from gui/app.py via export_report(data, filepath).

data keys (all optional — sections skipped if absent):
  meta          : dict {project_name, engineer, institution, company, revision, notes}
  narrative     : str
  m1_results    : list of dicts from recommend_materials()
  m1_inputs     : dict {sy_mpa, ro_kgm3, a5, unit_sys, sy, ro}
  m2_result     : dict from predict_risk()
  m2_inputs     : dict {member, sigma_mpa, tau_mpa, sy_mpa, su_mpa, sf_target}
  m3_results    : list of dicts from get_advisory()
  m3_inputs     : dict {grade, tool_mat, air, proc, rpm, torque, speed, feed, depth}
  mohr_png      : str  path to Mohr's Circle PNG
  toollife_png  : str  path to tool life curve PNG
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import os

# ── Palette ────────────────────────────────────────────────────────────────
C_ACCENT  = colors.HexColor("#3b5bd6")
C_ACCENT2 = colors.HexColor("#6d4fc4")
C_SUCCESS = colors.HexColor("#1a9e6e")
C_WARNING = colors.HexColor("#c47d00")
C_DANGER  = colors.HexColor("#c0392b")
C_DARK    = colors.HexColor("#1a1d27")
C_MID     = colors.HexColor("#4a5568")
C_WHITE   = colors.white
C_RULE    = colors.HexColor("#cbd5e0")
C_ROW_A   = colors.HexColor("#f7f8fa")
C_PASS    = colors.HexColor("#1a9e6e")
C_FAIL    = colors.HexColor("#c0392b")

RISK_C = {
    "Safe":          C_SUCCESS,
    "Yield Risk":    C_WARNING,
    "Fatigue Risk":  C_WARNING,
    "Fracture Risk": C_DANGER,
    "Buckling Risk": C_DANGER,
}

W = A4[0]
CONTENT_W = W - 30 * mm


# ── Styles ──────────────────────────────────────────────────────────────────

def _styles():
    return {
        "title": ParagraphStyle(
            "T", fontSize=22, leading=28, textColor=C_DARK,
            fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=4),
        "subtitle": ParagraphStyle(
            "S", fontSize=10, leading=14, textColor=C_MID,
            fontName="Helvetica", alignment=TA_LEFT, spaceAfter=2),
        "section": ParagraphStyle(
            "Sec", fontSize=13, leading=17, textColor=C_ACCENT,
            fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4),
        "subsection": ParagraphStyle(
            "SS", fontSize=10, leading=14, textColor=C_DARK,
            fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle(
            "B", fontSize=9, leading=13, textColor=C_MID,
            fontName="Helvetica", spaceAfter=3),
        "body_dark": ParagraphStyle(
            "BD", fontSize=9, leading=13, textColor=C_DARK,
            fontName="Helvetica", spaceAfter=3),
        "warning": ParagraphStyle(
            "W", fontSize=8.5, leading=12, textColor=C_WARNING,
            fontName="Helvetica", spaceAfter=2),
        "danger": ParagraphStyle(
            "D", fontSize=8.5, leading=12, textColor=C_DANGER,
            fontName="Helvetica", spaceAfter=2),
        "success": ParagraphStyle(
            "Su", fontSize=8.5, leading=12, textColor=C_SUCCESS,
            fontName="Helvetica", spaceAfter=2),
        "footer": ParagraphStyle(
            "F", fontSize=7.5, leading=10, textColor=C_MID,
            fontName="Helvetica", alignment=TA_CENTER),
        "kl": ParagraphStyle(
            "KL", fontSize=7.5, leading=10, textColor=C_MID,
            fontName="Helvetica"),
        "kv": ParagraphStyle(
            "KV", fontSize=10, leading=13, textColor=C_DARK,
            fontName="Helvetica-Bold"),
        "caption": ParagraphStyle(
            "Cap", fontSize=8, leading=11, textColor=C_MID,
            fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4),
        "badge_text": ParagraphStyle(
            "BT", fontSize=11, leading=16, textColor=C_WHITE,
            fontName="Helvetica-Bold"),
        "sf_badge_text": ParagraphStyle(
            "SB", fontSize=10, leading=14, textColor=C_WHITE,
            fontName="Helvetica-Bold"),
        "tblock_key": ParagraphStyle(
            "TK", fontSize=8.5, leading=12, textColor=C_MID,
            fontName="Helvetica"),
        "tblock_val": ParagraphStyle(
            "TV", fontSize=9, leading=13, textColor=C_DARK,
            fontName="Helvetica-Bold"),
    }


# ── Builders ────────────────────────────────────────────────────────────────

def _rule(story):
    story.append(HRFlowable(width="100%", thickness=0.5,
                            color=C_RULE, spaceAfter=6, spaceBefore=2))

def _section(story, title, st):
    story.append(Paragraph(title, st["section"]))
    _rule(story)

def _kv_table(rows_data, st, col_w=None):
    w = col_w or [55*mm, 105*mm]
    rows = [[Paragraph(k, st["kl"]), Paragraph(str(v), st["kv"])]
            for k, v in rows_data]
    t = Table(rows, colWidths=w)
    t.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_ROW_A, C_WHITE]),
        ("BOX",      (0,0), (-1,-1), 0.4, C_RULE),
        ("INNERGRID",(0,0), (-1,-1), 0.4, C_RULE),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("VALIGN",   (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t

def _badge(text, color, st_key, st, width_mm=50):
    b = Table([[Paragraph(f"  {text}  ", st[st_key])]], colWidths=[width_mm*mm])
    b.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), color),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    return b

def _embed_fig(story, path, st, caption="", max_w_mm=155):
    if not path or not os.path.exists(path):
        return
    try:
        img = Image(path)
        scale = min((max_w_mm*mm) / img.drawWidth, 1.0)
        img.drawWidth  *= scale
        img.drawHeight *= scale
        story.append(img)
        if caption:
            story.append(Paragraph(caption, st["caption"]))
        story.append(Spacer(1, 3*mm))
    except Exception:
        pass

def _m3_table(results, st):
    mc = {"Conservative": C_SUCCESS, "Balanced": C_ACCENT, "Aggressive": C_DANGER}
    header = ["Mode","Speed (m/min)","Feed (mm/rev)","Depth (mm)","Tool Life (min)","Failure Risk"]
    rows = [header]
    for r in results:
        tl = r.get("tool_life (min)", 0)
        rows.append([r["Mode"], str(r.get("speed (m/min)","-")),
                     str(r.get("feed (mm/rev)","-")), str(r.get("depth (mm)","-")),
                     ">10,000" if tl > 10000 else str(tl),
                     r.get("Failure Risk","-")])
    cw = [30*mm, 28*mm, 28*mm, 24*mm, 28*mm, 24*mm]
    t  = Table(rows, colWidths=cw)
    cmds = [
        ("BACKGROUND",   (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 8),
        ("BOX",          (0,0), (-1,-1), 0.4, C_RULE),
        ("INNERGRID",    (0,0), (-1,-1), 0.4, C_RULE),
        ("LEFTPADDING",  (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("ALIGN",        (1,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_ROW_A, C_WHITE]),
    ]
    for i, r in enumerate(results, 1):
        cmds.append(("TEXTCOLOR", (0,i), (0,i), mc.get(r["Mode"], C_MID)))
        cmds.append(("FONTNAME",  (0,i), (0,i), "Helvetica-Bold"))
        fr_c = C_DANGER if r.get("Failure Risk") == "Yes" else C_SUCCESS
        cmds.append(("TEXTCOLOR", (5,i), (5,i), fr_c))
    t.setStyle(TableStyle(cmds))
    return t

def _title_block_table(meta: dict, timestamp: str, st) -> Table:
    """Render the project title block as a two-column table."""
    engineer    = meta.get("engineer", "")
    institution = meta.get("institution", "")
    company     = meta.get("company", "")
    by_line     = engineer
    if institution: by_line += f"  |  {institution}"
    if company:     by_line += f"  |  {company}"

    rows = [
        ("Project",   meta.get("project_name", "MechAssist Engineering Analysis")),
        ("Engineer",  by_line),
        ("Date",      timestamp),
        ("Revision",  meta.get("revision", "Rev 1.0")),
        ("Generated", "MechAssist v1.0"),
    ]
    if meta.get("notes"):
        rows.append(("Notes", meta["notes"]))

    tbl_rows = [[Paragraph(k, st["tblock_key"]), Paragraph(v, st["tblock_val"])]
                for k, v in rows]
    t = Table(tbl_rows, colWidths=[35*mm, 130*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), C_ROW_A),
        ("BACKGROUND",   (0,0), (0,-1),  colors.HexColor("#edf0f7")),
        ("BOX",          (0,0), (-1,-1), 0.5, C_RULE),
        ("INNERGRID",    (0,0), (-1,-1), 0.3, C_RULE),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ]))
    return t


# ── Header / Footer ──────────────────────────────────────────────────────────

def _hf(timestamp, project="MechAssist Engineering Report"):
    def _draw(canvas, doc):
        canvas.saveState()
        H = A4[1]
        canvas.setFillColor(C_DARK)
        canvas.rect(15*mm, H-18*mm, W-30*mm, 10*mm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(20*mm, H-12.5*mm, "MechAssist")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#94a3b8"))
        canvas.drawString(48*mm, H-12.5*mm, project)
        canvas.drawRightString(W-20*mm, H-12.5*mm, f"Generated: {timestamp}")
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(C_MID)
        canvas.drawCentredString(W/2, 10*mm,
            f"MechAssist v1.0  |  Page {doc.page}")
        canvas.setStrokeColor(C_RULE)
        canvas.setLineWidth(0.4)
        canvas.line(15*mm, 14*mm, W-15*mm, 14*mm)
        canvas.restoreState()
    return _draw


# ── Main export ──────────────────────────────────────────────────────────────

def export_report(data: dict, filepath: str):
    timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M")
    st        = _styles()
    story     = []
    meta      = data.get("meta", {})

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=22*mm, bottomMargin=20*mm,
    )

    # ── Cover ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Engineering Decision Report", st["title"]))
    story.append(Spacer(1, 3*mm))
    story.append(_title_block_table(meta, timestamp, st))
    story.append(Spacer(1, 5*mm))
    _rule(story)
    story.append(Spacer(1, 2*mm))

    # ── 1. Narrative ──────────────────────────────────────────────────────
    if data.get("narrative"):
        _section(story, "1. Engineering Narrative", st)
        story.append(Paragraph(data["narrative"], st["body_dark"]))
        story.append(Spacer(1, 3*mm))

    # ── 2. Material Selection ─────────────────────────────────────────────
    if data.get("m1_results"):
        _section(story, "2. Material Selection — Module 1", st)

        inp = data.get("m1_inputs", {})
        if inp:
            story.append(Paragraph("Design Requirements", st["subsection"]))
            us  = inp.get("unit_sys", "SI")
            sl  = "ksi" if "ksi" in us else "MPa"
            dl  = "lb/ft3" if "lb" in us else "kg/m3"
            story.append(_kv_table([
                (f"Min Yield Strength ({sl})", f"{inp.get('sy','–')}"),
                (f"Max Density ({dl})",         f"{inp.get('ro','–')}"),
                ("Min Elongation (%)",           f"{inp.get('a5','–')}"),
                ("(Internal SI values)",
                 f"Sy={inp.get('sy_mpa','–'):.4g} MPa  |  "
                 f"Density={inp.get('ro_kgm3','–'):.4g} kg/m3"),
            ], st))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Candidate Materials", st["subsection"]))
        header = ["Rank","Material","Sy (MPa)","Density (kg/m3)","Elong (%)","Failure Concern"]
        rows = [header]
        fc_map = {}
        for i, r in enumerate(data["m1_results"], 1):
            fc = r["Failure Concern"]
            fc_map[i] = C_DANGER if "Fracture" in fc else C_WARNING if "Fatigue" in fc else C_MID
            rows.append([f"#{i}", r["Material"],
                         str(r["Yield Strength (MPa)"]),
                         str(r["Density (kg/m\u00b3)"]),
                         str(r["Elongation (%)"]), fc])
        cw = [12*mm, 50*mm, 22*mm, 28*mm, 22*mm, 32*mm]
        t  = Table(rows, colWidths=cw)
        cmds = [
            ("BACKGROUND",   (0,0), (-1,0), C_DARK),
            ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
            ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",     (0,0), (-1,-1), 8),
            ("BOX",          (0,0), (-1,-1), 0.4, C_RULE),
            ("INNERGRID",    (0,0), (-1,-1), 0.4, C_RULE),
            ("LEFTPADDING",  (0,0), (-1,-1), 5),
            ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",   (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ("ALIGN",        (2,0), (-1,-1), "CENTER"),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_ROW_A, C_WHITE]),
            *[("TEXTCOLOR", (5,i), (5,i), fc_map[i])
              for i in range(1, len(data["m1_results"])+1)],
        ]
        t.setStyle(TableStyle(cmds))
        story.append(t)

        top = data["m1_results"][0]
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph("Selection Rationale", st["subsection"]))
        story.append(Paragraph(
            f"Top-ranked material <b>{top['Material']}</b> selected based on highest "
            f"yield strength ({top['Yield Strength (MPa)']} MPa) within density and "
            f"elongation constraints. Primary failure concern: {top['Failure Concern']}. "
            f"Materials ranked by descending Sy, ascending density. "
            f"Su estimated as 1.3 x Sy where tabulated value unavailable.",
            st["body"]))
        story.append(Spacer(1, 3*mm))

    # ── 3. Stress Assessment ──────────────────────────────────────────────
    if data.get("m2_result"):
        _section(story, "3. Stress Assessment — Module 2", st)
        r         = data["m2_result"]
        risk      = r["Risk Category"]
        vm        = r["Von Mises Stress (Pa)"]
        conf      = r["Confidence (%)"]
        ratio     = r["Stress Ratio (\u03c3_vm/Sy)"]
        inp       = data.get("m2_inputs", {})
        sy_pa     = inp.get("sy_mpa", 1) * 1e6
        sf_target = inp.get("sf_target", 2.0)
        sf        = sy_pa / vm if vm > 0 else float("inf")
        sf_s      = "inf" if sf == float("inf") else f"{sf:.3f}"
        sf_pass   = sf >= sf_target
        allow_mpa = sy_pa / sf_target / 1e6

        if inp:
            story.append(Paragraph("Analysis Inputs", st["subsection"]))
            story.append(_kv_table([
                ("Member Type",          inp.get("member","–").capitalize()),
                ("Normal Stress s",      f"{inp.get('sigma_mpa','–'):.4g} MPa"),
                ("Shear Stress t",       f"{inp.get('tau_mpa','–'):.4g} MPa"),
                ("Yield Strength Sy",    f"{inp.get('sy_mpa','–'):.4g} MPa"),
                ("UTS Su",               f"{inp.get('su_mpa','–'):.4g} MPa"),
                ("Target Safety Factor", f"{sf_target:.1f}"),
                ("Allowable s_vm",       f"{allow_mpa:.4g} MPa  (= Sy / SF_target)"),
            ], st))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Assessment Result", st["subsection"]))

        ml_badge = _badge(risk, RISK_C.get(risk, C_MID), "badge_text", st, width_mm=52)
        sf_badge = _badge(
            "SF Check: PASS" if sf_pass else "SF Check: FAIL",
            C_PASS if sf_pass else C_FAIL,
            "sf_badge_text", st, width_mm=44)

        info_txt = (f"  SF = {sf_s}  vs  target {sf_target:.1f}  |  "
                    f"Certainty: {conf}%  |  s_vm/Sy: {ratio:.4f}")
        badge_row = Table(
            [[ml_badge, Spacer(4,1), sf_badge,
              Paragraph(info_txt, ParagraphStyle(
                  "BI", fontSize=8.5, fontName="Helvetica",
                  textColor=C_MID, leading=12))]],
            colWidths=[54*mm, 4*mm, 46*mm, 62*mm])
        badge_row.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (0,0), (-1,-1), 0),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
        ]))
        story.append(badge_row)
        story.append(Spacer(1, 3*mm))

        story.append(_kv_table([
            ("Von Mises Stress s_vm", f"{vm/1e6:.4g} MPa"),
            ("Yield Strength Sy",     f"{sy_pa/1e6:.4g} MPa"),
            ("Allowable s_vm",        f"{allow_mpa:.4g} MPa"),
            ("Safety Factor Sy/s_vm", sf_s),
            ("Stress Ratio s_vm/Sy",  f"{ratio:.4f}"),
            ("Model Certainty",       f"{conf}%"),
        ], st))

        story.append(Spacer(1, 3*mm))
        if sf_pass:
            margin = allow_mpa - vm/1e6
            story.append(Paragraph(
                f"SF Check PASS: s_vm is {margin:.4g} MPa below allowable "
                f"({allow_mpa:.4g} MPa). Design margin satisfied.",
                st["success"]))
        else:
            deficit = vm/1e6 - allow_mpa
            story.append(Paragraph(
                f"[!] SF Check FAIL: s_vm exceeds allowable by {deficit:.4g} MPa. "
                f"Reduce load, increase section, or select a higher-Sy material.",
                st["danger"]))

        if risk != "Safe":
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph("[!] Risk Interpretation", st["subsection"]))
            descs = {
                "Yield Risk":    "Stress exceeds yield strength — permanent deformation expected.",
                "Fatigue Risk":  "Repeated loading at this level will initiate cracks.",
                "Fracture Risk": "Stress near UTS — sudden fracture imminent.",
                "Buckling Risk": "Compressive load exceeds critical threshold — column will buckle.",
            }
            story.append(Paragraph(descs.get(risk, ""), st["warning"]))

        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("Mohr's Circle", st["subsection"]))
        if data.get("mohr_png") and os.path.exists(data["mohr_png"]):
            _embed_fig(story, data["mohr_png"], st,
                       caption="Figure 1 — Mohr's Circle: principal stresses and shear stress envelope.",
                       max_w_mm=155)
        else:
            story.append(Paragraph(
                "Mohr's Circle figure unavailable — run Module 2 before exporting.",
                st["body"]))
        story.append(Spacer(1, 3*mm))

    # ── 4. Machinability ─────────────────────────────────────────────────
    if data.get("m3_results"):
        _section(story, "4. Machinability Advisory — Module 3", st)

        inp = data.get("m3_inputs", {})
        if inp:
            story.append(Paragraph("Machining Parameters", st["subsection"]))
            story.append(_kv_table([
                ("Workpiece Grade",     inp.get("grade","–")),
                ("Tool Material",       inp.get("tool_mat","–")),
                ("Air Temperature",     f"{inp.get('air','–')} K"),
                ("Process Temperature", f"{inp.get('proc','–')} K"),
                ("Rotational Speed",    f"{inp.get('rpm','–')} rpm"),
                ("Torque",              f"{inp.get('torque','–')} Nm"),
                ("Base Cutting Speed",  f"{inp.get('speed','–')} m/min"),
                ("Base Feed Rate",      f"{inp.get('feed','–')} mm/rev"),
                ("Base Depth of Cut",   f"{inp.get('depth','–')} mm"),
            ], st))
            story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Cutting Condition Advisory", st["subsection"]))
        story.append(_m3_table(data["m3_results"], st))
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph("Warnings & Recommendations", st["subsection"]))
        any_warn = False
        for r in data["m3_results"]:
            for w in r.get("Warnings", []):
                story.append(Paragraph(f"[{r['Mode']}]  [!]  {w}", st["warning"]))
                any_warn = True
            for s in r.get("Suggestions", []):
                story.append(Paragraph(f"  ->  {s}", st["body"]))
        if not any_warn:
            story.append(Paragraph("No warnings — all cutting conditions nominal.", st["success"]))

        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("Tool Life Curve", st["subsection"]))
        if data.get("toollife_png") and os.path.exists(data["toollife_png"]):
            _embed_fig(story, data["toollife_png"], st,
                       caption="Figure 2 — Taylor tool life curve: tool life vs cutting speed "
                               "for Conservative, Balanced, and Aggressive modes.",
                       max_w_mm=145)
        else:
            story.append(Paragraph(
                "Tool life curve unavailable — run Module 3 before exporting.",
                st["body"]))
        story.append(Spacer(1, 3*mm))

    # ── 5. Conclusion ─────────────────────────────────────────────────────
    _section(story, "5. Conclusion", st)
    lines = []
    if data.get("m1_results"):
        top = data["m1_results"][0]
        lines.append(f"Selected material: <b>{top['Material']}</b> "
                     f"(Sy={top['Yield Strength (MPa)']} MPa, "
                     f"concern: {top['Failure Concern']}).")
    if data.get("m2_result"):
        r         = data["m2_result"]
        inp       = data.get("m2_inputs", {})
        sy_pa     = inp.get("sy_mpa", 1) * 1e6
        vm        = r["Von Mises Stress (Pa)"]
        sf        = sy_pa / vm if vm > 0 else float("inf")
        sf_s      = "inf" if sf == float("inf") else f"{sf:.3f}"
        sf_target = inp.get("sf_target", 2.0)
        sf_check  = "PASS" if sf >= sf_target else "FAIL"
        lines.append(f"Stress verdict: <b>{r['Risk Category']}</b>, "
                     f"SF={sf_s} (SF Check vs target {sf_target:.1f}: <b>{sf_check}</b>).")
    if data.get("m3_results"):
        bal = next((r for r in data["m3_results"] if r["Mode"] == "Balanced"), None)
        if bal:
            tl  = bal["tool_life (min)"]
            tls = ">10,000 min" if tl > 10000 else f"{tl} min"
            lines.append(f"Recommended machining: "
                         f"{bal.get('tool_material','Carbide')} tool at "
                         f"{bal['speed (m/min)']} m/min — tool life {tls}.")
    lines.append("All results must be verified by a qualified mechanical engineer "
                 "before implementation in a real design.")
    for line in lines:
        story.append(Paragraph(f"  {line}", st["body_dark"]))
        story.append(Spacer(1, 1*mm))
    story.append(Spacer(1, 3*mm))

    # ── Disclaimer ────────────────────────────────────────────────────────
    _rule(story)
    story.append(Paragraph(
        "Disclaimer: This report is generated by an AI-assisted decision support tool. "
        "All results should be verified by a qualified mechanical engineer before "
        "implementation. MechAssist does not replace professional engineering judgment.",
        st["footer"]))

    # ── Build ─────────────────────────────────────────────────────────────
    project = meta.get("project_name", "MechAssist Engineering Report")
    doc.build(story, onFirstPage=_hf(timestamp, project),
              onLaterPages=_hf(timestamp, project))
    return filepath