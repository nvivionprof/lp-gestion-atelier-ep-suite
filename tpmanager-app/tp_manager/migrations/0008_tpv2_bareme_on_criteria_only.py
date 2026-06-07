from django.db import migrations


def clear_competence_weights(apps, schema_editor):
    TPV2CompetenceOfficielle = apps.get_model('tp_manager', 'TPV2CompetenceOfficielle')
    TPV2CompetenceOfficielle.objects.update(pourcentage=None, bareme=None)


class Migration(migrations.Migration):
    dependencies = [
        ('tp_manager', '0007_alter_tpv2_domaine_principal_and_more'),
    ]

    operations = [
        migrations.RunPython(clear_competence_weights, migrations.RunPython.noop),
    ]
