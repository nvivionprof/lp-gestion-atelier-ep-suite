from __future__ import annotations
from datetime import timedelta, time
from django.utils import timezone
from .models import Reservation, EducationalSystem


def week_bounds(day=None):
    day = day or timezone.localdate()
    start = day - timedelta(days=day.weekday())
    end = start + timedelta(days=7)
    return start, end


def system_effective_status(system: EducationalSystem):
    now = timezone.now()
    if system.statut in {'maintenance', 'hors_service', 'archive'}:
        return system.statut
    if system.sessions.filter(statut='ouverte').exists():
        return 'en_utilisation'
    if system.anomalies.filter(blocking=True).exclude(statut__in=['resolue', 'annulee']).exists() or system.anomalies.filter(gravite='bloquante').exclude(statut__in=['resolue', 'annulee']).exists():
        return 'hors_service'
    if system.anomalies.exclude(statut__in=['resolue', 'annulee']).exists():
        return 'alerte'
    if system.reservations.filter(date_debut__lte=now, date_fin__gte=now).exclude(statut__in=['annulee', 'refusee']).exists():
        return 'reserve'
    return system.statut or 'disponible'


def current_reservation_for_system(system):
    now = timezone.now()
    return system.reservations.filter(date_debut__lte=now, date_fin__gte=now).exclude(statut__in=['annulee', 'refusee']).order_by('date_debut').first()


def upcoming_reservations(system, limit=5):
    return system.reservations.filter(date_fin__gte=timezone.now()).exclude(statut__in=['annulee', 'refusee']).order_by('date_debut')[:limit]
