from __future__ import annotations
from django import forms
from django.utils import timezone
from .models import (
    normalize_code,
    Formation, Niveau, FormationNiveau, ZoneApprentissage, ThemeGeneral, ThemeSecondaire, TypeTP,
    SystemePedagogiqueRef, Referentiel, BlocCompetence, Competence, ActiviteReferentiel, TacheReferentiel,
    TP, TPFormationNiveau, TPSysteme, TPCompetence, TPPrerequis, TPSuivant, TPDocument,
    SerieTP, SerieTPItem, SequencePedagogique, SequenceTP, ParcoursEleveTP, TraceEleveTP, EvaluationCompetenceTP,
    TpUser, SavoirAssocie, CritereEvaluation, IndicateurEvaluation, TacheCompetence, TPTache, TPSavoir, TPCritere, TPContributionPermission,
)


class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            if not isinstance(field.widget, forms.CheckboxInput) and not isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = (css + ' form-control').strip()
            if isinstance(field.widget, forms.ClearableFileInput) and ('photo' in name.lower() or field.__class__.__name__ == 'ImageField'):
                field.widget.attrs.setdefault('accept', 'image/*')
                field.widget.attrs.setdefault('data-camera-upload', '1')


class TPForm(BaseStyledForm):
    new_zone_apprentissage = forms.CharField(required=False, label='Nouvelle zone si absente')
    new_theme_general = forms.CharField(required=False, label='Nouveau thème général si absent')
    new_theme_secondaire = forms.CharField(required=False, label='Nouveau sous-thème si absent')
    new_type_tp = forms.CharField(required=False, label='Nouveau type de TP si absent')

    class Meta:
        model = TP
        fields = ['code', 'titre', 'resume_apprentissages', 'temps_estime_minutes', 'zone_apprentissage', 'new_zone_apprentissage', 'theme_general', 'new_theme_general', 'theme_secondaire', 'new_theme_secondaire', 'formation_principale', 'type_tp', 'new_type_tp', 'difficulte', 'statut', 'version', 'commentaire_interne']
        widgets = {
            'resume_apprentissages': forms.Textarea(attrs={'rows': 5}),
            'commentaire_interne': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {'code': 'Laisser vide pour générer automatiquement : CODE_ZONE-CODE_FORMATION-CODE_THEME-INDICE.'}

    def __init__(self, *args, **kwargs):
        allow_status = kwargs.pop('allow_status', True)
        super().__init__(*args, **kwargs)
        for name in ['new_zone_apprentissage', 'new_theme_general', 'new_theme_secondaire', 'new_type_tp']:
            self.fields[name].help_text = 'Créer automatiquement cette valeur locale si elle n’existe pas dans la liste.'
        if not allow_status:
            self.fields['statut'].disabled = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        nz = (self.cleaned_data.get('new_zone_apprentissage') or '').strip()
        if nz:
            obj.zone_apprentissage, _ = ZoneApprentissage.objects.get_or_create(code=normalize_code(nz, 'ZONE', 40), defaults={'nom': nz})
        ntg = (self.cleaned_data.get('new_theme_general') or '').strip()
        if ntg:
            obj.theme_general, _ = ThemeGeneral.objects.get_or_create(code=normalize_code(ntg, 'THEME', 40), defaults={'nom': ntg})
        nts = (self.cleaned_data.get('new_theme_secondaire') or '').strip()
        if nts:
            tg = obj.theme_general or self.cleaned_data.get('theme_general')
            obj.theme_secondaire, _ = ThemeSecondaire.objects.get_or_create(code=normalize_code(nts, 'STHEME', 40), defaults={'nom': nts, 'theme_general': tg})
        ntype = (self.cleaned_data.get('new_type_tp') or '').strip()
        if ntype:
            obj.type_tp, _ = TypeTP.objects.get_or_create(code=normalize_code(ntype, 'TYPE', 40), defaults={'nom': ntype})
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class TPFilterForm(forms.Form):
    q = forms.CharField(required=False, label='Recherche')
    formation = forms.ModelChoiceField(queryset=Formation.objects.filter(active=True), required=False)
    niveau = forms.ModelChoiceField(queryset=Niveau.objects.filter(active=True), required=False)
    zone = forms.ModelChoiceField(queryset=ZoneApprentissage.objects.filter(active=True), required=False)
    theme_general = forms.ModelChoiceField(queryset=ThemeGeneral.objects.filter(active=True), required=False)
    theme_secondaire = forms.ModelChoiceField(queryset=ThemeSecondaire.objects.filter(active=True), required=False)
    competence = forms.ModelChoiceField(queryset=Competence.objects.filter(active=True), required=False)
    temps_max = forms.IntegerField(required=False, min_value=1, label='Temps max. minutes')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TPDocumentForm(BaseStyledForm):
    class Meta:
        model = TPDocument
        fields = ['type_document', 'titre', 'fichier', 'version', 'visible_eleve', 'visible_prof', 'actif']


class TPFormationNiveauForm(BaseStyledForm):
    class Meta:
        model = TPFormationNiveau
        fields = ['formation', 'niveau']


class TPSystemeForm(BaseStyledForm):
    class Meta:
        model = TPSysteme
        fields = ['systeme', 'obligatoire', 'commentaire']


class TPCompetenceForm(BaseStyledForm):
    class Meta:
        model = TPCompetence
        fields = ['competence', 'type_lien']

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation', None)
        super().__init__(*args, **kwargs)
        qs = Competence.objects.filter(active=True).select_related('bloc__referentiel__formation')
        if formation:
            qs = qs.filter(bloc__referentiel__formation=formation)
        self.fields['competence'].queryset = qs


class TPPrerequisForm(BaseStyledForm):
    class Meta:
        model = TPPrerequis
        fields = ['prerequis', 'obligatoire']

    def __init__(self, *args, **kwargs):
        current_tp = kwargs.pop('current_tp', None)
        super().__init__(*args, **kwargs)
        if current_tp:
            self.fields['prerequis'].queryset = TP.objects.exclude(pk=current_tp.pk).order_by('code')


class TPSuivantForm(BaseStyledForm):
    class Meta:
        model = TPSuivant
        fields = ['suivant', 'commentaire']

    def __init__(self, *args, **kwargs):
        current_tp = kwargs.pop('current_tp', None)
        super().__init__(*args, **kwargs)
        if current_tp:
            self.fields['suivant'].queryset = TP.objects.exclude(pk=current_tp.pk).order_by('code')


class CodeNamedForm(BaseStyledForm):
    class Meta:
        fields = ['code', 'nom', 'description', 'active', 'ordre']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class ZoneApprentissageForm(CodeNamedForm):
    class Meta(CodeNamedForm.Meta):
        model = ZoneApprentissage


class ThemeGeneralForm(CodeNamedForm):
    class Meta(CodeNamedForm.Meta):
        model = ThemeGeneral


class ThemeSecondaireForm(CodeNamedForm):
    class Meta(CodeNamedForm.Meta):
        model = ThemeSecondaire
        fields = ['theme_general', 'code', 'nom', 'description', 'active', 'ordre']


class TypeTPForm(CodeNamedForm):
    class Meta(CodeNamedForm.Meta):
        model = TypeTP


class SystemeRefForm(BaseStyledForm):
    class Meta:
        model = SystemePedagogiqueRef
        fields = ['code', 'designation', 'zone_code', 'zone_nom', 'statut', 'actif']


class NiveauForm(BaseStyledForm):
    class Meta:
        model = Niveau
        fields = ['code', 'nom', 'ordre', 'active']


class FormationNiveauForm(BaseStyledForm):
    class Meta:
        model = FormationNiveau
        fields = ['formation', 'niveau', 'active']


class SequenceForm(BaseStyledForm):
    class Meta:
        model = SequencePedagogique
        fields = ['titre', 'description', 'formation', 'niveau', 'classe_ou_groupe', 'date_debut', 'date_fin', 'statut', 'eleves']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
            'eleves': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eleves'].queryset = TpUser.objects.filter(active=True).order_by('last_name', 'first_name')


class SequenceTPForm(BaseStyledForm):
    class Meta:
        model = SequenceTP
        fields = ['tp', 'ordre', 'date_prevue', 'temps_prevu_minutes']
        widgets = {'date_prevue': forms.DateInput(attrs={'type': 'date'})}


class ParcoursEleveTPForm(BaseStyledForm):
    class Meta:
        model = ParcoursEleveTP
        fields = ['eleve', 'tp', 'sequence', 'statut', 'difficulte', 'souhaite_refaire', 'commentaire_eleve', 'commentaire_prof', 'systeme_utilise']
        widgets = {'commentaire_eleve': forms.Textarea(attrs={'rows': 3}), 'commentaire_prof': forms.Textarea(attrs={'rows': 3})}


class StudentParcoursUpdateForm(BaseStyledForm):
    class Meta:
        model = ParcoursEleveTP
        fields = ['statut', 'difficulte', 'souhaite_refaire', 'commentaire_eleve', 'systeme_utilise']
        widgets = {'commentaire_eleve': forms.Textarea(attrs={'rows': 4})}


class ProfParcoursUpdateForm(BaseStyledForm):
    class Meta:
        model = ParcoursEleveTP
        fields = ['statut', 'commentaire_prof']
        widgets = {'commentaire_prof': forms.Textarea(attrs={'rows': 4})}


class TraceEleveTPForm(BaseStyledForm):
    class Meta:
        model = TraceEleveTP
        fields = ['type_trace', 'titre', 'contenu_texte', 'fichier', 'visible_prof']
        widgets = {
            'contenu_texte': forms.Textarea(attrs={'rows': 5}),
            'fichier': forms.ClearableFileInput(attrs={'data-camera-upload-conditional': 'photo', 'data-camera-select-name': 'type_trace'}),
        }


class EvaluationCompetenceForm(BaseStyledForm):
    class Meta:
        model = EvaluationCompetenceTP
        fields = ['competence', 'niveau', 'commentaire_prof', 'trace_associee']
        widgets = {'commentaire_prof': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        parcours = kwargs.pop('parcours', None)
        super().__init__(*args, **kwargs)
        if parcours:
            self.fields['competence'].queryset = Competence.objects.filter(tp_links__tp=parcours.tp).distinct()
            self.fields['trace_associee'].queryset = parcours.traces.all()


class ReferentielImportCsvForm(forms.Form):
    formation = forms.ModelChoiceField(queryset=Formation.objects.filter(active=True), required=True)
    nom = forms.CharField(max_length=220, initial='Référentiel importé')
    version = forms.CharField(max_length=80, required=False)
    fichier = forms.FileField(help_text='CSV séparateur ; avec colonnes : bloc_code, bloc_libelle, competence_code, competence_libelle, sous_competence_code, sous_competence_libelle, activite_code, activite_libelle, tache_code, tache_libelle')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class TPTacheForm(BaseStyledForm):
    class Meta:
        model = TPTache
        fields = ['tache', 'ordre_execution', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation', None)
        super().__init__(*args, **kwargs)
        qs = TacheReferentiel.objects.select_related('activite__referentiel__formation')
        if formation:
            qs = qs.filter(activite__referentiel__formation=formation)
        self.fields['tache'].queryset = qs


class TPSavoirForm(BaseStyledForm):
    class Meta:
        model = TPSavoir
        fields = ['savoir', 'niveau_mobilisation', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation', None)
        super().__init__(*args, **kwargs)
        qs = SavoirAssocie.objects.select_related('referentiel__formation')
        if formation:
            qs = qs.filter(referentiel__formation=formation)
        self.fields['savoir'].queryset = qs


class TPCritereForm(BaseStyledForm):
    class Meta:
        model = TPCritere
        fields = ['critere', 'indicateur', 'bareme', 'obligatoire', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        formation = kwargs.pop('formation', None)
        super().__init__(*args, **kwargs)
        qs = CritereEvaluation.objects.select_related('competence__bloc__referentiel__formation')
        if formation:
            qs = qs.filter(competence__bloc__referentiel__formation=formation)
        self.fields['critere'].queryset = qs
        self.fields['indicateur'].queryset = IndicateurEvaluation.objects.select_related('critere')


class TPContributionPermissionForm(BaseStyledForm):
    class Meta:
        model = TPContributionPermission
        fields = ['eleve', 'tp', 'date_debut', 'date_fin', 'peut_creer', 'peut_modifier', 'peut_ajouter_documents', 'commentaire', 'actif']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eleve'].queryset = TpUser.objects.filter(active=True).order_by('last_name', 'first_name')
        self.fields['tp'].queryset = TP.objects.exclude(statut='archive').order_by('code')
        self.fields['tp'].required = False
