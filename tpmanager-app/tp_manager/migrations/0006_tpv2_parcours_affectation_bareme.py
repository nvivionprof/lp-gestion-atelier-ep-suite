# Generated for TP Manager V2.8.6
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tp_manager', '0005_tpv2_links_resources_baremes_library'),
    ]

    operations = [
        migrations.AddField(
            model_name='tpv2',
            name='bareme_total',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Barème général indicatif du TP, renseigné dans la page Affecter / barème.', max_digits=7, null=True),
        ),
        migrations.AddField(
            model_name='tpv2competenceofficielle',
            name='pourcentage',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Poids indicatif en pourcentage pour l’évaluation.', max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='tpv2critereofficiel',
            name='pourcentage',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Poids indicatif en pourcentage pour l’évaluation.', max_digits=5, null=True),
        ),
    ]
