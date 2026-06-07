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
    transport_access=models.CharField(max_length=220, blank=True)
    student_visible_notes=models.TextField(blank=True)
    internal_comment=models.TextField(blank=True)
    safety_notes=models.TextField(blank=True)
    global_rating=models.PositiveSmallIntegerField(default=0)
    status=models.CharField(max_length=30, choices=STATUS_CHOICES, default='active')
    created_by=models.ForeignKey(PfmpUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='companies_created')
    updated_at=models.DateTimeField(auto_now=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name

class CompanyContact(models.Model):
    VISIBILITY=[('students','Visible élèves autorisés'),('professors','Professeurs seulement'),('admins','Administrateurs seulement')]
    CONTACT_TYPE=[('pfmp','PFMP'),('alternance','Alternance'),('emploi','Emploi'),('convention','Convention'),('administratif','Administratif'),('technique','Technique'),('rh','RH général')]
    company=models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts')
    full_name=models.CharField(max_length=160)
    role=models.CharField(max_length=120, blank=True)
    service=models.CharField(max_length=120, blank=True)
    email=models.EmailField(blank=True)
    phone=models.CharField(max_length=40, blank=True)
    contact_type=models.CharField(max_length=30, choices=CONTACT_TYPE, default='pfmp')
    visibility=models.CharField(max_length=30, choices=VISIBILITY, default='professors')
    formations=models.ManyToManyField(Formation, blank=True)
    active=models.BooleanField(default=True)
    note=models.TextField(blank=True)
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
