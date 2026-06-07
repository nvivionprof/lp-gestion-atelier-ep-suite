from __future__ import annotations
from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.urls import reverse
import re
import unicodedata


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


class SystemUser(TimeStampedModel):
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
        verbose_name = 'utilisateur System Manager synchronisé'
        verbose_name_plural = 'utilisateurs System Manager synchronisés'

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
        return role in {'professeur', 'responsable', 'admin', 'admin_suite', 'magasinier'} or any(r in rights for r in ['SYSTEM_EDIT', 'SYSTEM_ADMIN', 'CORE_ADMIN'])

    @property
    def is_admin_like(self):
        role = (self.role_principal or '').lower()
        rights = self.rights_list()
        return role in {'admin', 'admin_suite', 'responsable'} or any(r in rights for r in ['SYSTEM_ADMIN', 'CORE_ADMIN'])


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


class SchoolClass(TimeStampedModel):
    """Classe synchronisée depuis LP Core, utilisable dans les blocs et les réservations."""
    core_class_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    nom = models.CharField(max_length=120)
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='classes')
    formation_code = models.CharField(max_length=40, blank=True)
    school_year = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['formation__code', 'nom']
        unique_together = [('nom', 'school_year')]
        verbose_name = 'classe synchronisée'
        verbose_name_plural = 'classes synchronisées'

    def __str__(self):
        suffix = f' — {self.formation_code}' if self.formation_code else ''
        return f'{self.nom}{suffix}'


class WorkshopZone(TimeStampedModel):
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='zones_responsable')
    active = models.BooleanField(default=True)
    ordre_affichage = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['ordre_affichage', 'code']
        verbose_name = 'zone atelier'
        verbose_name_plural = 'zones atelier'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'ZONE', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class WorkshopSubZone(TimeStampedModel):
    zone = models.ForeignKey(WorkshopZone, on_delete=models.CASCADE, related_name='sous_zones')
    code = models.CharField(max_length=40)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    ordre_affichage = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['zone__code', 'ordre_affichage', 'code']
        unique_together = [('zone', 'code')]
        verbose_name = 'sous-zone atelier'
        verbose_name_plural = 'sous-zones atelier'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'SOUS_ZONE', 40)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.zone.code} / {self.code} — {self.nom}'


class EducationalSystem(TimeStampedModel):
    STATUS_CHOICES = [
        ('disponible', 'Disponible'),
        ('reserve', 'Réservé'),
        ('en_utilisation', 'En cours d’utilisation'),
        ('restitution_attente', 'Restitution en attente'),
        ('alerte', 'Disponible avec alerte'),
        ('maintenance', 'En maintenance'),
        ('hors_service', 'Hors service'),
        ('archive', 'Archivé'),
    ]
    code = models.CharField(max_length=80, unique=True, blank=True)
    designation = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='systems/photos/', blank=True)
    zone = models.ForeignKey(WorkshopZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='systemes')
    sous_zone = models.ForeignKey(WorkshopSubZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='systemes')
    formations = models.ManyToManyField(Formation, blank=True, related_name='systemes')
    niveaux = models.ManyToManyField(Niveau, blank=True, related_name='systemes')
    professeur_referent = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='systemes_referent')
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='disponible')
    actif = models.BooleanField(default=True)
    commentaire_interne = models.TextField(blank=True)

    class Meta:
        ordering = ['zone__code', 'code']
        verbose_name = 'système pédagogique'
        verbose_name_plural = 'systèmes pédagogiques'

    def save(self, *args, **kwargs):
        if not self.code:
            zone = self.zone.code if self.zone else 'SYS'
            base = normalize_code(self.designation, 'SYSTEME', 40)
            self.code = f'{zone}-{base}'[:80]
            original = self.code
            counter = 1
            while EducationalSystem.objects.exclude(pk=self.pk).filter(code=self.code).exists():
                counter += 1
                self.code = f'{original[:72]}-{counter:02d}'
        else:
            self.code = normalize_code(self.code, 'SYSTEME', 80)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.designation}'

    def get_absolute_url(self):
        return reverse('system_detail', args=[self.pk])

    @property
    def open_anomalies_count(self):
        return self.anomalies.exclude(statut__in=['resolue', 'annulee']).count()


class TemporarySystemPermission(TimeStampedModel):
    """Droits temporaires pour permettre à un élève de créer/modifier des systèmes."""
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE, related_name='temporary_system_permissions', null=True, blank=True, help_text='Utilisateur ciblé. Laisser vide si le droit est accordé à toute une classe.')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='temporary_system_permissions', null=True, blank=True, help_text='Classe ciblée. Optionnel si un utilisateur est choisi.')
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField()
    can_create = models.BooleanField(default=False, verbose_name='Peut créer des systèmes')
    can_edit = models.BooleanField(default=True, verbose_name='Peut modifier des systèmes')
    zones = models.ManyToManyField(WorkshopZone, blank=True, related_name='temporary_permissions')
    systems = models.ManyToManyField(EducationalSystem, blank=True, related_name='temporary_permissions')
    reason = models.TextField(blank=True, verbose_name='Motif / activité')
    granted_by = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='temporary_permissions_granted')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_debut', 'user__last_name', 'user__first_name']
        verbose_name = 'droit temporaire système'
        verbose_name_plural = 'droits temporaires systèmes'

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut >= self.date_fin:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')
        if not self.user_id and not self.school_class_id:
            raise ValidationError('Choisir au moins un utilisateur ou une classe.')

    def is_active_now(self):
        now = timezone.now()
        return self.active and self.date_debut <= now <= self.date_fin

    def allows_system(self, systeme=None, create=False):
        if not self.is_active_now():
            return False
        if create and not self.can_create:
            return False
        if not create and not self.can_edit:
            return False
        if systeme is None:
            return True
        system_ids = set(self.systems.values_list('id', flat=True))
        zone_ids = set(self.zones.values_list('id', flat=True))
        if system_ids and systeme.id not in system_ids:
            return False
        if zone_ids and systeme.zone_id not in zone_ids:
            return False
        return True

    def __str__(self):
        target = self.user or self.school_class or 'périmètre non défini'
        return f'{target} — {self.date_debut:%d/%m/%Y} → {self.date_fin:%d/%m/%Y}'


class DocumentCategory(TimeStampedModel):
    SECTION_CHOICES = [
        ('01', '01 - Présentation - CCTP - Analyse fonctionnelle'),
        ('02', '02 - Plans, schémas et notes de calcul'),
        ('03', '03 - Documentations techniques'),
        ('04', '04 - Programmes'),
        ('05', '05 - TP / TD associés'),
        ('06', '06 - Sécurité / risques / consignation'),
        ('07', '07 - Maintenance / dépannage'),
        ('08', '08 - Historique des modifications'),
    ]
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_categories')
    section_code = models.CharField(max_length=2, choices=SECTION_CHOICES, blank=True)
    ordre = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['section_code', 'ordre', 'code']
        verbose_name = 'catégorie documentaire'
        verbose_name_plural = 'catégories documentaires'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'DOC', 40)
        super().save(*args, **kwargs)

    @property
    def is_root(self):
        return self.parent_id is None

    def __str__(self):
        prefix = f'{self.parent.code} / ' if self.parent_id else ''
        return f'{prefix}{self.code} — {self.nom}'


class SystemDocument(TimeStampedModel):
    TYPE_CHOICES = [('pdf', 'PDF'), ('word', 'Word'), ('excel', 'Excel'), ('image', 'Image'), ('video', 'Vidéo'), ('lien', 'Lien'), ('autre', 'Autre')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='documents')
    categorie = models.ForeignKey(DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    titre = models.CharField(max_length=220)
    type_document = models.CharField(max_length=30, choices=TYPE_CHOICES, default='pdf')
    version = models.CharField(max_length=40, blank=True)
    parent_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='versions', help_text='Version précédente ou document remplacé.')
    fichier = models.FileField(upload_to='systems/documents/', blank=True)
    preview_pdf = models.FileField(upload_to='systems/previews/', blank=True, help_text='PDF de prévisualisation généré automatiquement pour les documents Office.')
    preview_status = models.CharField(max_length=40, blank=True, default='', help_text='État de la prévisualisation : pending / ok / error / unsupported.')
    preview_error = models.TextField(blank=True)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    visible_students = models.BooleanField(default=True, verbose_name='Visible élèves')
    teacher_only = models.BooleanField(default=False, verbose_name='Correction / contenu professeur uniquement')
    ajoute_par = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_ajoutes')
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['categorie__ordre', 'titre']
        verbose_name = 'document système'
        verbose_name_plural = 'documents systèmes'

    def clean(self):
        if not self.fichier and not self.url:
            raise ValidationError('Ajouter un fichier ou un lien URL.')

    def save(self, *args, **kwargs):
        if self.teacher_only:
            self.visible_students = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.systeme.code} — {self.titre}'


class DefaultCheckTemplate(TimeStampedModel):
    """Modèle de check par défaut appliqué automatiquement à la création d'un système."""
    RESPONSE_TYPE_CHOICES = [('oui_non_nc', 'Oui / Non / NC'), ('texte', 'Texte libre'), ('photo', 'Photo'), ('nombre', 'Nombre')]
    EXPECTED_RESPONSE_CHOICES = [('oui', 'Oui attendu'), ('non', 'Non attendu'), ('nc', 'NC attendu'), ('', 'Non contrôlé')]
    PHASE_CHOICES = [('prise', 'Prise de poste'), ('restitution', 'Restitution'), ('deux', 'Prise et restitution')]
    libelle = models.CharField(max_length=240)
    aide = models.TextField(blank=True)
    phase = models.CharField(max_length=30, choices=PHASE_CHOICES, default='deux')
    type_reponse = models.CharField(max_length=30, choices=RESPONSE_TYPE_CHOICES, default='oui_non_nc')
    expected_response = models.CharField(max_length=20, choices=EXPECTED_RESPONSE_CHOICES, default='oui', blank=True, verbose_name='Réponse attendue')
    obligatoire = models.BooleanField(default=True)
    bloquant_si_non = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=100)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'check par défaut système'
        verbose_name_plural = 'checks par défaut systèmes'

    def create_for_system(self, systeme):
        return CheckItem.objects.create(
            systeme=systeme,
            libelle=self.libelle,
            aide=self.aide,
            phase=self.phase,
            type_reponse=self.type_reponse,
            expected_response=self.expected_response,
            obligatoire=self.obligatoire,
            bloquant_si_non=self.bloquant_si_non,
            ordre=self.ordre,
            actif=True,
        )

    def __str__(self):
        return f'{self.ordre} — {self.libelle}'


class CheckItem(TimeStampedModel):
    RESPONSE_TYPE_CHOICES = [('oui_non_nc', 'Oui / Non / NC'), ('texte', 'Texte libre'), ('photo', 'Photo'), ('nombre', 'Nombre')]
    EXPECTED_RESPONSE_CHOICES = [('oui', 'Oui attendu'), ('non', 'Non attendu'), ('nc', 'NC attendu'), ('', 'Non contrôlé')]
    PHASE_CHOICES = [('prise', 'Prise de poste'), ('restitution', 'Restitution'), ('deux', 'Prise et restitution')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='check_items')
    libelle = models.CharField(max_length=240)
    aide = models.TextField(blank=True)
    phase = models.CharField(max_length=30, choices=PHASE_CHOICES, default='deux')
    type_reponse = models.CharField(max_length=30, choices=RESPONSE_TYPE_CHOICES, default='oui_non_nc')
    expected_response = models.CharField(max_length=20, choices=EXPECTED_RESPONSE_CHOICES, default='oui', blank=True, verbose_name='Réponse attendue')
    obligatoire = models.BooleanField(default=True)
    bloquant_si_non = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=100)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'point de check système'
        verbose_name_plural = 'points de check système'

    def __str__(self):
        return f'{self.systeme.code} — {self.libelle}'


class ReservationGroup(TimeStampedModel):
    """Dossier de réservation : métadonnées communes puis ajout des systèmes via recherche filtrée."""
    MODE_CHOICES = [('ponctuelle', 'Ponctuelle'), ('bloc_atelier', 'Bloc atelier'), ('sequence_tp', 'Séquence TP Manager')]
    STATUS_CHOICES = [('brouillon', 'Brouillon'), ('confirmee', 'Confirmée'), ('annulee', 'Annulée')]
    titre = models.CharField(max_length=220, blank=True)
    reservation_mode = models.CharField(max_length=30, choices=MODE_CHOICES, default='ponctuelle')
    professeur = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservation_groups')
    classe = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservation_groups')
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    block = models.ForeignKey('WorkshopBlock', on_delete=models.SET_NULL, null=True, blank=True, related_name='reservation_groups')
    slots = models.ManyToManyField('WorkshopBlockSlot', blank=True, related_name='reservation_groups')
    sequence_code = models.CharField(max_length=80, blank=True)
    sequence_title = models.CharField(max_length=220, blank=True)
    tp_code = models.CharField(max_length=80, blank=True)
    tp_titre = models.CharField(max_length=220, blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='brouillon')
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_debut', 'titre']
        verbose_name = 'dossier de réservation système'
        verbose_name_plural = 'dossiers de réservation systèmes'

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut >= self.date_fin:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')

    def __str__(self):
        label = self.titre or self.classe_ou_groupe or self.sequence_title or self.get_reservation_mode_display()
        return f'{label} — {timezone.localtime(self.date_debut):%d/%m/%Y}'


class Reservation(TimeStampedModel):
    group = models.ForeignKey(ReservationGroup, on_delete=models.CASCADE, null=True, blank=True, related_name='reservations')
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'), ('confirmee', 'Confirmée'), ('en_cours', 'En cours'),
        ('terminee', 'Terminée'), ('non_restituee', 'Non restituée'), ('annulee', 'Annulée'), ('refusee', 'Refusée')
    ]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='reservations')
    professeur = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    tp_code = models.CharField(max_length=80, blank=True, help_text='Lien prévu avec le futur module TP.')
    tp_titre = models.CharField(max_length=220, blank=True)
    reservation_mode = models.CharField(max_length=30, choices=[('ponctuelle', 'Ponctuelle'), ('bloc_atelier', 'Bloc atelier'), ('sequence_tp', 'Séquence TP Manager')], default='ponctuelle')
    block_code = models.CharField(max_length=80, blank=True)
    block_name = models.CharField(max_length=180, blank=True)
    slot_label = models.CharField(max_length=120, blank=True)
    sequence_code = models.CharField(max_length=80, blank=True)
    sequence_title = models.CharField(max_length=220, blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='confirmee')
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['date_debut', 'systeme__code']
        verbose_name = 'réservation système'
        verbose_name_plural = 'réservations systèmes'

    def clean(self):
        if self.date_debut and self.date_fin and self.date_debut >= self.date_fin:
            raise ValidationError('La date de fin doit être postérieure à la date de début.')
        if self.systeme_id and self.date_debut and self.date_fin and self.statut not in {'annulee', 'refusee'}:
            conflicts = Reservation.objects.filter(
                systeme=self.systeme,
                date_debut__lt=self.date_fin,
                date_fin__gt=self.date_debut,
            ).exclude(pk=self.pk).exclude(statut__in=['annulee', 'refusee'])
            if conflicts.exists():
                c = conflicts.first()
                raise ValidationError(f'Conflit : système déjà réservé de {timezone.localtime(c.date_debut):%d/%m/%Y %H:%M} à {timezone.localtime(c.date_fin):%H:%M}.')

    def __str__(self):
        return f'{self.systeme.code} — {timezone.localtime(self.date_debut):%d/%m/%Y %H:%M}'

    @property
    def is_current(self):
        now = timezone.now()
        return self.date_debut <= now <= self.date_fin and self.statut in {'confirmee', 'en_cours'}


class WorkSession(TimeStampedModel):
    STATUS_CHOICES = [('ouverte', 'Ouverte'), ('restituee', 'Restituée'), ('anomalie', 'Restituée avec anomalie'), ('non_restituee', 'Non restituée')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='sessions')
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    utilisateur = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_utilisateur')
    professeur_referent = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions_professeur')
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    tp_code = models.CharField(max_length=80, blank=True)
    tp_titre = models.CharField(max_length=220, blank=True)
    date_prise = models.DateTimeField(default=timezone.now)
    date_restitution = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='ouverte')
    commentaire_prise = models.TextField(blank=True)
    commentaire_restitution = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_prise']
        verbose_name = 'prise de poste système'
        verbose_name_plural = 'prises et restitutions de poste système'

    def __str__(self):
        return f'{self.systeme.code} — {self.utilisateur} — {self.date_prise:%d/%m/%Y %H:%M}'


class CheckResponse(TimeStampedModel):
    PHASE_CHOICES = [('prise', 'Prise de poste'), ('restitution', 'Restitution')]
    VALUE_CHOICES = [('oui', 'Oui'), ('non', 'Non'), ('nc', 'Non concerné')]
    session = models.ForeignKey(WorkSession, on_delete=models.CASCADE, related_name='reponses')
    item = models.ForeignKey(CheckItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='reponses')
    phase = models.CharField(max_length=30, choices=PHASE_CHOICES)
    valeur = models.CharField(max_length=20, choices=VALUE_CHOICES, blank=True)
    texte = models.TextField(blank=True)
    photo = models.ImageField(upload_to='systems/checks/', blank=True)

    class Meta:
        ordering = ['phase', 'item__ordre', 'id']
        verbose_name = 'réponse de check système'
        verbose_name_plural = 'réponses de check système'


class SystemAnomaly(TimeStampedModel):
    GRAVITY_CHOICES = [('info', 'Information'), ('mineure', 'Mineure'), ('majeure', 'Majeure'), ('bloquante', 'Bloquante')]
    STATUS_CHOICES = [('ouverte', 'Ouverte'), ('en_cours', 'En cours'), ('resolue', 'Résolue'), ('annulee', 'Annulée')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='anomalies')
    session = models.ForeignKey(WorkSession, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomalies')
    signalee_par = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomalies_signalees')
    titre = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    gravite = models.CharField(max_length=30, choices=GRAVITY_CHOICES, default='mineure')
    statut = models.CharField(max_length=30, choices=STATUS_CHOICES, default='ouverte')
    action_realisee = models.TextField(blank=True)
    blocking = models.BooleanField(default=False, verbose_name='Anomalie bloquante')
    lift_requested_by = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomaly_lift_requests')
    lift_requested_at = models.DateTimeField(null=True, blank=True)
    lift_request_comment = models.TextField(blank=True)
    lift_authorized_by = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='anomaly_lift_authorizations')
    lift_authorized_at = models.DateTimeField(null=True, blank=True)
    date_resolution = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'anomalie système'
        verbose_name_plural = 'anomalies systèmes'

    def __str__(self):
        return f'{self.systeme.code} — {self.titre}'


class WorkshopBlock(TimeStampedModel):
    """Profil de bloc atelier synchronisable depuis LP Core.

    Exemple : Terminale MELEC lundi matin + jeudi après-midi.
    System Manager l'utilise pour générer des réservations par lots.
    """
    core_block_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    code = models.CharField(max_length=80, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    # Formations/niveaux conservés pour compatibilité ; association métier prioritaire par classes.
    formations = models.ManyToManyField(Formation, blank=True, related_name='workshop_blocks')
    niveaux = models.ManyToManyField(Niveau, blank=True, related_name='workshop_blocks')
    classes = models.ManyToManyField(SchoolClass, blank=True, related_name='workshop_blocks')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'bloc atelier'
        verbose_name_plural = 'blocs atelier'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'BLOC_ATELIER', 80)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom}'


class WorkshopBlockSlot(TimeStampedModel):
    DAY_CHOICES = [(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi')]
    block = models.ForeignKey('WorkshopBlock', on_delete=models.CASCADE, related_name='slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    label = models.CharField(max_length=120, blank=True, help_text='Ex. Lundi matin, jeudi après-midi')
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['block__code', 'day_of_week', 'start_time']
        unique_together = [('block', 'day_of_week', 'start_time', 'end_time')]
        verbose_name = 'créneau de bloc atelier'
        verbose_name_plural = 'créneaux de blocs atelier'

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('L’heure de fin doit être postérieure à l’heure de début.')

    def __str__(self):
        return f'{self.block.code} — {self.get_day_of_week_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}'


class SystemTPAssociation(TimeStampedModel):
    SOURCE_CHOICES = [('manual', 'Ajout manuel'), ('tpmanager', 'Synchronisé TP Manager')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='tp_associations')
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='manual')
    tp_id = models.PositiveIntegerField(null=True, blank=True)
    tp_code = models.CharField(max_length=80, blank=True)
    tp_titre = models.CharField(max_length=220)
    sequence_code = models.CharField(max_length=80, blank=True)
    sequence_titre = models.CharField(max_length=220, blank=True)
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='tp_system_links')
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True, related_name='tp_system_links')
    url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['formation__code', 'niveau__ordre', 'tp_code', 'tp_titre']
        verbose_name = 'TP/TD associé au système'
        verbose_name_plural = 'TP/TD associés aux systèmes'

    def __str__(self):
        return f'{self.systeme.code} — {self.tp_code or "TP"} {self.tp_titre}'


class SystemSafetyLink(TimeStampedModel):
    SOURCE_CHOICES = [('manual', 'Ajout manuel'), ('safety_manager', 'Synchronisé Safety Manager')]
    TYPE_CHOICES = [('duerp', 'DUERP'), ('risk', 'Risque'), ('consignation', 'Consignation'), ('procedure', 'Procédure sécurité'), ('event', 'Événement / presque accident')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='safety_links')
    source = models.CharField(max_length=40, choices=SOURCE_CHOICES, default='manual')
    safety_object_type = models.CharField(max_length=40, choices=TYPE_CHOICES, default='risk')
    safety_object_id = models.CharField(max_length=80, blank=True)
    titre = models.CharField(max_length=220)
    niveau_risque = models.CharField(max_length=80, blank=True)
    consignation_requise = models.BooleanField(default=False)
    habilitations_requises = models.CharField(max_length=255, blank=True)
    epi_requis = models.TextField(blank=True)
    procedure_resume = models.TextField(blank=True)
    url = models.URLField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-consignation_requise', 'titre']
        verbose_name = 'lien sécurité système'
        verbose_name_plural = 'liens sécurité systèmes'

    def __str__(self):
        return f'{self.systeme.code} — {self.titre}'


class MaintenanceIntervention(TimeStampedModel):
    TYPE_CHOICES = [
        ('depannage', 'Dépannage'),
        ('corrective', 'Maintenance corrective'),
        ('preventive', 'Maintenance préventive'),
        ('controle_periodique', 'Contrôle périodique'),
        ('mise_en_service', 'Mise en service initiale'),
    ]
    STATUS_CHOICES = [('brouillon', 'Brouillon'), ('en_cours', 'En cours'), ('terminee', 'Terminée'), ('conforme', 'Conforme'), ('non_conforme', 'Non conforme'), ('a_surveiller', 'À surveiller')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='maintenance_interventions')
    reference = models.CharField(max_length=80, unique=True, blank=True)
    type_action = models.CharField(max_length=40, choices=TYPE_CHOICES, default='depannage')
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='brouillon')
    demandeur_nom = models.CharField(max_length=160, blank=True)
    executant_nom = models.CharField(max_length=160, blank=True)
    executant_prenom = models.CharField(max_length=160, blank=True)
    executant_classe = models.CharField(max_length=120, blank=True)
    habilitation = models.CharField(max_length=120, blank=True)
    exploitant_nom = models.CharField(max_length=160, blank=True)
    debut_intervention = models.DateTimeField(null=True, blank=True)
    fin_intervention = models.DateTimeField(null=True, blank=True)
    constat_operateur = models.TextField(blank=True)
    fonctionne_bien = models.TextField(blank=True)
    ne_fonctionne_pas = models.TextField(blank=True)
    procedure_conditions_mesure = models.TextField(blank=True)
    appareils_mesure_references = models.TextField(blank=True)
    calculs_prealables = models.TextField(blank=True)
    reglages_valeurs = models.TextField(blank=True)
    tableau_releves = models.TextField(blank=True)
    exploitation_releves = models.TextField(blank=True)
    conclusion_conformite = models.TextField(blank=True)
    epi = models.TextField(blank=True, help_text='EPI prévus/utilisés.')
    ecs = models.TextField(blank=True, help_text='Équipements collectifs de sécurité.')
    eis = models.TextField(blank=True, help_text='Équipements individuels de sécurité / consignation.')
    appareils_mesure = models.TextField(blank=True)
    action_realisee = models.TextField(blank=True)
    suite_a_donner = models.TextField(blank=True)
    safety_link = models.ForeignKey(SystemSafetyLink, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_interventions')
    intervention_par = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_interventions')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'intervention maintenance / GMAO'
        verbose_name_plural = 'interventions maintenance / GMAO'

    def save(self, *args, **kwargs):
        if not self.reference:
            stamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.reference = f'MAINT-{self.systeme.code}-{stamp}'[:80]
        super().save(*args, **kwargs)

    @property
    def duree_minutes(self):
        if self.debut_intervention and self.fin_intervention:
            return int((self.fin_intervention - self.debut_intervention).total_seconds() // 60)
        return None

    def __str__(self):
        return f'{self.reference} — {self.systeme.code}'


class MaintenanceCheckLine(TimeStampedModel):
    intervention = models.ForeignKey(MaintenanceIntervention, on_delete=models.CASCADE, related_name='check_lines')
    ordre = models.PositiveIntegerField(default=10)
    hypothese = models.TextField(blank=True)
    controle = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    bornes_test = models.CharField(max_length=160, blank=True)
    appareil_utilise = models.CharField(max_length=160, blank=True)
    sous_tension = models.BooleanField(default=False)
    hors_tension = models.BooleanField(default=False)
    valeur_attendue = models.CharField(max_length=160, blank=True)
    valeur_mesuree = models.CharField(max_length=160, blank=True)
    conclusion = models.TextField(blank=True)

    class Meta:
        ordering = ['ordre', 'id']
        verbose_name = 'ligne de contrôle maintenance'
        verbose_name_plural = 'lignes de contrôle maintenance'

    def __str__(self):
        return f'{self.intervention.reference} — contrôle {self.ordre}'


class MaintenanceDrawingZone(TimeStampedModel):
    ZONE_CHOICES = [('schema_defaut', 'Localisation sur schéma'), ('raccordement_mesure', 'Schéma de raccordement mesure'), ('photo_constat', 'Photo / constat'), ('croquis_libre', 'Croquis libre')]
    MODE_CHOICES = [('photo', 'Photo / appareil photo'), ('dessin', 'Dessin tablette'), ('mixte', 'Photo + annotation'), ('papier_quadrille', 'Zone quadrillée')]
    intervention = models.ForeignKey(MaintenanceIntervention, on_delete=models.CASCADE, related_name='drawing_zones')
    zone_type = models.CharField(max_length=40, choices=ZONE_CHOICES, default='croquis_libre')
    mode = models.CharField(max_length=40, choices=MODE_CHOICES, default='papier_quadrille')
    titre = models.CharField(max_length=220)
    image = models.ImageField(upload_to='systems/maintenance/drawings/', blank=True)
    canvas_data = models.TextField(blank=True, help_text='Image base64 issue du dessin tablette.')
    note = models.TextField(blank=True)
    grid_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['zone_type', 'id']
        verbose_name = 'zone dessin/photo maintenance'
        verbose_name_plural = 'zones dessin/photo maintenance'

    def __str__(self):
        return f'{self.intervention.reference} — {self.titre}'


class SystemChangeLog(TimeStampedModel):
    CHANGE_TYPE_CHOICES = [('document', 'Document'), ('programme', 'Programme'), ('schema', 'Schéma'), ('maintenance', 'Maintenance'), ('securite', 'Sécurité'), ('parametrage', 'Paramétrage'), ('autre', 'Autre')]
    systeme = models.ForeignKey(EducationalSystem, on_delete=models.CASCADE, related_name='change_logs')
    type_changement = models.CharField(max_length=40, choices=CHANGE_TYPE_CHOICES, default='autre')
    titre = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    version_avant = models.CharField(max_length=80, blank=True)
    version_apres = models.CharField(max_length=80, blank=True)
    effectue_par = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_changes')
    date_effet = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date_effet', '-created_at']
        verbose_name = 'historique modification système'
        verbose_name_plural = 'historiques modifications systèmes'

    def __str__(self):
        return f'{self.systeme.code} — {self.titre}'
