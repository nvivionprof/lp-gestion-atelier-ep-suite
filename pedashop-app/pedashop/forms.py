"""Formulaires Django PedaShop.

Les formulaires portent les validations utilisateur visibles. Les règles métier
plus complexes restent dans ``services.py`` afin de séparer clairement interface
et logique de stock.
"""
from django import forms
from django.db.models import Q
from .models import (
    Article, Bon, Emplacement, LigneBon, LigneProjectionPedagogique, LigneReservation,
    Magasin, ProjectionPedagogique, Reclamation, Reservation, StockArticleMagasin,
    SupplierConsultation, SupplierConsultationLine, PedaShopUser,
)




def teacher_queryset():
    """Retourne uniquement les comptes utilisables comme prof responsable.

    La liste déroulante professeur ne doit pas afficher les élèves ou les
    magasiniers simples. On filtre donc sur le rôle principal ou les droits
    synchronisés depuis LP Core.
    """
    return PedaShopUser.objects.filter(active=True).filter(
        Q(role_principal__icontains='prof') |
        Q(role_principal__icontains='responsable') |
        Q(rights__icontains='PEDASHOP_PROF') |
        Q(rights__icontains='CORE_PROF') |
        Q(rights__icontains='PROF')
    ).order_by('last_name', 'first_name', 'code')


class LoginForm(forms.Form):
    username = forms.CharField(label='Code utilisateur / identifiant')
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    mode = forms.ChoiceField(label='Mode de connexion', choices=[('utilisateur', 'Utilisateur'), ('magasinier', 'Magasinier')], initial='utilisateur')


class ArticleSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Recherche')
    fabricant = forms.CharField(required=False, label='Fabricant')
    categorie = forms.CharField(required=False, label='Catégorie')
    sous_categorie = forms.CharField(required=False, label='Sous-catégorie')
    marche = forms.CharField(required=False, label='Marché')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), required=False)
    disponible = forms.BooleanField(required=False, label='Stock disponible uniquement')
    substituable = forms.BooleanField(required=False, label='Substituable')

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['reference_interne', 'reference_fabricant', 'fabricant', 'designation', 'description', 'code_ean', 'photo', 'unite', 'categorie', 'sous_categorie', 'prix_coutant', 'prix_vente', 'tva', 'substituable', 'fournisseur', 'marche', 'archive']
        widgets = {'photo': forms.ClearableFileInput(attrs={'accept': 'image/*', 'data-camera-upload': '1'})}


class MagasinForm(forms.ModelForm):
    class Meta:
        model = Magasin
        fields = ['code', 'nom', 'description', 'responsable', 'actif']


class EmplacementForm(forms.ModelForm):
    class Meta:
        model = Emplacement
        fields = ['magasin', 'code', 'nom', 'description', 'actif']


class StockForm(forms.ModelForm):
    class Meta:
        model = StockArticleMagasin
        fields = ['article', 'magasin', 'emplacement', 'stock_reel', 'stock_minimum', 'stock_reserve_demande', 'stock_reserve_projection', 'stock_en_preparation', 'stock_temporairement_sorti', 'qte_ok', 'qte_use', 'stock_hs']


class BonHeaderForm(forms.ModelForm):
    class Meta:
        model = Bon
        fields = ['type_bon', 'magasin', 'professeur_responsable', 'nom_tp', 'classe_ou_groupe', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, user=None, active_role='utilisateur', allowed_magasins=None, initial_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professeur_responsable'].queryset = teacher_queryset()
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins
        # Les types de bons proposés dépendent du rôle actif, comme dans ToolMag.
        all_choices = list(Bon.TYPE_CHOICES)
        if user and (user.is_admin_like or user.is_teacher_like):
            choices = all_choices
        elif user and active_role == 'magasinier' and user.is_storekeeper_like:
            choices = [c for c in all_choices if c[0] in {'enlevement', 'comptoir', 'preparation', 'retour'}]
            self.initial.setdefault('type_bon', initial_type or 'comptoir')
        else:
            choices = [c for c in all_choices if c[0] == 'demande_eleve']
            self.initial.setdefault('type_bon', 'demande_eleve')
        if initial_type and any(c[0] == initial_type for c in choices):
            self.initial['type_bon'] = initial_type
        self.fields['type_bon'].choices = choices

class LigneBonForm(forms.ModelForm):
    class Meta:
        model = LigneBon
        fields = ['article', 'quantite_demandee', 'type_sortie', 'date_retour_prevue', 'commentaire']
        widgets = {'date_retour_prevue': forms.DateInput(attrs={'type': 'date'})}


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['magasin', 'titre', 'date_debut', 'date_fin', 'commentaire']
        widgets = {'date_debut': forms.DateInput(attrs={'type': 'date'}), 'date_fin': forms.DateInput(attrs={'type': 'date'})}


class LigneReservationForm(forms.ModelForm):
    class Meta:
        model = LigneReservation
        fields = ['article', 'quantite', 'commentaire']


class ProjectionForm(forms.ModelForm):
    class Meta:
        model = ProjectionPedagogique
        fields = ['professeur', 'nom_tp', 'classe_ou_groupe', 'formation', 'magasin', 'date_debut', 'date_fin', 'commentaire']
        widgets = {'date_debut': forms.DateInput(attrs={'type': 'date'}), 'date_fin': forms.DateInput(attrs={'type': 'date'}), 'commentaire': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['professeur'].queryset = teacher_queryset()


class LigneProjectionForm(forms.ModelForm):
    class Meta:
        model = LigneProjectionPedagogique
        fields = ['article', 'emplacement', 'quantite_reservee', 'date_retour_prevue_defaut', 'commentaire']
        widgets = {'date_retour_prevue_defaut': forms.DateInput(attrs={'type': 'date'})}


class ReclamationForm(forms.ModelForm):
    class Meta:
        model = Reclamation
        fields = ['ligne_bon', 'type_reclamation', 'description', 'piece_jointe']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class ExcelImportForm(forms.Form):
    fichier = forms.FileField(label='Fichier Excel .xlsx')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin de destination')
    feuille = forms.CharField(label='Feuille Excel', required=False, help_text='Laisser vide pour prendre la première feuille.')
    verifier_coherence_stock = forms.BooleanField(required=False, label='Vérifier la cohérence Qté stock / Qté OK + Usé + HS')

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins

class TransferForm(forms.Form):
    article = forms.ModelChoiceField(queryset=Article.objects.filter(archive=False))
    magasin_source = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True))
    magasin_destination = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True))
    quantite = forms.DecimalField(min_value=0)
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin_source'].queryset = allowed_magasins
            self.fields['magasin_destination'].queryset = allowed_magasins

class AlertFilterForm(forms.Form):
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), required=False)
    statut_alerte = forms.ChoiceField(required=False, choices=[('', 'Tous'), ('SOUS_STOCK_MINI', 'Sous stock mini'), ('ZERO_PAR_RESERVATION', 'Zéro par réservation'), ('RUPTURE_TEMPORAIRE_RETOUR_PREVU', 'Rupture avec retour prévu'), ('RUPTURE_REELLE', 'Rupture réelle'), ('STOCK_NEGATIF_AVEC_RESERVATION', 'Stock négatif')])
    fabricant = forms.CharField(required=False)
    categorie = forms.CharField(required=False)
    sous_categorie = forms.CharField(required=False)
    marche = forms.CharField(required=False, label='Numéro de marché')
    q = forms.CharField(required=False, label='Recherche')
    substituable = forms.NullBooleanField(required=False, label='Substituable')


class SupplierConsultationForm(forms.ModelForm):
    class Meta:
        model = SupplierConsultation
        fields = ['magasin', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}


class SupplierConsultationLineForm(forms.ModelForm):
    class Meta:
        model = SupplierConsultationLine
        fields = ['designation', 'fabricant', 'reference_constructeur', 'quantite_souhaitee', 'equivalence_possible']


class StockEntryForm(forms.Form):
    """Entrée de stock simple : réassort acheté, retour fournisseur ou stock initial."""
    TYPE_CHOICES = [
        ('reception_fournisseur', 'Réassort / réception fournisseur'),
        ('entree_initiale', 'Entrée initiale'),
        ('retour_produit', 'Retour produit en magasin'),
    ]
    article = forms.ModelChoiceField(queryset=Article.objects.filter(archive=False), label='Article')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin')
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), required=False, label='Emplacement')
    quantite = forms.DecimalField(min_value=0, label='Quantité à entrer')
    type_entree = forms.ChoiceField(choices=TYPE_CHOICES, label='Type d’entrée')
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins
            self.fields['emplacement'].queryset = Emplacement.objects.filter(magasin__in=allowed_magasins, actif=True)


class InventoryAdjustmentForm(forms.Form):
    """Mise à niveau ponctuelle du stock réel après inventaire physique.

    Le stock réel compté remplace uniquement la quantité présente physiquement
    en magasin. Les réservations et les sorties temporaires avec retour prévu
    ne sont pas modifiées par cette opération.
    """
    TYPE_CHOICES = [('inventaire', 'Inventaire / comptage physique'), ('reassort', 'Réassort / entrée magasin')]
    operation_type = forms.ChoiceField(choices=TYPE_CHOICES, label='Type d’opération')
    ean = forms.CharField(required=False, label='EAN / code-barres tablette')
    article = forms.ModelChoiceField(queryset=Article.objects.filter(archive=False), label='Article')
    magasin = forms.ModelChoiceField(queryset=Magasin.objects.filter(actif=True), label='Magasin')
    emplacement = forms.ModelChoiceField(queryset=Emplacement.objects.filter(actif=True), required=False, label='Emplacement constaté')
    stock_reel_compte = forms.DecimalField(min_value=0, label='Stock réel compté ou quantité à entrer')
    stock_mini = forms.DecimalField(min_value=0, required=False, label='Stock mini corrigé')
    commentaire = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Commentaire inventaire')

    def __init__(self, *args, allowed_magasins=None, **kwargs):
        super().__init__(*args, **kwargs)
        if allowed_magasins is not None:
            self.fields['magasin'].queryset = allowed_magasins
            self.fields['emplacement'].queryset = Emplacement.objects.filter(magasin__in=allowed_magasins, actif=True)


class UserVisibilityForm(forms.ModelForm):
    class Meta:
        model = PedaShopUser
        fields = ['magasins_visibles', 'rights']
        widgets = {
            'magasins_visibles': forms.CheckboxSelectMultiple,
            'rights': forms.Textarea(attrs={'rows': 3}),
        }

