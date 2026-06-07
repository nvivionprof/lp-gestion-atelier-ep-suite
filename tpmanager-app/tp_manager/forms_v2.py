from __future__ import annotations
from django import forms
from django.db.models import Q
from .models import (
    BacDiplome, BacChampTP, BacChampTPOption, BacCompetence,
    CompetencePivot, TPV2, TPV2ChampValeur, TPV2CompetenceOfficielle,
    TPV2CritereReussite, TPV2CritereEvaluationFinale, TPV2Document,
    TPV2ResourceGroup, TPV2ResourceItem, TPV2LinkedBlock, TPV2LinkedTPItem,
    TPV2CriterionLibrary, TpUser, SequencePedagogique, ParcoursEleveTP,
)


class V2StyledMixin:
    def _style_fields(self):
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            if not isinstance(field.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                field.widget.attrs['class'] = (css + ' form-control').strip()


class TPV2Form(V2StyledMixin, forms.ModelForm):
    # Champs volontairement libres avec datalist côté template : les listes guident,
    # mais un professeur peut ajouter une valeur non présente sans modifier le référentiel.
    type_activite = forms.CharField(label='Type', required=True, max_length=20)
    domaine_principal = forms.CharField(label='Thème principal', required=True, max_length=120)
    sous_theme = forms.CharField(label='Sous-thème', required=True, max_length=120)
    duree_heures = forms.DecimalField(label='Durée (h)', required=True, min_value=0, max_digits=5, decimal_places=2, help_text='Durée en heures. Exemple : 1,5 pour 1 h 30.')

    class Meta:
        model = TPV2
        fields = [
            'titre', 'domaine_principal', 'sous_theme', 'niveau_classe', 'type_activite',
            'usage_pedagogique', 'code', 'resume_eleve', 'objectifs_prof', 'problematique_metier',
            'statut', 'version', 'commentaire_interne',
        ]
        widgets = {
            'resume_eleve': forms.Textarea(attrs={'rows': 3}),
            'objectifs_prof': forms.Textarea(attrs={'rows': 5}),
            'problematique_metier': forms.Textarea(attrs={'rows': 5}),
            'commentaire_interne': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'niveau_classe': 'Classe / niveau',
            'usage_pedagogique': 'Usage',
            'code': 'Nom',
            'objectifs_prof': 'Description du contexte / mise en situation professionnelle',
            'problematique_metier': 'Problématique liée au métier / missions à réaliser',
            'commentaire_interne': 'Commentaire interne',
        }
        help_texts = {
            'domaine_principal': 'Liste déroulante avec ajout manuel possible. Sert au repère automatique.',
            'sous_theme': 'Liste déroulante avec ajout manuel possible. Précise le thème sans modifier le référentiel.',
            'niveau_classe': 'Liste filtrée selon le diplôme : Bac Pro = 2nde / 1ère / Tale ; BTS/CAP = 1ère année / 2ème année.',
            'code': 'Laisser vide ou cocher Nom - Auto pour générer : FORMATION-THEME-SOUSTHEME-001. Le titre reste séparé.',
        }

    def __init__(self, *args, **kwargs):
        allow_status = kwargs.pop('allow_status', True)
        super().__init__(*args, **kwargs)
        # Valeurs usuelles, non bloquantes : le champ reste un texte libre.
        self.fields['type_activite'].widget.attrs.update({'list': 'tpv2-type-list', 'placeholder': 'TP'})
        self.fields['domaine_principal'].widget.attrs.update({'list': 'tpv2-theme-list', 'placeholder': 'DOMOTIQUE'})
        self.fields['sous_theme'].widget.attrs.update({'list': 'tpv2-sous-theme-list', 'placeholder': 'KNX / GTB / PAC / IP...'})
        self.fields['niveau_classe'].widget.attrs.update({'list': 'tpv2-classe-list', 'placeholder': '1ère MELEC'})
        # Saisie en heures côté formulaire, stockage historique en minutes côté base.
        if self.instance and self.instance.pk:
            self.fields['duree_heures'].initial = round((self.instance.duree_minutes or 0) / 60, 2)
        else:
            self.fields['duree_heures'].initial = 2
        self.fields['duree_heures'].widget.attrs.update({'step': '0.25', 'placeholder': '2'})
        self.fields['code'].required = False
        self.fields['code'].widget.attrs.update({'placeholder': 'Auto si vide', 'data-auto-code-input': '1'})
        if not allow_status:
            self.fields['statut'].disabled = True
        self._style_fields()

    def clean_duree_heures(self):
        value = self.cleaned_data.get('duree_heures')
        if value is None:
            raise forms.ValidationError('Indiquer une durée en heures.')
        return value

    def save(self, commit=True):
        obj = super().save(commit=False)
        heures = self.cleaned_data.get('duree_heures')
        if heures is not None:
            obj.duree_minutes = max(1, int(round(float(heures) * 60)))
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class TPV2FilterForm(forms.Form):
    q = forms.CharField(required=False, label='Recherche')
    diplome = forms.ModelChoiceField(queryset=BacDiplome.objects.filter(actif=True), required=False)
    usage = forms.ChoiceField(required=False, choices=[('', '---------')] + list(TPV2.USAGE_CHOICES), label='Usage')
    pivot = forms.ModelChoiceField(queryset=CompetencePivot.objects.all(), required=False, label='Compétence pivot')
    temps_max = forms.DecimalField(required=False, min_value=0, max_digits=5, decimal_places=2, label='Temps max. heures')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TPV2OfficialCompetenceForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2CompetenceOfficielle
        fields = ['competence', 'type_lien', 'niveau_evaluation', 'bareme', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        self.tp = kwargs.pop('tp', None)
        super().__init__(*args, **kwargs)
        qs = BacCompetence.objects.filter(selectable_bac=True).select_related('diplome')
        if self.tp:
            qs = qs.filter(diplome=self.tp.diplome)
        self.fields['competence'].queryset = qs.order_by('code')
        self._style_fields()

    def clean(self):
        cleaned = super().clean()
        competence = cleaned.get('competence')
        if self.tp and competence and competence.diplome_id != self.tp.diplome_id:
            raise forms.ValidationError('Compétence hors référentiel du diplôme choisi.')
        return cleaned


class TPV2SuccessCriterionForm(V2StyledMixin, forms.ModelForm):
    library_criterion = forms.ModelChoiceField(queryset=TPV2CriterionLibrary.objects.none(), required=False, label='Critère prérempli')

    class Meta:
        model = TPV2CritereReussite
        fields = ['library_criterion', 'libelle', 'description', 'niveau_attendu', 'obligatoire', 'ordre']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'library_criterion': 'Liste filtrée par diplôme / métier / thème. Tu peux aussi saisir un critère manuel.'}

    def __init__(self, *args, **kwargs):
        tp = kwargs.pop('tp', None)
        super().__init__(*args, **kwargs)
        qs = TPV2CriterionLibrary.objects.filter(actif=True, type_critere='reussite')
        if tp:
            qs = qs.filter(Q(diplome=tp.diplome) | Q(diplome__isnull=True))
        self.fields['library_criterion'].queryset = qs.order_by('diplome__code', 'metier', 'theme', 'libelle')
        self._style_fields()


class TPV2FinalEvaluationCriterionForm(V2StyledMixin, forms.ModelForm):
    library_criterion = forms.ModelChoiceField(queryset=TPV2CriterionLibrary.objects.none(), required=False, label='Critère prérempli')

    class Meta:
        model = TPV2CritereEvaluationFinale
        fields = ['library_criterion', 'libelle', 'indicateur', 'bareme', 'commentaire', 'ordre']
        widgets = {'indicateur': forms.Textarea(attrs={'rows': 3}), 'commentaire': forms.Textarea(attrs={'rows': 2})}
        help_texts = {'library_criterion': 'Liste filtrée par diplôme / métier / thème. Tu peux aussi saisir un critère manuel.'}

    def __init__(self, *args, **kwargs):
        tp = kwargs.pop('tp', None)
        super().__init__(*args, **kwargs)
        qs = TPV2CriterionLibrary.objects.filter(actif=True, type_critere='evaluation_finale')
        if tp:
            qs = qs.filter(Q(diplome=tp.diplome) | Q(diplome__isnull=True))
        self.fields['library_criterion'].queryset = qs.order_by('diplome__code', 'metier', 'theme', 'libelle')
        self._style_fields()


class TPV2DocumentForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2Document
        fields = ['type_document', 'titre', 'fichier', 'visible_eleve', 'visible_prof', 'actif']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class TPV2ResourceGroupForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2ResourceGroup
        fields = ['titre', 'obligatoire', 'ordre', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'titre': 'Chaque bloc est un bloc OU : une ressource du bloc suffit. Plusieurs blocs successifs sont lus en ET.'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.operator = 'ANY'
        if commit:
            obj.save()
        return obj


class TPV2ResourceItemForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2ResourceItem
        fields = ['source_module', 'resource_type', 'external_id', 'external_code', 'libelle', 'quantite', 'unite', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}
        help_texts = {
            'source_module': 'Référence optionnelle. TP Manager ne modifie pas les données de ToolMag, PedaShop ou System Manager.',
            'external_id': 'Identifiant de l’objet source si connu. Peut rester vide pour une ressource manuelle.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class TPV2LinkedBlockForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2LinkedBlock
        fields = ['sens', 'titre', 'ordre', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class TPV2LinkedTPItemForm(V2StyledMixin, forms.ModelForm):
    class Meta:
        model = TPV2LinkedTPItem
        fields = ['linked_tp', 'niveau_lien', 'ordre', 'commentaire']

    def __init__(self, *args, **kwargs):
        self.block = kwargs.pop('block', None)
        filters = kwargs.pop('filters', None) or {}
        super().__init__(*args, **kwargs)
        qs = TPV2.objects.select_related('diplome').order_by('diplome__code', 'code')
        if self.block:
            qs = qs.exclude(pk=self.block.tp_id)
        q = (filters.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(titre__icontains=q) | Q(domaine_principal__icontains=q) | Q(sous_theme__icontains=q))
        diplome = (filters.get('diplome') or '').strip()
        if diplome:
            qs = qs.filter(diplome_id=diplome)
        niveau = (filters.get('niveau') or '').strip()
        if niveau:
            qs = qs.filter(niveau_classe__icontains=niveau)
        theme = (filters.get('theme') or '').strip()
        if theme:
            qs = qs.filter(Q(domaine_principal__icontains=theme) | Q(sous_theme__icontains=theme))
        usage = (filters.get('usage') or '').strip()
        if usage:
            qs = qs.filter(usage_pedagogique=usage)
        self.fields['linked_tp'].queryset = qs[:250]
        self._style_fields()


def build_dynamic_field_definitions(diplome: BacDiplome):
    """Retourne les champs dynamiques configurés pour le diplôme, avec options."""
    fields = []
    if not diplome:
        return fields
    for champ in BacChampTP.objects.filter(diplome=diplome, actif=True).prefetch_related('options').order_by('phase', 'ordre', 'code'):
        fields.append(champ)
    return fields


def save_dynamic_values(tp: TPV2, post_data):
    """Enregistre les valeurs des champs dynamiques du diplôme du TP."""
    for champ in BacChampTP.objects.filter(diplome=tp.diplome, actif=True):
        key = f'dyn_{champ.id}'
        if champ.type_champ == 'boolean':
            value = 'oui' if post_data.get(key) else 'non'
        else:
            value = (post_data.get(key) or '').strip()
        if value or champ.obligatoire:
            TPV2ChampValeur.objects.update_or_create(tp=tp, champ=champ, defaults={'valeur': value})
        else:
            TPV2ChampValeur.objects.filter(tp=tp, champ=champ).delete()


class TPV2ParcoursAssignForm(V2StyledMixin, forms.Form):
    tps = forms.ModelMultipleChoiceField(
        queryset=TPV2.objects.select_related('diplome').order_by('diplome__code', 'code'),
        label='TP à affecter',
        widget=forms.SelectMultiple(attrs={'size': 10}),
    )
    eleves = forms.ModelMultipleChoiceField(
        queryset=TpUser.objects.filter(active=True).order_by('class_name', 'last_name', 'first_name'),
        label='Élèves concernés',
        widget=forms.SelectMultiple(attrs={'size': 12}),
    )
    sequence = forms.ModelChoiceField(queryset=SequencePedagogique.objects.order_by('-date_debut', 'titre'), required=False, label='Séquence / parcours associé')
    statut = forms.ChoiceField(choices=ParcoursEleveTP.STATUT_CHOICES, initial='a_faire', label='Statut initial')
    commentaire_prof = forms.CharField(required=False, label='Commentaire professeur commun', widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, **kwargs):
        filters = kwargs.pop('filters', None) or {}
        super().__init__(*args, **kwargs)
        eleves = self.fields['eleves'].queryset
        classe = (filters.get('classe') or '').strip()
        formation = (filters.get('formation') or '').strip()
        q_eleve = (filters.get('q_eleve') or '').strip()
        if classe:
            eleves = eleves.filter(class_name__icontains=classe)
        if formation:
            eleves = eleves.filter(formation_code__icontains=formation)
        if q_eleve:
            eleves = eleves.filter(Q(code__icontains=q_eleve) | Q(username__icontains=q_eleve) | Q(first_name__icontains=q_eleve) | Q(last_name__icontains=q_eleve))
        self.fields['eleves'].queryset = eleves[:500]

        tps = self.fields['tps'].queryset
        diplome = (filters.get('diplome') or '').strip()
        q_tp = (filters.get('q_tp') or '').strip()
        theme = (filters.get('theme') or '').strip()
        niveau = (filters.get('niveau') or '').strip()
        if diplome:
            tps = tps.filter(diplome_id=diplome)
        if q_tp:
            tps = tps.filter(Q(code__icontains=q_tp) | Q(titre__icontains=q_tp) | Q(resume_eleve__icontains=q_tp))
        if theme:
            tps = tps.filter(Q(domaine_principal__icontains=theme) | Q(sous_theme__icontains=theme))
        if niveau:
            tps = tps.filter(niveau_classe__icontains=niveau)
        self.fields['tps'].queryset = tps[:500]
        self._style_fields()
