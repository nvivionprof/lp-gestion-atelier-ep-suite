from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import re
import unicodedata


def normalize_code(value, default='CODE', max_len=64):
    value = value or default
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^A-Za-z0-9]+', '_', value).strip('_').upper()
    return (value or default)[:max_len]


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class CoreFormation(TimeStampedModel):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=160)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ['code']
    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.name, 'FORMATION')
        super().save(*args, **kwargs)
    def __str__(self):
        return f'{self.code} — {self.name}'


class CoreClass(TimeStampedModel):
    formation = models.ForeignKey(CoreFormation, on_delete=models.SET_NULL, null=True, blank=True, related_name='classes')
    name = models.CharField(max_length=80)
    school_year = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)
    class Meta:
        ordering = ['formation__code', 'name']
        unique_together = [('formation', 'name', 'school_year')]
    def __str__(self):
        return f'{self.formation.code if self.formation else "GEN"} — {self.name}'


class CoreWorkshopZone(TimeStampedModel):
    """Zone atelier centrale, synchronisable vers les modules qui l'utilisent."""
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['order', 'code']
        verbose_name = 'zone atelier centrale'
        verbose_name_plural = 'zones atelier centrales'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.name, 'ZONE')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.name}'


class CoreWorkshopSubZone(TimeStampedModel):
    """Sous-zone atelier centrale rattachée à une zone LP Core."""
    zone = models.ForeignKey(CoreWorkshopZone, on_delete=models.CASCADE, related_name='subzones')
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['zone__code', 'order', 'code']
        unique_together = [('zone', 'code')]
        verbose_name = 'sous-zone atelier centrale'
        verbose_name_plural = 'sous-zones atelier centrales'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.name, 'SOUS_ZONE')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.zone.code} / {self.code} — {self.name}'


class CoreUser(TimeStampedModel):
    ROLE_CHOICES = [
        ('utilisateur', 'Utilisateur'),
        ('eleve', 'Élève'),
        ('magasinier', 'Magasinier'),
        ('professeur', 'Professeur'),
        ('responsable', 'Responsable'),
        ('admin', 'Administrateur'),
        ('lecture_seule', 'Lecture seule'),
    ]
    code = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=120, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    formation = models.ForeignKey(CoreFormation, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    class_name = models.CharField(max_length=80, blank=True)
    group_name = models.CharField(max_length=80, blank=True)
    role_principal = models.CharField(max_length=50, choices=ROLE_CHOICES, default='utilisateur')
    rights = models.TextField(blank=True, help_text='Droits séparés par ;')
    active = models.BooleanField(default=True)
    school_year = models.CharField(max_length=20, blank=True)
    password_hash = models.CharField(max_length=255, blank=True)
    initial_password_for_sync = models.CharField(max_length=80, blank=True, help_text='Mot de passe initial, réservé à la synchronisation locale')
    force_password_change = models.BooleanField(default=False, help_text='Oblige l’utilisateur à changer son mot de passe à la prochaine connexion LP Core.')
    source = models.CharField(max_length=80, blank=True, default='manual')

    IMAGE_CONSENT_CHOICES = [
        ('unknown', 'Non renseigné'),
        ('authorized', 'Autorisation image accordée'),
        ('refused', 'Opposition / refus de diffusion'),
    ]
    personal_email = models.EmailField(blank=True, help_text='Email personnel, facultatif, utile pour PFMP / stage.')
    personal_phone = models.CharField(max_length=40, blank=True, help_text='Téléphone personnel, facultatif.')
    identity_photo = models.FileField(upload_to='core/users/photos/', null=True, blank=True)
    image_consent_status = models.CharField(max_length=20, choices=IMAGE_CONSENT_CHOICES, default='unknown')
    image_consent_comment = models.CharField(max_length=255, blank=True)
    parent_image_opposition = models.BooleanField(default=False, help_text='Pour mineur : opposition parentale ou absence d’autorisation écrite.')
    personal_upload_blocked = models.BooleanField(default=False, help_text='Bloque les ajouts de photo/documents personnels par l’utilisateur.')


    class Meta:
        ordering = ['last_name', 'first_name']

    def save(self, *args, **kwargs):
        if not self.code:
            base = f'{self.last_name[:3]}_{self.first_name[:3]}' or self.username
            self.code = normalize_code(base, 'USER')
        if not self.username:
            self.username = self.code
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        if raw_password:
            self.password_hash = make_password(str(raw_password))

    def check_password(self, raw_password):
        return bool(self.password_hash and check_password(str(raw_password), self.password_hash))

    def rights_list(self):
        return [r.strip() for r in (self.rights or '').split(';') if r.strip()]

    def display_photo_allowed(self):
        return bool(self.identity_photo and self.image_consent_status == 'authorized' and not self.parent_image_opposition)

    def image_placeholder_text(self):
        if self.parent_image_opposition or self.image_consent_status == 'refused':
            return "L'utilisateur n'a pas souhaité diffuser son image."
        if not self.identity_photo:
            return "Aucune photo d'identité fournie."
        if self.image_consent_status == 'unknown':
            return "Photo présente, mais profil RGPD non renseigné."
        return "Photo non diffusée."

    @property
    def is_admin_like(self):
        return self.role_principal in {'admin', 'responsable', 'professeur'} or 'CORE_ADMIN' in self.rights_list()

    def __str__(self):
        return f'{self.first_name} {self.last_name} — {self.class_name}'



class CoreModuleAccessRule(TimeStampedModel):
    """Règle de visibilité des modules dans le portail LP Core."""
    MODULE_CHOICES = [
        ('toolmag', 'ToolMag'),
        ('safety', 'Safety Manager'),
        ('pedashop', 'PedaShop'),
        ('system', 'System Manager'),
        ('tpmanager', 'TP Manager'),
        ('lpdisplaymanager', 'LP Display Manager'),
    ]
    TARGET_CHOICES = [
        ('role', 'Fonction / rôle'),
        ('class', 'Classe'),
        ('formation', 'Formation'),
        ('group', 'Groupe'),
        ('user', 'Utilisateur / élève'),
        ('right', 'Droit LP Core'),
    ]
    module = models.CharField(max_length=40, choices=MODULE_CHOICES)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    target_value = models.CharField(max_length=120, help_text='Valeur exacte : eleve, 1MELEC, MELEC, groupe A, USR-0001, TOOLMAG_VIEW...')
    active = models.BooleanField(default=True)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['module', 'target_type', 'target_value']
        unique_together = [('module', 'target_type', 'target_value')]
        verbose_name = 'Règle accès module'
        verbose_name_plural = 'Règles accès modules'

    def save(self, *args, **kwargs):
        self.target_value = (self.target_value or '').strip()
        if self.target_type in {'formation', 'right'}:
            self.target_value = normalize_code(self.target_value, self.target_type.upper())
        super().save(*args, **kwargs)

    def matches(self, user):
        if not user or not self.active:
            return False
        value = (self.target_value or '').strip()
        if not value:
            return False
        if self.target_type == 'role':
            return user.role_principal == value
        if self.target_type == 'class':
            return (user.class_name or '').strip().lower() == value.lower()
        if self.target_type == 'formation':
            return bool(user.formation and user.formation.code == value)
        if self.target_type == 'group':
            return (user.group_name or '').strip().lower() == value.lower()
        if self.target_type == 'user':
            return value.lower() in {(user.code or '').lower(), (user.username or '').lower(), str(user.pk)}
        if self.target_type == 'right':
            return value in user.rights_list()
        return False

    def __str__(self):
        return f'{self.get_module_display()} — {self.get_target_type_display()} : {self.target_value}'


class CoreAuditLog(TimeStampedModel):
    actor = models.ForeignKey(CoreUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    action = models.CharField(max_length=200)
    target = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    class Meta:
        ordering = ['-created_at']



class CoreStore(TimeStampedModel):
    """Magasin métier connu par LP Core.

    LP Core ne gère pas le stock, mais il porte les droits d'accès aux
    magasins afin que PedaShop, ToolMag ou les modules futurs puissent filtrer
    les données visibles par utilisateur. Le code doit correspondre au code du
    magasin dans le module métier.
    """
    MODULE_CHOICES = [
        ('global', 'Tous modules'),
        ('pedashop', 'PedaShop'),
        ('toolmag', 'ToolMag'),
        ('safety', 'Safety Manager'),
        ('system', 'System Manager'),
        ('tpmanager', 'TP Manager'),
        ('other', 'Autre'),
    ]
    code = models.CharField(max_length=60)
    nom = models.CharField(max_length=160)
    module = models.CharField(max_length=40, choices=MODULE_CHOICES, default='global')
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['module', 'code']
        unique_together = [('module', 'code')]

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.nom, 'MAGASIN')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.module} — {self.code} — {self.nom}'


class CoreUserStoreAccess(TimeStampedModel):
    """Affectation d'un magasin visible à un utilisateur LP Core."""
    user = models.ForeignKey(CoreUser, on_delete=models.CASCADE, related_name='store_accesses')
    store = models.ForeignKey(CoreStore, on_delete=models.CASCADE, related_name='user_accesses')
    active = models.BooleanField(default=True)
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['user__last_name', 'store__module', 'store__code']
        unique_together = [('user', 'store')]

    def __str__(self):
        return f'{self.user.code} → {self.store.code}'


class CoreCertification(TimeStampedModel):
    """Certification, habilitation ou autorisation portée par LP Core.

    Les modules consomment ensuite ces données : Safety pour les SST du jour,
    PedaShop pour les droits magasin, ToolMag pour les autorisations liées au
    matériel, etc.
    """
    TYPE_CHOICES = [
        ('SST', 'SST'),
        ('HABILITATION_ELEC', 'Habilitation électrique'),
        ('B0', 'B0'), ('B1V', 'B1V'), ('BR', 'BR'), ('BC', 'BC'),
        ('R407', 'R407'), ('R408', 'R408'),
        ('CACES', 'CACES'),
        ('TRAVAIL_HAUTEUR', 'Travail en hauteur'),
        ('ECHAF', 'Échafaudage'),
        ('FLUIDE_FRIGO', 'Fluide frigorigène'),
        ('AUTRE', 'Autre'),
    ]
    user = models.ForeignKey(CoreUser, on_delete=models.CASCADE, related_name='certifications')
    type_certification = models.CharField(max_length=80, choices=TYPE_CHOICES)
    niveau = models.CharField(max_length=120, blank=True)
    date_obtention = models.DateField(null=True, blank=True)
    date_fin_validite = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    document = models.FileField(upload_to='core/certifications/', null=True, blank=True)
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['user__last_name', 'type_certification', '-date_fin_validite']

    def __str__(self):
        suffix = f' — {self.niveau}' if self.niveau else ''
        return f'{self.user.code} — {self.type_certification}{suffix}'



class CoreRightDefinition(TimeStampedModel):
    """Droit déclaratif visible dans LP Core et utilisable par les modules.

    Les droits fins restent gérés dans les modules, mais LP Core peut lister,
    cocher et synchroniser les droits communs ou transversaux.
    """
    MODULE_CHOICES = [
        ('core', 'LP Core'),
        ('toolmag', 'ToolMag'),
        ('safety', 'Safety Manager'),
        ('pedashop', 'PedaShop'),
        ('system', 'System Manager'),
        ('tpmanager', 'TP Manager'),
        ('global', 'Transversal'),
    ]
    code = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=160)
    module = models.CharField(max_length=40, choices=MODULE_CHOICES, default='global')
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['module', 'code']

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.label, 'DROIT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.module} — {self.code}'


class CoreCertificationType(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.label, 'CERTIFICATION')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.label


class CoreUserDocument(TimeStampedModel):
    DOC_TYPE_CHOICES = [
        ('cv', 'CV'),
        ('lettre_motivation', 'Lettre de motivation'),
        ('attestation', 'Attestation'),
        ('autorisation_image', 'Autorisation image'),
        ('pfmp', 'Document PFMP'),
        ('autre', 'Autre'),
    ]
    user = models.ForeignKey(CoreUser, on_delete=models.CASCADE, related_name='personal_documents')
    type_document = models.CharField(max_length=40, choices=DOC_TYPE_CHOICES, default='autre')
    title = models.CharField(max_length=180)
    file = models.FileField(upload_to='core/users/documents/')
    visible_to_prof = models.BooleanField(default=True)
    visible_to_admin = models.BooleanField(default=True)
    expires_at = models.DateField(null=True, blank=True)
    uploaded_by = models.ForeignKey(CoreUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.code} — {self.title}'


class RgpdPolicySettings(TimeStampedModel):
    """Paramètres RGPD opérationnels de la suite."""
    technical_logs_retention = models.CharField(max_length=120, default='90 jours')
    backup_retention_days = models.PositiveIntegerField(default=7)
    certification_support_note = models.TextField(default='Les sauvegardes automatiques sont conservées par défaut 7 jours glissants. Les sauvegardes manuelles et pré-mise-à-jour sont conservées sans suppression automatique, sauf action volontaire d’un administrateur.')
    photo_purpose = models.TextField(default='Photo facultative utilisée pour l’identification interne et l’édition d’attestations, notamment habilitations et certifications.')
    minor_authorization_note = models.TextField(default='Pour les élèves mineurs, une autorisation écrite des représentants légaux est exigée avant toute diffusion de photo dans la suite.')

    class Meta:
        verbose_name = 'Paramètres RGPD'
        verbose_name_plural = 'Paramètres RGPD'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BackupPolicySettings(TimeStampedModel):
    """Paramètres opérationnels de sauvegarde pilotés par LP Core.

    LP Core conserve la politique métier ; le conteneur suite-backup-scheduler
    lit le fichier généré backup-policy.env pour exécuter les sauvegardes.
    Les sauvegardes manuelles et pré-mise-à-jour ne sont pas supprimées par
    la rotation automatique.
    """
    automatic_enabled = models.BooleanField(default=True)
    daily_hour = models.PositiveSmallIntegerField(default=2)
    daily_minute = models.PositiveSmallIntegerField(default=0)
    daily_retention_days = models.PositiveIntegerField(default=7)
    manual_keep_forever = models.BooleanField(default=True)
    pre_upgrade_required = models.BooleanField(default=True)
    block_update_if_backup_failed = models.BooleanField(default=True)
    web_restore_enabled = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='Sauvegarde quotidienne automatique, conservation glissante configurable. Sauvegardes manuelles et pré-mise-à-jour conservées sans suppression automatique.')

    class Meta:
        verbose_name = 'Paramètres sauvegarde'
        verbose_name_plural = 'Paramètres sauvegarde'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def clean_values(self):
        self.daily_hour = max(0, min(int(self.daily_hour or 0), 23))
        self.daily_minute = max(0, min(int(self.daily_minute or 0), 59))
        self.daily_retention_days = max(1, int(self.daily_retention_days or 7))

    def save(self, *args, **kwargs):
        self.clean_values()
        super().save(*args, **kwargs)

    def to_env_text(self):
        return '\n'.join([
            '# Généré depuis LP Core > Sauvegardes / restauration',
            f'BACKUP_ENABLED={1 if self.automatic_enabled else 0}',
            f'BACKUP_DAILY_HOUR={int(self.daily_hour):02d}',
            f'BACKUP_DAILY_MINUTE={int(self.daily_minute):02d}',
            f'BACKUP_RETENTION_DAYS={int(self.daily_retention_days)}',
            f'BACKUP_MANUAL_KEEP_FOREVER={1 if self.manual_keep_forever else 0}',
            f'BACKUP_PRE_UPGRADE_REQUIRED={1 if self.pre_upgrade_required else 0}',
            f'BACKUP_BLOCK_UPDATE_IF_BACKUP_FAILED={1 if self.block_update_if_backup_failed else 0}',
            f'BACKUP_WEB_RESTORE_ENABLED={1 if self.web_restore_enabled else 0}',
            '',
        ])

    def __str__(self):
        return f'Sauvegarde {int(self.daily_hour):02d}:{int(self.daily_minute):02d} — {self.daily_retention_days} jours'


class PublicSuiteSettings(TimeStampedModel):
    """Paramètres publics de publication de la suite.

    Cette table sert à centraliser le domaine public, le protocole
    et la méthode de validation Let's Encrypt. Elle ne remplace pas les scripts
    serveur : elle fournit la configuration métier qui sert à générer les URLs,
    les QR codes et le fichier cert-manager.env exploitable par SSH.
    """
    CHALLENGE_CHOICES = [
        ('dns_duckdns', 'DNS-01 via DuckDNS'),
        ('http_01', 'HTTP-01 via passerelle HTTP'),
    ]
    MODE_CHOICES = [
        ('local', 'Local — ce poste / localhost'),
        ('network', 'Réseau local — adresse IP ou nom DNS interne'),
        ('domain', 'Domaine extérieur — DuckDNS / nom public'),
        ('reverse_proxy', 'Ancien mode — passerelle unique / chemins publics'),
    ]
    public_domain = models.CharField(max_length=255, default='localhost:9000')
    public_scheme = models.CharField(max_length=10, choices=[('http', 'HTTP'), ('https', 'HTTPS')], default='http')
    exposure_mode = models.CharField(max_length=40, choices=MODE_CHOICES, default='local')
    local_public_host = models.CharField(max_length=255, default='localhost:9000', help_text='Adresse utilisée sur le serveur ou en test local, par exemple localhost:9000.')
    network_public_host = models.CharField(max_length=255, blank=True, default='', help_text='Adresse réseau interne, par exemple 192.168.101.19:9000 ou lp-suite.local:9000.')
    external_public_domain = models.CharField(max_length=255, blank=True, default='', help_text='Domaine extérieur, par exemple stjoseph-lpsuite.duckdns.org.')
    challenge_method = models.CharField(max_length=40, choices=CHALLENGE_CHOICES, default='dns_duckdns')
    letsencrypt_email = models.EmailField(blank=True)
    duckdns_token = models.CharField(max_length=255, blank=True, help_text='Token DuckDNS, requis uniquement pour le challenge DNS-01.')
    enable_https = models.BooleanField(default=False)
    lp_core_port = models.PositiveIntegerField(default=9000)
    toolmag_port = models.PositiveIntegerField(default=9001)
    safety_port = models.PositiveIntegerField(default=9002)
    pedashop_port = models.PositiveIntegerField(default=9003)
    system_manager_port = models.PositiveIntegerField(default=9004)
    tpmanager_port = models.PositiveIntegerField(default=9005)
    pfmp_port = models.PositiveIntegerField(default=9006)
    ssl_cert_file = models.CharField(max_length=255, default='/ssl/fullchain.pem')
    ssl_key_file = models.CharField(max_length=255, default='/ssl/privkey.pem')

    class Meta:
        verbose_name = 'Paramètres publics de la suite'
        verbose_name_plural = 'Paramètres publics de la suite'

    def __str__(self):
        return f'{self.public_scheme}://{self.public_domain} — {self.get_challenge_method_display()}'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @staticmethod
    def _clean_host(value):
        return (value or '').strip().replace('https://', '').replace('http://', '').strip('/')

    def active_mode(self):
        return self.exposure_mode if self.exposure_mode in {'local', 'network', 'domain'} else 'domain'

    def selected_host(self):
        """Hôte actif selon le mode choisi dans LP Core.

        Les modules restent derrière la même passerelle unique ; seul le point
        d'entrée change : local, réseau interne ou domaine extérieur.
        """
        mode = self.active_mode()
        if mode == 'local':
            return self._clean_host(self.local_public_host) or 'localhost:9000'
        if mode == 'network':
            return self._clean_host(self.network_public_host) or self._clean_host(self.public_domain) or 'localhost:9000'
        return self._clean_host(self.external_public_domain) or self._clean_host(self.public_domain) or 'localhost:9000'

    def _base_url(self):
        """Retourne l'URL publique active de la passerelle unique.

        Bêta 2 conserve trois profils : local, réseau interne et domaine
        extérieur. Dans tous les cas, les applications restent exposées par
        chemins : /toolmag, /safety, /pedashop, /system, /tpmanager, /pfmp.
        """
        mode = self.active_mode()
        scheme = self.public_scheme or ('https' if self.enable_https else 'http')
        if mode in {'local', 'network'} and not self.enable_https and scheme == 'https':
            scheme = 'http'
        domain = self.selected_host()
        return f'{scheme}://{domain}'.rstrip('/')

    def module_urls(self):
        """URLs publiques générées en passerelle unique.

        Toutes les applications passent par le même domaine et par des chemins
        stables : /toolmag, /safety, /pedashop, /system, /tpmanager et /pfmp.
        Les anciens ports par module sont conservés en base uniquement pour
        compatibilité historique, mais ne sont plus utilisés pour générer les
        liens internes, les QR codes ou les URLs publiques.
        """
        base = self._base_url()
        return {
            'LP_CORE_PUBLIC_URL': base,
            'TOOLMAG_PUBLIC_URL': f'{base}/toolmag',
            'TOOLMAG_PUBLIC_BASE_URL': f'{base}/toolmag',
            'SAFETY_PUBLIC_URL': f'{base}/safety',
            'PEDASHOP_PUBLIC_URL': f'{base}/pedashop',
            'CONSUMABLES_PUBLIC_URL': f'{base}/pedashop',
            'INVENTORY_PUBLIC_URL': f'{base}/system',
            'SYSTEM_MANAGER_PUBLIC_URL': f'{base}/system',
            'TPMANAGER_PUBLIC_URL': f'{base}/tpmanager',
            'PFMP_PUBLIC_URL': f'{base}/pfmp',
        }

    def csrf_origins(self):
        origins = {self._base_url(), 'http://localhost:9000', 'http://127.0.0.1:9000'}
        for host in [self.local_public_host, self.network_public_host, self.external_public_domain, self.public_domain]:
            cleaned = self._clean_host(host)
            if cleaned:
                origins.add(f'http://{cleaned}')
                origins.add(f'https://{cleaned}')
        return ','.join(sorted(origins))

    def to_env_text(self):
        active_mode = self.active_mode()
        deploy_mode = active_mode
        gateway_http = 80 if active_mode == 'domain' and self.enable_https and self.public_scheme == 'https' else self.lp_core_port
        gateway_https = 443 if active_mode == 'domain' and self.enable_https and self.public_scheme == 'https' else 9443
        lines = [
            '# Généré depuis LP Core > Paramètres publics',
            f'LP_DEPLOY_MODE={deploy_mode}',
            f'PUBLIC_DOMAIN={self.selected_host()}',
            f'PUBLIC_SCHEME={self.public_scheme}',
            f'EXPOSURE_MODE={active_mode}',
            f'LOCAL_PUBLIC_HOST={self._clean_host(self.local_public_host)}',
            f'NETWORK_PUBLIC_HOST={self._clean_host(self.network_public_host)}',
            f'EXTERNAL_PUBLIC_DOMAIN={self._clean_host(self.external_public_domain)}',
            f'ENABLE_HTTPS={1 if self.enable_https else 0}',
            f'GATEWAY_HTTP_PORT={gateway_http}',
            f'GATEWAY_HTTPS_PORT={gateway_https}',
            f'CERT_CHALLENGE_METHOD={self.challenge_method}',
            f'LETSENCRYPT_EMAIL={self.letsencrypt_email}',
            f'DUCKDNS_TOKEN={self.duckdns_token}',
            f'SSL_CERT_FILE={self.ssl_cert_file}',
            f'SSL_KEY_FILE={self.ssl_key_file}',
            f'LP_CORE_PORT={self.lp_core_port}',
            f'TOOLMAG_PORT={self.toolmag_port}',
            f'SAFETY_PORT={self.safety_port}',
            f'PEDASHOP_PORT={self.pedashop_port}',
            f'CONSUMABLES_PORT={self.pedashop_port}',
            f'INVENTORY_PORT={self.system_manager_port}',
            f'SYSTEM_MANAGER_PORT={self.system_manager_port}',
            f'TPMANAGER_PORT={self.tpmanager_port}',
            f'PFMP_PORT={self.pfmp_port}',
        ]
        for key, value in self.module_urls().items():
            lines.append(f'{key}={value}')
        allowed_hosts = ['localhost', '127.0.0.1', '*']
        for host in [self.local_public_host, self.network_public_host, self.external_public_domain, self.public_domain, self.selected_host()]:
            cleaned = self._clean_host(host)
            if cleaned:
                allowed_hosts.append(cleaned.split(':')[0])
        lines.append('DJANGO_ALLOWED_HOSTS=' + ','.join(dict.fromkeys(allowed_hosts)))
        lines.append(f'CSRF_TRUSTED_ORIGINS={self.csrf_origins()}')
        lines.append(f'SESSION_COOKIE_SECURE={1 if self.enable_https else 0}')
        lines.append(f'CSRF_COOKIE_SECURE={1 if self.enable_https else 0}')
        return '\n'.join(lines) + '\n'

class UploadedUpdatePackage(TimeStampedModel):
    """Paquet ZIP de mise à jour déposé depuis LP Core.

    Le fichier reste dans /data/lp-core/updates/incoming et peut ensuite être
    installé par suite-admin-agent. Les données de production ne sont jamais
    stockées dans le ZIP : seules les sources applicatives sont remplacées.
    """
    STATUS_CHOICES = [
        ('uploaded', 'Déposé'),
        ('analyzed', 'Analysé'),
        ('invalid', 'Invalide'),
        ('installing', 'Installation en cours'),
        ('installed', 'Installé'),
        ('failed', 'Échec'),
    ]
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255, unique=True)
    stored_path = models.CharField(max_length=500)
    sha256 = models.CharField(max_length=64, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    detected_version = models.CharField(max_length=80, blank=True)
    manifest = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='uploaded')
    analysis_report = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(CoreUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.original_filename} — {self.detected_version or self.status}'


class SuiteMaintenanceJob(TimeStampedModel):
    """Action serveur demandée depuis LP Core et exécutée par suite-admin-agent."""
    ACTION_CHOICES = [
        ('apply_public_settings', 'Appliquer URLs / HTTPS'),
        ('issue_cert', 'Générer certificat'),
        ('renew_cert', 'Renouveler certificat'),
        ('cert_status', 'État certificat'),
        ('restart_services', 'Redémarrer services'),
        ('migrate_all', 'Lancer migrations'),
        ('backup_all', 'Sauvegarde historique'),
        ('full_backup', 'Sauvegarde complète de reprise'),
        ('restore_full_backup', 'Restauration complète après crash'),
        ('restore_existing_backup', 'Restaurer sauvegarde serveur'),
        ('backup_database', 'Sauvegarde base module/totale'),
        ('restore_database_backup', 'Restauration base module/totale'),
        ('install_update', 'Installer mise à jour ZIP'),
    ]
    STATUS_CHOICES = [
        ('requested', 'Demandée'),
        ('running', 'En cours'),
        ('success', 'Terminée'),
        ('failed', 'Échec'),
        ('unknown', 'Inconnu'),
    ]
    action = models.CharField(max_length=80, choices=ACTION_CHOICES)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='requested')
    agent_job_id = models.CharField(max_length=120, blank=True)
    package = models.ForeignKey(UploadedUpdatePackage, on_delete=models.SET_NULL, null=True, blank=True, related_name='jobs')
    requested_by = models.ForeignKey(CoreUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    result_message = models.TextField(blank=True)
    log_tail = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.status} — {self.agent_job_id}'


class CoreAtelierBlock(TimeStampedModel):
    """Bloc atelier commun à LP Core, Sequence Manager et System Manager."""
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    # Conservé pour compatibilité, mais l'association métier prioritaire se fait par classes.
    formations = models.ManyToManyField(CoreFormation, blank=True, related_name='atelier_blocks')
    classes = models.ManyToManyField(CoreClass, blank=True, related_name='atelier_blocks')
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'bloc atelier'
        verbose_name_plural = 'blocs atelier'

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code or self.name, 'BLOC_ATELIER', 80)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.name}'


class CoreAtelierBlockSlot(TimeStampedModel):
    DAY_CHOICES = [(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi')]
    block = models.ForeignKey(CoreAtelierBlock, on_delete=models.CASCADE, related_name='slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    label = models.CharField(max_length=120, blank=True, help_text='Ex. lundi matin, jeudi après-midi')
    start_time = models.TimeField()
    end_time = models.TimeField()
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['block__code', 'day_of_week', 'start_time']
        unique_together = [('block', 'day_of_week', 'start_time', 'end_time')]
        verbose_name = 'créneau bloc atelier'
        verbose_name_plural = 'créneaux blocs atelier'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('L’heure de fin doit être postérieure à l’heure de début.')

    def __str__(self):
        return f'{self.block.code} — {self.get_day_of_week_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}'
