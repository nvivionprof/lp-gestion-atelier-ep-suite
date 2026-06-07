from __future__ import annotations

from decimal import Decimal
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone
from .services import internal_barcode, next_monthly_code


class PedaShopUser(models.Model):
    """Copie locale minimale d'un utilisateur LP Core.

    LP Core reste la source de vérité. PedaShop ne stocke ici que les éléments
    nécessaires pour fonctionner de manière autonome : identification, classe,
    rôle principal et droits. Cette séparation permet de mettre à jour PedaShop
    sans casser LP Core ni ToolMag.
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
    magasins_visibles = models.ManyToManyField('Magasin', blank=True, related_name='utilisateurs_visibles', help_text='Magasins consultables par cet utilisateur. Vide = tous les magasins actifs.')
    synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'code']

    def __str__(self):
        return f'{self.code} — {self.last_name} {self.first_name}'.strip()

    def set_password(self, raw_password: str):
        if raw_password:
            self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return bool(self.password_hash and check_password(raw_password, self.password_hash))

    def rights_list(self):
        raw = self.rights or ''
        return [x.strip() for x in raw.replace(';', ',').split(',') if x.strip()]

    @property
    def is_admin_like(self) -> bool:
        role = (self.role_principal or '').lower()
        rights = set(self.rights_list())
        return role in {'admin', 'admin_suite', 'administrateur'} or bool({'PEDASHOP_ADMIN', 'CORE_ADMIN'} & rights)

    @property
    def is_storekeeper_like(self) -> bool:
        role = (self.role_principal or '').lower()
        rights = set(self.rights_list())
        return self.is_admin_like or role in {'magasinier'} or 'PEDASHOP_MAGASINIER' in rights

    @property
    def is_teacher_like(self) -> bool:
        role = (self.role_principal or '').lower()
        rights = set(self.rights_list())
        return self.is_admin_like or role in {'professeur'} or 'PEDASHOP_PROF' in rights


class Magasin(models.Model):
    """Magasin physique ou site de stockage.

    Le multi-site est natif : le stock appartient toujours au couple
    Article + Magasin, jamais à l'article seul.
    """
    code = models.CharField(max_length=40, unique=True)
    nom = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='magasins_responsables')
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.nom}'


class Emplacement(models.Model):
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='emplacements')
    code = models.CharField(max_length=60)
    nom = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        unique_together = [('magasin', 'code')]
        ordering = ['magasin__code', 'code']

    def __str__(self):
        return f'{self.magasin.code}/{self.code}'


class Article(models.Model):
    """Article consommable du magasin pédagogique.

    Le code produit est porté par ``reference_interne`` pour conserver la
    compatibilité avec les versions précédentes. La photo attendue lors des
    imports est robuste : ``<code produit>.jpg``.
    """
    reference_interne = models.CharField(max_length=100, unique=True, help_text='Code produit PedaShop, unique et bloquant à l’import.')
    reference_fabricant = models.CharField(max_length=120, blank=True)
    fabricant = models.CharField(max_length=120, blank=True)
    designation = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    code_ean = models.CharField(max_length=80, blank=True)
    code_barres_interne = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to='pedashop/articles/', blank=True, null=True)
    unite = models.CharField(max_length=30, default='u')
    categorie = models.CharField(max_length=120, blank=True)
    sous_categorie = models.CharField(max_length=120, blank=True)
    prix_coutant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=20)
    substituable = models.BooleanField(default=False)
    fournisseur = models.CharField(max_length=160, blank=True)
    marche = models.CharField(max_length=160, blank=True, help_text='Numéro de marché, contrat ou lot fournisseur.')
    archive = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['reference_interne']

    def save(self, *args, **kwargs):
        # Par défaut, si aucun EAN fabricant n'est saisi, on utilise le code produit.
        # Cela facilite la lecture tablette / code-barres avec une référence interne stable.
        if not self.code_ean:
            self.code_ean = self.reference_interne
        if not self.code_barres_interne:
            self.code_barres_interne = internal_barcode(self.reference_interne)
        super().save(*args, **kwargs)

    @property
    def code_produit(self):
        return self.reference_interne

    def __str__(self):
        return f'{self.reference_interne} — {self.designation}'


class StockArticleMagasin(models.Model):
    """Stock d'un article dans un magasin.

    - ``stock_reel`` = quantité physiquement au magasin.
    - ``stock_reserve_projection`` = réservation professeur / TP.
    - ``stock_reserve_demande`` = réservation issue des demandes élèves/profs.
    - ``stock_temporairement_sorti`` = quantité sortie avec retour attendu.
    - ``stock_hs`` = quantité hors service, non disponible et à traiter.
    """
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='stocks')
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='stocks')
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='stocks')
    stock_reel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_minimum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_reserve = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text='Ancien champ conservé pour compatibilité.')
    stock_reserve_demande = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_reserve_projection = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_en_preparation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_temporairement_sorti = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qte_ok = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    qte_use = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_hs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_perdu = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('article', 'magasin')]
        ordering = ['magasin__code', 'article__reference_interne']

    @property
    def reserve_total(self):
        return self.stock_reserve + self.stock_reserve_demande + self.stock_reserve_projection

    @property
    def stock_disponible(self):
        return self.stock_reel - self.reserve_total - self.stock_en_preparation

    @property
    def stock_exploitable_total(self):
        # Le matériel temporairement sorti reste exploitable car un retour est prévu.
        return self.stock_reel + self.stock_temporairement_sorti

    @property
    def stock_libre_avec_projection(self):
        return self.stock_reel - self.stock_reserve_demande - self.stock_en_preparation

    @property
    def sous_stock_minimum(self):
        return self.stock_disponible > 0 and self.stock_disponible < self.stock_minimum

    @property
    def alert_status(self):
        if self.stock_disponible < 0:
            return 'STOCK_NEGATIF_AVEC_RESERVATION'
        if self.stock_reel <= 0 and self.stock_temporairement_sorti <= 0:
            return 'RUPTURE_REELLE'
        if self.stock_reel <= 0 and self.stock_temporairement_sorti > 0:
            return 'RUPTURE_TEMPORAIRE_RETOUR_PREVU'
        if self.stock_disponible == 0 and self.stock_reel > 0 and (self.reserve_total > 0 or self.stock_en_preparation > 0):
            return 'ZERO_PAR_RESERVATION'
        if self.sous_stock_minimum:
            return 'SOUS_STOCK_MINI'
        return 'OK'

    def __str__(self):
        return f'{self.article.reference_interne} @ {self.magasin.code}'


class Bon(models.Model):
    TYPE_CHOICES = [
        ('demande_eleve', 'Demande élève'),
        ('demande_prof', 'Demande professeur'),
        ('preparation', 'Bon de préparation'),
        ('enlevement', 'Bon d’enlèvement'),
        ('comptoir', 'Bon comptoir'),
        ('retour', 'Bon de retour'),
        ('transfert', 'Transfert'),
        ('etat_stock', 'État de stock'),
    ]
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_demande', 'En demande'),
        ('en_preparation', 'En préparation'),
        ('en_cours_traitement', 'En cours de traitement'),
        ('demande_prete', 'Demande prête'),
        ('commande_prete', 'Commande prête'),
        ('en_attente_enlevement', 'En attente d’enlèvement'),
        ('enlevee', 'Enlevée'),
        ('distribuee', 'Distribuée'),
        ('reception_validee', 'Réception validée'),
        ('retour_attendu', 'Retour attendu'),
        ('retour_partiel', 'Retour partiel'),
        ('retour_complet', 'Retour complet'),
        ('reclamation_ouverte', 'Réclamation ouverte'),
        ('cloturee', 'Clôturée'),
        ('annulee', 'Annulée'),
    ]
    code = models.CharField(max_length=40, unique=True, blank=True)
    type_bon = models.CharField(max_length=30, choices=TYPE_CHOICES, default='demande_eleve')
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name='bons')
    demandeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='bons_demandes')
    professeur_responsable = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='bons_professeur')
    preparateur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='bons_prepares')
    distributeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='bons_distribues')
    receptionnaire = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='bons_recus')
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='en_demande')
    nom_tp = models.CharField(max_length=180, blank=True)
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    sortie_temporaire = models.BooleanField(default=False, help_text='Ancien champ global conservé ; la V1.7 gère surtout le type de sortie par ligne.')
    date_retour_prevue = models.DateField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_preparation_debut = models.DateTimeField(null=True, blank=True)
    date_preparation_fin = models.DateTimeField(null=True, blank=True)
    date_enlevement = models.DateTimeField(null=True, blank=True)
    date_cloture = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            prefix = {
                'demande_eleve': 'DEM-EL',
                'demande_prof': 'DEM-PR',
                'preparation': 'PREP',
                'enlevement': 'ENL',
                'comptoir': 'CPT',
                'retour': 'RET',
                'transfert': 'TRF',
                'etat_stock': 'STK',
            }.get(self.type_bon, 'BON')
            self.code = next_monthly_code(Bon, prefix)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.get_type_bon_display()}'

    @property
    def has_temporary_lines(self):
        return self.lignes.filter(type_sortie='temporaire').exists()


class ProjectionPedagogique(models.Model):
    """Pré-réservation professeur / TP.

    Elle bloque un stock pour un professeur et un TP, puis les demandes élèves
    rattachées au même professeur + TP viennent consommer ce solde sans créer de
    double réservation.
    """
    STATUS_CHOICES = [
        ('brouillon', 'Brouillon'), ('validee', 'Validée'), ('en_cours_utilisation', 'En cours'),
        ('partiellement_consommee', 'Partiellement consommée'), ('consommee', 'Consommée'),
        ('expiree', 'Expirée'), ('annulee', 'Annulée'), ('cloturee', 'Clôturée')
    ]
    code = models.CharField(max_length=40, unique=True, blank=True)
    professeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='projections_prof')
    nom_tp = models.CharField(max_length=180)
    classe_ou_groupe = models.CharField(max_length=120, blank=True)
    formation = models.CharField(max_length=80, blank=True)
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name='projections')
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=40, choices=STATUS_CHOICES, default='validee')
    commentaire = models.TextField(blank=True)
    created_by = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='projections_creees')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_debut', 'code']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_monthly_code(ProjectionPedagogique, 'RES-PR')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.nom_tp}'


class LigneProjectionPedagogique(models.Model):
    projection = models.ForeignKey(ProjectionPedagogique, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='lignes_projection')
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True)
    quantite_reservee = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    quantite_affectee_aux_demandes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_retour_prevue_defaut = models.DateField(null=True, blank=True)
    commentaire = models.CharField(max_length=255, blank=True)

    @property
    def quantite_restante(self):
        return self.quantite_reservee - self.quantite_affectee_aux_demandes

    def __str__(self):
        return f'{self.projection.code} — {self.article.reference_interne}'


class LigneBon(models.Model):
    TYPE_SORTIE_CHOICES = [('definitive', 'Définitive'), ('temporaire', 'Temporaire avec retour')]
    bon = models.ForeignKey(Bon, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='lignes_bon')
    emplacement = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True)
    quantite_demandee = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    quantite_preparee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_distribuee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_retour_prevue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_retournee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_usee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_hs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_perdue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    type_sortie = models.CharField(max_length=20, choices=TYPE_SORTIE_CHOICES, default='definitive')
    date_retour_prevue = models.DateField(null=True, blank=True)
    statut_ligne = models.CharField(max_length=40, default='en_demande')
    est_preparee = models.BooleanField(default=False)
    preparee_par = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_preparees')
    date_preparation = models.DateTimeField(null=True, blank=True)
    commentaire = models.CharField(max_length=255, blank=True)
    substitution_article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_substitution')
    projection_liee = models.ForeignKey(ProjectionPedagogique, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_bon_liees')
    ligne_projection_liee = models.ForeignKey(LigneProjectionPedagogique, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_bon_liees')
    quantite_prelevee_sur_projection = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']


class Reservation(models.Model):
    """Réservation classique conservée pour compatibilité V1.6."""
    code = models.CharField(max_length=40, unique=True, blank=True)
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name='reservations')
    demandeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    titre = models.CharField(max_length=180)
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=30, default='validee')
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_debut']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_monthly_code(Reservation, 'RES')
        super().save(*args, **kwargs)


class LigneReservation(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    commentaire = models.CharField(max_length=255, blank=True)


class RetourAttendu(models.Model):
    STATUS_CHOICES = [('attendu', 'Attendu'), ('partiel', 'Partiel'), ('retourne', 'Retourné'), ('retard', 'En retard'), ('perdu', 'Perdu')]
    ligne_bon = models.ForeignKey(LigneBon, on_delete=models.CASCADE, related_name='retours_attendus')
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='retours_attendus')
    magasin_retour_prevu = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name='retours_attendus')
    quantite_attendue = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    quantite_retournee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_usee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_cassee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantite_perdue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_retour_prevue = models.DateField()
    date_retour_reelle = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='attendu')
    commentaire_retour = models.TextField(blank=True)

    class Meta:
        ordering = ['date_retour_prevue']


class Reclamation(models.Model):
    TYPE_CHOICES = [
        ('mauvaise_reference', 'Mauvaise référence'), ('quantite_incorrecte', 'Quantité incorrecte'),
        ('materiel_casse', 'Matériel cassé'), ('materiel_use', 'Matériel usé'),
        ('materiel_manquant', 'Matériel manquant'), ('substitution_refusee', 'Substitution refusée'),
        ('autre', 'Autre')
    ]
    STATUS_CHOICES = [('ouverte', 'Ouverte'), ('en_cours', 'En cours'), ('acceptee', 'Acceptée'), ('refusee', 'Refusée'), ('corrigee', 'Corrigée'), ('cloturee', 'Clôturée')]
    code = models.CharField(max_length=40, unique=True, blank=True)
    bon = models.ForeignKey(Bon, on_delete=models.CASCADE, related_name='reclamations')
    ligne_bon = models.ForeignKey(LigneBon, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations')
    type_reclamation = models.CharField(max_length=40, choices=TYPE_CHOICES)
    description = models.TextField()
    declaree_par = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations_declarees')
    concerne = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations_concerne')
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ouverte')
    traitement = models.TextField(blank=True)
    traitee_par = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamations_traitees')
    date_declaration = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    piece_jointe = models.FileField(upload_to='pedashop/reclamations/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_monthly_code(Reclamation, 'REC')
        super().save(*args, **kwargs)


class BonHistorique(models.Model):
    bon = models.ForeignKey(Bon, on_delete=models.CASCADE, related_name='historiques')
    ligne_bon = models.ForeignKey(LigneBon, on_delete=models.SET_NULL, null=True, blank=True, related_name='historiques')
    action = models.CharField(max_length=80)
    ancien_statut = models.CharField(max_length=40, blank=True)
    nouveau_statut = models.CharField(max_length=40, blank=True)
    utilisateur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True)
    commentaire = models.TextField(blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']


class MouvementStock(models.Model):
    TYPE_CHOICES = [
        ('entree_initiale', 'Entrée initiale'), ('reception_fournisseur', 'Réception fournisseur'), ('retour_produit', 'Retour produit'),
        ('sortie_definitive', 'Sortie définitive'), ('sortie_temporaire', 'Sortie temporaire'),
        ('retour_temporaire', 'Retour temporaire'), ('correction_inventaire', 'Correction inventaire'),
        ('casse', 'Casse'), ('perte', 'Perte'), ('mise_au_rebut', 'Mise au rebut'),
        ('transfert_interne', 'Transfert interne'), ('substitution', 'Substitution'),
        ('reservation_projection', 'Réservation projection'), ('consultation_fournisseur', 'Consultation fournisseur')
    ]
    article = models.ForeignKey(Article, on_delete=models.PROTECT, related_name='mouvements')
    magasin_source = models.ForeignKey(Magasin, on_delete=models.PROTECT, null=True, blank=True, related_name='mouvements_sortants')
    magasin_destination = models.ForeignKey(Magasin, on_delete=models.PROTECT, null=True, blank=True, related_name='mouvements_entrants')
    emplacement_source = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_sortants')
    emplacement_destination = models.ForeignKey(Emplacement, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_entrants')
    type_mouvement = models.CharField(max_length=40, choices=TYPE_CHOICES)
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    stock_avant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_apres = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    utilisateur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_utilisateur')
    demandeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_demandeur')
    preparateur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_preparateur')
    distributeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_distributeur')
    receptionnaire = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements_receptionnaire')
    bon = models.ForeignKey(Bon, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements')
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, related_name='mouvements')
    commentaire = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']


class StockAlert(models.Model):
    STATUS_CHOICES = [
        ('OK', 'OK'), ('SOUS_STOCK_MINI', 'Sous stock mini'), ('ZERO_PAR_RESERVATION', 'Zéro par réservation'),
        ('RUPTURE_TEMPORAIRE_RETOUR_PREVU', 'Rupture temporaire, retour prévu'),
        ('RUPTURE_REELLE', 'Rupture réelle'), ('STOCK_NEGATIF_AVEC_RESERVATION', 'Stock négatif avec réservation')
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='alertes')
    magasin = models.ForeignKey(Magasin, on_delete=models.CASCADE, related_name='alertes_stock')
    statut_alerte = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OK')
    type_alerte = models.CharField(max_length=80, blank=True)
    stock_disponible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_reel = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_reserve = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_preparation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_exterieur = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_mini = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    message = models.TextField(blank=True)
    traitee = models.BooleanField(default=False)
    consultation_generee = models.BooleanField(default=False)
    date_calcul = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('article', 'magasin')]
        ordering = ['statut_alerte', 'article__reference_interne']


class SupplierConsultation(models.Model):
    code = models.CharField(max_length=40, unique=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True)
    magasin = models.ForeignKey(Magasin, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, default='brouillon')
    commentaire = models.TextField(blank=True)
    fichier_pdf = models.FileField(upload_to='pedashop/consultations/', blank=True, null=True)
    date_generation_pdf = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_creation']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_monthly_code(SupplierConsultation, 'CONS-FOUR')
        super().save(*args, **kwargs)


class SupplierConsultationLine(models.Model):
    consultation = models.ForeignKey(SupplierConsultation, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.CharField(max_length=255)
    fabricant = models.CharField(max_length=120, blank=True)
    reference_constructeur = models.CharField(max_length=120, blank=True)
    quantite_souhaitee = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    equivalence_possible = models.BooleanField(default=False)
    valeur_substituable_article = models.BooleanField(default=False)
    commentaire = models.CharField(max_length=255, blank=True)


class DemandeAchat(models.Model):
    code = models.CharField(max_length=40, unique=True, blank=True)
    magasin = models.ForeignKey(Magasin, on_delete=models.PROTECT, related_name='demandes_achat')
    demandeur = models.ForeignKey(PedaShopUser, on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=40, default='a_commander')
    commentaire = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = next_monthly_code(DemandeAchat, 'ACH')
        super().save(*args, **kwargs)


class LigneDemandeAchat(models.Model):
    demande = models.ForeignKey(DemandeAchat, on_delete=models.CASCADE, related_name='lignes')
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    commentaire = models.CharField(max_length=255, blank=True)
