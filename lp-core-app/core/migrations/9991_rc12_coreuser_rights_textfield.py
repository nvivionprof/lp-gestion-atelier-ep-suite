from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_coreuser_rights_textfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coreuser',
            name='rights',
            field=models.TextField(blank=True, help_text='Droits séparés par ;'),
        ),
    ]
