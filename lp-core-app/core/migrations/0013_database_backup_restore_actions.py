from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_beta2_access_modes_rgpd_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suitemaintenancejob',
            name='action',
            field=models.CharField(choices=[
                ('apply_public_settings', 'Appliquer URLs / HTTPS'),
                ('issue_cert', 'Générer certificat'),
                ('renew_cert', 'Renouveler certificat'),
                ('cert_status', 'État certificat'),
                ('restart_services', 'Redémarrer services'),
                ('migrate_all', 'Lancer migrations'),
                ('backup_all', 'Sauvegarde historique'),
                ('full_backup', 'Sauvegarde complète de reprise'),
                ('restore_full_backup', 'Restauration complète après crash'),
                ('restore_existing_backup', 'Restaurer sauvegarde serveur'),
                ('backup_database', 'Sauvegarde base module/totale'),
                ('restore_database_backup', 'Restauration base module/totale'),
                ('install_update', 'Installer mise à jour ZIP'),
            ], max_length=80),
        ),
    ]
