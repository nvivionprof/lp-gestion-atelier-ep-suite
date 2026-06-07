# Generated for LP Gestion Atelier EP Suite V0.4.0
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_v034_classes_zones_atelier'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicsuitesettings',
            name='pfmp_port',
            field=models.PositiveIntegerField(default=9006),
        ),
    ]
