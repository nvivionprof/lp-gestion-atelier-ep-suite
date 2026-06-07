from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tp_manager', '0004_tpv2_form_numbering_and_comp_codes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tpv2resourcegroup',
            name='operator',
            field=models.CharField(choices=[('ALL', 'ET — toutes les ressources du groupe sont nécessaires'), ('ANY', 'OU — une ressource du groupe suffit')], default='ANY', max_length=10),
        ),
        migrations.AddField(
            model_name='tpv2competenceofficielle',
            name='niveau_evaluation',
            field=models.CharField(blank=True, help_text='Découverte, entraînement, évaluation formative, certificative...', max_length=80),
        ),
        migrations.AddField(
            model_name='tpv2competenceofficielle',
            name='bareme',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Points affectés à cette compétence pour la notation automatique.', max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='tpv2competenceofficielle',
            name='type_lien',
            field=models.CharField(choices=[('mobilisee', 'Mobilisée — nécessaire au TP mais pas travaillée prioritairement'), ('travaillee', 'Travaillée — compétence travaillée dans le TP'), ('evaluee', 'Évaluée — compétence évaluée dans le TP'), ('certification', 'Certification — compétence support d’une évaluation certificative')], default='travaillee', max_length=30),
        ),
        migrations.AddField(
            model_name='tpv2critereofficiel',
            name='type_lien',
            field=models.CharField(choices=[('mobilisee', 'Mobilisée — nécessaire au TP mais pas travaillée prioritairement'), ('travaillee', 'Travaillée — compétence travaillée dans le TP'), ('evaluee', 'Évaluée — compétence évaluée dans le TP'), ('certification', 'Certification — compétence support d’une évaluation certificative')], default='travaillee', max_length=30),
        ),
        migrations.AddField(
            model_name='tpv2critereofficiel',
            name='bareme',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Points affectés à ce critère officiel.', max_digits=7, null=True),
        ),
        migrations.CreateModel(
            name='TPV2CriterionLibrary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type_critere', models.CharField(choices=[('reussite', 'Critère de réussite'), ('evaluation_finale', 'Critère d’évaluation finale')], default='reussite', max_length=30)),
                ('metier', models.CharField(blank=True, help_text='Métier ou famille métier concernée.', max_length=160)),
                ('theme', models.CharField(blank=True, max_length=160)),
                ('usage_recommande', models.CharField(blank=True, max_length=80)),
                ('libelle', models.CharField(max_length=320)),
                ('description', models.TextField(blank=True)),
                ('niveau_attendu', models.CharField(blank=True, max_length=120)),
                ('indicateur', models.TextField(blank=True)),
                ('bareme', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('diplome', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='criteres_bibliotheque', to='tp_manager.bacdiplome')),
            ],
            options={
                'verbose_name': 'V2 bibliothèque de critères ajoutables',
                'verbose_name_plural': 'V2 bibliothèque de critères ajoutables',
                'ordering': ['type_critere', 'diplome__code', 'metier', 'theme', 'ordre', 'libelle'],
            },
        ),
        migrations.CreateModel(
            name='TPV2LinkedBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('sens', models.CharField(choices=[('avant', 'TP liés avant / prérequis'), ('apres', 'TP liés après / poursuite')], default='avant', max_length=20)),
                ('titre', models.CharField(default='Bloc de TP liés', max_length=220)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('commentaire', models.TextField(blank=True)),
                ('tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linked_blocks', to='tp_manager.tpv2')),
            ],
            options={
                'verbose_name': 'V2 bloc de TP liés',
                'verbose_name_plural': 'V2 blocs de TP liés',
                'ordering': ['sens', 'ordre', 'id'],
            },
        ),
        migrations.CreateModel(
            name='TPV2LinkedTPItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('niveau_lien', models.CharField(choices=[('conseille', 'Conseillé'), ('obligatoire', 'Obligatoire')], default='conseille', max_length=20)),
                ('commentaire', models.CharField(blank=True, max_length=260)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='tp_manager.tpv2linkedblock')),
                ('linked_tp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linked_from_items', to='tp_manager.tpv2')),
            ],
            options={
                'verbose_name': 'V2 TP lié',
                'verbose_name_plural': 'V2 TP liés',
                'ordering': ['ordre', 'linked_tp__code'],
                'unique_together': {('block', 'linked_tp')},
            },
        ),
    ]
