from django.db import migrations, models


def seed_default_checks(apps, schema_editor):
    DefaultCheckTemplate = apps.get_model('system_manager', 'DefaultCheckTemplate')
    defaults = [
        (10, 'Système propre et en ordre', 'deux', 'oui', True, False),
        (20, 'Zone autour du système dégagée', 'deux', 'oui', True, False),
        (30, 'Classeur présent', 'deux', 'oui', True, False),
        (40, 'Classeur complet', 'deux', 'oui', True, False),
        (50, 'Système allumé ou éteint selon consigne', 'deux', 'oui', True, False),
        (60, 'Aucun câble, flexible ou accessoire visiblement endommagé', 'deux', 'oui', True, True),
        (70, 'Équipements de sécurité présents si nécessaires', 'deux', 'oui', True, True),
        (80, 'Défaut ou anomalie constatée', 'deux', 'non', False, False),
    ]
    for ordre, libelle, phase, expected, obligatoire, bloquant in defaults:
        DefaultCheckTemplate.objects.get_or_create(
            libelle=libelle,
            defaults={
                'ordre': ordre,
                'phase': phase,
                'type_reponse': 'oui_non_nc',
                'expected_response': expected,
                'obligatoire': obligatoire,
                'bloquant_si_non': bloquant,
                'active': True,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ('system_manager', '0005_v037_previews_checks_anomalies_class_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='DefaultCheckTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('libelle', models.CharField(max_length=240)),
                ('aide', models.TextField(blank=True)),
                ('phase', models.CharField(choices=[('prise', 'Prise de poste'), ('restitution', 'Restitution'), ('deux', 'Prise et restitution')], default='deux', max_length=30)),
                ('type_reponse', models.CharField(choices=[('oui_non_nc', 'Oui / Non / NC'), ('texte', 'Texte libre'), ('photo', 'Photo'), ('nombre', 'Nombre')], default='oui_non_nc', max_length=30)),
                ('expected_response', models.CharField(blank=True, choices=[('oui', 'Oui attendu'), ('non', 'Non attendu'), ('nc', 'NC attendu'), ('', 'Non contrôlé')], default='oui', max_length=20, verbose_name='Réponse attendue')),
                ('obligatoire', models.BooleanField(default=True)),
                ('bloquant_si_non', models.BooleanField(default=False)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'check par défaut système',
                'verbose_name_plural': 'checks par défaut systèmes',
                'ordering': ['ordre', 'id'],
            },
        ),
        migrations.RunPython(seed_default_checks, migrations.RunPython.noop),
    ]
