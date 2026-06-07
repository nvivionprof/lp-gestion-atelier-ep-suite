# Generated for LP Gestion Atelier Suite V2.5 web maintenance.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_public_suite_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedUpdatePackage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('original_filename', models.CharField(max_length=255)),
                ('stored_filename', models.CharField(max_length=255, unique=True)),
                ('stored_path', models.CharField(max_length=500)),
                ('sha256', models.CharField(blank=True, max_length=64)),
                ('size_bytes', models.PositiveBigIntegerField(default=0)),
                ('detected_version', models.CharField(blank=True, max_length=80)),
                ('manifest', models.JSONField(blank=True, default=dict)),
                ('status', models.CharField(choices=[('uploaded', 'Déposé'), ('analyzed', 'Analysé'), ('invalid', 'Invalide'), ('installing', 'Installation en cours'), ('installed', 'Installé'), ('failed', 'Échec')], default='uploaded', max_length=40)),
                ('analysis_report', models.TextField(blank=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.coreuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SuiteMaintenanceJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(choices=[('apply_public_settings', 'Appliquer URLs / HTTPS'), ('issue_cert', 'Générer certificat'), ('renew_cert', 'Renouveler certificat'), ('cert_status', 'État certificat'), ('restart_services', 'Redémarrer services'), ('migrate_all', 'Lancer migrations'), ('backup_all', 'Sauvegarde complète'), ('install_update', 'Installer mise à jour ZIP')], max_length=80)),
                ('status', models.CharField(choices=[('requested', 'Demandée'), ('running', 'En cours'), ('success', 'Terminée'), ('failed', 'Échec'), ('unknown', 'Inconnu')], default='requested', max_length=40)),
                ('agent_job_id', models.CharField(blank=True, max_length=120)),
                ('result_message', models.TextField(blank=True)),
                ('log_tail', models.TextField(blank=True)),
                ('package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='jobs', to='core.uploadedupdatepackage')),
                ('requested_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.coreuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
