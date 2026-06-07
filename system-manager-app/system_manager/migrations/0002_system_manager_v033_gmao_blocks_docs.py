# Generated for LP Gestion Atelier EP Suite V0.3.3
from django.db import migrations, models
import django.db.models.deletion


def seed_document_categories(apps, schema_editor):
    DocumentCategory = apps.get_model('system_manager', 'DocumentCategory')
    sections = [
        ('01', '01_PRESENTATION', '01 - Présentation - CCTP - Analyse Fonctionnelle', [
            ('01_PRESENTATION_GENERALE', 'Présentation générale'),
            ('01_CCTP', 'CCTP / cahier des charges'),
            ('01_ANALYSE_FONCTIONNELLE', 'Analyse fonctionnelle'),
            ('01_SYNOPTIQUE', 'Synoptique / architecture du système'),
        ]),
        ('02', '02_PLANS_SCHEMAS_CALCULS', '02 - Plans, Schémas et notes de calcul', [
            ('02_PLANS_IMPLANTATION', 'Plans d’implantation'),
            ('02_SCHEMAS_ELECTRIQUES', 'Schémas électriques'),
            ('02_SCHEMAS_FLUIDES_RESEAUX', 'Schémas fluides / réseaux'),
            ('02_NOTES_CALCUL', 'Notes de calcul'),
        ]),
        ('03', '03_DOCUMENTATIONS_TECHNIQUES', '03 - Documentations techniques', [
            ('03_CONSTRUCTEURS', 'Notices constructeurs'),
            ('03_DATASHEETS', 'Fiches techniques / datasheets'),
            ('03_PARAMETRAGE', 'Paramétrage matériel'),
            ('03_CERTIFICATS', 'Certificats / conformité'),
        ]),
        ('04', '04_PROGRAMMES', '04 - Programmes', [
            ('04_API_AUTOMATE', 'Automate / API'),
            ('04_IHM_SUPERVISION', 'IHM / supervision'),
            ('04_VARIATEURS_REGULATEURS', 'Variateurs / régulateurs'),
            ('04_SAUVEGARDES_PROGRAMMES', 'Sauvegardes programmes'),
        ]),
        ('05', '05_TP_TD_ASSOCIES', '05 - TP / TD associés', [
            ('05_TP_PUBLIES', 'TP publiés'),
            ('05_TD_RECHERCHE', 'TD / travaux de recherche'),
            ('05_SEQUENCES', 'Séquences pédagogiques'),
            ('05_GRILLES_EVALUATION', 'Grilles / attendus'),
        ]),
        ('06', '06_SECURITE_RISQUES_CONSIGNATION', '06 - Sécurité / risques / consignation', [
            ('06_DUERP', 'Risques DUERP'),
            ('06_CONSIGNATION', 'Procédures de consignation'),
            ('06_HABILITATIONS', 'Habilitations / autorisations'),
            ('06_EPI_ECS_EIS', 'EPI / ECS / EIS'),
        ]),
        ('07', '07_MAINTENANCE_DEPANNAGE', '07 - Maintenance / dépannage', [
            ('07_GMAO_INTERVENTIONS', 'Interventions GMAO'),
            ('07_DEPANNAGE', 'Dépannage'),
            ('07_CONTROLES_PERIODIQUES', 'Contrôles périodiques'),
            ('07_MISE_EN_SERVICE', 'Mise en service initiale'),
        ]),
        ('08', '08_HISTORIQUE_MODIFICATIONS', '08 - Historique des modifications', [
            ('08_MODIFS_DOCUMENTAIRES', 'Modifications documentaires'),
            ('08_MODIFS_PROGRAMMES', 'Modifications programmes'),
            ('08_MODIFS_MATERIELLES', 'Modifications matérielles'),
            ('08_VERSIONS_ARCHIVES', 'Versions archivées'),
        ]),
    ]
    order = 10
    for section_code, code, name, children in sections:
        root, _ = DocumentCategory.objects.get_or_create(code=code, defaults={'nom': name, 'section_code': section_code, 'ordre': order, 'active': True})
        root.nom = name; root.section_code = section_code; root.ordre = order; root.active = True; root.save()
        sub_order = order + 1
        for ccode, cname in children:
            child, _ = DocumentCategory.objects.get_or_create(code=ccode, defaults={'nom': cname, 'parent': root, 'section_code': section_code, 'ordre': sub_order, 'active': True})
            child.nom = cname; child.parent = root; child.section_code = section_code; child.ordre = sub_order; child.active = True; child.save()
            sub_order += 1
        order += 10


class Migration(migrations.Migration):
    dependencies = [('system_manager', '0001_initial')]
    operations = [
        migrations.AddField('documentcategory', 'parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sous_categories', to='system_manager.documentcategory')),
        migrations.AddField('documentcategory', 'section_code', models.CharField(blank=True, choices=[('01', '01 - Présentation - CCTP - Analyse fonctionnelle'), ('02', '02 - Plans, schémas et notes de calcul'), ('03', '03 - Documentations techniques'), ('04', '04 - Programmes'), ('05', '05 - TP / TD associés'), ('06', '06 - Sécurité / risques / consignation'), ('07', '07 - Maintenance / dépannage'), ('08', '08 - Historique des modifications')], default='', max_length=2)),
        migrations.AddField('reservation', 'reservation_mode', models.CharField(choices=[('ponctuelle', 'Ponctuelle'), ('bloc_atelier', 'Bloc atelier'), ('sequence_tp', 'Séquence TP Manager')], default='ponctuelle', max_length=30)),
        migrations.AddField('reservation', 'block_code', models.CharField(blank=True, default='', max_length=80)),
        migrations.AddField('reservation', 'block_name', models.CharField(blank=True, default='', max_length=180)),
        migrations.AddField('reservation', 'slot_label', models.CharField(blank=True, default='', max_length=120)),
        migrations.AddField('reservation', 'sequence_code', models.CharField(blank=True, default='', max_length=80)),
        migrations.AddField('reservation', 'sequence_title', models.CharField(blank=True, default='', max_length=220)),
        migrations.AlterModelOptions('documentcategory', {'ordering': ['section_code', 'ordre', 'code'], 'verbose_name': 'catégorie documentaire', 'verbose_name_plural': 'catégories documentaires'}),
        migrations.CreateModel(name='WorkshopBlock', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('core_block_id', models.PositiveIntegerField(blank=True, null=True, unique=True)), ('code', models.CharField(max_length=80, unique=True)), ('nom', models.CharField(max_length=180)), ('description', models.TextField(blank=True)), ('active', models.BooleanField(default=True)), ('formations', models.ManyToManyField(blank=True, related_name='workshop_blocks', to='system_manager.formation')), ('niveaux', models.ManyToManyField(blank=True, related_name='workshop_blocks', to='system_manager.niveau'))], options={'ordering': ['code'], 'verbose_name': 'bloc atelier', 'verbose_name_plural': 'blocs atelier'}),
        migrations.CreateModel(name='WorkshopBlockSlot', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('day_of_week', models.PositiveSmallIntegerField(choices=[(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi')])), ('label', models.CharField(blank=True, help_text='Ex. Lundi matin, jeudi après-midi', max_length=120)), ('start_time', models.TimeField()), ('end_time', models.TimeField()), ('active', models.BooleanField(default=True)), ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='system_manager.workshopblock'))], options={'ordering': ['block__code', 'day_of_week', 'start_time'], 'verbose_name': 'créneau de bloc atelier', 'verbose_name_plural': 'créneaux de blocs atelier', 'unique_together': {('block', 'day_of_week', 'start_time', 'end_time')}}),
        migrations.CreateModel(name='SystemTPAssociation', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('source', models.CharField(choices=[('manual', 'Ajout manuel'), ('tpmanager', 'Synchronisé TP Manager')], default='manual', max_length=30)), ('tp_id', models.PositiveIntegerField(blank=True, null=True)), ('tp_code', models.CharField(blank=True, max_length=80)), ('tp_titre', models.CharField(max_length=220)), ('sequence_code', models.CharField(blank=True, max_length=80)), ('sequence_titre', models.CharField(blank=True, max_length=220)), ('url', models.URLField(blank=True)), ('active', models.BooleanField(default=True)), ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tp_system_links', to='system_manager.formation')), ('niveau', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tp_system_links', to='system_manager.niveau')), ('systeme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tp_associations', to='system_manager.educationalsystem'))], options={'ordering': ['formation__code', 'niveau__ordre', 'tp_code', 'tp_titre'], 'verbose_name': 'TP/TD associé au système', 'verbose_name_plural': 'TP/TD associés aux systèmes'}),
        migrations.CreateModel(name='SystemSafetyLink', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('source', models.CharField(choices=[('manual', 'Ajout manuel'), ('safety_manager', 'Synchronisé Safety Manager')], default='manual', max_length=40)), ('safety_object_type', models.CharField(choices=[('duerp', 'DUERP'), ('risk', 'Risque'), ('consignation', 'Consignation'), ('procedure', 'Procédure sécurité'), ('event', 'Événement / presque accident')], default='risk', max_length=40)), ('safety_object_id', models.CharField(blank=True, max_length=80)), ('titre', models.CharField(max_length=220)), ('niveau_risque', models.CharField(blank=True, max_length=80)), ('consignation_requise', models.BooleanField(default=False)), ('habilitations_requises', models.CharField(blank=True, max_length=255)), ('epi_requis', models.TextField(blank=True)), ('procedure_resume', models.TextField(blank=True)), ('url', models.URLField(blank=True)), ('active', models.BooleanField(default=True)), ('systeme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='safety_links', to='system_manager.educationalsystem'))], options={'ordering': ['-consignation_requise', 'titre'], 'verbose_name': 'lien sécurité système', 'verbose_name_plural': 'liens sécurité systèmes'}),
        migrations.CreateModel(name='MaintenanceIntervention', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('reference', models.CharField(blank=True, max_length=80, unique=True)), ('type_action', models.CharField(choices=[('depannage', 'Dépannage'), ('corrective', 'Maintenance corrective'), ('preventive', 'Maintenance préventive'), ('controle_periodique', 'Contrôle périodique'), ('mise_en_service', 'Mise en service initiale')], default='depannage', max_length=40)), ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('en_cours', 'En cours'), ('terminee', 'Terminée'), ('conforme', 'Conforme'), ('non_conforme', 'Non conforme'), ('a_surveiller', 'À surveiller')], default='brouillon', max_length=40)), ('demandeur_nom', models.CharField(blank=True, max_length=160)), ('executant_nom', models.CharField(blank=True, max_length=160)), ('executant_prenom', models.CharField(blank=True, max_length=160)), ('executant_classe', models.CharField(blank=True, max_length=120)), ('habilitation', models.CharField(blank=True, max_length=120)), ('exploitant_nom', models.CharField(blank=True, max_length=160)), ('debut_intervention', models.DateTimeField(blank=True, null=True)), ('fin_intervention', models.DateTimeField(blank=True, null=True)), ('constat_operateur', models.TextField(blank=True)), ('fonctionne_bien', models.TextField(blank=True)), ('ne_fonctionne_pas', models.TextField(blank=True)), ('procedure_conditions_mesure', models.TextField(blank=True)), ('appareils_mesure_references', models.TextField(blank=True)), ('calculs_prealables', models.TextField(blank=True)), ('reglages_valeurs', models.TextField(blank=True)), ('tableau_releves', models.TextField(blank=True)), ('exploitation_releves', models.TextField(blank=True)), ('conclusion_conformite', models.TextField(blank=True)), ('epi', models.TextField(blank=True, help_text='EPI prévus/utilisés.')), ('ecs', models.TextField(blank=True, help_text='Équipements collectifs de sécurité.')), ('eis', models.TextField(blank=True, help_text='Équipements individuels de sécurité / consignation.')), ('appareils_mesure', models.TextField(blank=True)), ('action_realisee', models.TextField(blank=True)), ('suite_a_donner', models.TextField(blank=True)), ('intervention_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintenance_interventions', to='system_manager.systemuser')), ('safety_link', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintenance_interventions', to='system_manager.systemsafetylink')), ('systeme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_interventions', to='system_manager.educationalsystem'))], options={'ordering': ['-created_at'], 'verbose_name': 'intervention maintenance / GMAO', 'verbose_name_plural': 'interventions maintenance / GMAO'}),
        migrations.CreateModel(name='MaintenanceCheckLine', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('ordre', models.PositiveIntegerField(default=10)), ('hypothese', models.TextField(blank=True)), ('controle', models.TextField(blank=True)), ('conditions', models.TextField(blank=True)), ('bornes_test', models.CharField(blank=True, max_length=160)), ('appareil_utilise', models.CharField(blank=True, max_length=160)), ('sous_tension', models.BooleanField(default=False)), ('hors_tension', models.BooleanField(default=False)), ('valeur_attendue', models.CharField(blank=True, max_length=160)), ('valeur_mesuree', models.CharField(blank=True, max_length=160)), ('conclusion', models.TextField(blank=True)), ('intervention', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='check_lines', to='system_manager.maintenanceintervention'))], options={'ordering': ['ordre', 'id'], 'verbose_name': 'ligne de contrôle maintenance', 'verbose_name_plural': 'lignes de contrôle maintenance'}),
        migrations.CreateModel(name='MaintenanceDrawingZone', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('zone_type', models.CharField(choices=[('schema_defaut', 'Localisation sur schéma'), ('raccordement_mesure', 'Schéma de raccordement mesure'), ('photo_constat', 'Photo / constat'), ('croquis_libre', 'Croquis libre')], default='croquis_libre', max_length=40)), ('mode', models.CharField(choices=[('photo', 'Photo / appareil photo'), ('dessin', 'Dessin tablette'), ('mixte', 'Photo + annotation'), ('papier_quadrille', 'Zone quadrillée')], default='papier_quadrille', max_length=40)), ('titre', models.CharField(max_length=220)), ('image', models.ImageField(blank=True, upload_to='systems/maintenance/drawings/')), ('canvas_data', models.TextField(blank=True, help_text='Image base64 issue du dessin tablette.')), ('note', models.TextField(blank=True)), ('grid_enabled', models.BooleanField(default=True)), ('intervention', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drawing_zones', to='system_manager.maintenanceintervention'))], options={'ordering': ['zone_type', 'id'], 'verbose_name': 'zone dessin/photo maintenance', 'verbose_name_plural': 'zones dessin/photo maintenance'}),
        migrations.CreateModel(name='SystemChangeLog', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('type_changement', models.CharField(choices=[('document', 'Document'), ('programme', 'Programme'), ('schema', 'Schéma'), ('maintenance', 'Maintenance'), ('securite', 'Sécurité'), ('parametrage', 'Paramétrage'), ('autre', 'Autre')], default='autre', max_length=40)), ('titre', models.CharField(max_length=220)), ('description', models.TextField(blank=True)), ('version_avant', models.CharField(blank=True, max_length=80)), ('version_apres', models.CharField(blank=True, max_length=80)), ('date_effet', models.DateField(blank=True, null=True)), ('effectue_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_changes', to='system_manager.systemuser')), ('systeme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='change_logs', to='system_manager.educationalsystem'))], options={'ordering': ['-date_effet', '-created_at'], 'verbose_name': 'historique modification système', 'verbose_name_plural': 'historiques modifications systèmes'}),
        migrations.RunPython(seed_document_categories, migrations.RunPython.noop),
    ]
