import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from core.models import (
    CoreUser, CoreFormation, CoreClass, CoreRightDefinition, CoreCertificationType,
    CoreCertification, CoreStore, CoreUserStoreAccess, RgpdPolicySettings, CoreModuleAccessRule,
    normalize_code
)


class Command(BaseCommand):
    help = 'Crée une base LP Core minimale avec administrateur et comptes démo.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-username', default=os.getenv('LP_CORE_ADMIN_USERNAME', 'admin'), help='Identifiant admin LP Core initial')
        parser.add_argument('--admin-password', default=os.getenv('LP_CORE_ADMIN_PASSWORD', 'admin'), help='Mot de passe admin LP Core initial')

    def _upsert_user(self, *, code, username, password, first_name, last_name, formation, class_name, role, rights):
        CoreClass.objects.get_or_create(formation=formation, name=class_name, school_year='2025-2026')
        user, created = CoreUser.objects.get_or_create(
            code=code,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'formation': formation,
                'class_name': class_name,
                'role_principal': role,
                'rights': rights,
                'active': True,
                'school_year': '2025-2026',
                'initial_password_for_sync': password,
                'source': 'demo',
            }
        )
        changed = False
        for field, value in {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'formation': formation,
            'class_name': class_name,
            'role_principal': role,
            'rights': rights,
            'active': True,
            'school_year': '2025-2026',
            'initial_password_for_sync': password,
            'source': 'demo',
        }.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed = True
        if created or not user.password_hash:
            user.set_password(password)
            changed = True
        if changed:
            user.save()
        return user

    def handle(self, *args, **options):
        admin_formation, _ = CoreFormation.objects.get_or_create(code='ADMIN', defaults={'name': 'Administration'})
        CoreClass.objects.get_or_create(formation=admin_formation, name='ADMIN', school_year='2025-2026')
        admin_username = (options.get('admin_username') or 'admin').strip()
        admin_password = options['admin_password']
        if CoreUser.objects.filter(username=admin_username).exclude(code='ADMIN').exists():
            raise CommandError(f"Le nom d'utilisateur admin demandé existe déjà dans LP Core : {admin_username}")
        admin, created = CoreUser.objects.get_or_create(
            code='ADMIN',
            defaults={
                'username': admin_username, 'first_name': 'Admin', 'last_name': 'LP', 'formation': admin_formation,
                'class_name': 'ADMIN', 'role_principal': 'admin', 'rights': 'CORE_ADMIN;ALL', 'active': True,
                'school_year': '2025-2026', 'initial_password_for_sync': admin_password, 'source': 'system',
            }
        )
        admin.username = admin_username
        admin.first_name = admin.first_name or 'Admin'
        admin.last_name = admin.last_name or 'LP'
        admin.formation = admin_formation
        admin.class_name = 'ADMIN'
        admin.role_principal = 'admin'
        admin.rights = 'CORE_ADMIN;ALL'
        admin.active = True
        admin.school_year = admin.school_year or '2025-2026'
        admin.set_password(admin_password)
        admin.initial_password_for_sync = admin_password
        admin.force_password_change = True
        admin.source = 'system'
        admin.save()

        # Superutilisateur Django /admin/, avec le même identifiant demandé.
        DjangoUser = get_user_model()
        django_admin, _ = DjangoUser.objects.get_or_create(username=admin_username, defaults={'email': 'admin@local.local'})
        django_admin.is_staff = True
        django_admin.is_superuser = True
        django_admin.set_password(admin_password)
        django_admin.save()

        # Formations, classes et utilisateurs de démonstration cohérents pour toute la suite.
        formations = {
            'ELEC': 'CAP Électricien',
            'MTNE': '2de MTNE',
            'MELEC': 'Bac Pro MELEC',
            'CIEL': 'Bac Pro CIEL',
            'FED': 'BTS FED',
            'STEL': 'BTS Électrotechnique / STEL',
            'DEMO': 'Démonstration atelier',
        }
        fobjs = {}
        for code, name in formations.items():
            fobjs[code], _ = CoreFormation.objects.get_or_create(code=code, defaults={'name': name})
        demo_classes = [
            ('ELEC', 'ELEC 1'), ('ELEC', 'ELEC 2'), ('MTNE', '2MTNE1'), ('MTNE', '2MTNE2'),
            ('MELEC', '1MELEC'), ('MELEC', 'TMELEC'), ('CIEL', '1CIEL'), ('CIEL', 'TCIEL'),
            ('FED', 'BTS FED1'), ('FED', 'BTS FED2'), ('STEL', 'BTS STEL1'), ('STEL', 'BTS STEL2'),
            ('DEMO', 'DEMO'), ('DEMO', 'PROF'),
        ]
        for fcode, cname in demo_classes:
            CoreClass.objects.get_or_create(formation=fobjs[fcode], name=cname, school_year='2025-2026')

        prof_rights = 'CORE_ADMIN;TOOLMAG_ADMIN;TOOLMAG_VIEW;TOOLMAG_BORROW;TOOLMAG_RETURN;PEDASHOP_ADMIN;PEDASHOP_MAGASINIER;SAFETY_ADMIN;SAFETY_REFERENT;SYSTEM_ADMIN;SYSTEM_REFERENT_ZONE;TP_ADMIN;TP_PROF_CREATEUR;TP_REFERENTIEL_ADMIN'
        eleve_rights = 'TOOLMAG_VIEW;TOOLMAG_BORROW;PEDASHOP_VIEW;SAFETY_VIEW;SYSTEM_VIEW;MODULE_TOOLMAG;MODULE_SAFETY;MODULE_PEDASHOP;MODULE_SYSTEM'
        magasinier_rights = 'TOOLMAG_VIEW;TOOLMAG_BORROW;TOOLMAG_RETURN;PEDASHOP_MAGASINIER;PEDASHOP_VIEW'
        demo_users = [
            dict(code='PROF-0001', username='PROF-0001', password='prof1234', first_name='Professeur', last_name='Électricité', formation=fobjs['MELEC'], class_name='PROF', role='professeur', rights=prof_rights),
            dict(code='PROF-0002', username='PROF-0002', password='prof1234', first_name='Professeur', last_name='CIEL', formation=fobjs['CIEL'], class_name='PROF', role='professeur', rights=prof_rights),
            dict(code='MAG-0001', username='MAG-0001', password='mag1234', first_name='Magasinier', last_name='Atelier', formation=fobjs['DEMO'], class_name='MAGASIN', role='magasinier', rights=magasinier_rights),
            dict(code='USR-0001', username='USR-0001', password='user0001', first_name='Élève', last_name='MELEC Un', formation=fobjs['MELEC'], class_name='1MELEC', role='eleve', rights=eleve_rights),
            dict(code='USR-0002', username='USR-0002', password='user0002', first_name='Élève', last_name='MELEC Deux', formation=fobjs['MELEC'], class_name='TMELEC', role='eleve', rights=eleve_rights),
            dict(code='USR-0003', username='USR-0003', password='user0003', first_name='Élève', last_name='CIEL Un', formation=fobjs['CIEL'], class_name='1CIEL', role='eleve', rights=eleve_rights),
            dict(code='USR-0004', username='USR-0004', password='user0004', first_name='Élève', last_name='CIEL Deux', formation=fobjs['CIEL'], class_name='TCIEL', role='eleve', rights=eleve_rights),
            dict(code='USR-0005', username='USR-0005', password='user0005', first_name='Élève', last_name='CAP Un', formation=fobjs['ELEC'], class_name='ELEC 1', role='eleve', rights=eleve_rights),
            dict(code='USR-0006', username='USR-0006', password='user0006', first_name='Étudiant', last_name='FED Un', formation=fobjs['FED'], class_name='BTS FED1', role='eleve', rights=eleve_rights),
        ]
        demo_user_objs = {}
        for data in demo_users:
            demo_user_objs[data['code']] = self._upsert_user(**data)

        default_rights = [
            ('ADMIN', 'Administrateur global', 'global'),
            ('PROF', 'Professeur', 'global'),
            ('ELEVE', 'Élève', 'global'),
            ('UTILISATEUR', 'Utilisateur', 'global'),
            ('MAGASINIER', 'Magasinier', 'global'),
            ('CORE_ADMIN', 'Administration LP Core', 'core'),
            ('TOOLMAG_ADMIN', 'Administration ToolMag', 'toolmag'),
            ('TOOLMAG_VIEW', 'Lecture ToolMag', 'toolmag'),
            ('TOOLMAG_BORROW', 'Emprunt ToolMag', 'toolmag'),
            ('TOOLMAG_RETURN', 'Retour ToolMag', 'toolmag'),
            ('PEDASHOP_ADMIN', 'Administration PedaShop', 'pedashop'),
            ('PEDASHOP_MAGASINIER', 'Préparation PedaShop', 'pedashop'),
            ('PEDASHOP_VIEW', 'Lecture PedaShop', 'pedashop'),
            ('SAFETY_ADMIN', 'Administration Safety', 'safety'),
            ('SAFETY_REFERENT', 'Référent sécurité', 'safety'),
            ('SAFETY_VIEW', 'Lecture Safety Manager', 'safety'),
            ('SYSTEM_ADMIN', 'Administration System Manager', 'system'),
            ('SYSTEM_REFERENT_ZONE', 'Référent zone systèmes', 'system'),
            ('SYSTEM_VIEW', 'Lecture System Manager', 'system'),
            ('MODULE_TOOLMAG', 'Voir ToolMag dans le portail', 'core'),
            ('MODULE_SAFETY', 'Voir Safety Manager dans le portail', 'core'),
            ('MODULE_PEDASHOP', 'Voir PedaShop dans le portail', 'core'),
            ('MODULE_SYSTEM', 'Voir System Manager dans le portail', 'core'),
            ('MODULE_TPMANAGER', 'Voir TP Manager dans le portail', 'core'),
            ('TP_ADMIN', 'Administration TP Manager', 'tpmanager'),
            ('TP_PROF_CREATEUR', 'Créateur de TP', 'tpmanager'),
            ('TP_ELEVE_CONTRIBUTEUR', 'Contribution élève temporaire TP', 'tpmanager'),
            ('TP_REFERENTIEL_ADMIN', 'Administration des référentiels TP', 'tpmanager'),
        ]
        for code, label, module in default_rights:
            CoreRightDefinition.objects.get_or_create(code=code, defaults={'label': label, 'module': module})

        default_certs = [
            ('SST', 'SST'), ('HABILITATION_ELEC', 'Habilitation électrique'), ('B0', 'B0'), ('B1V', 'B1V'),
            ('BR', 'BR'), ('BC', 'BC'), ('R407', 'R407'), ('R408', 'R408'), ('CACES', 'CACES'),
            ('TRAVAIL_HAUTEUR', 'Travail en hauteur'), ('ECHAF', 'Échafaudage'), ('FLUIDE_FRIGO', 'Fluide frigorigène'),
        ]
        cert_type_objs = {}
        for code, label in default_certs:
            cert_type_objs[code], _ = CoreCertificationType.objects.get_or_create(code=code, defaults={'label': label})

        # Magasins de démonstration partagés avec PedaShop / ToolMag.
        demo_stores = [
            ('pedashop', 'MAG-ATELIER', 'Magasin consommables atelier'),
            ('pedashop', 'MAG-RESERVE', 'Réserve consommables'),
            ('toolmag', 'MAG-OUTILLAGE', 'Magasin outillage'),
            ('system', 'ZONE-ECOQ', 'Écoquartier pédagogique'),
            ('system', 'ZONE-INT', 'Zone intégration / réseaux'),
        ]
        store_objs = []
        for module, code, nom in demo_stores:
            module_norm = str(module or 'global').strip().lower()
            code_norm = normalize_code(code or nom, 'MAGASIN')
            # Idempotence forte : les anciennes versions stockaient le code normalisé
            # (MAG_ATELIER) alors que le seed cherchait parfois le code source
            # (MAG-ATELIER). On cherche donc par couple normalisé avant création.
            store = CoreStore.objects.filter(module=module_norm, code=code_norm).order_by('id').first()
            created = False
            if store is None:
                store = CoreStore(module=module_norm, code=code_norm)
                created = True
            store.nom = nom
            store.active = True
            store.save()
            store_objs.append(store)
        for user in [admin, *demo_user_objs.values()]:
            if user.role_principal in {'admin', 'professeur', 'magasinier'}:
                for store in store_objs:
                    CoreUserStoreAccess.objects.get_or_create(user=user, store=store, defaults={'active': True, 'comment': 'Accès démo initial'})

        # Quelques certifications / habilitations de démonstration.
        today = timezone.localdate()
        certs = [
            ('PROF-0001', 'HABILITATION_ELEC', 'BR'), ('PROF-0001', 'SST', ''),
            ('PROF-0002', 'SST', ''), ('MAG-0001', 'HABILITATION_ELEC', 'B0'),
            ('USR-0001', 'B1V', 'formation en cours'), ('USR-0003', 'SST', 'sensibilisation'),
        ]
        for ucode, ctype, niveau in certs:
            user = demo_user_objs.get(ucode)
            if user:
                CoreCertification.objects.get_or_create(
                    user=user, type_certification=ctype, niveau=niveau,
                    defaults={'date_obtention': today, 'date_fin_validite': today + timedelta(days=365*3), 'actif': True, 'commentaire': 'Donnée de démonstration'}
                )

        RgpdPolicySettings.get_solo()

        default_module_rules = [
            ('toolmag', 'right', 'MODULE_TOOLMAG', 'Accès portail ToolMag'),
            ('safety', 'right', 'MODULE_SAFETY', 'Accès portail Safety Manager'),
            ('pedashop', 'right', 'MODULE_PEDASHOP', 'Accès portail PedaShop'),
            ('system', 'right', 'MODULE_SYSTEM', 'Accès portail System Manager'),
            ('tpmanager', 'right', 'MODULE_TPMANAGER', 'Accès portail TP Manager'),
            ('tpmanager', 'role', 'professeur', 'TP Manager visible par les professeurs'),
            ('tpmanager', 'role', 'responsable', 'TP Manager visible par les responsables'),
        ]
        for module, target_type, target_value, comment in default_module_rules:
            rule, _ = CoreModuleAccessRule.objects.get_or_create(module=module, target_type=target_type, target_value=target_value)
            rule.active = True
            rule.comment = comment
            rule.save()

        self.stdout.write(self.style.SUCCESS('LP Core initialisé. Admin LP Core et Django : admin / ' + options['admin_password']))
        self.stdout.write(self.style.SUCCESS('Comptes démo : PROF-0001 / prof1234 ; PROF-0002 / prof1234 ; MAG-0001 / mag1234 ; USR-0001..0006 / user0001..user0006'))
