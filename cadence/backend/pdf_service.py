"""
PDF weekly report generation using ReportLab.
Dark-themed, premium design consistent with the Cadence brand.
"""
import io
from datetime import date, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Brand colours
BLACK  = colors.HexColor("#0A0A0A")
GOLD   = colors.HexColor("#C9A84C")
GOLD_L = colors.HexColor("#E5C472")
WHITE  = colors.HexColor("#F5F5F5")
MUTED  = colors.HexColor("#888888")
DARK   = colors.HexColor("#1A1A1A")
BORDER = colors.HexColor("#2A2A2A")


def _styles():
    return {
        "title":    ParagraphStyle("title",    fontName="Helvetica-Bold",  fontSize=22, textColor=GOLD,   spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica",       fontSize=10, textColor=MUTED,  spaceAfter=16),
        "h2":       ParagraphStyle("h2",       fontName="Helvetica-Bold",  fontSize=13, textColor=GOLD_L, spaceBefore=14, spaceAfter=6),
        "h3":       ParagraphStyle("h3",       fontName="Helvetica-Bold",  fontSize=10, textColor=WHITE,  spaceBefore=8,  spaceAfter=4),
        "body":     ParagraphStyle("body",     fontName="Helvetica",       fontSize=9,  textColor=WHITE,  spaceAfter=5,  leading=14),
        "muted":    ParagraphStyle("muted",    fontName="Helvetica",       fontSize=8,  textColor=MUTED,  spaceAfter=3),
        "label":    ParagraphStyle("label",    fontName="Helvetica-Bold",  fontSize=8,  textColor=MUTED,  spaceAfter=2),
        "gold":     ParagraphStyle("gold",     fontName="Helvetica-Bold",  fontSize=11, textColor=GOLD,   spaceAfter=4),
        "right":    ParagraphStyle("right",    fontName="Helvetica",       fontSize=8,  textColor=MUTED,  alignment=TA_RIGHT),
    }


def _pct(v):
    return f"{round(v * 100)}%" if v is not None else "—"


def _trend_arrow(trend):
    return {"improving": "↑", "declining": "↓", "stable": "→"}.get(trend or "", "—")


def generate_pdf(user_profile, metrics, patterns, review, friday, monday, week_start_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f"Cadence — Weekly Report {week_start_date}",
    )

    s = _styles()
    story = []

    # Header
    story.append(Paragraph("CADENCE", s["title"]))
    story.append(Paragraph(
        f"Weekly Operational Report &nbsp;·&nbsp; Week of {week_start_date} &nbsp;·&nbsp; {user_profile.get('role_type', '')}",
        s["subtitle"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=12))

    # Metrics grid
    story.append(Paragraph("OPERATIONAL METRICS", s["h2"]))

    est = metrics.get("execution_score_trend") or {}
    fpi = metrics.get("friction_pattern_index") or {}

    metric_data = [
        ["METRIC", "VALUE", "TREND"],
        ["Priority Completion Rate", _pct(metrics.get("priority_completion_rate")), ""],
        ["Deep Work Frequency", f"{metrics.get('deep_work_frequency', '—')} blocks/day", ""],
        ["Deferral Rate", _pct(metrics.get("deferral_rate")), ""],
        ["Planning Accuracy", _pct(metrics.get("planning_accuracy")), ""],
        ["Execution Score", f"{est.get('current_avg', '—')}/10", _trend_arrow(est.get("trend"))],
        ["Reactive Work Ratio", _pct(metrics.get("reactive_work_ratio")), ""],
        ["Primary Friction", (fpi.get("tag") or "—").replace("_", " "), f"{fpi.get('frequency_pct', '—')}% of days"],
    ]

    tbl = Table(metric_data, colWidths=[75*mm, 50*mm, 45*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), DARK),
        ("TEXTCOLOR",   (0,0), (-1,0), GOLD),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("TEXTCOLOR",   (0,1), (-1,-1), WHITE),
        ("BACKGROUND",  (0,1), (-1,-1), BLACK),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLACK, DARK]),
        ("GRID",        (0,0), (-1,-1), 0.3, BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # Weekly commitments vs outcomes
    if monday:
        story.append(Paragraph("PRIORITIES — COMMITMENTS VS OUTCOMES", s["h2"]))
        p_data = [["PRIORITY", "STATUS"]]
        for i in range(1, 6):
            p = monday.get(f"priority_{i}")
            if p:
                status = friday.get(f"priority_{i}_status", "—") if friday else "—"
                p_data.append([p, status.upper()])
        if len(p_data) > 1:
            ptbl = Table(p_data, colWidths=[120*mm, 50*mm])
            ptbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), DARK),
                ("TEXTCOLOR",   (0,0), (-1,0), GOLD),
                ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("TEXTCOLOR",   (0,1), (-1,-1), WHITE),
                ("BACKGROUND",  (0,1), (-1,-1), BLACK),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLACK, DARK]),
                ("GRID",        (0,0), (-1,-1), 0.3, BORDER),
                ("TOPPADDING",  (0,0), (-1,-1), 5),
                ("BOTTOMPADDING",(0,0), (-1,-1), 5),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
            ]))
            story.append(ptbl)
            story.append(Spacer(1, 10))

    # Time allocation
    if friday:
        story.append(Paragraph("TIME ALLOCATION", s["h2"]))
        time_data = [["CATEGORY", "HOURS"]]
        for k, label in [("deep_work_hours","Deep Work"), ("meetings_hours","Meetings"),
                          ("admin_hours","Admin"), ("reactive_work_hours","Reactive"),
                          ("learning_hours","Learning"), ("low_leverage_hours","Low-Leverage")]:
            h = friday.get(k) or 0
            time_data.append([label, f"{h}h"])
        ttbl = Table(time_data, colWidths=[100*mm, 70*mm])
        ttbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), GOLD),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("TEXTCOLOR",   (0,1), (-1,-1), WHITE),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [BLACK, DARK]),
            ("GRID",        (0,0), (-1,-1), 0.3, BORDER),
            ("TOPPADDING",  (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",(0,0), (-1,-1), 5),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(ttbl)
        story.append(Spacer(1, 10))

    # AI Review
    if review:
        story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=10))
        story.append(Paragraph("AI DIAGNOSTIC REVIEW", s["h2"]))

        if review.get("diagnosis"):
            story.append(Paragraph("DIAGNOSIS", s["label"]))
            story.append(Paragraph(review["diagnosis"], s["body"]))

        if review.get("evidence"):
            story.append(Paragraph("EVIDENCE", s["label"]))
            for line in review["evidence"].split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), s["body"]))

        if review.get("intervention"):
            story.append(Paragraph("INTERVENTION", s["label"]))
            story.append(Paragraph(review["intervention"], s["gold"]))

        if review.get("maturity_label"):
            story.append(Paragraph(f"Signal maturity: {review['maturity_label']}", s["muted"]))

    # Patterns
    if patterns:
        story.append(Paragraph("DETECTED FAILURE PATTERNS", s["h2"]))
        for p in patterns:
            story.append(Paragraph(
                f"{p['pattern_name']} — {p['maturity']} ({round(p['confidence_score']*100)}% confidence)",
                s["h3"]
            ))
            story.append(Paragraph(p["evidence"], s["muted"]))

    # Reflection
    if friday and friday.get("reflection_text"):
        story.append(Paragraph("WEEKLY REFLECTION", s["h2"]))
        story.append(Paragraph(friday["reflection_text"], s["body"]))

    # Footer
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.3, color=BORDER, spaceAfter=4))
    story.append(Paragraph(
        f"Generated by Cadence &nbsp;·&nbsp; {date.today().isoformat()} &nbsp;·&nbsp; Confidential",
        s["right"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
