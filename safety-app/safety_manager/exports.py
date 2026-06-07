from __future__ import annotations
from io import BytesIO
import csv
from django.http import HttpResponse
from django.utils import timezone
from .models import RiskAssessment, PreventionAction, SafetyEvent, DUERPVersion


def _pdf_response(filename: str):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _try_reportlab_canvas(response):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
        return canvas.Canvas(response, pagesize=A4), A4, cm
    except Exception:
        return None, None, None


def draw_wrapped(c, text, x, y, max_chars=95, line_height=12):
    text = str(text or '')
    words = text.replace('\r', '').split()
    lines, line = [], ''
    for w in words:
        if len(line) + len(w) + 1 > max_chars:
            lines.append(line)
            line = w
        else:
            line = f'{line} {w}'.strip()
    if line:
        lines.append(line)
    for line in lines or ['']:
        c.drawString(x, y, line[:max_chars])
        y -= line_height
    return y


def export_duerp_pdf(request):
    response = _pdf_response(f'duerp_safety_{timezone.localdate().isoformat()}.pdf')
    c, A4, cm = _try_reportlab_canvas(response)
    if not c:
        response.write(b'ReportLab non installe. Ajouter reportlab aux requirements puis rebuild.')
        return response
    width, height = A4
    y = height - 1.5 * cm
    c.setTitle('DUERP Safety Manager')
    c.setFont('Helvetica-Bold', 16)
    c.drawString(1.5 * cm, y, 'DUERP — Safety Manager')
    y -= 0.7 * cm
    c.setFont('Helvetica', 9)
    c.drawString(1.5 * cm, y, f'Generation : {timezone.localtime().strftime("%d/%m/%Y %H:%M")}')
    y -= 0.7 * cm
    c.setFont('Helvetica-Bold', 11)
    c.drawString(1.5 * cm, y, 'Inventaire des risques')
    y -= 0.5 * cm
    c.setFont('Helvetica', 8)
    risks = RiskAssessment.objects.select_related('unite_travail', 'famille_risque').exclude(statut='archive').order_by('priorite_calculee', 'code')
    for risk in risks:
        if y < 2.3 * cm:
            c.showPage(); y = height - 1.5 * cm; c.setFont('Helvetica', 8)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(1.5 * cm, y, f'{risk.code} — P{risk.priorite_calculee} — {risk.famille_risque.nom}')
        y -= 0.35 * cm
        c.setFont('Helvetica', 8)
        y = draw_wrapped(c, f'UT : {risk.unite_travail} | Danger : {risk.danger}', 1.7 * cm, y, 110, 10)
        y = draw_wrapped(c, f'Situation : {risk.situation_dangereuse}', 1.7 * cm, y, 110, 10)
        y = draw_wrapped(c, f'Mesures existantes : {risk.mesures_existantes}', 1.7 * cm, y, 110, 10)
        y = draw_wrapped(c, f'Actions proposees : {risk.mesures_a_proposer}', 1.7 * cm, y, 110, 10)
        y -= 0.25 * cm
    c.showPage(); c.save()
    DUERPVersion.objects.create(perimetre='Export DUERP complet', commentaire='Export PDF généré depuis Safety Manager')
    return response


def export_actions_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="actions_safety.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['code', 'titre', 'origine', 'responsable', 'priorite', 'echeance', 'statut', 'commentaire'])
    for action in PreventionAction.objects.select_related('responsable').all():
        writer.writerow([action.code, action.titre, action.get_origine_display(), action.responsable or '', action.priorite, action.echeance or '', action.get_statut_display(), action.commentaire])
    return response


def export_risks_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="risques_duerp_safety.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['code', 'unite_travail', 'famille', 'danger', 'situation_dangereuse', 'dommage', 'gravite', 'frequence', 'priorite', 'mesures_existantes', 'mesures_a_proposer', 'statut'])
    for risk in RiskAssessment.objects.select_related('unite_travail', 'famille_risque').all():
        writer.writerow([risk.code, risk.unite_travail, risk.famille_risque, risk.danger, risk.situation_dangereuse, risk.dommage_potentiel, risk.gravite, risk.frequence, risk.priorite_calculee, risk.mesures_existantes, risk.mesures_a_proposer, risk.get_statut_display()])
    return response


def export_event_pdf(request, event: SafetyEvent):
    response = _pdf_response(f'analyse_{event.code}.pdf')
    c, A4, cm = _try_reportlab_canvas(response)
    if not c:
        response.write(b'ReportLab non installe. Ajouter reportlab aux requirements puis rebuild.')
        return response
    width, height = A4
    y = height - 1.5 * cm
    c.setFont('Helvetica-Bold', 15)
    c.drawString(1.5 * cm, y, f'Analyse événement — {event.code}')
    y -= 0.7 * cm
    c.setFont('Helvetica', 9)
    for label, value in [
        ('Type', event.get_type_evenement_display()), ('Date', event.date), ('Zone', event.zone or ''),
        ('Personne concernée', event.personne_concernee or ''), ('Arrêt', 'Oui' if event.avec_arret else 'Non'),
    ]:
        c.drawString(1.5 * cm, y, f'{label} : {value}')
        y -= 0.4 * cm
    y -= 0.2 * cm
    y = draw_wrapped(c, f'Récit : {event.recit_detaille or event.description_courte}', 1.5 * cm, y, 105, 11)
    y -= 0.4 * cm
    c.setFont('Helvetica-Bold', 10); c.drawString(1.5 * cm, y, 'Faits recueillis'); y -= 0.4 * cm
    c.setFont('Helvetica', 8)
    for fact in event.facts.all():
        if y < 2 * cm:
            c.showPage(); y = height - 1.5 * cm; c.setFont('Helvetica', 8)
        y = draw_wrapped(c, f'- [{fact.get_categorie_display()} / {fact.get_type_fait_display()}] {fact.description}', 1.7 * cm, y, 105, 10)
    y -= 0.4 * cm
    c.setFont('Helvetica-Bold', 10); c.drawString(1.5 * cm, y, 'Actions correctives'); y -= 0.4 * cm
    c.setFont('Helvetica', 8)
    for action in event.actions.all():
        y = draw_wrapped(c, f'- {action.code} — {action.titre} — {action.get_statut_display()}', 1.7 * cm, y, 105, 10)
    c.showPage(); c.save()
    return response



def export_events_pdf(request):
    """Export PDF filtrable des événements Safety."""
    response = _pdf_response(f'evenements_safety_{timezone.localdate().isoformat()}.pdf')
    c, A4, cm = _try_reportlab_canvas(response)
    if not c:
        response.write(b'ReportLab non installe. Ajouter reportlab aux requirements puis rebuild.')
        return response
    qs = SafetyEvent.objects.select_related('zone', 'personne_concernee').all().order_by('-date')
    if request.GET.get('type_evenement'):
        qs = qs.filter(type_evenement=request.GET['type_evenement'])
    if request.GET.get('zone'):
        qs = qs.filter(zone_id=request.GET['zone'])
    if request.GET.get('classe'):
        qs = qs.filter(classe_ou_groupe=request.GET['classe'])
    if request.GET.get('date_debut'):
        qs = qs.filter(date__gte=request.GET['date_debut'])
    if request.GET.get('date_fin'):
        qs = qs.filter(date__lte=request.GET['date_fin'])
    width, height = A4
    y = height - 1.5 * cm
    c.setFont('Helvetica-Bold', 15)
    c.drawString(1.5 * cm, y, 'Rapport événements — Safety Manager')
    y -= 0.6 * cm
    c.setFont('Helvetica', 8)
    c.drawString(1.5 * cm, y, f'Génération : {timezone.localtime().strftime("%d/%m/%Y %H:%M")}')
    y -= 0.6 * cm
    for event in qs[:400]:
        if y < 2.2 * cm:
            c.showPage(); y = height - 1.5 * cm; c.setFont('Helvetica', 8)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(1.5 * cm, y, f'{event.code} — {event.get_type_evenement_display()} — {event.date}')
        y -= 0.35 * cm
        c.setFont('Helvetica', 8)
        person = event.personne_concernee or '—'
        zone = event.zone or '—'
        y = draw_wrapped(c, f'Zone : {zone} | Classe : {event.classe_ou_groupe or "—"} | Personne : {person}', 1.7 * cm, y, 105, 10)
        y = draw_wrapped(c, f'Description : {event.description_courte}', 1.7 * cm, y, 105, 10)
        y -= 0.25 * cm
    c.showPage(); c.save()
    return response
