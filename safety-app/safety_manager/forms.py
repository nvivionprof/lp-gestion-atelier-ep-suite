from django import forms
from .models import (
    SafetyZone, WorkUnit, RiskAssessment, PreventionAction, SafetyEvent, EventFact,
    CauseAnalysis, FiveWhyLine, IshikawaCause, CauseTreeNode, CauseTreeLink, SafetyDocument, DUERPVersion, SafetyUser, DangerousSituation
)


class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.ClearableFileInput)):
                field.widget.attrs.setdefault('class', 'input')
            if isinstance(field.widget, forms.ClearableFileInput) and ('photo' in name.lower() or field.__class__.__name__ == 'ImageField'):
                field.widget.attrs.setdefault('accept', 'image/*')
                field.widget.attrs.setdefault('data-camera-upload', '1')


class SafetyZoneForm(BaseStyledForm):
    class Meta:
        model = SafetyZone
        fields = ['code', 'nom', 'description', 'type_zone', 'actif', 'ordre_affichage']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class WorkUnitForm(BaseStyledForm):
    class Meta:
        model = WorkUnit
        fields = ['code', 'nom', 'description', 'zone', 'nombre_personnes_exposees', 'responsable', 'actif']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class RiskAssessmentForm(BaseStyledForm):
    class Meta:
        model = RiskAssessment
        fields = [
            'unite_travail', 'famille_risque', 'danger', 'situation_dangereuse', 'dommage_potentiel',
            'personnes_exposees', 'mesures_existantes', 'gravite', 'frequence', 'mesures_a_proposer',
            'responsable_suivi', 'statut', 'date_evaluation', 'date_revision_prevue'
        ]
        widgets = {
            'danger': forms.Textarea(attrs={'rows': 3}),
            'situation_dangereuse': forms.Textarea(attrs={'rows': 3}),
            'dommage_potentiel': forms.Textarea(attrs={'rows': 3}),
            'personnes_exposees': forms.Textarea(attrs={'rows': 2}),
            'mesures_existantes': forms.Textarea(attrs={'rows': 3}),
            'mesures_a_proposer': forms.Textarea(attrs={'rows': 3}),
            'date_evaluation': forms.DateInput(attrs={'type': 'date'}),
            'date_revision_prevue': forms.DateInput(attrs={'type': 'date'}),
        }


class PreventionActionForm(BaseStyledForm):
    class Meta:
        model = PreventionAction
        fields = [
            'titre', 'description', 'type_action', 'origine', 'risk_assessment', 'event', 'dangerous_situation', 'responsable',
            'priorite', 'echeance', 'cout_previsionnel', 'statut', 'date_realisation', 'preuve',
            'commentaire', 'efficacite_apres_action', 'nouveaux_risques_identifies', 'date_verification',
            'action_stable', 'integree_travail_reel', 'ne_deplace_pas_risque', 'agit_causes_profondes', 'portee_generale'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'echeance': forms.DateInput(attrs={'type': 'date'}),
            'date_realisation': forms.DateInput(attrs={'type': 'date'}),
            'date_verification': forms.DateInput(attrs={'type': 'date'}),
            'commentaire': forms.Textarea(attrs={'rows': 3}),
            'efficacite_apres_action': forms.Textarea(attrs={'rows': 3}),
            'nouveaux_risques_identifies': forms.Textarea(attrs={'rows': 3}),
        }


class SafetyEventQuickForm(BaseStyledForm):
    class Meta:
        model = SafetyEvent
        fields = [
            'type_evenement', 'date', 'heure', 'lieu', 'zone', 'unite_travail', 'personne_concernee',
            'classe_ou_groupe', 'temoins', 'description_courte', 'recit_detaille', 'dommage', 'nature_lesion',
            'siege_lesion', 'accident_declare', 'avec_arret', 'nombre_jours_arret', 'secours_intervenus',
            'sst_intervenus', 'materiel_source', 'materiel_implique', 'outil_toolmag_id', 'statut_analyse'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure': forms.TimeInput(attrs={'type': 'time'}),
            'temoins': forms.Textarea(attrs={'rows': 2}),
            'recit_detaille': forms.Textarea(attrs={'rows': 5}),
            'dommage': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        class_filter = kwargs.pop('class_filter', None)
        super().__init__(*args, **kwargs)
        classes = list(SafetyUser.objects.filter(active=True).exclude(class_name='').values_list('class_name', flat=True).distinct().order_by('class_name'))
        self.fields['classe_ou_groupe'] = forms.ChoiceField(required=False, choices=[('', '— Classe / groupe —')] + [(c, c) for c in classes], label='Classe / groupe')
        qs = SafetyUser.objects.filter(active=True).order_by('last_name', 'first_name', 'code')
        data = self.data if self.is_bound else None
        selected_class = class_filter or (data.get('classe_ou_groupe') if data else '') or (self.instance.class_name if getattr(self, 'instance', None) and self.instance.pk else '')
        if selected_class:
            qs = qs.filter(class_name=selected_class)
        self.fields['personne_concernee'].queryset = qs
        for name, field in self.fields.items():
            if field.required:
                field.label = f'{field.label or name} *'
                field.widget.attrs.setdefault('data-required', '1')


class EventFactForm(BaseStyledForm):
    class Meta:
        model = EventFact
        fields = ['description', 'categorie', 'type_fait', 'est_verifie', 'source', 'commentaire']
        widgets = {'description': forms.Textarea(attrs={'rows': 3}), 'commentaire': forms.Textarea(attrs={'rows': 2})}


class CauseAnalysisForm(BaseStyledForm):
    class Meta:
        model = CauseAnalysis
        fields = ['methode', 'synthese', 'causes_directes', 'causes_profondes', 'facteurs_potentiels_accident', 'statut', 'validateur', 'date_validation']
        widgets = {
            'synthese': forms.Textarea(attrs={'rows': 3}),
            'causes_directes': forms.Textarea(attrs={'rows': 3}),
            'causes_profondes': forms.Textarea(attrs={'rows': 3}),
            'facteurs_potentiels_accident': forms.Textarea(attrs={'rows': 3}),
            'date_validation': forms.DateInput(attrs={'type': 'date'}),
        }


class FiveWhyLineForm(BaseStyledForm):
    class Meta:
        model = FiveWhyLine
        fields = ['ordre', 'question', 'reponse_factuelle', 'cause_identifiee']
        widgets = {'reponse_factuelle': forms.Textarea(attrs={'rows': 2}), 'cause_identifiee': forms.Textarea(attrs={'rows': 2})}


class IshikawaCauseForm(BaseStyledForm):
    class Meta:
        model = IshikawaCause
        fields = ['categorie', 'cause', 'commentaire']
        widgets = {'cause': forms.Textarea(attrs={'rows': 2}), 'commentaire': forms.Textarea(attrs={'rows': 2})}


class CauseTreeNodeForm(BaseStyledForm):
    class Meta:
        model = CauseTreeNode
        fields = ['fact', 'libelle', 'type_node', 'position_x', 'position_y']


class CauseTreeLinkForm(BaseStyledForm):
    class Meta:
        model = CauseTreeLink
        fields = ['source_node', 'target_node', 'type_lien', 'groupe_logique']


class SafetyDocumentForm(BaseStyledForm):
    class Meta:
        model = SafetyDocument
        fields = ['titre', 'type_document', 'fichier', 'event', 'action', 'risk_assessment']


class DUERPVersionForm(BaseStyledForm):
    class Meta:
        model = DUERPVersion
        fields = ['perimetre', 'commentaire', 'statut']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 3})}


class DangerousSituationForm(BaseStyledForm):
    class Meta:
        model = DangerousSituation
        fields = ['titre', 'description', 'zone', 'unite_travail', 'famille_risque', 'inclure_duerp', 'risk_assessment', 'priorite', 'statut']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}


class PublicSafetyEventForm(BaseStyledForm):
    """Formulaire public de déclaration rapide.

    Ce formulaire est volontairement plus court que la fiche événement complète.
    Il sert à signaler vite un accident, incident, presqu'accident ou situation
    dangereuse depuis un poste atelier, sans exposer les fonctions d'analyse.
    """
    class Meta:
        model = SafetyEvent
        fields = [
            'type_evenement', 'date', 'heure', 'lieu', 'zone', 'unite_travail',
            'classe_ou_groupe', 'temoins', 'description_courte', 'recit_detaille',
            'dommage', 'secours_intervenus', 'sst_intervenus', 'materiel_implique'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure': forms.TimeInput(attrs={'type': 'time'}),
            'temoins': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Nom du témoin ou groupe, si connu.'}),
            'recit_detaille': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Décrire uniquement des faits observables : quoi, où, quand, comment.'}),
            'dommage': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dommage visible ou conséquence immédiate, sans diagnostic médical.'}),
        }
