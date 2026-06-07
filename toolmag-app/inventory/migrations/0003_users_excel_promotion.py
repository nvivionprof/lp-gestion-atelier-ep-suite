# Generated for ToolMag V4 — users Excel import/export and school-year promotion
from django.db import migrations, models
import django.db.models.deletion


def seed_formations(apps, schema_editor):
    Formation = apps.get_model('inventory', 'Formation')
    defaults = [
        ('CAP_ELEC', 'CAP Pro Électricité', 'CAP Pro Électricité — dérivé MELEC'),
        ('BAC_MELEC', 'Bac Pro MELEC', 'Bac Pro MELEC'),
        ('BAC_CIEL', 'Bac Pro CIEL', 'Bac Pro CIEL'),
        ('BTS_ET', 'BTS Électrotechnique', 'BTS Électrotechnique'),
        ('BTS_FED', 'BTS Fluides Énergies Domotique', 'BTS FED'),
    ]
    for code, name, ref in defaults:
        Formation.objects.get_or_create(code=code, defaults={'name': name, 'referential_name': ref, 'active': True})


def rollback_seed_formations(apps, schema_editor):
    Formation = apps.get_model('inventory', 'Formation')
    Formation.objects.filter(code__in=['CAP_ELEC', 'BAC_MELEC', 'BAC_CIEL', 'BTS_ET', 'BTS_FED']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_component_photo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Formation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(choices=[('CAP_ELEC', 'CAP Pro Électricité'), ('BAC_MELEC', 'Bac Pro MELEC'), ('BAC_CIEL', 'Bac Pro CIEL'), ('BTS_ET', 'BTS Électrotechnique'), ('BTS_FED', 'BTS FED')], max_length=32, unique=True)),
                ('name', models.CharField(max_length=160)),
                ('referential_name', models.CharField(blank=True, max_length=160)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.AddField(
            model_name='person',
            name='allowed_roles',
            field=models.CharField(blank=True, help_text='Rôles autorisés séparés par des points-virgules : UTILISATEUR;MAGASINIER;TECH_INVENTAIRE', max_length=255),
        ),
        migrations.AddField(
            model_name='person',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='person',
            name='class_name',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='person',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='person',
            name='group_name',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='person',
            name='level',
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name='person',
            name='username',
            field=models.CharField(blank=True, max_length=120, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='person',
            name='formation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='persons', to='inventory.formation'),
        ),
        migrations.CreateModel(
            name='EnrollmentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school_year', models.CharField(blank=True, max_length=20)),
                ('event_type', models.CharField(choices=[('created', 'Création'), ('promoted', 'Montée de niveau'), ('repeated', 'Redoublement'), ('transferred', 'Changement de filière'), ('group_changed', 'Changement de classe/groupe'), ('deactivated', 'Désactivation'), ('archived', 'Archivage'), ('deleted_requested', 'Suppression demandée'), ('import_updated', 'Mise à jour par import')], max_length=40)),
                ('old_class_name', models.CharField(blank=True, max_length=80)),
                ('new_class_name', models.CharField(blank=True, max_length=80)),
                ('old_group_name', models.CharField(blank=True, max_length=80)),
                ('new_group_name', models.CharField(blank=True, max_length=80)),
                ('comment', models.TextField(blank=True)),
                ('new_formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='inventory.formation')),
                ('old_formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='inventory.formation')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollment_history', to='inventory.person')),
            ],
            options={
                'verbose_name': 'Historique de parcours élève',
                'verbose_name_plural': 'Historiques de parcours élèves',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(seed_formations, rollback_seed_formations),
    ]
