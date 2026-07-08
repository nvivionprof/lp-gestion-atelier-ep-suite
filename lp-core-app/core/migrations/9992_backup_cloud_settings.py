# Generated manually for backup cloud settings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '9991_rc12_coreuser_rights_textfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_provider',
            field=models.CharField(choices=[('google_drive', 'Google Drive'), ('onedrive', 'Microsoft OneDrive'), ('sharepoint', 'Microsoft SharePoint'), ('other', 'Autre remote rclone')], default='google_drive', max_length=40),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_rclone_remote',
            field=models.CharField(blank=True, default='gdrive', help_text='Nom du remote rclone configuré sur le serveur, par exemple gdrive.', max_length=80),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_remote_path',
            field=models.CharField(blank=True, default='LP-Gestion-Atelier-Suite/backups', help_text='Dossier distant dans le cloud.', max_length=255),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_sync_full_backups',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_sync_database_backups',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='backuppolicysettings',
            name='cloud_restore_enabled',
            field=models.BooleanField(default=True),
        ),
    ]
