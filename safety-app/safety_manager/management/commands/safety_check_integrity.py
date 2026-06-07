from django.core.management.base import BaseCommand
from safety_manager.models import RiskFamily, SafetyZone, RiskAssessment, PreventionAction, SafetyEvent


class Command(BaseCommand):
    help = 'Contrôle simple d’intégrité Safety Manager.'

    def handle(self, *args, **options):
        errors = []
        if RiskFamily.objects.count() == 0:
            errors.append('Aucune famille de risque. Lancer seed_safety_manager.')
        if SafetyZone.objects.count() == 0:
            errors.append('Aucune zone Safety. Lancer seed_safety_manager.')
        orphan_actions = PreventionAction.objects.filter(risk_assessment__isnull=True, event__isnull=True).count()
        if orphan_actions:
            self.stdout.write(self.style.WARNING(f'{orphan_actions} action(s) sans risque ni événement associé.'))
        if errors:
            for e in errors:
                self.stdout.write(self.style.ERROR(e))
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('Contrôle Safety Manager OK.'))
        self.stdout.write(f'Risques : {RiskAssessment.objects.count()} | Actions : {PreventionAction.objects.count()} | Événements : {SafetyEvent.objects.count()}')
