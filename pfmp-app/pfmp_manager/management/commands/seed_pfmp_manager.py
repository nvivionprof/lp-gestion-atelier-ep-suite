from django.core.management.base import BaseCommand
from datetime import date
from pfmp_manager.models import Formation, Company, CompanyContact, PfmpPeriod
class Command(BaseCommand):
    def handle(self,*args,**opts):
        demo, _ = Formation.objects.get_or_create(code='DEMO', defaults={'nom':'Démonstration atelier'})
        melec, _ = Formation.objects.get_or_create(code='MELEC', defaults={'nom':'Bac Pro MELEC'})
        ciel, _ = Formation.objects.get_or_create(code='CIEL', defaults={'nom':'Bac Pro CIEL'})
        c1, _ = Company.objects.get_or_create(name='Entreprise Démo Énergies', defaults={'activity':'Installations électriques et smart building','city':'Le Mans','postal_code':'72000','status':'active','student_visible_notes':'Entreprise partenaire utilisée pour la démonstration PFMP.'})
        c1.formations.add(demo, melec, ciel)
        contact, _ = CompanyContact.objects.get_or_create(company=c1, full_name='Contact PFMP Démo', defaults={'role':'Tuteur entreprise','email':'contact.demo@example.local','visibility':'students','contact_type':'pfmp'})
        contact.formations.add(demo, melec, ciel)
        PfmpPeriod.objects.get_or_create(title='PFMP Démo 2025-2026', defaults={'start_date':date(2026,1,5),'end_date':date(2026,1,30),'status':'open','class_names':'1MELEC;1CIEL'})
        self.stdout.write('PFMP Manager initialisé : entreprises, contacts et période de démonstration créés/mis à jour.')
