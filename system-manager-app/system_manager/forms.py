from __future__ import annotations
from django import forms
from django.utils import timezone
from .models import (
    WorkshopZone, WorkshopSubZone, Formation, Niveau, SchoolClass, SystemUser, EducationalSystem, DocumentCategory, SystemDocument, SystemEquipment, DefaultCheckTemplate,
    CheckItem, ReservationGroup, Reservation, WorkSession, SystemAnomaly, WorkshopBlock, WorkshopBlockSlot, SystemTPAssociation, SystemSafetyLink, MaintenanceIntervention, MaintenanceCheckLine, MaintenanceDrawingZone, SystemChangeLog, TemporarySystemPermission
)


class BaseStyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
            if isinstance(field.widget, forms.ClearableFileInput) and ('photo' in name.lower() or field.__class__.__name__ == 'ImageField'):
                field.widget.attrs.setdefault('accept', 'image/*')
                field.widget.attrs.setdefault('capture', 'environment')
                field.widget.attrs.setdefault('data-camera-upload', '1')


class ZoneForm(BaseStyledForm):
    class Meta:
        model = WorkshopZone
        fields = ['code', 'nom', 'description', 'responsable', 'active', 'ordre_affichage']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class SubZoneForm(BaseStyledForm):
    class Meta:
        model = WorkshopSubZone
        fields = ['zone', 'code', 'nom', 'description', 'active', 'ordre_affichage']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}


class FormationForm(BaseStyledForm):
    class Meta:
        model = Formation
        fields = ['code', 'nom', 'active']


class NiveauForm(BaseStyledForm):
    class Meta:
        model = Niveau
        fields = ['code', 'nom', 'ordre', 'active']


class EducationalSystemForm(BaseStyledForm):
    class Meta:
        model = EducationalSystem
        fields = ['code', 'designation', 'description', 'parent_system', 'photo', 'zone', 'sous_zone', 'formations', 'niveaux', 'professeur_referent', 'statut', 'actif', 'commentaire_interne']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'commentaire_interne': forms.Textarea(attrs={'rows': 3}),
            'formations': forms.CheckboxSelectMultiple,
            'niveaux': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parents = EducationalSystem.objects.filter(actif=True).order_by(
            'zone__code', 'code'
        )
        if self.instance and self.instance.pk:
            excluded_ids = {self.instance.pk}
            frontier = [self.instance.pk]
            while frontier:
                child_ids = list(
                    EducationalSystem.objects.filter(parent_system_id__in=frontier)
                    .values_list('pk', flat=True)
                )
                frontier = [pk for pk in child_ids if pk not in excluded_ids]
                excluded_ids.update(frontier)
            parents = parents.exclude(pk__in=excluded_ids)
        self.fields['parent_system'].queryset = parents
        self.fields['parent_system'].required = False
        self.fields['parent_system'].label = 'Système parent (facultatif)'
        self.fields['parent_system'].help_text = (
            'Laisser vide pour une racine. Tout système actif peut devenir le parent '
            'd’un nouveau sous-système, quelle que soit sa profondeur.'
        )


class DocumentCategoryForm(BaseStyledForm):
    class Meta:
        model = DocumentCategory
        fields = ['code', 'nom', 'parent', 'section_code', 'ordre', 'active']


class SystemDocumentForm(BaseStyledForm):
    class Meta:
        model = SystemDocument
        fields = ['categorie', 'titre', 'type_document', 'version', 'parent_document', 'fichier', 'url', 'description', 'visible_students', 'teacher_only', 'actif']
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        systeme = kwargs.pop('systeme', None)
        super().__init__(*args, **kwargs)
        qs = SystemDocument.objects.filter(actif=True).order_by('titre')
        if systeme is not None:
            qs = qs.filter(systeme=systeme)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['parent_document'].queryset = qs
        self.fields['parent_document'].required = False
        self.fields['parent_document'].label = 'Version précédente / document remplacé'
        self.fields['visible_students'].label = 'Visible par les élèves'
        self.fields['teacher_only'].label = 'Correction / contenu professeur uniquement'
        self.fields['fichier'].help_text = 'DOCX/XLSX/PPTX : une prévisualisation PDF sera générée automatiquement si LibreOffice est disponible.'


class SystemEquipmentForm(BaseStyledForm):
    class Meta:
        model = SystemEquipment
        fields = [
            'code', 'designation', 'type_equipement', 'marque', 'modele',
            'numero_serie', 'quantite', 'toolmag_code', 'description',
            'ordre', 'actif',
        ]
        widgets = {'description': forms.Textarea(attrs={'rows': 3})}




class DefaultCheckTemplateForm(BaseStyledForm):
    class Meta:
        model = DefaultCheckTemplate
        fields = ['libelle', 'aide', 'phase', 'type_reponse', 'expected_response', 'obligatoire', 'bloquant_si_non', 'ordre', 'active']
        widgets = {'aide': forms.Textarea(attrs={'rows': 2})}


class CheckItemForm(BaseStyledForm):
    class Meta:
        model = CheckItem
        fields = ['libelle', 'aide', 'phase', 'type_reponse', 'expected_response', 'obligatoire', 'bloquant_si_non', 'ordre', 'actif']
        widgets = {'aide': forms.Textarea(attrs={'rows': 2})}


class ReservationForm(BaseStyledForm):
    class Meta:
        model = Reservation
        fields = ['systeme', 'professeur', 'formation', 'niveau', 'classe_ou_groupe', 'tp_code', 'tp_titre', 'date_debut', 'date_fin', 'statut', 'commentaire']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'commentaire': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['date_debut', 'date_fin']:
            if self.instance and getattr(self.instance, name, None):
                self.fields[name].initial = timezone.localtime(getattr(self.instance, name)).strftime('%Y-%m-%dT%H:%M')


class QuickReservationForm(ReservationForm):
    class Meta(ReservationForm.Meta):
        fields = ['professeur', 'formation', 'niveau', 'classe_ou_groupe', 'tp_code', 'tp_titre', 'date_debut', 'date_fin', 'commentaire']


class WorkSessionStartForm(BaseStyledForm):
    class Meta:
        model = WorkSession
        fields = ['reservation', 'professeur_referent', 'tp_code', 'tp_titre', 'commentaire_prise']
        widgets = {'commentaire_prise': forms.Textarea(attrs={'rows': 3})}


class WorkSessionReturnForm(BaseStyledForm):
    class Meta:
        model = WorkSession
        fields = ['commentaire_restitution']
        widgets = {'commentaire_restitution': forms.Textarea(attrs={'rows': 3})}


class SystemAnomalyForm(BaseStyledForm):
    class Meta:
        model = SystemAnomaly
        fields = ['titre', 'description', 'gravite', 'statut', 'blocking', 'action_realisee', 'lift_request_comment']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'action_realisee': forms.Textarea(attrs={'rows': 3}), 'lift_request_comment': forms.Textarea(attrs={'rows': 3})}


class WorkshopBlockForm(BaseStyledForm):
    class Meta:
        model = WorkshopBlock
        fields = ['code', 'nom', 'description', 'classes', 'active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'classes': forms.SelectMultiple(attrs={'size': 12, 'data-filterable': '1'}),
        }


class WorkshopBlockSlotForm(BaseStyledForm):
    class Meta:
        model = WorkshopBlockSlot
        fields = ['block', 'day_of_week', 'label', 'start_time', 'end_time', 'active']
        widgets = {'start_time': forms.TimeInput(attrs={'type': 'time'}), 'end_time': forms.TimeInput(attrs={'type': 'time'})}


class SystemTPAssociationForm(BaseStyledForm):
    class Meta:
        model = SystemTPAssociation
        fields = ['source', 'tp_code', 'tp_titre', 'sequence_code', 'sequence_titre', 'formation', 'niveau', 'url', 'active']


class SystemSafetyLinkForm(BaseStyledForm):
    class Meta:
        model = SystemSafetyLink
        fields = ['source', 'safety_object_type', 'safety_object_id', 'titre', 'niveau_risque', 'consignation_requise', 'habilitations_requises', 'epi_requis', 'procedure_resume', 'url', 'active']
        widgets = {'epi_requis': forms.Textarea(attrs={'rows': 3}), 'procedure_resume': forms.Textarea(attrs={'rows': 4})}


class MaintenanceInterventionForm(BaseStyledForm):
    class Meta:
        model = MaintenanceIntervention
        fields = [
            'type_action', 'statut', 'demandeur_nom', 'executant_nom', 'executant_prenom', 'executant_classe', 'habilitation', 'exploitant_nom',
            'debut_intervention', 'fin_intervention', 'constat_operateur', 'fonctionne_bien', 'ne_fonctionne_pas',
            'procedure_conditions_mesure', 'appareils_mesure_references', 'calculs_prealables', 'reglages_valeurs', 'tableau_releves',
            'exploitation_releves', 'conclusion_conformite', 'epi', 'ecs', 'eis', 'appareils_mesure', 'action_realisee', 'suite_a_donner', 'safety_link'
        ]
        widgets = {
            'debut_intervention': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fin_intervention': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'constat_operateur': forms.Textarea(attrs={'rows': 3}), 'fonctionne_bien': forms.Textarea(attrs={'rows': 3}), 'ne_fonctionne_pas': forms.Textarea(attrs={'rows': 3}),
            'procedure_conditions_mesure': forms.Textarea(attrs={'rows': 4}), 'appareils_mesure_references': forms.Textarea(attrs={'rows': 2}),
            'calculs_prealables': forms.Textarea(attrs={'rows': 3}), 'reglages_valeurs': forms.Textarea(attrs={'rows': 3}), 'tableau_releves': forms.Textarea(attrs={'rows': 4}),
            'exploitation_releves': forms.Textarea(attrs={'rows': 3}), 'conclusion_conformite': forms.Textarea(attrs={'rows': 4}),
            'epi': forms.Textarea(attrs={'rows': 3}), 'ecs': forms.Textarea(attrs={'rows': 3}), 'eis': forms.Textarea(attrs={'rows': 3}), 'appareils_mesure': forms.Textarea(attrs={'rows': 2}),
            'action_realisee': forms.Textarea(attrs={'rows': 4}), 'suite_a_donner': forms.Textarea(attrs={'rows': 3}),
        }


class MaintenanceCheckLineForm(BaseStyledForm):
    class Meta:
        model = MaintenanceCheckLine
        fields = ['ordre', 'hypothese', 'controle', 'conditions', 'bornes_test', 'appareil_utilise', 'sous_tension', 'hors_tension', 'valeur_attendue', 'valeur_mesuree', 'conclusion']
        widgets = {'hypothese': forms.Textarea(attrs={'rows': 2}), 'controle': forms.Textarea(attrs={'rows': 2}), 'conditions': forms.Textarea(attrs={'rows': 2}), 'conclusion': forms.Textarea(attrs={'rows': 2})}


class MaintenanceDrawingZoneForm(BaseStyledForm):
    class Meta:
        model = MaintenanceDrawingZone
        fields = ['zone_type', 'mode', 'titre', 'image', 'canvas_data', 'note', 'grid_enabled']
        widgets = {'canvas_data': forms.HiddenInput(attrs={'data-drawing-canvas-data': '1'}), 'note': forms.Textarea(attrs={'rows': 3})}


class SystemChangeLogForm(BaseStyledForm):
    source_ref = forms.ChoiceField(required=False, label='Préremplir depuis un élément existant')

    class Meta:
        model = SystemChangeLog
        fields = ['source_ref', 'type_changement', 'titre', 'description', 'version_avant', 'version_apres', 'date_effet']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}), 'date_effet': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        systeme = kwargs.pop('systeme', None)
        super().__init__(*args, **kwargs)
        choices = [('', '— Saisie libre —')]
        if systeme is not None:
            for d in systeme.documents.filter(actif=True).order_by('titre')[:200]:
                label = f'Document — {d.titre}' + (f' / v{d.version}' if d.version else '')
                choices.append((f'doc:{d.pk}', label))
            for m in systeme.maintenance_interventions.order_by('-created_at')[:100]:
                choices.append((f'maint:{m.pk}', f'Maintenance — {m.reference} — {m.get_type_action_display()}'))
        self.fields['source_ref'].choices = choices


class TemporarySystemPermissionForm(BaseStyledForm):
    class Meta:
        model = TemporarySystemPermission
        fields = ['user', 'school_class', 'date_debut', 'date_fin', 'can_create', 'can_edit', 'zones', 'systems', 'reason', 'active']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'zones': forms.SelectMultiple(attrs={'size': 8, 'data-filterable': '1'}),
            'systems': forms.SelectMultiple(attrs={'size': 12, 'data-filterable': '1'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = SystemUser.objects.filter(active=True).order_by('class_name', 'last_name', 'first_name', 'code')
        self.fields['user'].required = False
        self.fields['user'].widget.attrs['data-filterable'] = '1'
        self.fields['school_class'].required = False
        self.fields['school_class'].queryset = SchoolClass.objects.filter(active=True).order_by('nom', 'school_year')
        self.fields['school_class'].widget.attrs['data-filterable'] = '1'
        self.fields['zones'].queryset = WorkshopZone.objects.filter(active=True).order_by('ordre_affichage', 'code')
        self.fields['systems'].queryset = EducationalSystem.objects.filter(actif=True).select_related('zone').order_by('zone__code', 'code')
        for name in ['date_debut', 'date_fin']:
            if self.instance and getattr(self.instance, name, None):
                self.fields[name].initial = timezone.localtime(getattr(self.instance, name)).strftime('%Y-%m-%dT%H:%M')


class ReservationGroupForm(BaseStyledForm):
    classe_ou_groupe_libre = forms.CharField(max_length=120, required=False, label='Groupe libre / complément')

    class Meta:
        model = ReservationGroup
        fields = ['titre', 'reservation_mode', 'professeur', 'classe', 'classe_ou_groupe_libre', 'block', 'slots', 'sequence_code', 'sequence_title', 'tp_code', 'tp_titre', 'date_debut', 'date_fin', 'statut', 'commentaire']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'commentaire': forms.Textarea(attrs={'rows': 3}),
            'slots': forms.SelectMultiple(attrs={'size': 8, 'data-filterable': '1'}),
            'sequence_title': forms.TextInput(attrs={'list': 'sequence-suggestions'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['classe'].queryset = SchoolClass.objects.filter(active=True).select_related('formation').order_by('nom', 'school_year')
        self.fields['classe'].widget.attrs['data-filterable'] = '1'
        self.fields['professeur'].queryset = SystemUser.objects.filter(active=True).order_by('last_name', 'first_name')
        self.fields['professeur'].widget.attrs['data-filterable'] = '1'
        self.fields['block'].queryset = WorkshopBlock.objects.filter(active=True).prefetch_related('classes').order_by('code')
        self.fields['block'].widget.attrs['data-filterable'] = '1'
        self.fields['slots'].queryset = WorkshopBlockSlot.objects.filter(active=True).select_related('block').order_by('block__code', 'day_of_week', 'start_time')
        for name in ['date_debut', 'date_fin']:
            if self.instance and getattr(self.instance, name, None):
                self.fields[name].initial = timezone.localtime(getattr(self.instance, name)).strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.pk and self.instance.classe_ou_groupe:
            self.fields['classe_ou_groupe_libre'].initial = self.instance.classe_ou_groupe

    def save(self, commit=True):
        obj = super().save(commit=False)
        libre = self.cleaned_data.get('classe_ou_groupe_libre') or ''
        if obj.classe and not libre:
            obj.classe_ou_groupe = obj.classe.nom
        else:
            obj.classe_ou_groupe = libre
        if commit:
            obj.save()
            self.save_m2m()
        return obj


class SystemSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Recherche système')
    zone = forms.ModelChoiceField(queryset=WorkshopZone.objects.filter(active=True).order_by('ordre_affichage', 'code'), required=False)
    sous_zone = forms.ModelChoiceField(queryset=WorkshopSubZone.objects.filter(active=True).select_related('zone').order_by('zone__code', 'ordre_affichage', 'code'), required=False)
    statut = forms.ChoiceField(required=False, choices=[('', 'Tous les statuts')] + EducationalSystem.STATUS_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()
