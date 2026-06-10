from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_database_backup_restore_actions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coreuser',
            name='rights',
            field=models.TextField(blank=True, help_text='Droits séparés par ;'),
        ),
    ]
