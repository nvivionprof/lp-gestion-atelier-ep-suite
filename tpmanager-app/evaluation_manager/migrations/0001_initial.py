# Generated manually for LP Gestion Atelier EP Suite v2.9.0
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('tp_manager', '0008_tpv2_bareme_on_criteria_only'),
    ]
    operations = [
        migrations.CreateModel(
            name='EvalActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sequence_code', models.CharField(blank=True, help_text='Code ou libellé de la séquence source si disponible.', max_length=120)),
                ('code_eval', models.CharField(blank=True, help_text='Code court affiché en colonne de tableau de bord.', max_length=120)),
                ('intitule', models.CharField(max_length=260)),
                ('date_activite', models.DateField(default=django.utils.timezone.localdate)),
                ('formation_code', models.CharField(blank=True, max_length=40)),
                ('classe', models.CharField(blank=True, max_length=80)),
                ('zone_code', models.CharField(blank=True, max_length=80)),
                ('systeme_code', models.CharField(blank=True, max_length=120)),
                ('statut', models.CharField(choices=[('brouillon', 'Brouillon'), ('auto_evalue', 'Autoévalué par l’élève'), ('evalue_prof', 'Évalué par le professeur'), ('bilan', 'Bilan intermédiaire'), ('archive', 'Archivé')], default='evalue_prof', max_length=30)),
                ('absent', models.BooleanField(default=False, help_text='Une seule case professeur : applique AB à toutes les lignes de l’activité.')),
                ('non_fait', models.BooleanField(default=False)),
                ('a_refaire', models.BooleanField(default=False)),
                ('remediation_necessaire', models.BooleanField(default=False)),
                ('tp_note', models.BooleanField(default=False, help_text='Affiche une note en bas de la colonne si activé dans la séquence.')),
                ('bareme_total', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('note_calculee', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('auto_commentaire', models.TextField(blank=True)),
                ('prof_commentaire', models.TextField(blank=True)),
                ('date_validation_prof', models.DateTimeField(blank=True, null=True)),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eval_activities', to='tp_manager.tpuser')),
                ('evaluateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='evals_professeur', to='tp_manager.tpuser')),
                ('tp', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eval_activities', to='tp_manager.tpv2')),
            ],
            options={'verbose_name': 'activité évaluée', 'verbose_name_plural': 'activités évaluées', 'ordering': ['eleve__last_name', 'eleve__first_name', 'date_activite', 'code_eval']},
        ),
        migrations.CreateModel(
            name='EvalBilanIntermediaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('nom', models.CharField(max_length=180)),
                ('type_bilan', models.CharField(choices=[('periode', 'Bilan de période'), ('pfmp', 'Bilan avant/après PFMP'), ('ccf', 'Bilan avant CCF'), ('final', 'Bilan final'), ('libre', 'Bilan libre')], default='periode', max_length=20)),
                ('date_bilan', models.DateField(default=django.utils.timezone.localdate)),
                ('formation_code', models.CharField(blank=True, max_length=40)),
                ('classe', models.CharField(blank=True, max_length=80)),
                ('commentaire', models.TextField(blank=True)),
                ('verrouille', models.BooleanField(default=False)),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='eval_bilans', to='tp_manager.tpuser')),
                ('validateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eval_bilans_valides', to='tp_manager.tpuser')),
            ],
            options={'verbose_name': 'bilan intermédiaire de compétences', 'verbose_name_plural': 'bilans intermédiaires de compétences', 'ordering': ['eleve__last_name', 'eleve__first_name', 'date_bilan']},
        ),
        migrations.CreateModel(
            name='EvalCriterionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('auto_niveau', models.CharField(blank=True, choices=[('NE', 'Non évaluable'), ('NA', 'Non acquis'), ('EC', 'En cours d’acquisition'), ('A', 'Acquis'), ('PA', 'Parfaitement acquis / transférable'), ('AB', 'Absent')], max_length=2)),
                ('prof_niveau', models.CharField(choices=[('NE', 'Non évaluable'), ('NA', 'Non acquis'), ('EC', 'En cours d’acquisition'), ('A', 'Acquis'), ('PA', 'Parfaitement acquis / transférable'), ('AB', 'Absent')], default='NE', max_length=2)),
                ('pourcentage', models.DecimalField(blank=True, decimal_places=2, help_text='Pourcentage du barème total du TP. Les points se calculent automatiquement.', max_digits=5, null=True)),
                ('a_refaire', models.BooleanField(default=False)),
                ('commentaire_eleve', models.TextField(blank=True)),
                ('commentaire_prof', models.TextField(blank=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='criteria_results', to='evaluation_manager.evalactivity')),
                ('critere', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='eval_results', to='tp_manager.baccompetencecritere')),
            ],
            options={'verbose_name': 'résultat de critère évalué', 'verbose_name_plural': 'résultats de critères évalués', 'ordering': ['critere__competence__code', 'critere__ordre'], 'unique_together': {('activity', 'critere')}},
        ),
        migrations.CreateModel(
            name='EvalBilanCompetence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('niveau', models.CharField(choices=[('NE', 'Non évaluable'), ('NA', 'Non acquis'), ('EC', 'En cours d’acquisition'), ('A', 'Acquis'), ('PA', 'Parfaitement acquis / transférable'), ('AB', 'Absent')], default='NE', max_length=2)),
                ('commentaire', models.TextField(blank=True)),
                ('date_validation', models.DateField(blank=True, null=True)),
                ('bilan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='competence_results', to='evaluation_manager.evalbilanintermediaire')),
                ('competence', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='eval_bilan_results', to='tp_manager.baccompetence')),
            ],
            options={'verbose_name': 'résultat de bilan compétence', 'verbose_name_plural': 'résultats de bilan compétences', 'ordering': ['competence__code'], 'unique_together': {('bilan', 'competence')}},
        ),
    ]
