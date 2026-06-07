from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventory.models import Category, Component, Equipment, Formation, Loan, Location, Person, SchoolClass


class Command(BaseCommand):
    help = 'Crée un jeu de données de démonstration ToolMag.'

    def handle(self, *args, **options):
        formations = {
            'BAC_CIEL': ('Bac Pro CIEL', 'Bac Pro CIEL'),
            'BAC_MELEC': ('Bac Pro MELEC', 'Bac Pro MELEC'),
            'CAP_ELEC': ('CAP Pro Électricité', 'CAP Pro Électricité — dérivé MELEC'),
            'BTS_ET': ('BTS Électrotechnique', 'BTS Électrotechnique'),
            'BTS_FED': ('BTS Fluides Énergies Domotique', 'BTS FED'),
            'STAFF': ('Équipe pédagogique', 'Aucun référentiel élève'),
        }
        formation_objs = {}
        for code, (name, ref) in formations.items():
            formation_objs[code], _ = Formation.objects.get_or_create(code=code, defaults={'name': name, 'referential_name': ref})

        for formation_code, class_name in [
            ('BAC_CIEL', '1CIEL'),
            ('BAC_CIEL', 'TCIEL'),
            ('BAC_MELEC', '1MELEC'),
            ('BAC_MELEC', 'TMELEC'),
            ('CAP_ELEC', 'CAP ELEC 1'),
            ('CAP_ELEC', 'CAP ELEC 2'),
            ('BTS_ET', 'BTS ET 1'),
            ('BTS_ET', 'BTS ET 2'),
            ('BTS_FED', 'BTS FED 1'),
            ('BTS_FED', 'BTS FED 2'),
            ('STAFF', 'Équipe pédagogique'),
        ]:
            SchoolClass.objects.get_or_create(formation=formation_objs[formation_code], name=class_name)

        elec, _ = Category.objects.get_or_create(name='Électroportatif')
        mesure, _ = Category.objects.get_or_create(name='Mesure')
        fibre, _ = Category.objects.get_or_create(name='Fibre optique')
        magasin, _ = Location.objects.get_or_create(name='Magasin atelier')

        admin, _ = Person.objects.get_or_create(code='MAG-0001', defaults={
            'first_name': 'Marc', 'last_name': 'Durand', 'username': 'marc.durand', 'role': Person.Role.STOREKEEPER,
            'allowed_roles': 'MAGASINIER;RESPONSABLE', 'department': 'Magasin', 'active': True,
        })
        user1, _ = Person.objects.get_or_create(code='USR-0001', defaults={
            'first_name': 'Lucas', 'last_name': 'Martin', 'username': 'lucas.martin', 'role': Person.Role.USER,
            'allowed_roles': 'UTILISATEUR;MAGASINIER', 'department': 'Atelier', 'formation': formation_objs['BAC_CIEL'],
            'class_name': '1CIEL', 'group_name': 'A', 'level': 'Première', 'active': True,
        })
        user2, _ = Person.objects.get_or_create(code='USR-0002', defaults={
            'first_name': 'Nora', 'last_name': 'Bernard', 'username': 'nora.bernard', 'role': Person.Role.USER,
            'allowed_roles': 'UTILISATEUR;TECH_INVENTAIRE', 'department': 'Maintenance', 'formation': formation_objs['BTS_FED'],
            'class_name': 'BTS FED 1', 'group_name': 'B', 'level': 'Première année', 'active': True,
        })
        prof, _ = Person.objects.get_or_create(code='PROF-0001', defaults={
            'first_name': 'Nicolas', 'last_name': 'Vivion', 'username': 'nicolas.vivion', 'role': Person.Role.ADMIN,
            'allowed_roles': 'UTILISATEUR;MAGASINIER;RESPONSABLE;ADMIN', 'department': 'Équipe pédagogique',
            'formation': formation_objs['STAFF'], 'class_name': 'PROF', 'group_name': 'PROF', 'level': 'Professeur', 'active': True,
        })

        # Mots de passe de démonstration. Ils sont remis à chaque seed_demo pour faciliter les essais.
        demo_passwords = {
            admin: 'mag1234',
            user1: 'user1234',
            user2: 'user1234',
            prof: 'prof1234',
        }
        for person, password in demo_passwords.items():
            person.set_password(password)
            person.must_change_password = False
            person.save()

        drill, _ = Equipment.objects.get_or_create(code='MAT-0001', defaults={'name':'Perceuse Bosch GSB 18V','description':'Perceuse-visseuse électroportative','equipment_type':Equipment.EquipmentType.SIMPLE,'category':elec,'brand':'Bosch','model':'GSB 18V','location':magasin})
        meter, _ = Equipment.objects.get_or_create(code='MAT-0002', defaults={'name':'Multimètre Fluke 179','description':'Multimètre numérique True RMS','equipment_type':Equipment.EquipmentType.KIT,'category':mesure,'brand':'Fluke','model':'179','location':magasin,'inventory_required_out':True,'inventory_required_return':True,'sensitive':True})
        analyser, _ = Equipment.objects.get_or_create(code='MAT-0003', defaults={'name':'Analyseur réseau CA8336','description':'Analyseur réseau triphasé','equipment_type':Equipment.EquipmentType.KIT,'category':mesure,'brand':'Chauvin Arnoux','model':'CA8336','location':magasin,'inventory_required_out':True,'inventory_required_return':True,'sensitive':True})
        fiber, _ = Equipment.objects.get_or_create(code='MAT-0004', defaults={'name':'Caisse fibre optique','description':'Kit soudure et contrôle fibre optique','equipment_type':Equipment.EquipmentType.KIT,'category':fibre,'location':magasin,'inventory_required_out':True,'inventory_required_return':True})

        components = {
            meter: ['Appareil principal', 'Cordons de mesure rouge/noir', 'Pointes de touche', 'Gaine de protection', 'Pile 9V', 'Housse'],
            analyser: ['Appareil principal', 'Alimentation secteur', 'Cordon tension L1', 'Cordon tension L2', 'Cordon tension L3', 'Cordon neutre', 'Pince ampèremétrique 1', 'Pince ampèremétrique 2', 'Pince ampèremétrique 3', 'Câble USB', 'Mallette'],
            fiber: ['Soudeuse fibre', 'Cliveuse', 'Pince à dénuder', 'Alimentation', 'Batterie', 'Lingettes nettoyage', 'Mallette'],
        }
        for equipment, names in components.items():
            for idx, name in enumerate(names):
                Component.objects.get_or_create(equipment=equipment, name=name, defaults={'sort_order':idx, 'required': name not in ['Câble USB', 'Lingettes nettoyage']})

        if not Loan.objects.filter(equipment=drill, status=Loan.LoanStatus.OPEN).exists():
            Loan.objects.create(equipment=drill, borrower=user1, checkout_storekeeper=admin, checked_out_at=timezone.now()-timedelta(hours=2), due_at=timezone.now()+timedelta(hours=3), condition_out=Equipment.Condition.GOOD)
            drill.status = Equipment.Status.OUT
            drill.save()
        if not Loan.objects.filter(equipment=fiber, status=Loan.LoanStatus.OPEN).exists():
            Loan.objects.create(equipment=fiber, borrower=user2, checkout_storekeeper=admin, checked_out_at=timezone.now()-timedelta(days=1), due_at=timezone.now()-timedelta(hours=1), condition_out=Equipment.Condition.GOOD)
            fiber.status = Equipment.Status.OUT
            fiber.save()

        self.stdout.write(self.style.SUCCESS('Données de démonstration créées.'))
