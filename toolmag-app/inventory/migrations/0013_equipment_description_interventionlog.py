# Generated manually for ToolMag V28
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_add_absent_condition'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='description',
            field=models.CharField(blank=True, help_text='Exemple : contrôleur d’installation, oscilloscope triphasé, kit soudure fibre…', max_length=255, verbose_name='Descriptif matériel'),
        ),
        migrations.CreateModel(
            name='InterventionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('intervention_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('intervention_type', models.CharField(choices=[('control', 'Contrôle'), ('cleaning', 'Nettoyage'), ('periodic_check', 'Vérification périodique'), ('reconditioning', 'Reconditionnement'), ('accessory_check', 'Contrôle accessoires'), ('functional_test', 'Test fonctionnement'), ('light_maintenance', 'Maintenance légère'), ('other', 'Autre')], default='control', max_length=40)),
                ('finding', models.TextField(blank=True, verbose_name='Constat')),
                ('action_done', models.TextField(blank=True, verbose_name='Action réalisée')),
                ('result', models.CharField(choices=[('no_issue', 'RAS'), ('watch', 'À surveiller'), ('available', 'Matériel disponible'), ('incomplete', 'Matériel incomplet'), ('send_maintenance', 'Envoyer en maintenance'), ('out_of_service', 'Hors service')], default='no_issue', max_length=40)),
                ('resulting_condition', models.CharField(choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux'), ('absent', 'Absent')], default='good', max_length=30)),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire bon d’intervention')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='interventions', to='inventory.equipment')),
                ('storekeeper', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='interventions_done', to='inventory.person')),
            ],
            options={
                'verbose_name': 'Bon d’intervention',
                'verbose_name_plural': 'Bons d’intervention',
                'ordering': ['-intervention_at'],
            },
        ),
    ]
