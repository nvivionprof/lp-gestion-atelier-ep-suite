from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('system_manager', '0004_v036_document_versions_temp_permissions'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemdocument',
            name='preview_pdf',
            field=models.FileField(blank=True, help_text='PDF de prévisualisation généré automatiquement pour les documents Office.', upload_to='systems/previews/'),
        ),
        migrations.AddField(
            model_name='systemdocument',
            name='preview_status',
            field=models.CharField(blank=True, default='', help_text='État de la prévisualisation : pending / ok / error / unsupported.', max_length=40),
        ),
        migrations.AddField(
            model_name='systemdocument',
            name='preview_error',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='checkitem',
            name='expected_response',
            field=models.CharField(blank=True, choices=[('oui', 'Oui attendu'), ('non', 'Non attendu'), ('nc', 'NC attendu'), ('', 'Non contrôlé')], default='oui', max_length=20, verbose_name='Réponse attendue'),
        ),
        migrations.AlterField(
            model_name='temporarysystempermission',
            name='user',
            field=models.ForeignKey(blank=True, help_text='Utilisateur ciblé. Laisser vide si le droit est accordé à toute une classe.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='temporary_system_permissions', to='system_manager.systemuser'),
        ),
        migrations.AddField(
            model_name='temporarysystempermission',
            name='school_class',
            field=models.ForeignKey(blank=True, help_text='Classe ciblée. Optionnel si un utilisateur est choisi.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='temporary_system_permissions', to='system_manager.schoolclass'),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='blocking',
            field=models.BooleanField(default=False, verbose_name='Anomalie bloquante'),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='lift_requested_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='anomaly_lift_requests', to='system_manager.systemuser'),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='lift_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='lift_request_comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='lift_authorized_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='anomaly_lift_authorizations', to='system_manager.systemuser'),
        ),
        migrations.AddField(
            model_name='systemanomaly',
            name='lift_authorized_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
