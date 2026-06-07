from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import MinValueValidator
import re
import unicodedata




def normalize_text_code(value, default='CODE'):
    """Normalise un libellé en code stable : Équipe pédagogique -> EQUIPE_PEDAGOGIQUE."""
    value = value or default
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_').upper()
    return value or default


def unique_model_code(model_cls, base_code, field='code'):
    base = normalize_text_code(base_code)
    candidate = base
    idx = 2
    while model_cls.objects.filter(**{field: candidate}).exists():
        candidate = f'{base}_{idx:03d}'
        idx += 1
    return candidate

def normalize_code_prefix(value, default='MAT'):
    """Return the first 3 ASCII letters of a label, uppercased.
    Example: "Outil à main" -> "OUT".
    """
    value = value or ''
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    letters = ''.join(ch for ch in value.upper() if ch.isalnum())
    if not letters:
        letters = default
    return (letters[:3]).ljust(3, 'X')


def next_equipment_code_for_category(category):
    prefix = normalize_code_prefix(category.name if category else '', default='MAT')
    pattern = re.compile(rf'^{re.escape(prefix)}-(\d+)$')
    max_index = 0
    for code in Equipment.objects.filter(code__startswith=f'{prefix}-').values_list('code', flat=True):
        match = pattern.match(code)
        if match:
            max_index = max(max_index, int(match.group(1)))
    return f'{prefix}-{max_index + 1:03d}'

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Formation(TimeStampedModel):
    # Code libre : il est généré automatiquement depuis le nom si laissé vide.
    # Exemples : Bac Pro CIEL -> BAC_PRO_CIEL ; Équipe pédagogique -> EQUIPE_PEDAGOGIQUE.
    code = models.CharField('Code', max_length=64, unique=True, blank=True)
    name = models.CharField('Nom', max_length=160)
    referential_name = models.CharField('Nom du référentiel', max_length=160, blank=True)
    active = models.BooleanField('Actif', default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = unique_model_code(Formation, self.name or self.referential_name or 'FORMATION')
        else:
            self.code = normalize_text_code(self.code)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.name}'


class SchoolClass(TimeStampedModel):
    """Classe pédagogique canonique créée manuellement ou depuis l’import Excel."""
    formation = models.ForeignKey(Formation, verbose_name='Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='school_classes')
    name = models.CharField('Classe', max_length=80)
    active = models.BooleanField('Active', default=True)

    class Meta:
        ordering = ['formation__code', 'name']
        unique_together = [('formation', 'name')]
        verbose_name = 'Classe pédagogique'
        verbose_name_plural = 'Classes pédagogiques'

    def __str__(self):
        if self.formation:
            return f'{self.formation.code} — {self.name}'
        return self.name


class Person(TimeStampedModel):
    class Role(models.TextChoices):
        USER = 'user', 'Utilisateur'
        STOREKEEPER = 'storekeeper', 'Magasinier'
        TECH_INVENTORY = 'tech_inventory', 'Technicien inventaire'
        RESPONSIBLE = 'responsible', 'Responsable'
        READ_ONLY = 'read_only', 'Lecture seule'
        ADMIN = 'admin', 'Administrateur'

    ROLE_IMPORT_ALIASES = {
        'UTILISATEUR': Role.USER,
        'USER': Role.USER,
        'MAGASINIER': Role.STOREKEEPER,
        'STOREKEEPER': Role.STOREKEEPER,
        'TECH_INVENTAIRE': Role.TECH_INVENTORY,
        'TECHNICIEN_INVENTAIRE': Role.TECH_INVENTORY,
        'RESPONSABLE': Role.RESPONSIBLE,
        'LECTURE_SEULE': Role.READ_ONLY,
        'ADMIN': Role.ADMIN,
        'ADMINISTRATEUR': Role.ADMIN,
    }

    code = models.CharField('Code', max_length=32, unique=True)
    first_name = models.CharField('Prénom', max_length=80)
    last_name = models.CharField('Nom', max_length=80)
    username = models.CharField('Identifiant', max_length=120, blank=True, unique=True, null=True)
    email = models.EmailField('Email', blank=True)
    role = models.CharField('Rôle principal', max_length=30, choices=Role.choices, default=Role.USER)
    allowed_roles = models.CharField(
        max_length=255,
        blank=True,
        help_text='Rôles autorisés séparés par des points-virgules : UTILISATEUR;MAGASINIER;TECH_INVENTAIRE',
    )
    formation = models.ForeignKey(Formation, verbose_name='Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='persons')
    class_name = models.CharField('Classe', max_length=80, blank=True)
    group_name = models.CharField('Groupe', max_length=80, blank=True)
    level = models.CharField('Niveau', max_length=80, blank=True)
    department = models.CharField('Service / département', max_length=120, blank=True)
    rfid_uid = models.CharField('UID RFID', max_length=120, blank=True)
    active = models.BooleanField('Actif', default=True)
    archived = models.BooleanField('Archivé', default=False)
    password_hash = models.CharField(max_length=255, blank=True, help_text='Mot de passe ToolMag chiffré')
    must_change_password = models.BooleanField(default=False, help_text='Forcer le changement de mot de passe à la prochaine connexion')

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Personne'
        verbose_name_plural = 'Personnes'

    def __str__(self):
        formation = f' — {self.formation.code}' if self.formation else ''
        classe = f' {self.class_name}' if self.class_name else ''
        return f'{self.first_name} {self.last_name} ({self.get_role_display()}{formation}{classe})'

    def set_password(self, raw_password):
        if raw_password:
            self.password_hash = make_password(str(raw_password))

    def check_password(self, raw_password):
        if not self.password_hash:
            return False
        return check_password(str(raw_password), self.password_hash)

    def has_role(self, *roles):
        """True if the person has one of the requested technical roles.
        Accepts Person.Role values and checks both the main role and allowed_roles.
        """
        requested = {str(role) for role in roles if role}
        if self.role in requested:
            return True
        aliases = {
            Person.Role.USER: {'UTILISATEUR', 'USER', Person.Role.USER},
            Person.Role.STOREKEEPER: {'MAGASINIER', 'STOREKEEPER', Person.Role.STOREKEEPER},
            Person.Role.TECH_INVENTORY: {'TECH_INVENTAIRE', 'TECHNICIEN_INVENTAIRE', Person.Role.TECH_INVENTORY},
            Person.Role.RESPONSIBLE: {'RESPONSABLE', Person.Role.RESPONSIBLE},
            Person.Role.READ_ONLY: {'LECTURE_SEULE', Person.Role.READ_ONLY},
            Person.Role.ADMIN: {'ADMIN', 'ADMINISTRATEUR', Person.Role.ADMIN},
        }
        allowed = {raw.strip().upper() for raw in (self.allowed_roles or '').split(';') if raw.strip()}
        for requested_role in requested:
            for value in aliases.get(requested_role, {requested_role}):
                if str(value).upper() in allowed:
                    return True
        return False

    @property
    def qr_payload(self):
        return f'TOOLMAG:USR:{self.code}'

    def allowed_roles_list(self):
        if not self.allowed_roles:
            return [self.role]
        roles = []
        for raw in self.allowed_roles.split(';'):
            role = raw.strip()
            if role:
                roles.append(role)
        return roles


class EnrollmentHistory(TimeStampedModel):
    class EventType(models.TextChoices):
        CREATED = 'created', 'Création'
        PROMOTED = 'promoted', 'Montée de niveau'
        REPEATED = 'repeated', 'Redoublement'
        TRANSFERRED = 'transferred', 'Changement de filière'
        GROUP_CHANGED = 'group_changed', 'Changement de classe/groupe'
        DEACTIVATED = 'deactivated', 'Désactivation'
        ARCHIVED = 'archived', 'Archivage'
        DELETED_REQUESTED = 'deleted_requested', 'Suppression demandée'
        IMPORT_UPDATED = 'import_updated', 'Mise à jour par import'

    person = models.ForeignKey(Person, related_name='enrollment_history', on_delete=models.CASCADE)
    school_year = models.CharField(max_length=20, blank=True)
    event_type = models.CharField(max_length=40, choices=EventType.choices)
    old_formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    new_formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    old_class_name = models.CharField('Classe', max_length=80, blank=True)
    new_class_name = models.CharField('Classe', max_length=80, blank=True)
    old_group_name = models.CharField('Groupe', max_length=80, blank=True)
    new_group_name = models.CharField('Groupe', max_length=80, blank=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Historique de parcours élève'
        verbose_name_plural = 'Historiques de parcours élèves'

    def __str__(self):
        return f'{self.person.code} — {self.get_event_type_display()} — {self.created_at:%d/%m/%Y}'


class Location(TimeStampedModel):
    class Meta:
        ordering = ['name']
        verbose_name = 'Emplacement'
        verbose_name_plural = 'Emplacements'

    name = models.CharField('Nom', max_length=120, unique=True)
    description = models.TextField('Description', blank=True)

    def __str__(self):
        return self.name


class Category(TimeStampedModel):
    class Meta:
        ordering = ['name']
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'

    name = models.CharField('Nom', max_length=120, unique=True)
    description = models.TextField('Description', blank=True)

    def __str__(self):
        return self.name


class Equipment(TimeStampedModel):
    class EquipmentType(models.TextChoices):
        SIMPLE = 'simple', 'Matériel simple'
        KIT = 'kit', 'Matériel composé / kit'
        CONSUMABLE = 'consumable', 'Consommable'

    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Disponible'
        TO_VERIFY = 'to_verify', 'À vérifier'
        OUT = 'out', 'Sorti'
        LATE = 'late', 'En retard'
        MAINTENANCE = 'maintenance', 'Maintenance'
        INCOMPLETE = 'incomplete', 'Incomplet'
        OUT_OF_SERVICE = 'out_of_service', 'Hors service'
        LOST = 'lost', 'Perdu'

    class Condition(models.TextChoices):
        NEW = 'new', 'Neuf'
        GOOD = 'good', 'Bon état'
        NORMAL_WEAR = 'normal_wear', 'Usure normale'
        WATCH = 'watch', 'À surveiller'
        DAMAGED = 'damaged', 'Abîmé'
        INCOMPLETE = 'incomplete', 'Incomplet'
        DANGEROUS = 'dangerous', 'Dangereux'
        ABSENT = 'absent', 'Absent'

    code = models.CharField('Code matériel', max_length=32, unique=True, blank=True, help_text='Laisser vide pour générer automatiquement : 3 premières lettres de la catégorie + indice. Exemple : OUT-004')
    name = models.CharField('Nom', max_length=160)
    equipment_type = models.CharField('Type de matériel', max_length=20, choices=EquipmentType.choices, default=EquipmentType.SIMPLE)
    category = models.ForeignKey(Category, verbose_name='Catégorie', on_delete=models.SET_NULL, null=True, blank=True)
    brand = models.CharField('Marque', max_length=120, blank=True)
    model = models.CharField('Modèle', max_length=120, blank=True)
    serial_number = models.CharField('Numéro de série', max_length=120, blank=True)
    location = models.ForeignKey(Location, verbose_name='Emplacement', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255, blank=True, verbose_name='Descriptif matériel', help_text='Exemple : contrôleur d’installation, oscilloscope triphasé, kit soudure fibre…')
    status = models.CharField('Statut', max_length=30, choices=Status.choices, default=Status.AVAILABLE)
    current_condition = models.CharField('État actuel', max_length=30, choices=Condition.choices, default=Condition.GOOD)
    inventory_required_out = models.BooleanField('Inventaire requis à la sortie', default=False)
    inventory_required_return = models.BooleanField('Inventaire requis au retour', default=False)
    sensitive = models.BooleanField('Matériel sensible', default=False)
    display_on_public_screen = models.BooleanField('Afficher sur écran dynamique', default=True)
    secure_storage = models.BooleanField(default=False, verbose_name='Stocké en armoire sécurisée')
    secure_cabinet = models.CharField(max_length=50, blank=True, verbose_name='Numéro d’armoire')
    secure_locker = models.CharField(max_length=50, blank=True, verbose_name='Numéro de casier')
    photo = models.ImageField('Photo', upload_to='equipment/', blank=True)
    notes = models.TextField('Notes', blank=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Matériel'
        verbose_name_plural = 'Matériels'

    def __str__(self):
        return f'{self.code} — {self.name}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_equipment_code_for_category(self.category)
        super().save(*args, **kwargs)

    @property
    def qr_payload(self):
        return f'TOOLMAG:MAT:{self.code}'


class EquipmentDocument(TimeStampedModel):
    class DocumentType(models.TextChoices):
        NOTICE = 'notice', 'Notice constructeur'
        QUICKSTART = 'quickstart', 'Fiche de prise en main'
        SAFETY = 'safety', 'Consignes de sécurité'
        MAINTENANCE = 'maintenance', 'Fiche maintenance'
        OTHER = 'other', 'Autre document'

    equipment = models.ForeignKey(Equipment, related_name='documents', on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices, default=DocumentType.NOTICE)
    file = models.FileField(upload_to='equipment_documents/')
    description = models.TextField('Description', blank=True)
    active = models.BooleanField('Actif', default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'document_type', 'title']
        verbose_name = 'Document matériel'
        verbose_name_plural = 'Documents matériels'

    def __str__(self):
        return f'{self.equipment.code} — {self.title}'


class Component(TimeStampedModel):
    equipment = models.ForeignKey(Equipment, related_name='components', on_delete=models.CASCADE)
    name = models.CharField('Nom', max_length=160)
    required = models.BooleanField(default=True)
    expected_quantity = models.PositiveIntegerField(default=1)
    default_condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    photo = models.ImageField(upload_to='components/', blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = [('equipment', 'name')]
        verbose_name = 'Composant'
        verbose_name_plural = 'Composants'

    def __str__(self):
        return f'{self.equipment.code} / {self.name}'


class Loan(TimeStampedModel):
    class LoanStatus(models.TextChoices):
        OPEN = 'open', 'En cours'
        CLOSED = 'closed', 'Clôturé'
        PROBLEM = 'problem', 'Clôturé avec anomalie'

    equipment = models.ForeignKey(Equipment, related_name='loans', on_delete=models.PROTECT)
    borrower = models.ForeignKey(Person, related_name='borrowed_loans', on_delete=models.PROTECT)
    checkout_storekeeper = models.ForeignKey(Person, related_name='checkout_loans', on_delete=models.PROTECT)
    checked_out_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    condition_out = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment_out = models.TextField(blank=True)

    return_storekeeper = models.ForeignKey(Person, related_name='return_loans', on_delete=models.PROTECT, null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    condition_return = models.CharField(max_length=30, choices=Equipment.Condition.choices, blank=True)
    comment_return = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=LoanStatus.choices, default=LoanStatus.OPEN)

    class Meta:
        ordering = ['-checked_out_at']
        verbose_name = 'Sortie / emprunt'
        verbose_name_plural = 'Sorties / emprunts'

    def __str__(self):
        return f'{self.equipment.code} → {self.borrower} ({self.get_status_display()})'

    @property
    def is_late(self):
        return self.status == self.LoanStatus.OPEN and self.due_at and timezone.now() > self.due_at


class ComponentCheck(TimeStampedModel):
    class CheckType(models.TextChoices):
        OUT = 'out', 'Sortie'
        RETURN = 'return', 'Retour'

    loan = models.ForeignKey(Loan, related_name='component_checks', on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    check_type = models.CharField(max_length=10, choices=CheckType.choices)
    present = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment = models.CharField(max_length=255, blank=True)
    checked_by = models.ForeignKey(Person, related_name='component_checks_done', on_delete=models.SET_NULL, null=True, blank=True)
    checked_by_role = models.CharField(max_length=30, blank=True, help_text='Fonction active au moment de l’inventaire : utilisateur ou magasinier')

    class Meta:
        ordering = ['component__sort_order', 'component__name']
        unique_together = [('loan', 'component', 'check_type')]

    def __str__(self):
        return f'{self.loan_id} / {self.component.name} / {self.get_check_type_display()}'



class UserInventory(TimeStampedModel):
    """Inventaire préparatoire réalisé par l'utilisateur connecté.
    Il ne valide jamais administrativement une sortie ou un retour :
    le magasinier relit puis valide.
    """
    class InventoryType(models.TextChoices):
        OUT = 'out', 'Contrôle utilisateur avant sortie'
        RETURN = 'return', 'Contrôle utilisateur avant retour'

    class InventoryStatus(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        SUBMITTED = 'submitted', 'Soumis au magasinier'
        APPLIED = 'applied', 'Validé par le magasinier'
        CANCELLED = 'cancelled', 'Annulé'

    equipment = models.ForeignKey(Equipment, related_name='user_inventories', on_delete=models.PROTECT)
    loan = models.ForeignKey(Loan, related_name='user_inventories', on_delete=models.CASCADE, null=True, blank=True)
    borrower = models.ForeignKey(Person, related_name='user_inventories', on_delete=models.PROTECT)
    inventory_type = models.CharField(max_length=10, choices=InventoryType.choices)
    status = models.CharField(max_length=20, choices=InventoryStatus.choices, default=InventoryStatus.SUBMITTED)
    submitted_at = models.DateTimeField(default=timezone.now)
    global_condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment = models.TextField(blank=True)
    applied_by = models.ForeignKey(Person, related_name='applied_user_inventories', on_delete=models.SET_NULL, null=True, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Inventaire utilisateur'
        verbose_name_plural = 'Inventaires utilisateurs'

    def __str__(self):
        return f'{self.equipment.code} — {self.get_inventory_type_display()} — {self.borrower.code} — {self.get_status_display()}'


class UserInventoryItem(TimeStampedModel):
    inventory = models.ForeignKey(UserInventory, related_name='items', on_delete=models.CASCADE)
    component = models.ForeignKey(Component, on_delete=models.PROTECT)
    present = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=1)
    condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['component__sort_order', 'component__name']
        unique_together = [('inventory', 'component')]
        verbose_name = 'Ligne inventaire utilisateur'
        verbose_name_plural = 'Lignes inventaires utilisateurs'

    def __str__(self):
        return f'{self.inventory_id} / {self.component.name}'




class LockerSettings(TimeStampedModel):
    """Paramètres globaux du module armoires sécurisées.
    Un seul enregistrement est attendu ; l'administration Django permet de l'activer/désactiver.
    """
    module_enabled = models.BooleanField(default=False, verbose_name='Module armoires sécurisées actif')
    require_authorized_terminal = models.BooleanField(default=True, verbose_name='Exiger un terminal autorisé')
    require_allowed_public_ip = models.BooleanField(default=True, verbose_name='Exiger une IP publique autorisée')
    allowed_public_ips = models.TextField(blank=True, help_text='IP publiques autorisées, une par ligne ou séparées par des virgules. Exemple : 82.120.45.18')
    allow_superadmin_force_without_terminal = models.BooleanField(default=False, verbose_name='Autoriser le forçage super admin sans terminal autorisé')
    allow_superadmin_force_without_ip = models.BooleanField(default=False, verbose_name='Autoriser le forçage super admin hors IP autorisée')
    script_timeout_seconds = models.PositiveSmallIntegerField(default=5, validators=[MinValueValidator(1)], help_text='Temps maximum d’attente du script d’ouverture casier')

    class Meta:
        verbose_name = 'Paramètres armoires sécurisées'
        verbose_name_plural = 'Paramètres armoires sécurisées'

    def __str__(self):
        return 'Paramètres armoires sécurisées'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def allowed_ip_set(self):
        raw = (self.allowed_public_ips or '').replace(';', ',').replace('\n', ',')
        return {item.strip() for item in raw.split(',') if item.strip()}


class AuthorizedTerminal(TimeStampedModel):
    class TerminalType(models.TextChoices):
        TABLET = 'tablet', 'Tablette'
        PC = 'pc', 'PC'
        DISPLAY = 'display', 'Affichage dynamique'
        OTHER = 'other', 'Autre'

    name = models.CharField(max_length=120)
    terminal_type = models.CharField(max_length=20, choices=TerminalType.choices, default=TerminalType.TABLET)
    token = models.CharField(max_length=128, unique=True)
    can_open_lockers = models.BooleanField(default=False, verbose_name='Autorisé à ouvrir les casiers')
    active = models.BooleanField('Actif', default=True)
    created_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='terminals_created')
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_ip = models.CharField(max_length=80, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Terminal autorisé'
        verbose_name_plural = 'Terminaux autorisés'

    def __str__(self):
        return f'{self.name} — {self.get_terminal_type_display()}'


class LockerOpenLog(TimeStampedModel):
    class Context(models.TextChoices):
        CHECKOUT = 'checkout', 'Sortie'
        RETURN = 'return', 'Retour'
        MAINTENANCE = 'maintenance', 'Maintenance / contrôle'
        FORCE = 'force', 'Forçage super admin'
        DETAIL = 'detail', 'Fiche matériel'

    equipment = models.ForeignKey(Equipment, on_delete=models.SET_NULL, null=True, blank=True, related_name='locker_logs')
    storekeeper = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='locker_open_logs')
    terminal = models.ForeignKey(AuthorizedTerminal, on_delete=models.SET_NULL, null=True, blank=True, related_name='locker_open_logs')
    cabinet = models.CharField(max_length=50)
    locker = models.CharField(max_length=50)
    context = models.CharField(max_length=30, choices=Context.choices, default=Context.DETAIL)
    success = models.BooleanField(default=False)
    refused = models.BooleanField(default=False)
    refusal_reason = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    controller_response = models.TextField(blank=True)
    client_ip = models.CharField(max_length=80, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Journal ouverture casier'
        verbose_name_plural = 'Journal ouvertures casiers'

    def __str__(self):
        status = 'OK' if self.success else 'REFUS' if self.refused else 'ERREUR'
        return f'{self.created_at:%d/%m/%Y %H:%M:%S} — {self.cabinet}/{self.locker} — {status}'


class InterventionLog(TimeStampedModel):
    class InterventionType(models.TextChoices):
        CONTROL = 'control', 'Contrôle'
        CLEANING = 'cleaning', 'Nettoyage'
        PERIODIC_CHECK = 'periodic_check', 'Vérification périodique'
        RECONDITIONING = 'reconditioning', 'Reconditionnement'
        ACCESSORY_CHECK = 'accessory_check', 'Contrôle accessoires'
        FUNCTIONAL_TEST = 'functional_test', 'Test fonctionnement'
        LIGHT_MAINTENANCE = 'light_maintenance', 'Maintenance légère'
        OTHER = 'other', 'Autre'

    class Result(models.TextChoices):
        NO_ISSUE = 'no_issue', 'RAS'
        WATCH = 'watch', 'À surveiller'
        AVAILABLE = 'available', 'Matériel disponible'
        INCOMPLETE = 'incomplete', 'Matériel incomplet'
        SEND_MAINTENANCE = 'send_maintenance', 'Envoyer en maintenance'
        OUT_OF_SERVICE = 'out_of_service', 'Hors service'

    equipment = models.ForeignKey(Equipment, related_name='interventions', on_delete=models.PROTECT)
    storekeeper = models.ForeignKey(Person, related_name='interventions_done', on_delete=models.PROTECT)
    intervention_at = models.DateTimeField(default=timezone.now)
    intervention_type = models.CharField(max_length=40, choices=InterventionType.choices, default=InterventionType.CONTROL)
    finding = models.TextField(blank=True, verbose_name='Constat')
    action_done = models.TextField(blank=True, verbose_name='Action réalisée')
    result = models.CharField(max_length=40, choices=Result.choices, default=Result.NO_ISSUE)
    resulting_condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment = models.TextField(blank=True, verbose_name='Commentaire bon d’intervention')

    class Meta:
        ordering = ['-intervention_at']
        verbose_name = 'Bon d’intervention'
        verbose_name_plural = 'Bons d’intervention'

    def __str__(self):
        return f'{self.equipment.code} — {self.get_intervention_type_display()} — {self.intervention_at:%d/%m/%Y %H:%M}'

    @property
    def target_status(self):
        mapping = {
            self.Result.NO_ISSUE: self.equipment.status,
            self.Result.WATCH: self.equipment.status,
            self.Result.AVAILABLE: Equipment.Status.AVAILABLE,
            self.Result.INCOMPLETE: Equipment.Status.INCOMPLETE,
            self.Result.SEND_MAINTENANCE: Equipment.Status.MAINTENANCE,
            self.Result.OUT_OF_SERVICE: Equipment.Status.OUT_OF_SERVICE,
        }
        return mapping.get(self.result, self.equipment.status)



class RepairLog(TimeStampedModel):
    class RepairType(models.TextChoices):
        TROUBLESHOOTING = 'troubleshooting', 'Dépannage'
        CONTROL = 'control', 'Contrôle'
        ACCESSORY_REPLACEMENT = 'accessory_replacement', 'Remplacement accessoire'
        CLEANING = 'cleaning', 'Nettoyage / remise en état'
        POST_ANOMALY_CHECK = 'post_anomaly_check', 'Vérification après anomalie'
        OTHER = 'other', 'Autre'

    class Result(models.TextChoices):
        REPAIRED_AVAILABLE = 'repaired_available', 'Dépanné et disponible'
        STILL_MAINTENANCE = 'still_maintenance', 'Toujours en maintenance'
        INCOMPLETE = 'incomplete', 'Incomplet'
        OUT_OF_SERVICE = 'out_of_service', 'Hors service'

    equipment = models.ForeignKey(Equipment, related_name='repairs', on_delete=models.PROTECT)
    storekeeper = models.ForeignKey(Person, related_name='repairs_done', on_delete=models.PROTECT)
    repaired_at = models.DateTimeField(default=timezone.now)
    repair_type = models.CharField(max_length=40, choices=RepairType.choices, default=RepairType.TROUBLESHOOTING)
    diagnosis = models.TextField(blank=True, verbose_name='Diagnostic / constat')
    action_done = models.TextField(blank=True, verbose_name='Action réalisée')
    parts_replaced = models.TextField(blank=True, verbose_name='Pièces ou composants remplacés')
    result = models.CharField(max_length=40, choices=Result.choices, default=Result.REPAIRED_AVAILABLE)
    resulting_condition = models.CharField(max_length=30, choices=Equipment.Condition.choices, default=Equipment.Condition.GOOD)
    comment = models.TextField(blank=True, verbose_name='Commentaire bon de réparation')

    class Meta:
        ordering = ['-repaired_at']
        verbose_name = 'Bon de réparation'
        verbose_name_plural = 'Bons de réparation'

    def __str__(self):
        return f'{self.equipment.code} — {self.get_result_display()} — {self.repaired_at:%d/%m/%Y %H:%M}'

    @property
    def target_status(self):
        mapping = {
            self.Result.REPAIRED_AVAILABLE: Equipment.Status.AVAILABLE,
            self.Result.STILL_MAINTENANCE: Equipment.Status.MAINTENANCE,
            self.Result.INCOMPLETE: Equipment.Status.INCOMPLETE,
            self.Result.OUT_OF_SERVICE: Equipment.Status.OUT_OF_SERVICE,
        }
        return mapping.get(self.result, Equipment.Status.MAINTENANCE)


class MaterialEditGrant(TimeStampedModel):
    """Droits ponctuels accordés par un prof à une formation/classe/groupe pour modifier la base matériel."""
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_edit_grants')
    class_name = models.CharField('Classe', max_length=80, blank=True)
    group_name = models.CharField('Groupe', max_length=80, blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField('Actif', default=True)

    can_create_equipment = models.BooleanField(default=False, verbose_name='Créer matériel')
    can_edit_equipment = models.BooleanField(default=False, verbose_name='Modifier fiche matériel')
    can_add_photo = models.BooleanField(default=False, verbose_name='Ajouter / modifier photo')
    can_add_document = models.BooleanField(default=False, verbose_name='Ajouter document')
    can_edit_components = models.BooleanField(default=False, verbose_name='Modifier composants')
    can_edit_location = models.BooleanField(default=False, verbose_name='Modifier emplacement')
    can_edit_description = models.BooleanField(default=False, verbose_name='Modifier descriptif')
    can_generate_qr = models.BooleanField(default=False, verbose_name='Générer QR')

    granted_by = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True, related_name='material_grants_given')
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_date', 'formation__code', 'class_name', 'group_name']
        verbose_name = 'Droit ponctuel matériel'
        verbose_name_plural = 'Droits ponctuels matériel'

    def __str__(self):
        cible = self.formation.code if self.formation else 'Toutes formations'
        if self.class_name:
            cible += f' / {self.class_name}'
        if self.group_name:
            cible += f' / {self.group_name}'
        return f'{cible} — {self.start_date} → {self.end_date or "sans fin"}'

    def is_current(self, today=None):
        today = today or timezone.localdate()
        return self.active and self.start_date <= today and (self.end_date is None or today <= self.end_date)

    def applies_to(self, person):
        if not person or not self.is_current():
            return False
        if self.formation_id and person.formation_id != self.formation_id:
            return False
        if self.class_name and (person.class_name or '').strip().lower() != self.class_name.strip().lower():
            return False
        if self.group_name and (person.group_name or '').strip().lower() != self.group_name.strip().lower():
            return False
        return True


class Competence(TimeStampedModel):
    class LevelScale(models.TextChoices):
        ZERO_TO_FOUR = '0_4', 'Échelle 0 à 4'

    formation = models.ForeignKey(Formation, related_name='competences', on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=220)
    block = models.CharField(max_length=160, blank=True)
    unit = models.CharField(max_length=80, blank=True)
    description = models.TextField('Description', blank=True)
    active = models.BooleanField('Actif', default=True)

    class Meta:
        ordering = ['formation__code', 'code']
        unique_together = [('formation', 'code')]
        verbose_name = 'Compétence référentiel'
        verbose_name_plural = 'Compétences référentiel'

    def __str__(self):
        return f'{self.formation.code} — {self.code} — {self.title}'


class PedagogicalSession(TimeStampedModel):
    title = models.CharField(max_length=220)
    date = models.DateField(default=timezone.localdate)
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    class_name = models.CharField('Classe', max_length=80, blank=True)
    group_name = models.CharField('Groupe', max_length=80, blank=True)
    school_year = models.CharField(max_length=20, blank=True)
    objectives = models.TextField(blank=True)
    targeted_competences = models.ManyToManyField(Competence, blank=True, related_name='targeted_sessions')
    active = models.BooleanField('Actif', default=True)

    class Meta:
        ordering = ['-date', 'title']
        verbose_name = 'Séance pédagogique'
        verbose_name_plural = 'Séances pédagogiques'

    def __str__(self):
        return f'{self.date:%d/%m/%Y} — {self.title}'


class SessionRoleAssignment(TimeStampedModel):
    session = models.ForeignKey(PedagogicalSession, related_name='assignments', on_delete=models.CASCADE)
    person = models.ForeignKey(Person, related_name='session_assignments', on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=Person.Role.choices, default=Person.Role.USER)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['session', 'person__last_name', 'person__first_name']
        unique_together = [('session', 'person', 'role')]
        verbose_name = 'Affectation de rôle séance'
        verbose_name_plural = 'Affectations de rôles séance'

    def __str__(self):
        return f'{self.session} — {self.person} — {self.get_role_display()}'


class CompetenceMapping(TimeStampedModel):
    class ActionType(models.TextChoices):
        CHECKOUT = 'checkout', 'Sortie matériel'
        RETURN = 'return', 'Retour matériel'
        INVENTORY_OUT = 'inventory_out', 'Inventaire sortie kit'
        INVENTORY_RETURN = 'inventory_return', 'Inventaire retour kit'
        USER_INVENTORY_OUT = 'user_inventory_out', 'Inventaire utilisateur sortie'
        USER_INVENTORY_RETURN = 'user_inventory_return', 'Inventaire utilisateur retour'
        EQUIPMENT_CREATE = 'equipment_create', 'Création fiche matériel'
        EQUIPMENT_UPDATE = 'equipment_update', 'Modification fiche matériel'
        USER_MANAGEMENT = 'user_management', 'Gestion utilisateurs'
        PROMOTION = 'promotion', 'Montée pédagogique'

    formation = models.ForeignKey(Formation, related_name='competence_mappings', on_delete=models.CASCADE)
    action_type = models.CharField(max_length=40, choices=ActionType.choices)
    role = models.CharField(max_length=30, choices=Person.Role.choices, blank=True)
    competence = models.ForeignKey(Competence, related_name='mappings', on_delete=models.CASCADE)
    weight = models.PositiveSmallIntegerField(default=1)
    criterion = models.CharField(max_length=255, blank=True)
    active = models.BooleanField('Actif', default=True)

    class Meta:
        ordering = ['formation__code', 'action_type', 'role', 'competence__code']
        unique_together = [('formation', 'action_type', 'role', 'competence')]
        verbose_name = 'Correspondance action-compétence'
        verbose_name_plural = 'Correspondances actions-compétences'

    def __str__(self):
        role = f' / {self.get_role_display()}' if self.role else ''
        return f'{self.formation.code} — {self.get_action_type_display()}{role} → {self.competence.code}'


class EvaluationRecord(TimeStampedModel):
    class Source(models.TextChoices):
        AUTO = 'auto', 'Proposition automatique'
        TEACHER = 'teacher', 'Validation professeur'

    session = models.ForeignKey(PedagogicalSession, related_name='evaluations', on_delete=models.CASCADE, null=True, blank=True)
    person = models.ForeignKey(Person, related_name='evaluations', on_delete=models.CASCADE)
    competence = models.ForeignKey(Competence, related_name='evaluations', on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=Person.Role.choices, blank=True)
    proposed_level = models.PositiveSmallIntegerField(default=0)
    validated_level = models.PositiveSmallIntegerField(null=True, blank=True)
    evidence_count = models.PositiveIntegerField(default=0)
    comment = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.AUTO)
    validated_by = models.ForeignKey(Person, related_name='validated_evaluations', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('session', 'person', 'competence', 'role')]
        verbose_name = 'Évaluation compétence'
        verbose_name_plural = 'Évaluations compétences'

    def __str__(self):
        return f'{self.person.code} — {self.competence.code} — proposé {self.proposed_level}'
