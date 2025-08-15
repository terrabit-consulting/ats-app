from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

BRAND_PRIMARY = colors.HexColor("#0B5FFF")   # Terrabit-like blue
BRAND_ACCENT  = colors.HexColor("#111827")   # near-black text
BRAND_WARN    = colors.HexColor("#C62828")   # red accent

def build_softskills_pdf(path, candidate_name, role_title, rubric, overall_score, narrative, logo_path=None):
    doc = SimpleDocTemplate(path, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = []

    # Header with brand bar + logo
    bar = Table([[""]], colWidths=[(A4[0]-56)], rowHeights=[10])
    bar.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), BRAND_PRIMARY)]))
    story.append(bar); story.append(Spacer(1,6))

    if logo_path:
        try:
            story.append(Image(logo_path, width=60*mm, height=18*mm))
        except Exception:
            pass
    story.append(Spacer(1,6))

    title = Paragraph(f"<font color='{BRAND_ACCENT.hexval}'><b>Soft Skills Evaluation Report</b></font>", styles['Title'])
    meta  = Paragraph(f"<b>Candidate:</b> {candidate_name} &nbsp;&nbsp;&nbsp; <b>Role:</b> {role_title}", styles['Normal'])
    story += [title, Spacer(1,6), meta, Spacer(1,12)]

    data = [["Metric","Score (/5.0)"]]
    order = ["Clarity of Explanation","Depth of Knowledge","Relevance of Examples","Problem Solving Approach","Communication Skills"]
    for k in order:
        v = rubric.get(k, 0)
        data.append([k, f"{v:.2f}"])

    tbl = Table(data, colWidths=[110*mm, 40*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.whitesmoke),
        ('TEXTCOLOR',(0,0),(-1,0), BRAND_ACCENT),
        ('FONT',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.25, colors.HexColor("#e5e7eb")),
        ('ALIGN',(1,1),(1,-1),'CENTER'),
        ('BOTTOMPADDING',(0,0),(-1,0),10),
    ]))
    story += [tbl, Spacer(1,10)]

    badge = Table([[f"Soft Skills Overall Fit", f"{overall_score:.1f} / 5.0"]], colWidths=[120*mm, 30*mm])
    badge.setStyle(TableStyle([
        ('BACKGROUND',(1,0),(1,0), BRAND_WARN),
        ('TEXTCOLOR',(1,0),(1,0), colors.white),
        ('ALIGN',(1,0),(1,0),'CENTER'),
        ('FONT',(0,0),(-1,-1),'Helvetica-Bold'),
        ('BOX',(0,0),(-1,-1),0.5, BRAND_WARN),
        ('PADDING',(0,0),(-1,-1),6),
    ]))
    story += [badge, Spacer(1,8)]

    story += [Paragraph("<b>Summary</b>", styles['Heading3']), Spacer(1,2)]
    body = ParagraphStyle(name="Body", parent=styles["BodyText"], leading=14, textColor=BRAND_ACCENT)
    story += [Paragraph(narrative, body)]

    doc.build(story)
