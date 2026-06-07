from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone


class EvalLevel(models.TextChoices):
    NE = 'NE', 'Non évaluable'
    NA = 'NA', 'Non acquis'
    EC = 'EC', 'En cours d’acquisition'
    A = 'A', 'Acquis'
    PA = 'PA', 'Parfaitement acquis / transférable'
    AB = 'AB', 'Absent'


LEVEL_COLORS = {
    EvalLevel.NE: '#2f80ed',
    EvalLevel.NA: '#d90429',
    EvalLevel.EC: '#f59e0b',
    EvalLevel.A: '#9be37d',
    EvalLevel.PA: '#3f8f29',
    EvalLevel.AB: '#9ca3af',
}
LEVEL_SCORES = {
    EvalLevel.NE: Decimal('0'),
    EvalLevel.NA: Decimal('0'),
    EvalLevel.EC: Decimal('0.50'),
    EvalLevel.A: Decimal('0.80'),
    EvalLevel.PA: Decimal('1.00'),
    EvalLevel.AB: Decimal('0'),
}


class EvalTimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EvalActivity(EvalTimeStampedModel):
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('auto_evalue', 'Autoévalué par l’élève'),
        ('evalue_prof', 'Évalué par le professeur'),
        ('bilan', 'Bilan intermédiaire'),
        ('archive', 'Archivé'),
    ]
    eleve = models.ForeignKey('tp_manager.TpUser', on_delete=models.CASCADE, related_name='eval_activities')
    tp = models.ForeignKey('tp_manager.TPV2', on_delete=models.SET_NULL, null=True, blank=True, related_name='eval_activities')
    sequence_code = models.CharField(max_length=120, blank=True, help_text='Code ou libellé de la séquence source si disponible.')
    code_eval = models.CharField(max_length=120, blank=True, help_text='Code court affiché en colonne de tableau de bord.')
    intitule = models.CharField(max_length=260)
    date_activite = models.DateField(default=timezone.localdate)
    formation_code = models.CharField(max_length=40, blank=True)
    classe = models.CharField(max_length=80, blank=True)
    zone_code = models.CharField(max_length=80, blank=True)
    systeme_code = models.CharField(max_length=120, blank=True)
    statut = models.CharField(max_length=30, choices=STATUS_CHOICES, default='evalue_prof')
    absent = models.BooleanField(default=False, help_text='Une seule case professeur : applique AB à toutes les lignes de l’activité.')
    non_fait = models.BooleanField(default=False)
    a_refaire = models.BooleanField(default=False)
    remediation_necessaire = models.BooleanField(default=False)
    tp_note = models.BooleanField(default=False, help_text='Affiche une note en bas de la colonne si activé dans la séquence.')
    bareme_total = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    note_calculee = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    auto_commentaire = models.TextField(blank=True)
    prof_commentaire = models.TextField(blank=True)
    evaluateur = models.ForeignKey('tp_manager.TpUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='evals_professeur')
    date_validation_prof = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['eleve__last_name', 'eleve__first_name', 'date_activite', 'code_eval']
        verbose_name = 'activité évaluée'
        verbose_name_plural = 'activités évaluées'

    def __str__(self):
        code = self.code_eval or (self.tp.code if self.tp_id else 'ACT')
        return f'{self.eleve.full_name} — {code}'

    def calculate_note(self, save=True):
        if self.absent or self.non_fait or not self.tp_note or not self.bareme_total:
            self.note_calculee = None
            if save:
                self.save(update_fields=['note_calculee', 'updated_at'])
            return self.note_calculee
        total = Decimal('0')
        for result in self.criteria_results.all():
            total += result.points_professeur()
        self.note_calculee = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if save:
            self.save(update_fields=['note_calculee', 'updated_at'])
        return self.note_calculee


class EvalCriterionResult(EvalTimeStampedModel):
    activity = models.ForeignKey(EvalActivity, on_delete=models.CASCADE, related_name='criteria_results')
    critere = models.ForeignKey('tp_manager.BacCompetenceCritere', on_delete=models.PROTECT, related_name='eval_results')
    auto_niveau = models.CharField(max_length=2, choices=EvalLevel.choices, blank=True)
    prof_niveau = models.CharField(max_length=2, choices=EvalLevel.choices, default=EvalLevel.NE)
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Pourcentage du barème total du TP. Les points se calculent automatiquement.')
    a_refaire = models.BooleanField(default=False)
    commentaire_eleve = models.TextField(blank=True)
    commentaire_prof = models.TextField(blank=True)

    class Meta:
        unique_together = [('activity', 'critere')]
        ordering = ['critere__competence__code', 'critere__ordre']
        verbose_name = 'résultat de critère évalué'
        verbose_name_plural = 'résultats de critères évalués'

    def __str__(self):
        return f'{self.activity} — {self.critere.competence.code}/{self.critere.code}'

    @property
    def competence(self):
        return self.critere.competence

    def niveau_prof_effectif(self):
        if self.activity.absent:
            return EvalLevel.AB
        if self.activity.non_fait:
            return EvalLevel.NE
        return self.prof_niveau or EvalLevel.NE

    def level_color(self):
        return LEVEL_COLORS.get(self.niveau_prof_effectif(), '#e5e7eb')

    def points_professeur(self):
        if not self.activity.bareme_total or not self.pourcentage:
            return Decimal('0')
        coef = LEVEL_SCORES.get(self.niveau_prof_effectif(), Decimal('0'))
        raw = Decimal(self.activity.bareme_total) * Decimal(self.pourcentage) / Decimal('100') * coef
        return raw.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class EvalBilanIntermediaire(EvalTimeStampedModel):
    TYPE_CHOICES = [('periode', 'Bilan de période'), ('pfmp', 'Bilan avant/après PFMP'), ('ccf', 'Bilan avant CCF'), ('final', 'Bilan final'), ('libre', 'Bilan libre')]
    eleve = models.ForeignKey('tp_manager.TpUser', on_delete=models.CASCADE, related_name='eval_bilans')
    nom = models.CharField(max_length=180)
    type_bilan = models.CharField(max_length=20, choices=TYPE_CHOICES, default='periode')
    date_bilan = models.DateField(default=timezone.localdate)
    formation_code = models.CharField(max_length=40, blank=True)
    classe = models.CharField(max_length=80, blank=True)
    commentaire = models.TextField(blank=True)
    verrouille = models.BooleanField(default=False)
    validateur = models.ForeignKey('tp_manager.TpUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='eval_bilans_valides')

    class Meta:
        ordering = ['eleve__last_name', 'eleve__first_name', 'date_bilan']
        verbose_name = 'bilan intermédiaire de compétences'
        verbose_name_plural = 'bilans intermédiaires de compétences'

    def __str__(self):
        return f'{self.eleve.full_name} — {self.nom}'


class EvalBilanCompetence(EvalTimeStampedModel):
    bilan = models.ForeignKey(EvalBilanIntermediaire, on_delete=models.CASCADE, related_name='competence_results')
    competence = models.ForeignKey('tp_manager.BacCompetence', on_delete=models.PROTECT, related_name='eval_bilan_results')
    niveau = models.CharField(max_length=2, choices=EvalLevel.choices, default=EvalLevel.NE)
    commentaire = models.TextField(blank=True)
    date_validation = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [('bilan', 'competence')]
        ordering = ['competence__code']
        verbose_name = 'résultat de bilan compétence'
        verbose_name_plural = 'résultats de bilan compétences'

    def __str__(self):
        return f'{self.bilan} — {self.competence.code} : {self.niveau}'

    def level_color(self):
        return LEVEL_COLORS.get(self.niveau, '#e5e7eb')
