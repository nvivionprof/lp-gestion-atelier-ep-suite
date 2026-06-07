"""Exports PDF PedaShop.

Les PDF restent volontairement simples : une en-tête, un tableau, une zone de
validation. Cette sobriété facilite l'impression atelier et limite les
problèmes de mise en page.
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HEADER_COLOR = colors.HexColor('#0f766e')
ACCENT_COLOR = colors.HexColor('#f97316')
GRID_COLOR = colors.HexColor('#d1d5db')


def _build_pdf(title: str, rows: list[list[str]], subtitle: str = '') -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    story = [Paragraph(f'<b>{title}</b>', styles['Title'])]
    if subtitle:
        story.append(Paragraph(subtitle, styles['Normal']))
    story.append(Spacer(1, 12))
    table = Table(rows, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.25, GRID_COLOR),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
    ]))
    story.append(table)
    story.append(Spacer(1, 18))
    story.append(Paragraph('Validation / signature : ______________________________', styles['Normal']))
    doc.build(story)
    return buffer.getvalue()


def pdf_response_bytes(title: str, rows: list[list[str]], subtitle: str = '') -> bytes:
    return _build_pdf(title, rows, subtitle)


def supplier_consultation_pdf_bytes(consultation) -> bytes:
    """PDF demandé : seulement les colonnes utiles au fournisseur."""
    rows = [['Désignation', 'Fabricant', 'Référence constructeur', 'Quantité souhaitée', 'Équivalence possible']]
    for line in consultation.lignes.all():
        rows.append([
            line.designation,
            line.fabricant,
            line.reference_constructeur,
            str(line.quantite_souhaitee),
            'Oui' if line.equivalence_possible else 'Non',
        ])
    subtitle = f'N° {consultation.code} — Date : {consultation.date_creation:%d/%m/%Y}'
    return _build_pdf('PedaShop — Consultation fournisseur', rows, subtitle)
