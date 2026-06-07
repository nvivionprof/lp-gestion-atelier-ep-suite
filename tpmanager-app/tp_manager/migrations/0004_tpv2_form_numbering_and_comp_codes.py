from django.db import migrations, models
import re


def _norm_comp_code(value):
    raw = str(value or '').strip().upper()
    if re.fullmatch(r'C\d+', raw):
        return f'C{int(raw[1:]):02d}'
    return raw


def normalize_competence_codes(apps, schema_editor):
    BacCompetence = apps.get_model('tp_manager', 'BacCompetence')
    BacCompetenceCritere = apps.get_model('tp_manager', 'BacCompetenceCritere')
    BacTacheCompetence = apps.get_model('tp_manager', 'BacTacheCompetence')
    BacBlocCompetence = apps.get_model('tp_manager', 'BacBlocCompetence')
    BacCompetenceAttitude = apps.get_model('tp_manager', 'BacCompetenceAttitude')
    TPV2CompetenceOfficielle = apps.get_model('tp_manager', 'TPV2CompetenceOfficielle')

    for comp in list(BacCompetence.objects.all().order_by('id')):
        new_code = _norm_comp_code(comp.code)
        if new_code == comp.code:
            continue
        duplicate = BacCompetence.objects.filter(diplome_id=comp.diplome_id, code=new_code).exclude(pk=comp.pk).first()
        if duplicate:
            BacTacheCompetence.objects.filter(competence=comp).update(competence=duplicate)
            BacBlocCompetence.objects.filter(competence=comp).update(competence=duplicate)
            BacCompetenceAttitude.objects.filter(competence=comp).update(competence=duplicate)
            TPV2CompetenceOfficielle.objects.filter(competence=comp).update(competence=duplicate)
            for crit in BacCompetenceCritere.objects.filter(competence=comp):
                new_crit_code = crit.code.replace(comp.code, duplicate.code, 1) if crit.code.startswith(comp.code) else crit.code
                if not BacCompetenceCritere.objects.filter(competence=duplicate, code=new_crit_code).exists():
                    crit.competence = duplicate
                    crit.code = new_crit_code
                    crit.save(update_fields=['competence', 'code'])
                else:
                    crit.delete()
            comp.delete()
        else:
            old_code = comp.code
            comp.code = new_code
            comp.save(update_fields=['code'])
            for crit in BacCompetenceCritere.objects.filter(competence=comp, code__startswith=old_code):
                crit.code = crit.code.replace(old_code, new_code, 1)
                crit.save(update_fields=['code'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tp_manager', '0003_tpv2_referentiel_mecanique_melec'),
    ]

    operations = [
        migrations.AddField(
            model_name='tpv2',
            name='sous_theme',
            field=models.CharField(blank=True, help_text='Sous-thème libre ou issu de la liste du diplôme. Exemple : KNX, GTB, PAC air/eau, adressage IP...', max_length=120),
        ),
        migrations.AddField(
            model_name='tpv2',
            name='problematique_metier',
            field=models.TextField(blank=True, help_text='Problématique liée au métier / missions à réaliser.'),
        ),
        migrations.RunPython(normalize_competence_codes, noop_reverse),
    ]
