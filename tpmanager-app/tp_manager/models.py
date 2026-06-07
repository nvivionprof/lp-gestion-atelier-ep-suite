from __future__ import annotations
import re
import unicodedata
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


def normalize_code(value, default='CODE', max_len=80):
    value = value or default
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_').upper()
    return (value or default)[:max_len]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class TpUser(TimeStampedModel):
    core_user_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    code = models.CharField(max_length=80, unique=True)
    username = models.CharField(max_length=120, unique=True)
    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    formation_code = models.CharField(max_length=40, blank=True)
    formation_name = models.CharField(max_length=180, blank=True)
    class_name = models.CharField(max_length=80, blank=True)
    group_name = models.CharField(max_length=80, blank=True)
    role_principal = models.CharField(max_length=80, blank=True, default='utilisateur')
    rights = models.TextField(blank=True)
    school_year = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)
    password_hash = models.TextField(blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'code']
        verbose_name = 'utilisateur TP Manager synchronisé'
        verbose_name_plural = 'utilisateurs TP Manager synchronisés'

    def __str__(self):
        label = f'{self.last_name} {self.first_name}'.strip() or self.username
        return f'{self.code} — {label}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username

    def set_password(self, raw_password: str):
        if raw_password:
            self.password_hash = make_password(str(raw_password))

    def check_password(self, raw_password: str) -> bool:
        return bool(self.password_hash and check_password(str(raw_password), self.password_hash))

    def rights_list(self):
        raw = self.rights or ''
        return [x.strip() for x in raw.replace(';', ',').split(',') if x.strip()]

    @property
    def is_prof_like(self):
        role = (self.role_principal or '').lower()
        rights = self.rights_list()
        return role in {'professeur', 'responsable', 'admin', 'admin_suite', 'magasinier'} or any(r in rights for r in ['TP_EDIT', 'TP_ADMIN', 'SYSTEM_EDIT', 'CORE_ADMIN'])

    @property
    def is_admin_like(self):
        role = (self.role_principal or '').lower()
        rights = self.rights_list()
        return role in {'admin', 'admin_suite', 'responsable'} or any(r in rights for r in ['TP_ADMIN', 'CORE_ADMIN'])


class Formation(TimeStampedModel):
    core_formation_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'formation'
        verbose_name_plural = 'formations'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'FORMATION', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class Niveau(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=160)
    ordre = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'code']
        verbose_name = 'niveau'
        verbose_name_plural = 'niveaux'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'NIVEAU', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class FormationNiveau(TimeStampedModel):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='niveaux_associes')
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='formations_associees')
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('formation', 'niveau')]
        ordering = ['formation__code', 'niveau__ordre']
        verbose_name = 'niveau autorisé par formation'
        verbose_name_plural = 'niveaux autorisés par formation'

    def __str__(self):
        return f'{self.formation.code} — {self.niveau.nom}'


class CodeNamedModel(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        abstract = True
        ordering = ['ordre', 'code']

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, self.__class__.__name__.upper(), 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class ZoneApprentissage(CodeNamedModel):
    class Meta(CodeNamedModel.Meta):
        verbose_name = 'zone d’apprentissage'
        verbose_name_plural = 'zones d’apprentissage'


class ThemeGeneral(CodeNamedModel):
    class Meta(CodeNamedModel.Meta):
        verbose_name = 'thème général'
        verbose_name_plural = 'thèmes généraux'


class ThemeSecondaire(CodeNamedModel):
    theme_general = models.ForeignKey(ThemeGeneral, on_delete=models.SET_NULL, null=True, blank=True, related_name='themes_secondaires')
    class Meta(CodeNamedModel.Meta):
        verbose_name = 'thème secondaire'
        verbose_name_plural = 'thèmes secondaires'


class TypeTP(CodeNamedModel):
    class Meta(CodeNamedModel.Meta):
        verbose_name = 'type de TP'
        verbose_name_plural = 'types de TP'


class SystemePedagogiqueRef(TimeStampedModel):
    system_manager_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    code = models.CharField(max_length=80, unique=True)
    designation = models.CharField(max_length=220)
    zone_code = models.CharField(max_length=40, blank=True)
    zone_nom = models.CharField(max_length=180, blank=True)
    statut = models.CharField(max_length=40, blank=True)
    actif = models.BooleanField(default=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['zone_code', 'code']
        verbose_name = 'système pédagogique synchronisé'
        verbose_name_plural = 'systèmes pédagogiques synchronisés'

    def __str__(self):
        return f'{self.code} — {self.designation}'


class Referentiel(TimeStampedModel):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='referentiels')
    nom = models.CharField(max_length=220)
    version = models.CharField(max_length=80, blank=True)
    source = models.CharField(max_length=220, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['formation__code', 'nom']
        verbose_name = 'référentiel'
        verbose_name_plural = 'référentiels'

    def __str__(self):
        return f'{self.formation.code} — {self.nom}'


class BlocCompetence(TimeStampedModel):
    referentiel = models.ForeignKey(Referentiel, on_delete=models.CASCADE, related_name='blocs')
    code = models.CharField(max_length=40)
    libelle = models.CharField(max_length=260)
    unite = models.CharField(max_length=80, blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('referentiel', 'code')]
        ordering = ['referentiel__formation__code', 'ordre', 'code']
        verbose_name = 'bloc de compétence'
        verbose_name_plural = 'blocs de compétences'

    def __str__(self):
        return f'{self.referentiel.formation.code} {self.code} — {self.libelle}'


class Competence(TimeStampedModel):
    bloc = models.ForeignKey(BlocCompetence, on_delete=models.CASCADE, related_name='competences')
    code = models.CharField(max_length=40)
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('bloc', 'code')]
        ordering = ['bloc__referentiel__formation__code', 'bloc__ordre', 'ordre', 'code']
        verbose_name = 'compétence'
        verbose_name_plural = 'compétences'

    @property
    def formation(self):
        return self.bloc.referentiel.formation

    def __str__(self):
        return f'{self.formation.code} {self.code} — {self.libelle}'


class SousCompetence(TimeStampedModel):
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='sous_competences')
    code = models.CharField(max_length=40)
    libelle = models.CharField(max_length=320)
    criteres = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('competence', 'code')]
        ordering = ['competence__code', 'ordre']
        verbose_name = 'sous-compétence'
        verbose_name_plural = 'sous-compétences'

    def __str__(self):
        return f'{self.competence.code}-{self.code} — {self.libelle}'


class ActiviteReferentiel(TimeStampedModel):
    referentiel = models.ForeignKey(Referentiel, on_delete=models.CASCADE, related_name='activites')
    code = models.CharField(max_length=40)
    libelle = models.CharField(max_length=320)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('referentiel', 'code')]
        ordering = ['referentiel__formation__code', 'ordre', 'code']
        verbose_name = 'activité du référentiel'
        verbose_name_plural = 'activités du référentiel'

    def __str__(self):
        return f'{self.referentiel.formation.code} {self.code} — {self.libelle}'


class TacheReferentiel(TimeStampedModel):
    activite = models.ForeignKey(ActiviteReferentiel, on_delete=models.CASCADE, related_name='taches')
    code = models.CharField(max_length=40)
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('activite', 'code')]
        ordering = ['activite__code', 'ordre']
        verbose_name = 'tâche du référentiel'
        verbose_name_plural = 'tâches du référentiel'

    def __str__(self):
        return f'{self.activite.code}-{self.code} — {self.libelle}'


class TP(TimeStampedModel):
    STATUT_CHOICES = [('brouillon', 'Brouillon'), ('brouillon_eleve', 'Brouillon élève'), ('relecture', 'En relecture'), ('valide', 'Validé'), ('publie', 'Publié'), ('archive', 'Archivé')]
    DIFFICULTE_CHOICES = [('decouverte', 'Découverte'), ('application', 'Application'), ('approfondissement', 'Approfondissement'), ('autonomie', 'Autonomie'), ('evaluation', 'Évaluation'), ('remediation', 'Remédiation')]
    code = models.CharField(max_length=120, unique=True, blank=True)
    titre = models.CharField(max_length=260)
    resume_apprentissages = models.TextField(blank=True)
    temps_estime_minutes = models.PositiveIntegerField(default=120)
    zone_apprentissage = models.ForeignKey(ZoneApprentissage, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps')
    theme_general = models.ForeignKey(ThemeGeneral, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps')
    theme_secondaire = models.ForeignKey(ThemeSecondaire, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps')
    formation_principale = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps_principaux')
    type_tp = models.ForeignKey(TypeTP, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps')
    difficulte = models.CharField(max_length=40, choices=DIFFICULTE_CHOICES, default='application')
    statut = models.CharField(max_length=40, choices=STATUT_CHOICES, default='brouillon')
    version = models.CharField(max_length=40, default='V1')
    auteur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps_crees')
    commentaire_interne = models.TextField(blank=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'TP modèle'
        verbose_name_plural = 'TP modèles'

    def save(self, *args, **kwargs):
        if not self.code:
            zone = self.zone_apprentissage.code if self.zone_apprentissage else 'ZONE'
            formation = self.formation_principale.code if self.formation_principale else 'FORM'
            theme = self.theme_secondaire.code if self.theme_secondaire else (self.theme_general.code if self.theme_general else 'THEME')
            prefix = f'{normalize_code(zone, "ZONE", 40)}-{normalize_code(formation, "FORM", 40)}-{normalize_code(theme, "THEME", 40)}'
            existing = TP.objects.exclude(pk=self.pk).filter(code__startswith=prefix + '-').count()
            self.code = f'{prefix}-{existing + 1:03d}'
            while TP.objects.exclude(pk=self.pk).filter(code=self.code).exists():
                existing += 1
                self.code = f'{prefix}-{existing + 1:03d}'
        else:
            self.code = normalize_code(self.code, 'TP', 120).replace('_', '-')
        super().save(*args, **kwargs)


    @property
    def duree_heures_affichage(self):
        heures = (self.duree_minutes or 0) / 60
        if heures.is_integer():
            return f'{int(heures)} h'
        return f'{heures:.2f}'.replace('.', ',') + ' h'

    def __str__(self):
        return f'{self.code} — {self.titre}'

    def get_absolute_url(self):
        return reverse('tp_detail', args=[self.pk])

    @property
    def pdf_documents(self):
        return self.documents.filter(type_document='pdf_eleve', actif=True)

    @property
    def docx_documents(self):
        return self.documents.filter(type_document='docx_prof', actif=True)


class TPFormationNiveau(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='formations_niveaux')
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='tp_links')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='tp_links')

    class Meta:
        unique_together = [('tp', 'formation', 'niveau')]
        ordering = ['formation__code', 'niveau__ordre']
        verbose_name = 'formation et niveau du TP'
        verbose_name_plural = 'formations et niveaux des TP'

    def __str__(self):
        return f'{self.tp.code} — {self.formation.code} {self.niveau.code if self.niveau else ""}'


class TPSysteme(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='systemes')
    systeme = models.ForeignKey(SystemePedagogiqueRef, on_delete=models.CASCADE, related_name='tp_links')
    obligatoire = models.BooleanField(default=True)
    commentaire = models.CharField(max_length=220, blank=True)

    class Meta:
        unique_together = [('tp', 'systeme')]
        ordering = ['systeme__code']
        verbose_name = 'système nécessaire au TP'
        verbose_name_plural = 'systèmes nécessaires aux TP'

    def __str__(self):
        return f'{self.tp.code} — {self.systeme.code}'


class TPCompetence(TimeStampedModel):
    TYPE_CHOICES = [('mobilisee', 'Mobilisée'), ('travaillee', 'Travaillée'), ('dominante', 'Dominante'), ('evaluee', 'Évaluée'), ('certificative', 'Certificative')]
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='competences')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='tp_links')
    type_lien = models.CharField(max_length=30, choices=TYPE_CHOICES, default='travaillee')
    niveau_travail = models.CharField(max_length=50, blank=True, help_text='Découverte, entraînement, consolidation, évaluation...')
    niveau_evaluation = models.CharField(max_length=50, blank=True, help_text='Formatif, certificatif, non évalué...')
    ponderation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('tp', 'competence', 'type_lien')]
        ordering = ['competence__bloc__ordre', 'competence__ordre']
        verbose_name = 'compétence liée au TP'
        verbose_name_plural = 'compétences liées aux TP'

    def __str__(self):
        return f'{self.tp.code} — {self.competence.code} ({self.type_lien})'


class TPPrerequis(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='prerequis')
    prerequis = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='debloque_tps')
    obligatoire = models.BooleanField(default=True)

    class Meta:
        unique_together = [('tp', 'prerequis')]
        verbose_name = 'prérequis de TP'
        verbose_name_plural = 'prérequis de TP'

    def clean(self):
        if self.tp_id and self.prerequis_id and self.tp_id == self.prerequis_id:
            raise ValidationError('Un TP ne peut pas être prérequis de lui-même.')

    def __str__(self):
        return f'{self.prerequis.code} → {self.tp.code}'


class TPSuivant(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='suivants')
    suivant = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='precedents_conseilles')
    commentaire = models.CharField(max_length=220, blank=True)

    class Meta:
        unique_together = [('tp', 'suivant')]
        verbose_name = 'TP suivant conseillé'
        verbose_name_plural = 'TP suivants conseillés'


class TPDocument(TimeStampedModel):
    TYPE_CHOICES = [
        ('pdf_eleve', 'PDF élève'), ('docx_prof', 'DOCX professeur'), ('corrige', 'Corrigé'),
        ('annexe_eleve', 'Annexe élève'), ('annexe_prof', 'Annexe professeur'), ('ressource', 'Ressource'),
    ]
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=30, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=220)
    fichier = models.FileField(upload_to='tp/documents/')
    version = models.CharField(max_length=40, blank=True)
    visible_eleve = models.BooleanField(default=False)
    visible_prof = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_tp')

    class Meta:
        ordering = ['tp__code', 'type_document', 'titre']
        verbose_name = 'document TP'
        verbose_name_plural = 'documents TP'

    def save(self, *args, **kwargs):
        if self.type_document in {'pdf_eleve', 'annexe_eleve'}:
            self.visible_eleve = True
        if self.type_document in {'docx_prof', 'corrige', 'annexe_prof'}:
            self.visible_prof = True
            self.visible_eleve = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.tp.code} — {self.titre}'


class SerieTP(TimeStampedModel):
    titre = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='series_tp')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='series_tp')
    auteur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='series_tp')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['titre']
        verbose_name = 'série de TP'
        verbose_name_plural = 'séries de TP'

    def __str__(self):
        return self.titre


class SerieTPItem(TimeStampedModel):
    serie = models.ForeignKey(SerieTP, on_delete=models.CASCADE, related_name='items')
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='series_items')
    ordre = models.PositiveIntegerField(default=1)
    obligatoire = models.BooleanField(default=True)

    class Meta:
        unique_together = [('serie', 'tp')]
        ordering = ['serie__titre', 'ordre']
        verbose_name = 'TP dans une série'
        verbose_name_plural = 'TP dans les séries'


class SequencePedagogique(TimeStampedModel):
    STATUT_CHOICES = [('brouillon', 'Brouillon'), ('active', 'Active'), ('terminee', 'Terminée'), ('archive', 'Archivée')]
    titre = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    professeur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='sequences')
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=40, choices=STATUT_CHOICES, default='brouillon')
    eleves = models.ManyToManyField(TpUser, blank=True, related_name='sequences_assignees')

    class Meta:
        ordering = ['-date_debut', 'titre']
        verbose_name = 'séquence pédagogique'
        verbose_name_plural = 'séquences pédagogiques'

    def __str__(self):
        return self.titre


class SequenceTP(TimeStampedModel):
    sequence = models.ForeignKey(SequencePedagogique, on_delete=models.CASCADE, related_name='items')
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='sequence_items')
    ordre = models.PositiveIntegerField(default=1)
    date_prevue = models.DateField(null=True, blank=True)
    temps_prevu_minutes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [('sequence', 'tp')]
        ordering = ['sequence__titre', 'ordre']
        verbose_name = 'TP dans une séquence'
        verbose_name_plural = 'TP dans les séquences'


class ParcoursEleveTP(TimeStampedModel):
    STATUT_CHOICES = [('a_faire', 'À faire'), ('en_cours', 'En cours'), ('realise', 'Réalisé'), ('a_corriger', 'À corriger'), ('valide', 'Validé'), ('a_refaire', 'À refaire'), ('bloque', 'Bloqué par prérequis'), ('archive', 'Archivé')]
    DIFFICULTE_CHOICES = [('non_renseignee', 'Non renseignée'), ('facile', 'Facile'), ('moyen', 'Moyen'), ('difficile', 'Difficile')]
    eleve = models.ForeignKey(TpUser, on_delete=models.CASCADE, related_name='parcours_tp')
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='parcours_eleves')
    sequence = models.ForeignKey(SequencePedagogique, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcours_eleves')
    statut = models.CharField(max_length=40, choices=STATUT_CHOICES, default='a_faire')
    difficulte = models.CharField(max_length=40, choices=DIFFICULTE_CHOICES, default='non_renseignee')
    souhaite_refaire = models.BooleanField(default=False)
    commentaire_eleve = models.TextField(blank=True)
    commentaire_prof = models.TextField(blank=True)
    systeme_utilise = models.ForeignKey(SystemePedagogiqueRef, on_delete=models.SET_NULL, null=True, blank=True, related_name='parcours_tp')
    date_debut = models.DateTimeField(null=True, blank=True)
    date_realisation = models.DateTimeField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    validateur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='validations_tp')

    class Meta:
        unique_together = [('eleve', 'tp', 'sequence')]
        ordering = ['-updated_at']
        verbose_name = 'parcours élève TP'
        verbose_name_plural = 'parcours élèves TP'

    def __str__(self):
        return f'{self.eleve.full_name} — {self.tp.code}'

    def prerequis_valides(self):
        required = self.tp.prerequis.filter(obligatoire=True).select_related('prerequis')
        missing = []
        for link in required:
            ok = ParcoursEleveTP.objects.filter(eleve=self.eleve, tp=link.prerequis, statut='valide').exists()
            if not ok:
                missing.append(link.prerequis)
        return missing


class TraceEleveTP(TimeStampedModel):
    TYPE_CHOICES = [('photo', 'Photo'), ('texte', 'Texte'), ('fichier', 'Fichier'), ('reponse', 'Réponse'), ('commentaire', 'Commentaire')]
    parcours = models.ForeignKey(ParcoursEleveTP, on_delete=models.CASCADE, related_name='traces')
    type_trace = models.CharField(max_length=30, choices=TYPE_CHOICES, default='texte')
    titre = models.CharField(max_length=180, blank=True)
    contenu_texte = models.TextField(blank=True)
    fichier = models.FileField(upload_to='tp/traces/', blank=True)
    visible_prof = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'trace élève TP'
        verbose_name_plural = 'traces élèves TP'

    def __str__(self):
        return f'{self.parcours} — {self.get_type_trace_display()}'


class EvaluationCompetenceTP(TimeStampedModel):
    NIVEAU_CHOICES = [(0, 'Non observée'), (1, 'Insuffisant'), (2, 'En cours'), (3, 'Maîtrisé'), (4, 'Très bien maîtrisé')]
    parcours = models.ForeignKey(ParcoursEleveTP, on_delete=models.CASCADE, related_name='evaluations')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='evaluations_tp')
    niveau = models.PositiveSmallIntegerField(choices=NIVEAU_CHOICES, default=0)
    commentaire_prof = models.TextField(blank=True)
    trace_associee = models.ForeignKey(TraceEleveTP, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations')
    evaluateur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='evaluations_realisees')
    date_evaluation = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [('parcours', 'competence')]
        ordering = ['competence__code']
        verbose_name = 'évaluation de compétence TP'
        verbose_name_plural = 'évaluations de compétences TP'

    def __str__(self):
        return f'{self.parcours} — {self.competence.code}'


# -----------------------------------------------------------------------------
# Extension V2.7.1 — référentiels officiels, savoirs, critères et contribution
# élève encadrée. Les appellations officielles sont conservées par diplôme, mais
# rangées dans une structure homogène.
# -----------------------------------------------------------------------------
class PoleActivite(TimeStampedModel):
    referentiel = models.ForeignKey(Referentiel, on_delete=models.CASCADE, related_name='poles_activites')
    code = models.CharField(max_length=50, blank=True)
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('referentiel', 'code')]
        ordering = ['referentiel__formation__code', 'ordre', 'code']
        verbose_name = "pôle d'activité officiel"
        verbose_name_plural = "pôles d'activités officiels"

    def __str__(self):
        return f'{self.referentiel.formation.code} {self.code} — {self.libelle}'.strip()


class UniteCertificative(TimeStampedModel):
    referentiel = models.ForeignKey(Referentiel, on_delete=models.CASCADE, related_name='unites_certificatives')
    code = models.CharField(max_length=50)
    libelle = models.CharField(max_length=320)
    coefficient = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    modalite_evaluation = models.TextField(blank=True)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('referentiel', 'code')]
        ordering = ['referentiel__formation__code', 'ordre', 'code']
        verbose_name = 'unité certificative officielle'
        verbose_name_plural = 'unités certificatives officielles'

    def __str__(self):
        return f'{self.referentiel.formation.code} {self.code} — {self.libelle}'


class BlocUnite(TimeStampedModel):
    bloc = models.ForeignKey(BlocCompetence, on_delete=models.CASCADE, related_name='unites_links')
    unite = models.ForeignKey(UniteCertificative, on_delete=models.CASCADE, related_name='blocs_links')
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('bloc', 'unite')]
        verbose_name = 'liaison bloc / unité'
        verbose_name_plural = 'liaisons blocs / unités'


class SavoirAssocie(TimeStampedModel):
    referentiel = models.ForeignKey(Referentiel, on_delete=models.CASCADE, related_name='savoirs_associes')
    code = models.CharField(max_length=80, blank=True)
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    famille = models.CharField(max_length=120, blank=True)
    niveau_taxonomique = models.CharField(max_length=50, blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('referentiel', 'code')]
        ordering = ['referentiel__formation__code', 'famille', 'ordre', 'code']
        verbose_name = 'savoir / connaissance associé officiel'
        verbose_name_plural = 'savoirs / connaissances associés officiels'

    def __str__(self):
        return f'{self.referentiel.formation.code} {self.code} — {self.libelle}'.strip()


class CompetenceSavoir(TimeStampedModel):
    NIVEAU_CHOICES = [('decouverte', 'Découverte'), ('application', 'Application'), ('maitrise', 'Maîtrise'), ('expertise', 'Expertise')]
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='savoirs_links')
    savoir = models.ForeignKey(SavoirAssocie, on_delete=models.CASCADE, related_name='competences_links')
    niveau_mobilisation = models.CharField(max_length=40, choices=NIVEAU_CHOICES, blank=True)
    obligatoire = models.BooleanField(default=False)

    class Meta:
        unique_together = [('competence', 'savoir')]
        verbose_name = 'liaison compétence / savoir'
        verbose_name_plural = 'liaisons compétences / savoirs'


class CritereEvaluation(TimeStampedModel):
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='criteres_evaluation')
    code = models.CharField(max_length=80, blank=True)
    libelle = models.TextField()
    description = models.TextField(blank=True)
    niveau_exigence = models.CharField(max_length=80, blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['competence__code', 'ordre', 'code']
        verbose_name = "critère d'évaluation officiel"
        verbose_name_plural = "critères d'évaluation officiels"

    def __str__(self):
        return f'{self.competence.code} — {self.libelle[:80]}'


class IndicateurEvaluation(TimeStampedModel):
    critere = models.ForeignKey(CritereEvaluation, on_delete=models.CASCADE, related_name='indicateurs')
    libelle = models.TextField()
    observable = models.BooleanField(default=True)
    ponderation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['critere__competence__code', 'critere__ordre', 'ordre']
        verbose_name = "indicateur d'évaluation officiel"
        verbose_name_plural = "indicateurs d'évaluation officiels"


class TacheCompetence(TimeStampedModel):
    NIVEAU_CHOICES = [('mobilisee', 'Mobilisée'), ('travaillee', 'Travaillée'), ('evaluable', 'Évaluable')]
    tache = models.ForeignKey(TacheReferentiel, on_delete=models.CASCADE, related_name='competences_links')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='taches_links')
    niveau_mobilisation = models.CharField(max_length=40, choices=NIVEAU_CHOICES, default='mobilisee')
    evaluable_dans_tache = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('tache', 'competence')]
        verbose_name = 'liaison tâche / compétence'
        verbose_name_plural = 'liaisons tâches / compétences'


class TPTache(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='taches_referentiel')
    tache = models.ForeignKey(TacheReferentiel, on_delete=models.CASCADE, related_name='tp_links')
    ordre_execution = models.PositiveIntegerField(default=100)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('tp', 'tache')]
        ordering = ['ordre_execution', 'tache__code']
        verbose_name = 'tâche officielle liée au TP'
        verbose_name_plural = 'tâches officielles liées aux TP'


class TPSavoir(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='savoirs_associes')
    savoir = models.ForeignKey(SavoirAssocie, on_delete=models.CASCADE, related_name='tp_links')
    niveau_mobilisation = models.CharField(max_length=50, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('tp', 'savoir')]
        verbose_name = 'savoir associé au TP'
        verbose_name_plural = 'savoirs associés aux TP'


class TPCritere(TimeStampedModel):
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='criteres')
    critere = models.ForeignKey(CritereEvaluation, on_delete=models.CASCADE, related_name='tp_links')
    indicateur = models.ForeignKey(IndicateurEvaluation, on_delete=models.SET_NULL, null=True, blank=True, related_name='tp_links')
    bareme = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    obligatoire = models.BooleanField(default=False)
    commentaire = models.TextField(blank=True)

    class Meta:
        verbose_name = "critère d'évaluation lié au TP"
        verbose_name_plural = "critères d'évaluation liés aux TP"


class TPContributionPermission(TimeStampedModel):
    """Droit temporaire donné par un professeur à un élève pour contribuer à un brouillon de TP."""
    eleve = models.ForeignKey(TpUser, on_delete=models.CASCADE, related_name='permissions_contribution_tp')
    tp = models.ForeignKey(TP, on_delete=models.CASCADE, related_name='contributeurs_temporaires', null=True, blank=True)
    accordee_par = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='permissions_contribution_donnees')
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(null=True, blank=True)
    peut_creer = models.BooleanField(default=True)
    peut_modifier = models.BooleanField(default=True)
    peut_ajouter_documents = models.BooleanField(default=True)
    commentaire = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'droit temporaire de contribution TP élève'
        verbose_name_plural = 'droits temporaires de contribution TP élèves'

    def is_valid_now(self):
        now = timezone.now()
        return self.actif and (not self.date_debut or self.date_debut <= now) and (not self.date_fin or self.date_fin >= now)

    def __str__(self):
        target = self.tp.code if self.tp_id else 'création libre encadrée'
        return f'{self.eleve.full_name} — {target}'


# ---------------------------------------------------------------------------
# TP MANAGER V2 — modèle refondu, non destructif
# ---------------------------------------------------------------------------
# Ces modèles sont ajoutés en parallèle de l'ancien TP Manager afin de conserver
# les données existantes et l'identité visuelle, tout en repartant sur une base
# fonctionnelle conforme au cahier des charges V0.2.

class BacDiplome(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    intitule = models.CharField(max_length=260)
    niveau = models.CharField(max_length=20, default='4')
    version_ref = models.CharField(max_length=220, blank=True)
    source_document = models.CharField(max_length=260, blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    locked_official = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'V2 diplôme Bac Pro'
        verbose_name_plural = 'V2 diplômes Bac Pro'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.intitule, 'BAC', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.intitule}'


class BacPole(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='poles')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=320)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'ordre', 'code']
        verbose_name = 'V2 pôle officiel'
        verbose_name_plural = 'V2 pôles officiels'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'


class BacUnite(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='unites')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=320)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'ordre', 'code']
        verbose_name = 'V2 unité officielle'
        verbose_name_plural = 'V2 unités officielles'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'


class BacCompetence(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='competences_officielles')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=420)
    selectable_bac = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'code']
        verbose_name = 'V2 compétence officielle'
        verbose_name_plural = 'V2 compétences officielles'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'



class BacActivite(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='activites_officielles')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=360)
    description = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'ordre', 'code']
        verbose_name = 'V2 activité officielle'
        verbose_name_plural = 'V2 activités officielles'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'


class BacTache(TimeStampedModel):
    AUTONOMIE_CHOICES = [('non_precise', 'Non précisée'), ('partielle', 'Partielle'), ('totale', 'Totale'), ('mixte', 'Partielle ou totale selon contexte')]
    activite = models.ForeignKey(BacActivite, on_delete=models.CASCADE, related_name='taches')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=520)
    autonomie = models.CharField(max_length=30, choices=AUTONOMIE_CHOICES, default='non_precise')
    responsabilite_personnes = models.BooleanField(default=False)
    responsabilite_moyens = models.BooleanField(default=False)
    responsabilite_resultat = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    moyens_ressources = models.TextField(blank=True)
    resultats_attendus = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('activite', 'code')]
        ordering = ['activite__diplome__code', 'activite__ordre', 'ordre', 'code']
        verbose_name = 'V2 tâche officielle'
        verbose_name_plural = 'V2 tâches officielles'

    @property
    def responsabilite_resume(self):
        values = []
        if self.responsabilite_personnes:
            values.append('personnes')
        if self.responsabilite_moyens:
            values.append('moyens')
        if self.responsabilite_resultat:
            values.append('résultat')
        return ', '.join(values) or 'non précisée'

    def __str__(self):
        return f'{self.activite.diplome.code} {self.code} — {self.libelle_officiel}'


class BacTacheCompetence(TimeStampedModel):
    tache = models.ForeignKey(BacTache, on_delete=models.CASCADE, related_name='competences_liees')
    competence = models.ForeignKey(BacCompetence, on_delete=models.CASCADE, related_name='taches_liees_v2')
    poids = models.PositiveSmallIntegerField(null=True, blank=True, help_text='1 = secondaire, 2 = essentielle selon le tableau officiel quand disponible.')
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('tache', 'competence')]
        ordering = ['tache__activite__ordre', 'tache__ordre', 'competence__code']
        verbose_name = 'V2 lien tâche-compétence officiel'
        verbose_name_plural = 'V2 liens tâche-compétence officiels'

    def __str__(self):
        return f'{self.tache.code} → {self.competence.code} ({self.poids or "—"})'


class BacCompetenceCritere(TimeStampedModel):
    competence = models.ForeignKey(BacCompetence, on_delete=models.CASCADE, related_name='criteres_officiels')
    code = models.CharField(max_length=60)
    libelle_officiel = models.CharField(max_length=520)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('competence', 'code')]
        ordering = ['competence__diplome__code', 'competence__code', 'ordre', 'code']
        verbose_name = 'V2 critère officiel de compétence'
        verbose_name_plural = 'V2 critères officiels de compétence'

    def __str__(self):
        return f'{self.competence.code} — {self.libelle_officiel}'


class BacAttitudeProfessionnelle(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='attitudes_professionnelles')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=320)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'ordre', 'code']
        verbose_name = 'V2 attitude professionnelle officielle'
        verbose_name_plural = 'V2 attitudes professionnelles officielles'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'


class BacCompetenceAttitude(TimeStampedModel):
    competence = models.ForeignKey(BacCompetence, on_delete=models.CASCADE, related_name='attitudes_liees')
    attitude = models.ForeignKey(BacAttitudeProfessionnelle, on_delete=models.CASCADE, related_name='competences_liees')

    class Meta:
        unique_together = [('competence', 'attitude')]
        ordering = ['competence__code', 'attitude__code']
        verbose_name = 'V2 lien compétence-attitude officielle'
        verbose_name_plural = 'V2 liens compétence-attitude officielles'

    def __str__(self):
        return f'{self.competence.code} → {self.attitude.code}'


class BacBloc(TimeStampedModel):
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='blocs_officiels')
    unite = models.ForeignKey(BacUnite, on_delete=models.SET_NULL, null=True, blank=True, related_name='blocs')
    code = models.CharField(max_length=40)
    libelle_officiel = models.CharField(max_length=360)
    ordre = models.PositiveIntegerField(default=100)
    locked_official = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'ordre', 'code']
        verbose_name = 'V2 bloc officiel'
        verbose_name_plural = 'V2 blocs officiels'

    def __str__(self):
        return f'{self.diplome.code} {self.code} — {self.libelle_officiel}'


class BacBlocCompetence(TimeStampedModel):
    bloc = models.ForeignKey(BacBloc, on_delete=models.CASCADE, related_name='competences_liees')
    competence = models.ForeignKey(BacCompetence, on_delete=models.CASCADE, related_name='blocs_lies')
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('bloc', 'competence')]
        ordering = ['bloc__diplome__code', 'bloc__ordre', 'ordre']
        verbose_name = 'V2 compétence dans bloc officiel'
        verbose_name_plural = 'V2 compétences dans blocs officiels'

    def __str__(self):
        return f'{self.bloc} ← {self.competence.code}'


class BacChampTP(TimeStampedModel):
    TYPE_CHOICES = [('text', 'Texte'), ('textarea', 'Texte long'), ('choice', 'Liste'), ('number', 'Nombre'), ('boolean', 'Oui / non')]
    PHASE_CHOICES = [('general', 'Création'), ('pedagogie', 'Pédagogie'), ('evaluation', 'Évaluation'), ('ressources', 'Ressources')]
    diplome = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='champs_tp')
    code = models.CharField(max_length=80)
    libelle = models.CharField(max_length=220)
    type_champ = models.CharField(max_length=30, choices=TYPE_CHOICES, default='text')
    phase = models.CharField(max_length=30, choices=PHASE_CHOICES, default='general')
    obligatoire = models.BooleanField(default=False)
    aide = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)
    actif = models.BooleanField(default=True)

    class Meta:
        unique_together = [('diplome', 'code')]
        ordering = ['diplome__code', 'phase', 'ordre', 'code']
        verbose_name = 'V2 champ dynamique par diplôme'
        verbose_name_plural = 'V2 champs dynamiques par diplôme'

    def __str__(self):
        return f'{self.diplome.code} — {self.libelle}'


class BacChampTPOption(TimeStampedModel):
    champ = models.ForeignKey(BacChampTP, on_delete=models.CASCADE, related_name='options')
    valeur = models.CharField(max_length=120)
    libelle = models.CharField(max_length=220)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('champ', 'valeur')]
        ordering = ['champ__ordre', 'ordre']
        verbose_name = 'V2 option champ dynamique'
        verbose_name_plural = 'V2 options champs dynamiques'

    def __str__(self):
        return f'{self.champ.code} — {self.libelle}'


class CompetencePivot(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True)
    libelle = models.CharField(max_length=220)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'V2 compétence pivot interne'
        verbose_name_plural = 'V2 compétences pivot internes'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.libelle, 'PIVOT', 80)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.libelle}'


class TPV2(TimeStampedModel):
    STATUT_CHOICES = [('brouillon', 'Brouillon'), ('relecture', 'En relecture'), ('valide', 'Validé'), ('publie', 'Publié'), ('archive', 'Archivé')]
    USAGE_CHOICES = [('decouverte', 'Découverte'), ('entrainement', 'Entraînement'), ('consolidation', 'Consolidation'), ('evaluation', 'Évaluation'), ('projet', 'Projet'), ('remediation', 'Remédiation')]
    TYPE_ACTIVITE_CHOICES = [('TP', 'TP'), ('TD', 'TD'), ('PROJET', 'Projet'), ('EVAL', 'Évaluation'), ('RECH', 'Recherche'), ('SAE', 'Situation / SAE')]
    code = models.CharField(max_length=120, unique=True, blank=True)
    titre = models.CharField(max_length=260)
    type_activite = models.CharField(max_length=20, choices=TYPE_ACTIVITE_CHOICES, default='TP', help_text='Utilisé pour la numérotation automatique.')
    diplome = models.ForeignKey(BacDiplome, on_delete=models.PROTECT, related_name='tps_v2')
    niveau_classe = models.CharField(max_length=80, blank=True, help_text='Seconde, Première, Terminale, groupe spécifique...')
    domaine_principal = models.CharField(max_length=120, blank=True, help_text='Thème principal utilisé dans le repère automatique : domotique, PAC, réseau, câblage...')
    sous_theme = models.CharField(max_length=120, blank=True, help_text='Sous-thème libre ou issu de la liste du diplôme. Exemple : KNX, GTB, PAC air/eau, adressage IP...')
    usage_pedagogique = models.CharField(max_length=40, choices=USAGE_CHOICES, default='entrainement')
    duree_minutes = models.PositiveIntegerField(default=120)
    resume_eleve = models.TextField(blank=True, help_text='Formulation simple, lisible par l’élève.')
    objectifs_prof = models.TextField(blank=True, help_text='Description du contexte / mise en situation professionnelle.')
    problematique_metier = models.TextField(blank=True, help_text='Problématique liée au métier / missions à réaliser.')
    mots_cles = models.CharField(max_length=360, blank=True, help_text='Recherche élève/parcours : domotique, PAC, diagnostic, réseau...')
    bareme_total = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Barème général indicatif du TP, renseigné dans la page Affecter / barème.')
    competence_pivot = models.ForeignKey(CompetencePivot, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps')
    statut = models.CharField(max_length=40, choices=STATUT_CHOICES, default='brouillon')
    version = models.CharField(max_length=40, default='V1')
    auteur = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='tps_v2_crees')
    source_tp = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='copies_transferees')
    commentaire_interne = models.TextField(blank=True)

    class Meta:
        ordering = ['diplome__code', 'code']
        verbose_name = 'V2 TP'
        verbose_name_plural = 'V2 TP'

    FORMATION_NUMBERING_ALIASES = {
        'CIEL': 'CIEL',
        'MELEC': 'MELEC',
        'MFER': 'MFER',
        'BTS_FED': 'FED',
        'BTS_ELEC': 'STEL',
    }

    def formation_repere(self):
        if not self.diplome_id:
            return 'FORMATION'
        return self.FORMATION_NUMBERING_ALIASES.get(self.diplome.code, normalize_code(self.diplome.code, 'FORMATION', 16))

    @staticmethod
    def short_theme_code(value):
        value = value or 'DOMAINE'
        # Format attendu : RES - Réseau. Si le préfixe existe, il pilote la numérotation.
        prefix = str(value).split('-', 1)[0].strip() if '-' in str(value) else str(value).strip()
        prefix = unicodedata.normalize('NFKD', prefix).encode('ascii', 'ignore').decode('ascii')
        prefix = re.sub(r'[^A-Za-z0-9]+', '', prefix).upper()
        if not prefix:
            prefix = normalize_code(value, 'DOMAINE', 12).replace('_', '')
        return (prefix[:3] or 'DOM').ljust(3, 'X')

    def auto_code_prefix(self):
        """Repère TP : FORMATION-THEME-SOUSTHEME.

        Le titre reste un champ séparé. L’interface affiche le nom complet sous la
        forme FORMATION-THEME-SOUSTHEME-001 — Titre.
        """
        formation_code = self.formation_repere()
        theme_code = self.short_theme_code(self.domaine_principal or (self.diplome.code if self.diplome_id else 'THEME'))
        sous_theme_code = self.short_theme_code(self.sous_theme or self.domaine_principal or 'SOU')
        return f'{formation_code}-{theme_code}-{sous_theme_code}'

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = self.auto_code_prefix()
            count = TPV2.objects.exclude(pk=self.pk).filter(code__startswith=prefix + '-').count() + 1
            self.code = f'{prefix}-{count:03d}'
            while TPV2.objects.exclude(pk=self.pk).filter(code=self.code).exists():
                count += 1
                self.code = f'{prefix}-{count:03d}'
        else:
            self.code = normalize_code(self.code, 'TPV2', 120).replace('_', '-')
        super().save(*args, **kwargs)


    @property
    def duree_heures_affichage(self):
        heures = (self.duree_minutes or 0) / 60
        if heures.is_integer():
            return f'{int(heures)} h'
        return f'{heures:.2f}'.replace('.', ',') + ' h'

    def __str__(self):
        return f'{self.code} — {self.titre}'

    def get_absolute_url(self):
        return reverse('tp_detail', args=[self.pk])


class TPV2ChampValeur(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='valeurs_champs')
    champ = models.ForeignKey(BacChampTP, on_delete=models.PROTECT, related_name='valeurs_tp')
    valeur = models.TextField(blank=True)

    class Meta:
        unique_together = [('tp', 'champ')]
        ordering = ['champ__phase', 'champ__ordre']
        verbose_name = 'V2 valeur champ dynamique TP'
        verbose_name_plural = 'V2 valeurs champs dynamiques TP'

    def __str__(self):
        return f'{self.tp.code} — {self.champ.libelle}'


class TPV2CompetenceOfficielle(TimeStampedModel):
    TYPE_CHOICES = [
        ('mobilisee', 'Mobilisée — nécessaire au TP mais pas travaillée prioritairement'),
        ('travaillee', 'Travaillée — compétence travaillée dans le TP'),
        ('evaluee', 'Évaluée — compétence évaluée dans le TP'),
        ('certification', 'Certification — compétence support d’une évaluation certificative'),
    ]
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='competences_officielles')
    competence = models.ForeignKey(BacCompetence, on_delete=models.PROTECT, related_name='tps_v2')
    type_lien = models.CharField(max_length=30, choices=TYPE_CHOICES, default='travaillee')
    niveau_evaluation = models.CharField(max_length=80, blank=True, help_text='Découverte, entraînement, évaluation formative, certificative...')
    bareme = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Points affectés à cette compétence pour la notation automatique.')
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Poids indicatif en pourcentage pour l’évaluation.')
    commentaire = models.TextField(blank=True)

    class Meta:
        unique_together = [('tp', 'competence', 'type_lien')]
        ordering = ['competence__code']
        verbose_name = 'V2 compétence officielle associée'
        verbose_name_plural = 'V2 compétences officielles associées'

    def clean(self):
        if self.tp_id and self.competence_id and self.tp.diplome_id != self.competence.diplome_id:
            raise ValidationError('Cette compétence n’appartient pas au diplôme du TP.')

    def __str__(self):
        return f'{self.tp.code} — {self.competence.code}'



class TPV2ActiviteOfficielle(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='activites_officielles')
    activite = models.ForeignKey(BacActivite, on_delete=models.PROTECT, related_name='tps_v2')

    class Meta:
        unique_together = [('tp', 'activite')]
        ordering = ['activite__ordre']
        verbose_name = 'V2 activité officielle associée au TP'
        verbose_name_plural = 'V2 activités officielles associées au TP'

    def clean(self):
        if self.tp_id and self.activite_id and self.tp.diplome_id != self.activite.diplome_id:
            raise ValidationError('Cette activité n’appartient pas au diplôme du TP.')


class TPV2TacheOfficielle(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='taches_officielles')
    tache = models.ForeignKey(BacTache, on_delete=models.PROTECT, related_name='tps_v2')

    class Meta:
        unique_together = [('tp', 'tache')]
        ordering = ['tache__activite__ordre', 'tache__ordre']
        verbose_name = 'V2 tâche officielle associée au TP'
        verbose_name_plural = 'V2 tâches officielles associées au TP'

    def clean(self):
        if self.tp_id and self.tache_id and self.tp.diplome_id != self.tache.activite.diplome_id:
            raise ValidationError('Cette tâche n’appartient pas au diplôme du TP.')


class TPV2CritereOfficiel(TimeStampedModel):
    TYPE_CHOICES = TPV2CompetenceOfficielle.TYPE_CHOICES
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='criteres_officiels_selectionnes')
    critere = models.ForeignKey(BacCompetenceCritere, on_delete=models.PROTECT, related_name='tps_v2')
    type_lien = models.CharField(max_length=30, choices=TYPE_CHOICES, default='travaillee')
    bareme = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='Points affectés à ce critère officiel.')
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='Poids indicatif en pourcentage pour l’évaluation.')

    class Meta:
        unique_together = [('tp', 'critere')]
        ordering = ['critere__competence__code', 'critere__ordre']
        verbose_name = 'V2 critère officiel sélectionné'
        verbose_name_plural = 'V2 critères officiels sélectionnés'

    def clean(self):
        if self.tp_id and self.critere_id and self.tp.diplome_id != self.critere.competence.diplome_id:
            raise ValidationError('Ce critère n’appartient pas au diplôme du TP.')


class TPV2AttitudeOfficielle(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='attitudes_officielles_selectionnees')
    attitude = models.ForeignKey(BacAttitudeProfessionnelle, on_delete=models.PROTECT, related_name='tps_v2')

    class Meta:
        unique_together = [('tp', 'attitude')]
        ordering = ['attitude__ordre']
        verbose_name = 'V2 attitude professionnelle sélectionnée'
        verbose_name_plural = 'V2 attitudes professionnelles sélectionnées'

    def clean(self):
        if self.tp_id and self.attitude_id and self.tp.diplome_id != self.attitude.diplome_id:
            raise ValidationError('Cette attitude professionnelle n’appartient pas au diplôme du TP.')


class TPV2CritereReussite(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='criteres_reussite')
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    niveau_attendu = models.CharField(max_length=120, blank=True)
    obligatoire = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'V2 critère de réussite TP'
        verbose_name_plural = 'V2 critères de réussite TP'

    def __str__(self):
        return f'{self.tp.code} — {self.libelle}'


class TPV2CritereEvaluationFinale(TimeStampedModel):
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='criteres_evaluation_finale')
    libelle = models.CharField(max_length=320)
    indicateur = models.TextField(blank=True)
    bareme = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    commentaire = models.TextField(blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'V2 critère d’évaluation finale TP'
        verbose_name_plural = 'V2 critères d’évaluation finale TP'

    def __str__(self):
        return f'{self.tp.code} — {self.libelle}'


class TPV2Document(TimeStampedModel):
    TYPE_CHOICES = [('pdf_eleve', 'PDF élève'), ('docx_prof', 'DOCX professeur'), ('corrige', 'Corrigé'), ('annexe', 'Annexe'), ('ressource', 'Ressource')]
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='documents_v2')
    type_document = models.CharField(max_length=30, choices=TYPE_CHOICES, default='ressource')
    titre = models.CharField(max_length=220)
    fichier = models.FileField(upload_to='tpv2/documents/')
    visible_eleve = models.BooleanField(default=True)
    visible_prof = models.BooleanField(default=True)
    actif = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(TpUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_tpv2')

    class Meta:
        ordering = ['tp__code', 'titre']
        verbose_name = 'V2 document TP'
        verbose_name_plural = 'V2 documents TP'

    def __str__(self):
        return f'{self.tp.code} — {self.titre}'


class TPV2LinkedBlock(TimeStampedModel):
    SENS_CHOICES = [('avant', 'TP liés avant / prérequis'), ('apres', 'TP liés après / poursuite')]
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='linked_blocks')
    sens = models.CharField(max_length=20, choices=SENS_CHOICES, default='avant')
    titre = models.CharField(max_length=220, default='Bloc de TP liés')
    ordre = models.PositiveIntegerField(default=100)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['sens', 'ordre', 'id']
        verbose_name = 'V2 bloc de TP liés'
        verbose_name_plural = 'V2 blocs de TP liés'

    def __str__(self):
        return f'{self.tp.code} — {self.get_sens_display()} — {self.titre}'


class TPV2LinkedTPItem(TimeStampedModel):
    NIVEAU_CHOICES = [('conseille', 'Conseillé'), ('obligatoire', 'Obligatoire')]
    block = models.ForeignKey(TPV2LinkedBlock, on_delete=models.CASCADE, related_name='items')
    linked_tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='linked_from_items')
    niveau_lien = models.CharField(max_length=20, choices=NIVEAU_CHOICES, default='conseille')
    commentaire = models.CharField(max_length=260, blank=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = [('block', 'linked_tp')]
        ordering = ['ordre', 'linked_tp__code']
        verbose_name = 'V2 TP lié'
        verbose_name_plural = 'V2 TP liés'

    def clean(self):
        if self.block_id and self.linked_tp_id and self.block.tp_id == self.linked_tp_id:
            raise ValidationError('Un TP ne peut pas être lié à lui-même.')

    def __str__(self):
        return f'{self.block.tp.code} → {self.linked_tp.code} ({self.niveau_lien})'


class TPV2CriterionLibrary(TimeStampedModel):
    TYPE_CHOICES = [('reussite', 'Critère de réussite'), ('evaluation_finale', 'Critère d’évaluation finale')]
    diplome = models.ForeignKey(BacDiplome, on_delete=models.SET_NULL, null=True, blank=True, related_name='criteres_bibliotheque')
    type_critere = models.CharField(max_length=30, choices=TYPE_CHOICES, default='reussite')
    metier = models.CharField(max_length=160, blank=True, help_text='Métier ou famille métier concernée.')
    theme = models.CharField(max_length=160, blank=True)
    usage_recommande = models.CharField(max_length=80, blank=True)
    libelle = models.CharField(max_length=320)
    description = models.TextField(blank=True)
    niveau_attendu = models.CharField(max_length=120, blank=True)
    indicateur = models.TextField(blank=True)
    bareme = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['type_critere', 'diplome__code', 'metier', 'theme', 'ordre', 'libelle']
        verbose_name = 'V2 bibliothèque de critères ajoutables'
        verbose_name_plural = 'V2 bibliothèque de critères ajoutables'

    def __str__(self):
        diplome = self.diplome.code if self.diplome_id else 'Tous'
        return f'{diplome} — {self.get_type_critere_display()} — {self.libelle}'


class TPV2ResourceGroup(TimeStampedModel):
    OPERATOR_CHOICES = [('ALL', 'ET — toutes les ressources du groupe sont nécessaires'), ('ANY', 'OU — une ressource du groupe suffit')]
    # Règle métier V2.8.5 : chaque bloc ajouté depuis l’interface est un bloc OU.
    # Plusieurs blocs successifs sont interprétés comme des blocs nécessaires entre eux : bloc 1 ET bloc 2 ET bloc 3.
    tp = models.ForeignKey(TPV2, on_delete=models.CASCADE, related_name='resource_groups')
    titre = models.CharField(max_length=220, default='Groupe de ressources')
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES, default='ANY')
    obligatoire = models.BooleanField(default=True)
    ordre = models.PositiveIntegerField(default=100)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'V2 groupe ressources TP'
        verbose_name_plural = 'V2 groupes ressources TP'

    def __str__(self):
        return f'{self.tp.code} — {self.titre} ({self.operator})'


class TPV2ResourceItem(TimeStampedModel):
    SOURCE_CHOICES = [('system_manager', 'System Manager'), ('toolmag', 'ToolMag'), ('pedashop', 'PedaShop'), ('manual', 'Saisie manuelle')]
    RESOURCE_TYPE_CHOICES = [('systeme', 'Système'), ('outil', 'Outil'), ('mesure', 'Appareil de mesure'), ('materiel', 'Matériel'), ('consommable', 'Consommable'), ('logiciel', 'Logiciel'), ('autre', 'Autre')]
    group = models.ForeignKey(TPV2ResourceGroup, on_delete=models.CASCADE, related_name='items')
    source_module = models.CharField(max_length=40, choices=SOURCE_CHOICES, default='manual')
    resource_type = models.CharField(max_length=40, choices=RESOURCE_TYPE_CHOICES, default='autre')
    external_id = models.CharField(max_length=120, blank=True, help_text='ID de l’objet dans le module source si connu.')
    external_code = models.CharField(max_length=120, blank=True)
    libelle = models.CharField(max_length=260)
    quantite = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unite = models.CharField(max_length=40, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['group__ordre', 'source_module', 'libelle']
        verbose_name = 'V2 ressource TP'
        verbose_name_plural = 'V2 ressources TP'

    def __str__(self):
        return f'{self.get_source_module_display()} — {self.libelle}'


class TPV2TransferRule(TimeStampedModel):
    LEVEL_CHOICES = [('T0', 'T0 — non transférable'), ('T1', 'T1 — découverte'), ('T2', 'T2 — partiel'), ('T3', 'T3 — adapté'), ('T4', 'T4 — fort')]
    source = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='transfer_rules_source')
    cible = models.ForeignKey(BacDiplome, on_delete=models.CASCADE, related_name='transfer_rules_cible')
    competence_pivot = models.ForeignKey(CompetencePivot, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfer_rules')
    niveau = models.CharField(max_length=2, choices=LEVEL_CHOICES, default='T2')
    recommandation = models.TextField(blank=True)
    limites = models.TextField(blank=True)

    class Meta:
        unique_together = [('source', 'cible', 'competence_pivot')]
        ordering = ['source__code', 'cible__code', 'niveau']
        verbose_name = 'V2 règle de transfert référentiel'
        verbose_name_plural = 'V2 règles de transfert référentiel'

    def __str__(self):
        return f'{self.source.code} → {self.cible.code} {self.niveau}'
