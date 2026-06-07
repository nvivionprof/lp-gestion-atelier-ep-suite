
# Generated for LP Gestion Atelier EP Suite V0.3.4
from django.db import migrations, models
import django.db.models.deletion

CANONICAL_ROOT_CODES = {
    '01_PRESENTATION', '02_PLANS_SCHEMAS_CALCULS', '03_DOCUMENTATIONS_TECHNIQUES', '04_PROGRAMMES',
    '05_TP_TD_ASSOCIES', '06_SECURITE_RISQUES_CONSIGNATION', '07_MAINTENANCE_DEPANNAGE', '08_HISTORIQUE_MODIFICATIONS'
}

def sync_classes_from_users(apps, schema_editor):
    SystemUser = apps.get_model('system_manager', 'SystemUser')
    Formation = apps.get_model('system_manager', 'Formation')
    SchoolClass = apps.get_model('system_manager', 'SchoolClass')
    for row in SystemUser.objects.exclude(class_name='').values('class_name', 'formation_code', 'formation_name', 'school_year').distinct():
        name = (row.get('class_name') or '').strip()
        if not name:
            continue
        formation = None
        fcode = (row.get('formation_code') or '').strip()
        if fcode:
            formation, _ = Formation.objects.get_or_create(code=fcode, defaults={'nom': row.get('formation_name') or fcode, 'active': True})
        obj, _ = SchoolClass.objects.get_or_create(nom=name, school_year=row.get('school_year') or '')
        obj.formation = formation
        obj.formation_code = fcode
        obj.active = True
        obj.save()

def clean_document_tree(apps, schema_editor):
    DocumentCategory = apps.get_model('system_manager', 'DocumentCategory')
    SystemDocument = apps.get_model('system_manager', 'SystemDocument')
    mapping = [
        (['documentation constructeur', 'constructeur'], '03_CONSTRUCTEURS'),
        (['plans électriques', 'schema electrique', 'schémas électriques'], '02_SCHEMAS_ELECTRIQUES'),
        (['fluides', 'reseaux', 'réseaux', 'implantation'], '02_SCHEMAS_FLUIDES_RESEAUX'),
        (['analyse fonctionnelle'], '01_ANALYSE_FONCTIONNELLE'),
        (['mise en service'], '07_MISE_EN_SERVICE'),
        (['procédure d’arrêt', 'procedure d arret', 'arrêt'], '06_CONSIGNATION'),
        (['sécurité', 'securite', 'risques', 'consignation'], '06_SECURITE_RISQUES_CONSIGNATION'),
        (['prise de poste'], '01_PRESENTATION_GENERALE'),
        (['tp associés', 'tp associes', 'tp'], '05_TP_PUBLIES'),
        (['maintenance', 'dépannage', 'depannage'], '07_DEPANNAGE'),
        (['historique'], '08_MODIFS_DOCUMENTAIRES'),
    ]
    canonical = {c.code: c for c in DocumentCategory.objects.filter(code__in=CANONICAL_ROOT_CODES)}
    for cat in list(DocumentCategory.objects.filter(parent__isnull=True)):
        if cat.code in CANONICAL_ROOT_CODES:
            continue
        hay = f'{cat.code} {cat.nom}'.lower()
        target = None
        for keys, code in mapping:
            if any(k in hay for k in keys):
                target = DocumentCategory.objects.filter(code=code).first()
                break
        if target:
            SystemDocument.objects.filter(categorie=cat).update(categorie=target)
            # rattache les enfants sous la cible si existants
            for child in DocumentCategory.objects.filter(parent=cat):
                if child.code != target.code:
                    child.parent = target.parent if target.parent_id else target
                    child.active = False
                    child.save()
        cat.active = False
        cat.save()

class Migration(migrations.Migration):
    dependencies = [('system_manager', '0002_system_manager_v033_gmao_blocks_docs')]
    operations = [
        migrations.CreateModel(
            name='SchoolClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('core_class_id', models.PositiveIntegerField(blank=True, null=True, unique=True)),
                ('nom', models.CharField(max_length=120)),
                ('formation_code', models.CharField(blank=True, max_length=40)),
                ('school_year', models.CharField(blank=True, max_length=20)),
                ('active', models.BooleanField(default=True)),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes', to='system_manager.formation')),
            ],
            options={'ordering': ['formation__code', 'nom'], 'verbose_name': 'classe synchronisée', 'verbose_name_plural': 'classes synchronisées', 'unique_together': {('nom', 'school_year')}},
        ),
        migrations.CreateModel(
            name='ReservationGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('titre', models.CharField(blank=True, max_length=220)),
                ('reservation_mode', models.CharField(choices=[('ponctuelle', 'Ponctuelle'), ('bloc_atelier', 'Bloc atelier'), ('sequence_tp', 'Séquence TP Manager')], default='ponctuelle', max_length=30)),
                ('classe_ou_groupe', models.CharField(blank=True, max_length=120)),
                ('sequence_code', models.CharField(blank=True, max_length=80)),
                ('sequence_title', models.CharField(blank=True, max_length=220)),
                ('tp_code', models.CharField(blank=True, max_length=80)),
                ('tp_titre', models.CharField(blank=True, max_length=220)),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('confirmee', 'Confirmée'), ('annulee', 'Annulée')], default='brouillon', max_length=40)),
                ('commentaire', models.TextField(blank=True)),
                ('block', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservation_groups', to='system_manager.workshopblock')),
                ('classe', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservation_groups', to='system_manager.schoolclass')),
                ('professeur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservation_groups', to='system_manager.systemuser')),
            ],
            options={'ordering': ['-date_debut', 'titre'], 'verbose_name': 'dossier de réservation système', 'verbose_name_plural': 'dossiers de réservation systèmes'},
        ),
        migrations.AddField(model_name='reservationgroup', name='slots', field=models.ManyToManyField(blank=True, related_name='reservation_groups', to='system_manager.workshopblockslot')),
        migrations.AddField(model_name='workshopblock', name='classes', field=models.ManyToManyField(blank=True, related_name='workshop_blocks', to='system_manager.schoolclass')),
        migrations.AddField(model_name='reservation', name='group', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='system_manager.reservationgroup')),
        migrations.RunPython(sync_classes_from_users, migrations.RunPython.noop),
        migrations.RunPython(clean_document_tree, migrations.RunPython.noop),
    ]
