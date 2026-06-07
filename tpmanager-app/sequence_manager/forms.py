from __future__ import annotations
from django import forms
from tp_manager.models import TpUser, TPV2, SystemePedagogiqueRef, BacDiplome
from .models import (
    SeqSequence, SeqRotationBlock, SeqZone, SeqColoration, SeqWeeklySlot,
    SeqSequenceFormation, SeqPresenceWave, SeqStudentGroup, SeqStudentGroupMember,
    SeqSession, SeqAssignment, SeqFreeChoiceRequest,
)


class SequenceCreateForm(forms.ModelForm):
    class Meta:
        model = SeqSequence
        fields = ['titre', 'description', 'rotation_block', 'zone_principale', 'coloration', 'axe_principal', 'date_debut', 'nb_semaines', 'statut', 'auto_inscription_libre', 'validation_prof_requise', 'notes_tp_activees', 'sequence_modele']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SequenceFormationForm(forms.ModelForm):
    class Meta:
        model = SeqSequenceFormation
        fields = ['diplome', 'formation_code', 'classe', 'niveau', 'effectif']


class PresenceWaveForm(forms.ModelForm):
    eleves = forms.ModelMultipleChoiceField(queryset=TpUser.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = SeqPresenceWave
        fields = ['nom', 'formation_code', 'classe', 'type_presence', 'semaine_debut', 'duree_semaines', 'eleves']

    def __init__(self, *args, formation_code=None, classe=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = TpUser.objects.filter(active=True).exclude(role_principal__in=['professeur', 'admin', 'admin_suite', 'responsable'])
        if formation_code:
            qs = qs.filter(formation_code__iexact=formation_code)
        if classe:
            qs = qs.filter(class_name__iexact=classe)
        self.fields['eleves'].queryset = qs.order_by('class_name', 'last_name', 'first_name')[:400]


class StudentGroupForm(forms.ModelForm):
    class Meta:
        model = SeqStudentGroup
        fields = ['wave', 'nom', 'type_groupe', 'formation_dominante', 'ordre', 'parcours_libre']


class GroupMemberForm(forms.Form):
    eleves = forms.ModelMultipleChoiceField(queryset=TpUser.objects.none(), required=True, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, sequence=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = TpUser.objects.filter(active=True).exclude(role_principal__in=['professeur', 'admin', 'admin_suite', 'responsable'])
        if sequence:
            wave_ids = sequence.waves.values_list('eleves__id', flat=True)
            qs = qs.filter(id__in=wave_ids)
        self.fields['eleves'].queryset = qs.distinct().order_by('class_name', 'last_name', 'first_name')[:500]


class SessionGenerateForm(forms.Form):
    replace_existing = forms.BooleanField(required=False, label='Regénérer les séances existantes')


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = SeqAssignment
        fields = ['session', 'group', 'eleve_individuel', 'tp', 'systeme', 'zone', 'professeur', 'mode', 'status', 'tp_note', 'capacite_max', 'commentaire']
        widgets = {'commentaire': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, sequence=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sequence:
            self.fields['session'].queryset = sequence.sessions.all()
            self.fields['group'].queryset = sequence.student_groups.all()
            self.fields['zone'].queryset = sequence.zones.all() if sequence.zones.exists() else SeqZone.objects.filter(active=True)
            self.fields['professeur'].queryset = TpUser.objects.filter(id__in=sequence.professeurs.values_list('id', flat=True)) if sequence.professeurs.exists() else TpUser.objects.filter(active=True, role_principal__in=['professeur','admin','responsable'])
        self.fields['tp'].queryset = TPV2.objects.exclude(statut='archive').select_related('diplome').order_by('diplome__code', 'code')[:1000]
        self.fields['systeme'].queryset = SystemePedagogiqueRef.objects.filter(actif=True).order_by('zone_code', 'code')[:1000]


class FreeChoiceFilterForm(forms.Form):
    competence = forms.CharField(required=False, label='Compétence')
    theme = forms.CharField(required=False, label='Thématique')
    systeme = forms.ModelChoiceField(queryset=SystemePedagogiqueRef.objects.filter(actif=True).order_by('code'), required=False)
    diplome = forms.ModelChoiceField(queryset=BacDiplome.objects.filter(actif=True).order_by('code'), required=False)
