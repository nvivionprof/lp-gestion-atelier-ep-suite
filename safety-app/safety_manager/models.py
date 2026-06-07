from __future__ import annotations
from django.db import models
from django.utils import timezone
from .services import next_code, priority_from_matrix

from django.contrib.auth.hashers import check_password, make_password


class SafetyUser(models.Model):
    """Copie locale synchronisée depuis LP Core.

    Safety Manager reste indépendant : il ne lit pas directement la base LP Core.
    Les utilisateurs sont synchronisés via l’API interne LP Core, comme ToolMag.
    """
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'code']
        verbose_name = 'utilisateur Safety synchronisé'
        verbose_name_plural = 'utilisateurs Safety synchronisés'

    def __str__(self):
        return f'{self.code} — {self.last_name} {self.first_name}'.strip()

    def set_password(self, raw_password: str):
        if raw_password:
            self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)

    def rights_list(self):
        raw = self.rights or ''
        return [x.strip() for x in raw.replace(';', ',').split(',') if x.strip()]

    @property
    def is_admin_like(self) -> bool:
        role = (self.role_principal or '').lower()
        return role in {'admin', 'admin_suite', 'responsable', 'responsable_securite'} or 'SAFETY_ADMIN' in self.rights_list() or 'CORE_ADMIN' in self.rights_list()



class SafetyZone(models.Model):
    TYPE_ZONE_CHOICES = [
        ('atelier', 'Atelier'), ('chantier', 'Chantier pédagogique'), ('stockage', 'Stockage'),
        ('salle', 'Salle'), ('circulation', 'Circulation'), ('exterieur', 'Extérieur'), ('autre', 'Autre')
    ]
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    type_zone = models.CharField(max_length=40, choices=TYPE_ZONE_CHOICES, default='atelier')
    actif = models.BooleanField(default=True)
    ordre_affichage = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['ordre_affichage', 'nom']
        verbose_name = 'zone Safety'
        verbose_name_plural = 'zones Safety'

    def __str__(self):
        return f'{self.code} — {self.nom}'


class WorkUnit(models.Model):
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    zone = models.ForeignKey(SafetyZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='work_units')
    nombre_personnes_exposees = models.PositiveIntegerField(default=0)
    responsable = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_workunits')
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'unité de travail'
        verbose_name_plural = 'unités de travail'

    def __str__(self):
        return f'{self.code} — {self.nom}'


class RiskFamily(models.Model):
    code = models.CharField(max_length=60, unique=True)
    nom = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    exemples_dangers = models.TextField(blank=True)
    exemples_prevention = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['nom']
        verbose_name = 'famille de risques'
        verbose_name_plural = 'familles de risques'

    def __str__(self):
        return self.nom


class RiskAssessment(models.Model):
    STATUS_CHOICES = [('brouillon', 'Brouillon'), ('valide', 'Validé'), ('a_revoir', 'À revoir'), ('archive', 'Archivé')]
    GRAVITY_CHOICES = [(1, '1 — faible, sans arrêt'), (2, '2 — moyenne, avec arrêt'), (3, '3 — grave, IPP'), (4, '4 — très grave, mortel')]
    FREQUENCY_CHOICES = [(1, '1 — faible, annuelle'), (2, '2 — moyenne, mensuelle'), (3, '3 — fréquente, hebdomadaire'), (4, '4 — très fréquente, quotidienne/permanente')]

    code = models.CharField(max_length=40, unique=True, blank=True)
    unite_travail = models.ForeignKey(WorkUnit, on_delete=models.PROTECT, related_name='risks')
    famille_risque = models.ForeignKey(RiskFamily, on_delete=models.PROTECT, related_name='risks')
    danger = models.TextField()
    situation_dangereuse = models.TextField()
    dommage_potentiel = models.TextField()
    personnes_exposees = models.TextField(blank=True)
    mesures_existantes = models.TextField(blank=True)
    gravite = models.PositiveSmallIntegerField(choices=GRAVITY_CHOICES, default=1)
    frequence = models.PositiveSmallIntegerField(choices=FREQUENCY_CHOICES, default=1)
    niveau_calcule = models.PositiveSmallIntegerField(default=1)
    priorite_calculee = models.PositiveSmallIntegerField(default=3)
    priorite_libelle = models.CharField(max_length=120, blank=True)
    mesures_a_proposer = models.TextField(blank=True)
    responsable_suivi = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_risks_to_follow')
    statut = models.CharField(max_length=30, choices=STATUS_CHOICES, default='brouillon')
    date_evaluation = models.DateField(default=timezone.localdate)
    date_revision_prevue = models.DateField(null=True, blank=True)
    redacteur = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_risks_written')
    validateur = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_risks_validated')
    historique = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priorite_calculee', 'famille_risque__nom', 'code']
        verbose_name = 'évaluation de risque'
        verbose_name_plural = 'évaluations de risques'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_code(RiskAssessment, 'RISK')
        priority, label, score = priority_from_matrix(self.gravite, self.frequence)
        self.priorite_calculee = priority
        self.priorite_libelle = label
        self.niveau_calcule = score
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — P{self.priorite_calculee} — {self.famille_risque}'


class SafetyEvent(models.Model):
    TYPE_CHOICES = [('accident', 'Accident'), ('incident', 'Incident'), ('presqu_accident', 'Presqu’accident'), ('evenement_indesirable', 'Événement indésirable')]
    ANALYSIS_STATUS_CHOICES = [('a_analyser', 'À analyser'), ('analyse_en_cours', 'Analyse en cours'), ('analyse_validee', 'Analyse validée'), ('cloture', 'Clôturé')]

    code = models.CharField(max_length=40, unique=True, blank=True)
    type_evenement = models.CharField(max_length=40, choices=TYPE_CHOICES, default='presqu_accident')
    date = models.DateField(default=timezone.localdate)
    heure = models.TimeField(null=True, blank=True)
    lieu = models.CharField(max_length=180, blank=True)
    zone = models.ForeignKey(SafetyZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    unite_travail = models.ForeignKey(WorkUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    personne_concernee = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_events_concerned')
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    temoins = models.TextField(blank=True)
    description_courte = models.CharField(max_length=255)
    recit_detaille = models.TextField(blank=True)
    dommage = models.TextField(blank=True)
    nature_lesion = models.CharField(max_length=180, blank=True)
    siege_lesion = models.CharField(max_length=180, blank=True)
    accident_declare = models.BooleanField(default=False)
    avec_arret = models.BooleanField(default=False)
    nombre_jours_arret = models.PositiveIntegerField(default=0)
    secours_intervenus = models.BooleanField(default=False)
    sst_intervenus = models.BooleanField(default=False)
    materiel_source = models.CharField(max_length=40, choices=[('toolmag', 'ToolMag'), ('systeme', 'Système pédagogique'), ('hors_base', 'Équipement hors base')], default='hors_base')
    materiel_implique = models.CharField(max_length=255, blank=True)
    outil_toolmag_id = models.CharField(max_length=80, blank=True, help_text='Identifiant optionnel ToolMag si module installé')
    statut_analyse = models.CharField(max_length=40, choices=ANALYSIS_STATUS_CHOICES, default='a_analyser')
    created_by = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_events_created')
    updated_by = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_events_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'événement sécurité'
        verbose_name_plural = 'événements sécurité'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_code(SafetyEvent, 'EVT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.get_type_evenement_display()}'


class DangerousSituation(models.Model):
    """Situation dangereuse déclarable hors DUERP ou intégrable au DUERP.

    Elle permet de capter les signaux faibles d'atelier sans forcer leur
    inscription immédiate dans le Document Unique. Une action peut être
    rattachée à cette situation, même si elle reste hors DUERP.
    """
    STATUS_CHOICES = [
        ('nouvelle', 'Nouvelle'), ('a_qualifier', 'À qualifier'), ('hors_duerp', 'Hors DUERP'),
        ('integree_duerp', 'Intégrée DUERP'), ('action_en_cours', 'Action en cours'),
        ('traitee', 'Traitée'), ('archivee', 'Archivée')
    ]
    code = models.CharField(max_length=40, unique=True, blank=True)
    titre = models.CharField(max_length=220)
    description = models.TextField()
    zone = models.ForeignKey(SafetyZone, on_delete=models.SET_NULL, null=True, blank=True, related_name='dangerous_situations')
    unite_travail = models.ForeignKey(WorkUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='dangerous_situations')
    famille_risque = models.ForeignKey(RiskFamily, on_delete=models.SET_NULL, null=True, blank=True, related_name='dangerous_situations')
    inclure_duerp = models.BooleanField(default=False, verbose_name='Document Unique')
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.SET_NULL, null=True, blank=True, related_name='situations_origine')
    priorite = models.PositiveSmallIntegerField(default=3)
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='a_qualifier')
    declaree_par = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='situations_dangereuses_declarees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priorite', '-created_at']
        verbose_name = 'situation dangereuse'
        verbose_name_plural = 'situations dangereuses'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_code(DangerousSituation, 'SIT')
        if self.inclure_duerp and self.statut in {'nouvelle', 'a_qualifier', 'hors_duerp'}:
            self.statut = 'integree_duerp'
        elif not self.inclure_duerp and self.statut in {'nouvelle', 'a_qualifier'}:
            self.statut = 'hors_duerp'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.titre}'


class PreventionAction(models.Model):
    TYPE_CHOICES = [('technique', 'Technique'), ('organisationnelle', 'Organisationnelle'), ('humaine', 'Humaine'), ('formation', 'Formation'), ('epi', 'EPI'), ('epc', 'EPC'), ('controle', 'Contrôle'), ('procedure', 'Procédure'), ('autre', 'Autre')]
    ORIGIN_CHOICES = [('duerp', 'DUERP'), ('accident', 'Accident'), ('incident', 'Incident'), ('presqu_accident', 'Presqu’accident'), ('audit', 'Audit'), ('observation', 'Observation'), ('autre', 'Autre')]
    STATUS_CHOICES = [('a_etudier', 'À étudier'), ('validee', 'Validée'), ('en_cours', 'En cours'), ('realisee', 'Réalisée'), ('verifiee', 'Vérifiée'), ('abandonnee', 'Abandonnée avec justification')]

    code = models.CharField(max_length=40, unique=True, blank=True)
    titre = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    type_action = models.CharField(max_length=40, choices=TYPE_CHOICES, default='organisationnelle')
    origine = models.CharField(max_length=40, choices=ORIGIN_CHOICES, default='duerp')
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions')
    event = models.ForeignKey(SafetyEvent, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions')
    dangerous_situation = models.ForeignKey(DangerousSituation, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions')
    responsable = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_actions')
    priorite = models.PositiveSmallIntegerField(default=2)
    echeance = models.DateField(null=True, blank=True)
    cout_previsionnel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='a_etudier')
    date_realisation = models.DateField(null=True, blank=True)
    preuve = models.FileField(upload_to='safety/actions/', blank=True)
    commentaire = models.TextField(blank=True)
    efficacite_apres_action = models.TextField(blank=True)
    nouveaux_risques_identifies = models.TextField(blank=True)
    date_verification = models.DateField(null=True, blank=True)
    action_stable = models.BooleanField(default=False)
    integree_travail_reel = models.BooleanField(default=False)
    ne_deplace_pas_risque = models.BooleanField(default=False)
    agit_causes_profondes = models.BooleanField(default=False)
    portee_generale = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['priorite', 'echeance', 'code']
        verbose_name = 'action de prévention'
        verbose_name_plural = 'actions de prévention'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_code(PreventionAction, 'ACT')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.titre}'


class EventFact(models.Model):
    CATEGORY_CHOICES = [('individu', 'Individu'), ('tache_activite', 'Tâche / activité'), ('materiel', 'Matériel'), ('milieu', 'Milieu'), ('organisation', 'Organisation'), ('autre', 'Autre')]
    FACT_TYPE_CHOICES = [('habituel', 'Fait habituel / état'), ('inhabituel_variation', 'Fait inhabituel / variation')]
    SOURCE_CHOICES = [('observation', 'Observation'), ('entretien', 'Entretien'), ('document', 'Document'), ('mesure', 'Mesure'), ('autre', 'Autre')]
    event = models.ForeignKey(SafetyEvent, on_delete=models.CASCADE, related_name='facts')
    description = models.TextField()
    categorie = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='autre')
    type_fait = models.CharField(max_length=40, choices=FACT_TYPE_CHOICES, default='inhabituel_variation')
    est_verifie = models.BooleanField(default=False)
    source = models.CharField(max_length=40, choices=SOURCE_CHOICES, default='observation')
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'fait d’événement'
        verbose_name_plural = 'faits d’événement'

    def __str__(self):
        return self.description[:80]


class CauseAnalysis(models.Model):
    METHOD_CHOICES = [('5_pourquoi', '5 pourquoi'), ('ishikawa', 'Ishikawa / 5M'), ('arbre_des_causes', 'Arbre des causes')]
    STATUS_CHOICES = [('brouillon', 'Brouillon'), ('en_cours', 'En cours'), ('validee', 'Validée'), ('archivee', 'Archivée')]
    event = models.ForeignKey(SafetyEvent, on_delete=models.CASCADE, related_name='analyses')
    methode = models.CharField(max_length=40, choices=METHOD_CHOICES, default='5_pourquoi')
    synthese = models.TextField(blank=True)
    causes_directes = models.TextField(blank=True)
    causes_profondes = models.TextField(blank=True)
    facteurs_potentiels_accident = models.TextField(blank=True)
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='brouillon')
    validateur = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_analyses_validated')
    date_validation = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'analyse causale'
        verbose_name_plural = 'analyses causales'

    def __str__(self):
        return f'{self.event.code} — {self.get_methode_display()}'


class FiveWhyLine(models.Model):
    analysis = models.ForeignKey(CauseAnalysis, on_delete=models.CASCADE, related_name='fivewhy_lines')
    ordre = models.PositiveIntegerField(default=1)
    question = models.CharField(max_length=255, default='Pourquoi ?')
    reponse_factuelle = models.TextField(blank=True)
    cause_identifiee = models.TextField(blank=True)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'ligne 5 pourquoi'
        verbose_name_plural = 'lignes 5 pourquoi'


class IshikawaCause(models.Model):
    CATEGORY_CHOICES = [('milieu', 'Milieu'), ('materiel', 'Matériel'), ('methode', 'Méthode'), ('matiere', 'Matière'), ('main_oeuvre', 'Main d’œuvre'), ('management', 'Management'), ('mesure', 'Mesure'), ('autre', 'Autre')]
    analysis = models.ForeignKey(CauseAnalysis, on_delete=models.CASCADE, related_name='ishikawa_causes')
    categorie = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='methode')
    cause = models.TextField()
    commentaire = models.TextField(blank=True)

    class Meta:
        ordering = ['categorie', 'id']
        verbose_name = 'cause Ishikawa'
        verbose_name_plural = 'causes Ishikawa'


class CauseTreeNode(models.Model):
    TYPE_CHOICES = [('fait_habituel', 'Fait habituel / état'), ('fait_inhabituel', 'Fait inhabituel / variation'), ('dommage', 'Dommage')]
    analysis = models.ForeignKey(CauseAnalysis, on_delete=models.CASCADE, related_name='tree_nodes')
    fact = models.ForeignKey(EventFact, on_delete=models.SET_NULL, null=True, blank=True, related_name='tree_nodes')
    libelle = models.CharField(max_length=255)
    type_node = models.CharField(max_length=40, choices=TYPE_CHOICES, default='fait_inhabituel')
    position_x = models.IntegerField(default=100)
    position_y = models.IntegerField(default=100)

    class Meta:
        ordering = ['position_y', 'position_x']
        verbose_name = 'nœud arbre des causes'
        verbose_name_plural = 'nœuds arbre des causes'


class CauseTreeLink(models.Model):
    TYPE_CHOICES = [('enchainement', 'Enchaînement'), ('conjonction', 'Conjonction'), ('disjonction', 'Disjonction')]
    analysis = models.ForeignKey(CauseAnalysis, on_delete=models.CASCADE, related_name='tree_links')
    source_node = models.ForeignKey(CauseTreeNode, on_delete=models.CASCADE, related_name='links_out')
    target_node = models.ForeignKey(CauseTreeNode, on_delete=models.CASCADE, related_name='links_in')
    type_lien = models.CharField(max_length=40, choices=TYPE_CHOICES, default='enchainement')
    groupe_logique = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = 'lien arbre des causes'
        verbose_name_plural = 'liens arbre des causes'


class SafetyDocument(models.Model):
    TYPE_CHOICES = [('photo', 'Photo'), ('rapport', 'Rapport'), ('fiche', 'Fiche'), ('procedure', 'Procédure'), ('preuve', 'Preuve'), ('autre', 'Autre')]
    titre = models.CharField(max_length=180)
    type_document = models.CharField(max_length=40, choices=TYPE_CHOICES, default='autre')
    fichier = models.FileField(upload_to='safety/documents/')
    event = models.ForeignKey(SafetyEvent, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    action = models.ForeignKey(PreventionAction, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    risk_assessment = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='safety_documents')

    class Meta:
        ordering = ['-date_ajout']
        verbose_name = 'document Safety'
        verbose_name_plural = 'documents Safety'


class DUERPVersion(models.Model):
    STATUS_CHOICES = [('brouillon', 'Brouillon'), ('valide', 'Validé'), ('archive', 'Archivé')]
    code = models.CharField(max_length=40, unique=True, blank=True)
    date_generation = models.DateTimeField(auto_now_add=True)
    perimetre = models.CharField(max_length=255, blank=True, default='Ateliers / plateaux techniques')
    commentaire = models.TextField(blank=True)
    genere_par = models.ForeignKey('SafetyUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='duerp_versions')
    fichier_pdf = models.FileField(upload_to='safety/duerp/', null=True, blank=True)
    fichier_docx = models.FileField(upload_to='safety/duerp/', null=True, blank=True)
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='brouillon')

    class Meta:
        ordering = ['-date_generation']
        verbose_name = 'version DUERP'
        verbose_name_plural = 'versions DUERP'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_code(DUERPVersion, 'DUERP')
        super().save(*args, **kwargs)
