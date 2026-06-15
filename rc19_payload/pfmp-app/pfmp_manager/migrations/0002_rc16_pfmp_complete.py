# Migration robuste générée pour LP Gestion Atelier EP Suite V0.0.1-RC18.
# Elle remplace la migration RC16 classique par une migration idempotente :
# si tables/colonnes existent déjà, elles ne sont pas recréées.
from django.db import migrations, models
import django.db.models.deletion


def repair_schema(apps, schema_editor):
    from pfmp_manager.schema_repair import repair_pfmp_rc16_schema
    repair_pfmp_rc16_schema(mark_migration=False, stdout=None)


def noop_reverse(apps, schema_editor):
    # Pas de suppression automatique : migration volontairement non destructive.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('pfmp_manager', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(repair_schema, reverse_code=noop_reverse),
            ],
            state_operations=[
                migrations.CreateModel(
                    name='CompanyTag',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('code', models.CharField(max_length=80, unique=True)),
                        ('label', models.CharField(max_length=140)),
                        ('category', models.CharField(choices=[('activite', 'Activité'), ('formation', 'Formation'), ('statut', 'Statut'), ('recherche', 'Recherche'), ('autre', 'Autre')], default='autre', max_length=30)),
                        ('active', models.BooleanField(default=True)),
                    ],
                ),
                migrations.CreateModel(
                    name='ImportBatch',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('file_name', models.CharField(max_length=240)),
                        ('mode', models.CharField(choices=[('simulation', 'Simulation'), ('append_only', 'Ajout uniquement'), ('upsert', 'Ajout / modification'), ('replace_all', 'Remplacement total'), ('delete_all_then_import', 'Suppression totale puis import')], max_length=40)),
                        ('key_strategy', models.CharField(choices=[('code_entreprise', 'Code entreprise'), ('siret', 'SIRET'), ('nom_code_postal_ville', 'Nom + CP + ville')], default='code_entreprise', max_length=60)),
                        ('started_at', models.DateTimeField(auto_now_add=True)),
                        ('finished_at', models.DateTimeField(blank=True, null=True)),
                        ('created_count', models.PositiveIntegerField(default=0)),
                        ('updated_count', models.PositiveIntegerField(default=0)),
                        ('deleted_count', models.PositiveIntegerField(default=0)),
                        ('ignored_count', models.PositiveIntegerField(default=0)),
                        ('error_count', models.PositiveIntegerField(default=0)),
                        ('report_json', models.JSONField(blank=True, default=dict)),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pfmp_manager.pfmpuser')),
                    ],
                ),
                migrations.AddField('pfmpuser', 'address', models.CharField(blank=True, max_length=240)),
                migrations.AddField('pfmpuser', 'postal_code', models.CharField(blank=True, max_length=20)),
                migrations.AddField('pfmpuser', 'city', models.CharField(blank=True, max_length=120)),
                migrations.AddField('pfmpuser', 'latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                migrations.AddField('pfmpuser', 'longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                migrations.AddField('company', 'external_key', models.CharField(blank=True, max_length=120, null=True, unique=True)),
                migrations.AddField('company', 'siret', models.CharField(blank=True, db_index=True, max_length=20)),
                migrations.AddField('company', 'naf_ape', models.CharField(blank=True, max_length=20)),
                migrations.AddField('company', 'source_activity', models.CharField(blank=True, max_length=260)),
                migrations.AddField('company', 'domains_text', models.CharField(blank=True, max_length=260)),
                migrations.AddField('company', 'subdomains_text', models.CharField(blank=True, max_length=260)),
                migrations.AddField('company', 'country', models.CharField(blank=True, default='France', max_length=80)),
                migrations.AddField('company', 'full_address', models.CharField(blank=True, max_length=360)),
                migrations.AddField('company', 'geocoding_status', models.CharField(blank=True, default='A_GEOCODER', max_length=40)),
                migrations.AddField('company', 'osm_search_url', models.URLField(blank=True)),
                migrations.AddField('company', 'student_visible', models.BooleanField(default=True)),
                migrations.AddField('company', 'import_source', models.CharField(blank=True, max_length=160)),
                migrations.AddField('company', 'import_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='companies', to='pfmp_manager.importbatch')),
                migrations.AddField('company', 'tags', models.ManyToManyField(blank=True, to='pfmp_manager.companytag')),
                migrations.AddIndex('company', models.Index(fields=['name'], name='pfmp_manage_name_4567_idx')),
                migrations.AddIndex('company', models.Index(fields=['city'], name='pfmp_manage_city_93d0_idx')),
                migrations.AddIndex('company', models.Index(fields=['postal_code'], name='pfmp_manage_postal_c1d1_idx')),
                migrations.AddField('companycontact', 'mobile_phone', models.CharField(blank=True, max_length=40)),
                migrations.AddField('companycontact', 'student_visible', models.BooleanField(default=False)),
                migrations.AddField('companycontact', 'teacher_visible', models.BooleanField(default=True)),
                migrations.AddField('companycontact', 'personal_address', models.CharField(blank=True, max_length=240)),
                migrations.AddField('companycontact', 'personal_postal_code', models.CharField(blank=True, max_length=20)),
                migrations.AddField('companycontact', 'personal_city', models.CharField(blank=True, max_length=120)),
                migrations.AddField('companycontact', 'personal_latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                migrations.AddField('companycontact', 'personal_longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                migrations.AddField('companycontact', 'use_personal_location_for_student_search', models.BooleanField(default=False)),
                migrations.AddField('companycontact', 'can_help_transport', models.BooleanField(default=False)),
                migrations.AddField('companycontact', 'import_source', models.CharField(blank=True, max_length=160)),
                migrations.AddField('companycontact', 'import_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contacts', to='pfmp_manager.importbatch')),
                migrations.AddIndex('companycontact', models.Index(fields=['email'], name='pfmp_manage_email_71f0_idx')),
                migrations.AddIndex('companycontact', models.Index(fields=['contact_type'], name='pfmp_manage_contact_1b3e_idx')),
                migrations.CreateModel(
                    name='StudentCompanySearch',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('status', models.CharField(choices=[('recherche', 'Recherche'), ('mail_envoye', 'Mail envoyé'), ('appel_effectue', 'Appel effectué'), ('demande_envoyee', 'Demande de stage envoyée'), ('a_relancer', 'À relancer'), ('accord_oral', 'Accord oral'), ('accord_mail', 'Accord OK mail'), ('refus', 'Refus'), ('sans_reponse', 'Sans réponse'), ('convention_a_preparer', 'Convention à préparer'), ('convention_envoyee', 'Convention envoyée'), ('convention_signee', 'Convention signée'), ('stage_valide', 'Stage validé'), ('abandonne', 'Abandonné')], default='recherche', max_length=40)),
                        ('tags_text', models.CharField(blank=True, help_text='Tags séparés par ;', max_length=240)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('last_action_at', models.DateTimeField(blank=True, null=True)),
                        ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_searches', to='pfmp_manager.company')),
                        ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='student_searches', to='pfmp_manager.companycontact')),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='searches_created', to='pfmp_manager.pfmpuser')),
                        ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_searches', to='pfmp_manager.pfmpperiod')),
                        ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_searches', to='pfmp_manager.pfmpuser')),
                    ],
                    options={'unique_together': {('student', 'period', 'company')}},
                ),
                migrations.AddIndex('studentcompanysearch', models.Index(fields=['student', 'period', 'status'], name='pfmp_manage_student_24f1_idx')),
                migrations.AddIndex('studentcompanysearch', models.Index(fields=['status'], name='pfmp_manage_status_34e3_idx')),
                migrations.CreateModel(
                    name='StudentCompanyAction',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('action_type', models.CharField(choices=[('mail', 'Mail'), ('telephone', 'Téléphone'), ('visite', 'Visite'), ('depot_cv', 'Dépôt CV'), ('relance', 'Relance'), ('reponse', 'Réponse'), ('accord', 'Accord'), ('refus', 'Refus'), ('convention', 'Convention'), ('autre', 'Autre')], default='mail', max_length=40)),
                        ('comment', models.TextField(blank=True)),
                        ('status_after', models.CharField(choices=[('recherche', 'Recherche'), ('mail_envoye', 'Mail envoyé'), ('appel_effectue', 'Appel effectué'), ('demande_envoyee', 'Demande de stage envoyée'), ('a_relancer', 'À relancer'), ('accord_oral', 'Accord oral'), ('accord_mail', 'Accord OK mail'), ('refus', 'Refus'), ('sans_reponse', 'Sans réponse'), ('convention_a_preparer', 'Convention à préparer'), ('convention_envoyee', 'Convention envoyée'), ('convention_signee', 'Convention signée'), ('stage_valide', 'Stage validé'), ('abandonne', 'Abandonné')], default='recherche', max_length=40)),
                        ('next_action', models.CharField(blank=True, max_length=180)),
                        ('next_action_date', models.DateField(blank=True, null=True)),
                        ('attachment', models.FileField(blank=True, upload_to='pfmp/search_actions/')),
                        ('contact', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_actions', to='pfmp_manager.companycontact')),
                        ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_actions_created', to='pfmp_manager.pfmpuser')),
                        ('search', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='pfmp_manager.studentcompanysearch')),
                    ],
                    options={'ordering': ['-created_at']},
                ),
            ]
        ),
    ]
