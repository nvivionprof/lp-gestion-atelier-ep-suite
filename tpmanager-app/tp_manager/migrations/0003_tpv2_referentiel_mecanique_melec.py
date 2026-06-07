# Generated manually for LP Gestion Atelier EP Suite — TP Manager V2.8.2

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tp_manager', '0002_tpmanager_v2'),
    ]

    operations = [
        migrations.AddField(
            model_name='tpv2',
            name='type_activite',
            field=models.CharField(choices=[('TP', 'TP'), ('TD', 'TD'), ('PROJET', 'Projet'), ('EVAL', 'Évaluation'), ('RECH', 'Recherche'), ('SAE', 'Situation / SAE')], default='TP', help_text='Utilisé pour la numérotation automatique.', max_length=20),
        ),
        migrations.AddField(
            model_name='tpv2',
            name='domaine_principal',
            field=models.CharField(blank=True, help_text='Domaine utilisé dans le code automatique : domotique, PAC, réseau, câblage...', max_length=120),
        ),
        migrations.CreateModel(
            name='BacActivite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=40)),
                ('libelle_officiel', models.CharField(max_length=360)),
                ('description', models.TextField(blank=True)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('locked_official', models.BooleanField(default=True)),
                ('diplome', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activites_officielles', to='tp_manager.bacdiplome')),
            ],
            options={'verbose_name': 'V2 activité officielle', 'verbose_name_plural': 'V2 activités officielles', 'ordering': ['diplome__code', 'ordre', 'code'], 'unique_together': {('diplome', 'code')}},
        ),
        migrations.CreateModel(
            name='BacAttitudeProfessionnelle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=40)),
                ('libelle_officiel', models.CharField(max_length=320)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('locked_official', models.BooleanField(default=True)),
                ('diplome', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attitudes_professionnelles', to='tp_manager.bacdiplome')),
            ],
            options={'verbose_name': 'V2 attitude professionnelle officielle', 'verbose_name_plural': 'V2 attitudes professionnelles officielles', 'ordering': ['diplome__code', 'ordre', 'code'], 'unique_together': {('diplome', 'code')}},
        ),
        migrations.CreateModel(
            name='BacCompetenceCritere',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=60)),
                ('libelle_officiel', models.CharField(max_length=520)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('locked_official', models.BooleanField(default=True)),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteres_officiels', to='tp_manager.baccompetence')),
            ],
            options={'verbose_name': 'V2 critère officiel de compétence', 'verbose_name_plural': 'V2 critères officiels de compétence', 'ordering': ['competence__diplome__code', 'competence__code', 'ordre', 'code'], 'unique_together': {('competence', 'code')}},
        ),
        migrations.CreateModel(
            name='BacTache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=40)),
                ('libelle_officiel', models.CharField(max_length=520)),
                ('autonomie', models.CharField(choices=[('non_precise', 'Non précisée'), ('partielle', 'Partielle'), ('totale', 'Totale'), ('mixte', 'Partielle ou totale selon contexte')], default='non_precise', max_length=30)),
                ('responsabilite_personnes', models.BooleanField(default=False)),
                ('responsabilite_moyens', models.BooleanField(default=False)),
                ('responsabilite_resultat', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True)),
                ('moyens_ressources', models.TextField(blank=True)),
                ('resultats_attendus', models.TextField(blank=True)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('locked_official', models.BooleanField(default=True)),
                ('activite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taches', to='tp_manager.bacactivite')),
            ],
            options={'verbose_name': 'V2 tâche officielle', 'verbose_name_plural': 'V2 tâches officielles', 'ordering': ['activite__diplome__code', 'activite__ordre', 'ordre', 'code'], 'unique_together': {('activite', 'code')}},
        ),
        migrations.CreateModel(
            name='BacCompetenceAttitude',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attitude', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competences_liees', to='tp_manager.bacattitudeprofessionnelle')),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attitudes_liees', to='tp_manager.baccompetence')),
            ],
            options={'verbose_name': 'V2 lien compétence-attitude officielle', 'verbose_name_plural': 'V2 liens compétence-attitude officielles', 'ordering': ['competence__code', 'attitude__code'], 'unique_together': {('competence', 'attitude')}},
        ),
        migrations.CreateModel(
            name='BacTacheCompetence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('poids', models.PositiveSmallIntegerField(blank=True, help_text='1 = secondaire, 2 = essentielle selon le tableau officiel quand disponible.', null=True)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taches_liees_v2', to='tp_manager.baccompetence')),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competences_liees', to='tp_manager.bactache')),
            ],
            options={'verbose_name': 'V2 lien tâche-compétence officiel', 'verbose_name_plural': 'V2 liens tâche-compétence officiels', 'ordering': ['tache__activite__ordre', 'tache__ordre', 'competence__code'], 'unique_together': {('tache', 'competence')}},
        ),
        migrations.CreateModel(
            name='TPV2ActiviteOfficielle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('activite', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tps_v2', to='tp_manager.bacactivite')),
                ('tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activites_officielles', to='tp_manager.tpv2')),
            ],
            options={'verbose_name': 'V2 activité officielle associée au TP', 'verbose_name_plural': 'V2 activités officielles associées au TP', 'ordering': ['activite__ordre'], 'unique_together': {('tp', 'activite')}},
        ),
        migrations.CreateModel(
            name='TPV2AttitudeOfficielle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attitude', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tps_v2', to='tp_manager.bacattitudeprofessionnelle')),
                ('tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attitudes_officielles_selectionnees', to='tp_manager.tpv2')),
            ],
            options={'verbose_name': 'V2 attitude professionnelle sélectionnée', 'verbose_name_plural': 'V2 attitudes professionnelles sélectionnées', 'ordering': ['attitude__ordre'], 'unique_together': {('tp', 'attitude')}},
        ),
        migrations.CreateModel(
            name='TPV2CritereOfficiel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('critere', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tps_v2', to='tp_manager.baccompetencecritere')),
                ('tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteres_officiels_selectionnes', to='tp_manager.tpv2')),
            ],
            options={'verbose_name': 'V2 critère officiel sélectionné', 'verbose_name_plural': 'V2 critères officiels sélectionnés', 'ordering': ['critere__competence__code', 'critere__ordre'], 'unique_together': {('tp', 'critere')}},
        ),
        migrations.CreateModel(
            name='TPV2TacheOfficielle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tache', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tps_v2', to='tp_manager.bactache')),
                ('tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='taches_officielles', to='tp_manager.tpv2')),
            ],
            options={'verbose_name': 'V2 tâche officielle associée au TP', 'verbose_name_plural': 'V2 tâches officielles associées au TP', 'ordering': ['tache__activite__ordre', 'tache__ordre'], 'unique_together': {('tp', 'tache')}},
        ),
    ]
