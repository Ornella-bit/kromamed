"""Rapport PDF (A4) d'une analyse. Généré en mémoire, jamais enregistré."""
from __future__ import annotations
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from kromamed import config as C

NAVY, TEAL = colors.HexColor("#0B1F3A"), colors.HexColor("#0E6B6E")
GREEN, RED, AMBER, GREY = (colors.HexColor("#1E7F5C"), colors.HexColor("#B42318"),
                           colors.HexColor("#B7791F"), colors.HexColor("#5B6B7F"))
ICON = Path(__file__).resolve().parent.parent / "web" / "static" / "02_icone_application.png"


def _fmt_time(seconds: int) -> str:
    return f"{seconds} s" if seconds < 60 else f"{seconds // 60} min" if seconds % 60 == 0 else f"{seconds} s"


def build_report_pdf(patient_id: str, date_text: str | None, result: dict) -> bytes:
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13)
    small = ParagraphStyle("small", parent=body, fontSize=8, leading=10.5, textColor=GREY)
    h2 = ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, spaceBefore=10, spaceAfter=4)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=34 * mm, bottomMargin=18 * mm,
                            title="Rapport d'analyse urinaire - KromaMed", author="KromaMed")

    def header(canvas, d):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 26 * mm, A4[0], 26 * mm, stroke=0, fill=1)
        if ICON.exists():
            canvas.drawImage(str(ICON), 18 * mm, A4[1] - 22 * mm, 16 * mm, 16 * mm, mask="auto")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(38 * mm, A4[1] - 14 * mm, "KROMA MED")
        canvas.setFont("Helvetica", 9.5)
        canvas.drawString(38 * mm, A4[1] - 20 * mm, "Rapport d'analyse urinaire (aide a la lecture)")
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(18 * mm, 10 * mm, "Ce document n'est pas un diagnostic medical. Consultez un professionnel de sante.")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {d.page}")
        canvas.restoreState()

    when = date_text or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story = []
    meta = Table([
        ["Date du test", when, "Identifiant", patient_id or "ANONYME"],
        ["Bandelette", C.BRAND + " (demo)", "Qualite capture",
         f"{round(result['quality']['overall'] * 100)} %"],
    ], colWidths=[26 * mm, 62 * mm, 30 * mm, 54 * mm])
    meta.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9), ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9), ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story += [meta, Spacer(1, 6)]

    summ = result.get("summary", {})
    tone = {"ok": GREEN, "alert": RED, "warn": AMBER}.get(summ.get("level"), GREY)
    banner = Table([[Paragraph(f"<font color='white'><b>{summ.get('headline', '')}</b></font>", body)]],
                   colWidths=[172 * mm])
    banner.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), tone),
                                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [banner, Spacer(1, 4)]
    for line in summ.get("details", []):
        story.append(Paragraph("- " + line, body))

    story.append(Paragraph("Resultats par parametre", h2))
    rows = [["#", "Parametre", "Resultat", "Statut", "Lecture ideale"]]
    styles_cmds = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                   ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9), ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
                   ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7DBD5")),
                   ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F6F7F4")]),
                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    for i, p in enumerate(result["pads"], start=1):
        if p["status"] == "ok":
            status, col = ("Normal", GREEN) if p["normal"] else ("Anormal", RED)
        else:
            status, col = "Indetermine", GREY
        rows.append([str(i), C.LABELS_FR.get(p["param"], p["param"]), p["level"] or "-", status,
                     _fmt_time(C.READ_TIME_S.get(p["param"], 60))])
        styles_cmds.append(("TEXTCOLOR", (3, i), (3, i), col))
        styles_cmds.append(("FONT", (3, i), (3, i), "Helvetica-Bold", 9))
    table = Table(rows, colWidths=[10 * mm, 52 * mm, 40 * mm, 34 * mm, 36 * mm])
    table.setStyle(TableStyle(styles_cmds))
    story.append(table)

    story.append(Paragraph("A savoir", h2))
    story.append(Paragraph(
        "Chaque parametre de la bandelette a son propre temps de lecture (30 s a 2 min). "
        "Une photo unique a 60 s est un compromis : les leucocytes (2 min) peuvent etre sous-estimes, "
        "le glucose et la bilirubine (30 s) peuvent etre sur-estimes. "
        "Les couleurs de reference utilisees sont des valeurs de demonstration, non validees cliniquement.", body))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "AVERTISSEMENT : resultat issu d'un traitement algorithmique experimental. Il ne remplace ni un "
        "examen de laboratoire ni l'avis d'un medecin.", small))
    doc.build(story, onFirstPage=header, onLaterPages=header)
    return buf.getvalue()
