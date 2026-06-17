from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


def norm(value, default='', max_len=80):
    value = (value or default or '').strip()
    return value[:max_len]


class Formation(models.Model):
    core_formation_id = models.IntegerField(null=True, blank=True, unique=True)
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=160)
    active = models.BooleanField(default=True)
    def __str__(self): return self.nom or self.code


class PfmpUser(models.Model):
    ROLE_CHOICES=[('eleve','Élève'),('utilisateur','Utilisateur'),('magasinier','Magasinier'),('professeur','Professeur'),('responsable','Responsable'),('admin','Administrateur')]
    core_user_id=models.IntegerField(null=True, blank=True, unique=True)
    code=models.CharField(max_length=40, db_index=True)
    username=models.CharField(max_length=80, unique=True)
    first_name=models.CharField(max_length=80, blank=True)
    last_name=models.CharField(max_length=80, blank=True)
    email=models.EmailField(blank=True)
    formation_code=models.CharField(max_length=40, blank=True)
    formation_name=models.CharField(max_length=160, blank=True)
    class_name=models.CharField(max_length=80, blank=True)
    group_name=models.CharField(max_length=80, blank=True)
    role_principal=models.CharField(max_length=30, choices=ROLE_CHOICES, default='utilisateur')
    rights=models.TextField(blank=True)
    active=models.BooleanField(default=True)
    school_year=models.CharField(max_length=20, blank=True)
    password=models.CharField(max_length=160, blank=True)
    # Champs optionnels utilisés pour la recherche de proximité élève.
    address=models.CharField(max_length=240, blank=True)
    postal_code=models.CharField(max_length=20, blank=True)
    city=models.CharField(max_length=120, blank=True)
    latitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    synced_at=models.DateTimeField(null=True, blank=True)
    def set_password(self, raw): self.password=make_password(raw)
    def check_password(self, raw): return check_password(raw, self.password)
    @property
    def full_name(self): return (f'{self.first_name} {self.last_name}'.strip() or self.username)
    @property
    def is_prof_like(self): return self.role_principal in {'professeur','responsable','admin'} or 'PFMP_ADMIN' in (self.rights or '') or 'PFMP_PROF' in (self.rights or '')
    @property
    def is_admin_like(self): return self.role_principal in {'responsable','admin'} or 'PFMP_ADMIN' in (self.rights or '')
    def __str__(self): return f'{self.code} — {self.full_name}'


class CompanyTag(models.Model):
    CATEGORY=[('activite','Activité'),('formation','Formation'),('statut','Statut'),('recherche','Recherche'),('autre','Autre')]
    code=models.CharField(max_length=80, unique=True)
    label=models.CharField(max_length=140)
    category=models.CharField(max_length=30, choices=CATEGORY, default='autre')
    active=models.BooleanField(default=True)
    def __str__(self): return self.label


class ImportBatch(models.Model):
    MODE=[('simulation','Simulation'),('append_only','Ajout uniquement'),('upsert','Ajout / modification'),('replace_all','Remplacement total'),('delete_all_then_import','Suppression totale puis import')]
    KEY=[('code_entreprise','Code entreprise'),('siret','SIRET'),('nom_code_postal_ville','Nom + CP + ville')]
    file_name=models.CharField(max_length=240)
    mode=models.CharField(max_length=40, choices=MODE)
    key_strategy=models.CharField(max_length=60, choices=KEY, default='code_entreprise')
    started_at=models.DateTimeField(auto_now_add=True)
    finished_at=models.DateTimeField(null=True, blank=True)
    created_count=models.PositiveIntegerField(default=0)
    updated_count=models.PositiveIntegerField(default=0)
    deleted_count=models.PositiveIntegerField(default=0)
    ignored_count=models.PositiveIntegerField(default=0)
    error_count=models.PositiveIntegerField(default=0)
    report_json=models.JSONField(default=dict, blank=True)
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self): return f'{self.file_name} — {self.mode} — {self.started_at:%Y-%m-%d %H:%M}'


class Company(models.Model):
    STATUS_CHOICES=[('active','Active'),('a_verifier','À vérifier'),('provisoire','Provisoire élève'),('inactive','Inactive')]
    name=models.CharField(max_length=180)
    activity=models.CharField(max_length=220, blank=True)
    address=models.CharField(max_length=240, blank=True)
    city=models.CharField(max_length=120, blank=True)
    postal_code=models.CharField(max_length=20, blank=True)
    latitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone=models.CharField(max_length=40, blank=True)
    email=models.EmailField(blank=True)
    website=models.URLField(blank=True)
    formations=models.ManyToManyField(Formation, blank=True)
    tags=models.ManyToManyField(CompanyTag, blank=True)
    transport_access=models.CharField(max_length=220, blank=True)
    student_visible_notes=models.TextField(blank=True)
    internal_comment=models.TextField(blank=True)
    safety_notes=models.TextField(blank=True)
    global_rating=models.PositiveSmallIntegerField(default=0)
    status=models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='companies_created')
    # RC16 : import, visibilité et géocodage.
    external_key=models.CharField(max_length=120, blank=True, null=True, unique=True)
    siret=models.CharField(max_length=20, blank=True, db_index=True)
    naf_ape=models.CharField(max_length=20, blank=True)
    source_activity=models.CharField(max_length=260, blank=True)
    domains_text=models.CharField(max_length=260, blank=True)
    subdomains_text=models.CharField(max_length=260, blank=True)
    country=models.CharField(max_length=80, blank=True, default='France')
    full_address=models.CharField(max_length=360, blank=True)
    geocoding_status=models.CharField(max_length=40, blank=True, default='A_GEOCODER')
    osm_search_url=models.URLField(blank=True)
    student_visible=models.BooleanField(default=True)
    import_source=models.CharField(max_length=160, blank=True)
    import_batch=models.ForeignKey(ImportBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name='companies')
    updated_at=models.DateTimeField(auto_now=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        indexes=[models.Index(fields=['name']), models.Index(fields=['city']), models.Index(fields=['postal_code'])]
    def __str__(self): return self.name


class CompanyContact(models.Model):
    VISIBILITY=[('students','Visible élèves autorisés'),('professors','Professeurs seulement'),('admins','Administrateurs seulement')]
    CONTACT_TYPE=[('pfmp','PFMP'),('alternance','Alternance'),('emploi','Emploi'),('convention','Convention'),('administratif','Administratif'),('technique','Technique'),('rh','RH général'),('dirigeant','Dirigeant'),('tuteur','Tuteur')]
    company=models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts')
    full_name=models.CharField(max_length=160)
    role=models.CharField(max_length=120, blank=True)
    service=models.CharField(max_length=120, blank=True)
    email=models.EmailField(blank=True)
    phone=models.CharField(max_length=40, blank=True)
    mobile_phone=models.CharField(max_length=40, blank=True)
    contact_type=models.CharField(max_length=30, choices=CONTACT_TYPE, default='pfmp')
    visibility=models.CharField(max_length=30, choices=VISIBILITY, default='professors')
    student_visible=models.BooleanField(default=False)
    teacher_visible=models.BooleanField(default=True)
    formations=models.ManyToManyField(Formation, blank=True)
    active=models.BooleanField(default=True)
    note=models.TextField(blank=True)
    student_extra_info=models.TextField(
        blank=True,
        verbose_name='Info complémentaire visible élèves',
        help_text='Information affichée aux élèves pour ce contact, sans donnée personnelle sensible.'
    )
    local_relay_possible=models.BooleanField(
        default=False,
        verbose_name='Relais de proximité possible',
        help_text='Si activé, le contact n’est pas affiché comme contact élève classique mais son point GPS peut servir de relais de proximité.'
    )
    relay_student_info=models.TextField(
        blank=True,
        verbose_name='Info relais visible élèves',
        help_text='Texte affiché aux élèves avec la mention relais de proximité possible.'
    )
    personal_address=models.CharField(max_length=240, blank=True)
    personal_postal_code=models.CharField(max_length=20, blank=True)
    personal_city=models.CharField(max_length=120, blank=True)
    personal_latitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    personal_longitude=models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    use_personal_location_for_student_search=models.BooleanField(default=False)
    can_help_transport=models.BooleanField(default=False)
    import_source=models.CharField(max_length=160, blank=True)
    import_batch=models.ForeignKey(ImportBatch, null=True, blank=True, on_delete=models.SET_NULL, related_name='contacts')
    class Meta:
        indexes=[models.Index(fields=['email']), models.Index(fields=['contact_type'])]
    def __str__(self): return f'{self.full_name} — {self.company}'


class PfmpPeriod(models.Model):
    STATUS=[('preparation','Préparation'),('open','Saisie ouverte'),('closed','Saisie fermée'),('archived','Archivée')]
    title=models.CharField(max_length=160)
    start_date=models.DateField()
    end_date=models.DateField()
    search_deadline=models.DateField(null=True, blank=True)
    formations=models.ManyToManyField(Formation, blank=True)
    class_names=models.CharField(max_length=255, blank=True, help_text='Classes concernées, séparées par ;')
    referent=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='pfmp_periods')
    status=models.CharField(max_length=30, choices=STATUS, default='preparation')
    notes=models.TextField(blank=True)
    def __str__(self): return self.title


class StudentAssignment(models.Model):
    STATUS=[('searching','Recherche'),('proposed','Entreprise proposée'),('validated','Validée'),('convention','Convention en cours'),('in_progress','En PFMP'),('completed','Terminée'),('blocked','Bloquée')]
    student=models.ForeignKey(PfmpUser, on_delete=models.CASCADE, related_name='pfmp_assignments')
    period=models.ForeignKey(PfmpPeriod, on_delete=models.CASCADE, related_name='assignments')
    company=models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL, related_name='assignments')
    tutor=models.ForeignKey(CompanyContact, null=True, blank=True, on_delete=models.SET_NULL, related_name='tutored_assignments')
    teacher=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='pfmp_followed_students')
    status=models.CharField(max_length=30, choices=STATUS, default='searching')
    student_comment=models.TextField(blank=True)
    teacher_comment=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        unique_together=[('student','period')]
    def __str__(self): return f'{self.student} — {self.period}'


class StudentStep(models.Model):
    STEP=[('contact','Contact entreprise'),('cv','CV'),('letter','Lettre'),('phone','Appel'),('mail','Mail'),('visit','Visite'),('document','Document'),('other','Autre')]
    assignment=models.ForeignKey(StudentAssignment, on_delete=models.CASCADE, related_name='steps')
    step_type=models.CharField(max_length=30, choices=STEP, default='contact')
    date=models.DateField(default=timezone.localdate)
    title=models.CharField(max_length=180)
    comment=models.TextField(blank=True)
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL)
    def __str__(self): return self.title


class StudentCompanySearch(models.Model):
    STATUS=[
        ('recherche','Recherche'),('mail_envoye','Mail envoyé'),('appel_effectue','Appel effectué'),
        ('demande_envoyee','Demande de stage envoyée'),('a_relancer','À relancer'),('accord_oral','Accord oral'),
        ('accord_mail','Accord OK mail'),('refus','Refus'),('sans_reponse','Sans réponse'),
        ('convention_a_preparer','Convention à préparer'),('convention_envoyee','Convention envoyée'),
        ('convention_signee','Convention signée'),('stage_valide','Stage validé'),('abandonne','Abandonné')]
    student=models.ForeignKey(PfmpUser, on_delete=models.CASCADE, related_name='company_searches')
    period=models.ForeignKey(PfmpPeriod, on_delete=models.CASCADE, related_name='company_searches')
    company=models.ForeignKey(Company, on_delete=models.CASCADE, related_name='student_searches')
    contact=models.ForeignKey(CompanyContact, null=True, blank=True, on_delete=models.SET_NULL, related_name='student_searches')
    status=models.CharField(max_length=40, choices=STATUS, default='recherche')
    tags_text=models.CharField(max_length=240, blank=True, help_text='Tags séparés par ;')
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='searches_created')
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    last_action_at=models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together=[('student','period','company')]
        indexes=[models.Index(fields=['student','period','status']), models.Index(fields=['status'])]
    def __str__(self): return f'{self.student} — {self.company} — {self.period}'


class StudentCompanyAction(models.Model):
    ACTION=[('mail','Mail'),('telephone','Téléphone'),('visite','Visite'),('depot_cv','Dépôt CV'),('relance','Relance'),('reponse','Réponse'),('accord','Accord'),('refus','Refus'),('convention','Convention'),('autre','Autre')]
    search=models.ForeignKey(StudentCompanySearch, on_delete=models.CASCADE, related_name='actions')
    created_at=models.DateTimeField(auto_now_add=True)
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='company_actions_created')
    action_type=models.CharField(max_length=40, choices=ACTION, default='mail')
    contact=models.ForeignKey(CompanyContact, null=True, blank=True, on_delete=models.SET_NULL, related_name='company_actions')
    comment=models.TextField(blank=True)
    status_after=models.CharField(max_length=40, choices=StudentCompanySearch.STATUS, default='recherche')
    next_action=models.CharField(max_length=180, blank=True)
    next_action_date=models.DateField(null=True, blank=True)
    attachment=models.FileField(upload_to='pfmp/search_actions/', blank=True)
    class Meta:
        ordering=['-created_at']
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        StudentCompanySearch.objects.filter(pk=self.search_id).update(status=self.status_after, last_action_at=self.created_at, updated_at=timezone.now())
    def __str__(self): return f'{self.get_action_type_display()} — {self.search}'


class CompanyAnnouncement(models.Model):
    TYPE=[('pfmp','Offre PFMP'),('alternance','Alternance'),('emploi','Emploi'),('job','Job étudiant'),('visite','Visite entreprise'),('evenement','Événement recrutement')]
    STATUS=[('draft','Brouillon'),('pending','En attente de validation'),('published','Publiée'),('expired','Expirée'),('archived','Archivée')]
    company=models.ForeignKey(Company, on_delete=models.CASCADE, related_name='announcements')
    title=models.CharField(max_length=180)
    announcement_type=models.CharField(max_length=30, choices=TYPE, default='pfmp')
    formations=models.ManyToManyField(Formation, blank=True)
    places=models.PositiveIntegerField(default=1)
    period_text=models.CharField(max_length=160, blank=True)
    missions=models.TextField(blank=True)
    expected_profile=models.TextField(blank=True)
    mobility=models.CharField(max_length=160, blank=True)
    requires_driving_license=models.BooleanField(default=False)
    requires_vehicle=models.BooleanField(default=False)
    public_transport_ok=models.BooleanField(default=True)
    deadline=models.DateField(null=True, blank=True)
    status=models.CharField(max_length=30, choices=STATUS, default='draft')
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title
