# Generated manually for ToolMag
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='component',
            name='photo',
            field=models.ImageField(blank=True, upload_to='components/'),
        ),
    ]
