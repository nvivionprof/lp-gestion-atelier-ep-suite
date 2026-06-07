from __future__ import annotations
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from tp_manager.models import TpUser, BacDiplome, BacCompetence, BacCompetenceCritere, TPV2, SystemePedagogiqueRef, TimeStampedModel, normalize_code


class SeqColoration(TimeStampedModel):
    STATUS_CHOICES = [('formelle', 'Formelle'), ('etablissement', 'Établissement'), ('locale', 'Locale')]
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=30, choices=STATUS_CHOICES, default='formelle')
    couleur = models.CharField(max_length=20, default='#2563eb')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'coloration de séquence'
        verbose_name_plural = 'colorations de séquence'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'COLORATION', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class SeqZone(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    capacite_max = models.PositiveIntegerField(null=True, blank=True)
    systemes = models.ManyToManyField(SystemePedagogiqueRef, blank=True, related_name='seq_zones')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'zone Sequence Manager'
        verbose_name_plural = 'zones Sequence Manager'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'ZONE', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class SeqWeeklySlot(TimeStampedModel):
    DAY_CHOICES = [
        (1, 'Lundi'), (2, 'Mardi'), (3, 'Mercredi'), (4, 'Jeudi'), (5, 'Vendredi'), (6, 'Samedi'),
    ]
    HALF_CHOICES = [('AM', 'Matin'), ('PM', 'Après-midi')]
    code = models.CharField(max_length=20, unique=True, blank=True)
    day = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    half_day = models.CharField(max_length=2, choices=HALF_CHOICES)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('day', 'half_day')]
        ordering = ['day', 'half_day']
        verbose_name = 'créneau hebdomadaire'
        verbose_name_plural = 'créneaux hebdomadaires'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f'{self.get_day_display()[:3].upper()}_{self.half_day}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.get_day_display()} {self.get_half_day_display().lower()}'


class SeqRotationBlock(TimeStampedModel):
    nom = models.CharField(max_length=180)
    code = models.CharField(max_length=40, unique=True, blank=True)
    description = models.TextField(blank=True)
    slots = models.ManyToManyField(SeqWeeklySlot, blank=True, related_name='rotation_blocks')
    zones = models.ManyToManyField(SeqZone, blank=True, related_name='rotation_blocks')
    professeurs = models.ManyToManyField(TpUser, blank=True, related_name='seq_rotation_blocks', limit_choices_to={'role_principal__in': ['professeur', 'admin', 'responsable']})
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'bloc de rotation'
        verbose_name_plural = 'blocs de rotation'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'BLOC', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class SeqRotationFormation(TimeStampedModel):
    block = models.ForeignKey(SeqRotationBlock, on_delete=models.CASCADE, related_name='formations')
    formation_code = models.CharField(max_length=40)
    classe = models.CharField(max_length=120, blank=True)
    niveau = models.CharField(max_length=80, blank=True)
    effectif_prevu = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['block__nom', 'formation_code', 'classe']
        verbose_name = 'formation dans bloc de rotation'
        verbose_name_plural = 'formations dans blocs de rotation'

    def __str__(self):
        return f'{self.block.code} — {self.formation_code} {self.classe}'.strip()


class SeqSequence(TimeStampedModel):
    STATUS_CHOICES = [('draft', 'Brouillon'), ('active', 'Active'), ('locked', 'Verrouillée'), ('done', 'Terminée'), ('archived', 'Archivée')]
    titre = models.CharField(max_length=220)
    code = models.CharField(max_length=80, unique=True, blank=True)
    description = models.TextField(blank=True)
    rotation_block = models.ForeignKey(SeqRotationBlock, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    zone_principale = models.ForeignKey(SeqZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    coloration = models.ForeignKey(SeqColoration, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    axe_principal = models.CharField(max_length=180, blank=True)
    date_debut = models.DateField(default=timezone.localdate)
    nb_semaines = models.PositiveIntegerField(default=3)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    professeurs = models.ManyToManyField(TpUser, blank=True, related_name='seq_sequences_prof')
    zones = models.ManyToManyField(SeqZone, blank=True, related_name='seq_sequences')
    slots = models.ManyToManyField(SeqWeeklySlot, blank=True, related_name='seq_sequences')
    auto_inscription_libre = models.BooleanField(default=False, help_text='Premier arrivé, premier servi pour les parcours libres.')
    validation_prof_requise = models.BooleanField(default=True)
    notes_tp_activees = models.BooleanField(default=False)
    sequence_modele = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_debut', 'titre']
        verbose_name = 'séquence'
        verbose_name_plural = 'séquences'

    def save(self, *args, **kwargs):
        if not self.code:
            base = normalize_code(self.titre, 'SEQ', 30)
            year = self.date_debut.year if self.date_debut else timezone.localdate().year
            prefix = f'{base}-{year}'
            n = SeqSequence.objects.exclude(pk=self.pk).filter(code__startswith=prefix).count() + 1
            self.code = f'{prefix}-{n:03d}'
        super().save(*args, **kwargs)

    @property
    def date_fin(self):
        return self.date_debut + timedelta(weeks=max(self.nb_semaines, 1)) - timedelta(days=1)

    def __str__(self):
        return f'{self.code} — {self.titre}'


class SeqSequenceFormation(TimeStampedModel):
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='formations')
    diplome = models.ForeignKey(BacDiplome, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_formations')
    formation_code = models.CharField(max_length=40)
    classe = models.CharField(max_length=120, blank=True)
    niveau = models.CharField(max_length=80, blank=True)
    effectif = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('sequence', 'formation_code', 'classe')]
        ordering = ['sequence__date_debut', 'formation_code', 'classe']
        verbose_name = 'formation concernée par séquence'
        verbose_name_plural = 'formations concernées par séquence'

    def __str__(self):
        return f'{self.sequence.code} — {self.formation_code} {self.classe}'


class SeqPresenceWave(TimeStampedModel):
    TYPE_CHOICES = [('fixed', 'Groupe fixe'), ('wave', 'Vague courte'), ('free', 'Parcours libre'), ('pfmp', 'PFMP')]
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='waves')
    nom = models.CharField(max_length=120)
    formation_code = models.CharField(max_length=40)
    classe = models.CharField(max_length=120, blank=True)
    type_presence = models.CharField(max_length=20, choices=TYPE_CHOICES, default='fixed')
    semaine_debut = models.PositiveIntegerField(default=1)
    duree_semaines = models.PositiveIntegerField(default=1)
    eleves = models.ManyToManyField(TpUser, blank=True, related_name='seq_waves')

    class Meta:
        ordering = ['sequence', 'semaine_debut', 'formation_code', 'nom']
        verbose_name = 'vague de présence'
        verbose_name_plural = 'vagues de présence'

    @property
    def semaine_fin(self):
        return self.semaine_debut + self.duree_semaines - 1

    def is_active_week(self, week_num: int):
        return self.semaine_debut <= week_num <= self.semaine_fin

    def __str__(self):
        return f'{self.sequence.code} — {self.nom}'


class SeqStudentGroup(TimeStampedModel):
    TYPE_CHOICES = [('solo', 'Élève seul'), ('binome', 'Binôme'), ('trinome', 'Trinôme'), ('group', 'Groupe'), ('mixed', 'Groupe mixte'), ('free', 'Parcours libre')]
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='student_groups')
    wave = models.ForeignKey(SeqPresenceWave, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups')
    nom = models.CharField(max_length=120)
    type_groupe = models.CharField(max_length=20, choices=TYPE_CHOICES, default='binome')
    formation_dominante = models.CharField(max_length=40, blank=True)
    ordre = models.PositiveIntegerField(default=1)
    parcours_libre = models.BooleanField(default=False)

    class Meta:
        ordering = ['sequence', 'ordre', 'nom']
        verbose_name = 'groupe élève de séquence'
        verbose_name_plural = 'groupes élèves de séquence'

    def __str__(self):
        return f'{self.sequence.code} — {self.nom}'


class SeqStudentGroupMember(TimeStampedModel):
    group = models.ForeignKey(SeqStudentGroup, on_delete=models.CASCADE, related_name='members')
    eleve = models.ForeignKey(TpUser, on_delete=models.CASCADE, related_name='seq_group_memberships')
    role = models.CharField(max_length=40, default='membre')
    ordre = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [('group', 'eleve')]
        ordering = ['group__ordre', 'ordre', 'eleve__last_name']
        verbose_name = 'membre de groupe séquence'
        verbose_name_plural = 'membres de groupes séquence'

    def __str__(self):
        return f'{self.group.nom} — {self.eleve.full_name}'


class SeqSession(TimeStampedModel):
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='sessions')
    numero = models.PositiveIntegerField(default=1)
    semaine = models.PositiveIntegerField(default=1)
    date = models.DateField()
    slot = models.ForeignKey(SeqWeeklySlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    titre = models.CharField(max_length=160, blank=True)

    class Meta:
        unique_together = [('sequence', 'numero')]
        ordering = ['sequence', 'date', 'slot__day', 'slot__half_day']
        verbose_name = 'séance'
        verbose_name_plural = 'séances'

    def __str__(self):
        label = self.titre or f'S{self.semaine} — {self.date}'
        if self.slot_id:
            label += f' — {self.slot}'
        return label


class SeqAssignment(TimeStampedModel):
    MODE_CHOICES = [('impose', 'Parcours imposé'), ('libre', 'Parcours libre'), ('remediation', 'Remédiation'), ('pfmp', 'PFMP'), ('evaluation', 'Évaluation')]
    STATUS_CHOICES = [('planned', 'Prévu'), ('requested', 'Demandé'), ('validated', 'Validé'), ('done', 'Réalisé'), ('cancelled', 'Annulé'), ('postponed', 'Reporté')]
    session = models.ForeignKey(SeqSession, on_delete=models.CASCADE, related_name='assignments')
    group = models.ForeignKey(SeqStudentGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    eleve_individuel = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_assignments')
    tp = models.ForeignKey(TPV2, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_assignments')
    systeme = models.ForeignKey(SystemePedagogiqueRef, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_assignments')
    zone = models.ForeignKey(SeqZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    professeur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_assignments_prof')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='impose')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    commentaire = models.TextField(blank=True)
    tp_note = models.BooleanField(default=False)
    capacite_max = models.PositiveIntegerField(default=2)

    class Meta:
        ordering = ['session__date', 'session__numero', 'group__ordre', 'id']
        verbose_name = 'affectation de séance'
        verbose_name_plural = 'affectations de séance'

    def clean(self):
        if not self.group_id and not self.eleve_individuel_id:
            raise ValidationError('Affecter un groupe ou un élève individuel.')

    def __str__(self):
        target = self.group.nom if self.group_id else (self.eleve_individuel.full_name if self.eleve_individuel_id else 'Affectation')
        return f'{self.session} — {target}'


class SeqSystemBooking(TimeStampedModel):
    STATUS_CHOICES = [('pre_reserved', 'Pré-réservé'), ('reserved', 'Réservé'), ('used', 'Utilisé'), ('cancelled', 'Annulé'), ('conflict', 'Conflit')]
    SOURCE_CHOICES = [('sequence', 'Séquence'), ('system_manager', 'System Manager'), ('manual', 'Manuel')]
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='system_bookings')
    session = models.ForeignKey(SeqSession, on_delete=models.CASCADE, related_name='system_bookings')
    assignment = models.ForeignKey(SeqAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_bookings')
    systeme = models.ForeignKey(SystemePedagogiqueRef, on_delete=models.CASCADE, related_name='seq_bookings')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reserved')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='sequence')
    note = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ['session__date', 'systeme__code']
        verbose_name = 'réservation système séquence'
        verbose_name_plural = 'réservations systèmes séquence'

    def __str__(self):
        return f'{self.systeme.code} — {self.session}'


class SeqFreeChoiceRequest(TimeStampedModel):
    STATUS_CHOICES = [('draft', 'Brouillon élève'), ('submitted', 'Soumise'), ('validated', 'Validée'), ('rejected', 'Refusée'), ('cancelled', 'Annulée')]
    sequence = models.ForeignKey(SeqSequence, on_delete=models.CASCADE, related_name='free_requests')
    session = models.ForeignKey(SeqSession, on_delete=models.CASCADE, related_name='free_requests')
    eleve = models.ForeignKey(TpUser, on_delete=models.CASCADE, related_name='seq_free_requests')
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='seq_free_requests')
    systeme = models.ForeignKey(SystemePedagogiqueRef, on_delete=models.SET_NULL, null=True, blank=True, related_name='seq_free_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    commentaire_eleve = models.TextField(blank=True)
    commentaire_prof = models.TextField(blank=True)

    class Meta:
        unique_together = [('session', 'eleve')]
        ordering = ['-created_at']
        verbose_name = 'demande parcours libre'
        verbose_name_plural = 'demandes parcours libre'

    def __str__(self):
        return f'{self.eleve.full_name} — {self.tp.code}'
