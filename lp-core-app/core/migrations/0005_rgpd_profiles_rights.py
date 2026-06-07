# Generated for LP Gestion Atelier Suite V2.6
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_web_maintenance'),
    ]

    operations = [
        migrations.AddField(
            model_name='coreuser',
            name='personal_email',
            field=models.EmailField(blank=True, help_text='Email personnel, facultatif, utile pour PFMP / stage.', max_length=254),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='personal_phone',
            field=models.CharField(blank=True, help_text='Téléphone personnel, facultatif.', max_length=40),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='identity_photo',
            field=models.FileField(blank=True, null=True, upload_to='core/users/photos/'),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='image_consent_status',
            field=models.CharField(choices=[('unknown', 'Non renseigné'), ('authorized', 'Autorisation image accordée'), ('refused', 'Opposition / refus de diffusion')], default='unknown', max_length=20),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='image_consent_comment',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='parent_image_opposition',
            field=models.BooleanField(default=False, help_text='Pour mineur : opposition parentale ou absence d’autorisation écrite.'),
        ),
        migrations.AddField(
            model_name='coreuser',
            name='personal_upload_blocked',
            field=models.BooleanField(default=False, help_text='Bloque les ajouts de photo/documents personnels par l’utilisateur.'),
        ),
        migrations.AlterField(
            model_name='corestore',
            name='module',
            field=models.CharField(choices=[('global', 'Tous modules'), ('pedashop', 'PedaShop'), ('toolmag', 'ToolMag'), ('safety', 'Safety Manager'), ('system', 'System Manager'), ('tpmanager', 'TP Manager'), ('other', 'Autre')], default='global', max_length=40),
        ),
        migrations.CreateModel(
            name='CoreRightDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=80, unique=True)),
                ('label', models.CharField(max_length=160)),
                ('module', models.CharField(choices=[('core', 'LP Core'), ('toolmag', 'ToolMag'), ('safety', 'Safety Manager'), ('pedashop', 'PedaShop'), ('system', 'System Manager'), ('tpmanager', 'TP Manager'), ('global', 'Transversal')], default='global', max_length=40)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['module', 'code']},
        ),
        migrations.CreateModel(
            name='CoreCertificationType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=80, unique=True)),
                ('label', models.CharField(max_length=160)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='CoreUserDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type_document', models.CharField(choices=[('cv', 'CV'), ('lettre_motivation', 'Lettre de motivation'), ('attestation', 'Attestation'), ('autorisation_image', 'Autorisation image'), ('pfmp', 'Document PFMP'), ('autre', 'Autre')], default='autre', max_length=40)),
                ('title', models.CharField(max_length=180)),
                ('file', models.FileField(upload_to='core/users/documents/')),
                ('visible_to_prof', models.BooleanField(default=True)),
                ('visible_to_admin', models.BooleanField(default=True)),
                ('expires_at', models.DateField(blank=True, null=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.coreuser')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='personal_documents', to='core.coreuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='RgpdPolicySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('technical_logs_retention', models.CharField(default='Année scolaire en cours', max_length=120)),
                ('backup_retention_days', models.PositiveIntegerField(default=90)),
                ('certification_support_note', models.TextField(default='Conservation de 90 jours retenue pour les sauvegardes afin de sécuriser les supports de certification et permettre le retour arrière en cas d’erreur de manipulation ou d’incident de sécurité.')),
                ('photo_purpose', models.TextField(default='Photo facultative utilisée pour l’identification interne et l’édition d’attestations, notamment habilitations et certifications.')),
                ('minor_authorization_note', models.TextField(default='Pour les élèves mineurs, une autorisation écrite des représentants légaux est exigée avant toute diffusion de photo dans la suite.')),
            ],
            options={'verbose_name': 'Paramètres RGPD', 'verbose_name_plural': 'Paramètres RGPD'},
        ),
    ]
