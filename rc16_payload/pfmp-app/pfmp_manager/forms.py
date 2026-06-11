from django import forms
from django.db.models import Q
from .models import (
    Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep,
    CompanyAnnouncement, StudentCompanySearch, StudentCompanyAction
)


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'external_key', 'name', 'student_visible', 'status',
            'activity', 'source_activity', 'domains_text', 'subdomains_text', 'tags',
            'siret', 'naf_ape', 'address', 'postal_code', 'city', 'country', 'full_address',
            'latitude', 'longitude', 'geocoding_status', 'osm_search_url',
            'phone', 'email', 'website', 'formations', 'transport_access',
            'student_visible_notes', 'internal_comment', 'safety_notes', 'global_rating'
        ]
        widgets = {
            'formations': forms.CheckboxSelectMultiple,
            'tags': forms.CheckboxSelectMultiple,
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'ex. 48.006110'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'ex. 0.199556'}),
        }
        help_texts = {
            'student_visible': 'Si décoché, l’entreprise est masquée dans les recherches élèves.',
            'latitude': 'Coordonnée GPS en degrés décimaux. Nécessaire pour l’affichage sur la carte PFMP.',
            'longitude': 'Coordonnée GPS en degrés décimaux. Nécessaire pour le filtrage par distance.',
        }


class CompanyContactForm(forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = [
            'full_name', 'role', 'service', 'email', 'phone', 'mobile_phone',
            'contact_type', 'visibility', 'student_visible', 'teacher_visible',
            'formations', 'active', 'can_help_transport',
            'personal_address', 'personal_postal_code', 'personal_city',
            'personal_latitude', 'personal_longitude', 'use_personal_location_for_student_search',
            'note'
        ]
        widgets = {
            'formations': forms.CheckboxSelectMultiple,
            'personal_latitude': forms.NumberInput(attrs={'step': '0.000001'}),
            'personal_longitude': forms.NumberInput(attrs={'step': '0.000001'}),
        }
        help_texts = {
            'student_visible': 'Même si activé, l’élève ne verra que l’adresse mail du contact.',
            'use_personal_location_for_student_search': 'Utilise les coordonnées personnelles pour la recherche par proximité sans afficher l’adresse à l’élève.',
        }


class PeriodForm(forms.ModelForm):
    class Meta:
        model = PfmpPeriod
        fields = ['title', 'start_date', 'end_date', 'search_deadline', 'formations', 'class_names', 'referent', 'status', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'search_deadline': forms.DateInput(attrs={'type': 'date'}),
            'formations': forms.CheckboxSelectMultiple,
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = StudentAssignment
        fields = ['student', 'period', 'company', 'tutor', 'teacher', 'status', 'student_comment', 'teacher_comment']


class StepForm(forms.ModelForm):
    class Meta:
        model = StudentStep
        fields = ['step_type', 'date', 'title', 'comment']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}


class StudentCompanySearchForm(forms.ModelForm):
    first_action_type = forms.ChoiceField(choices=StudentCompanyAction.ACTION, label='Première démarche', initial='mail')
    first_comment = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False, label='Commentaire de première démarche')
    class Meta:
        model = StudentCompanySearch
        fields = ['period', 'contact', 'tags_text']

    def __init__(self, *args, company=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            qs = company.contacts.filter(active=True)
            if user and not user.is_prof_like:
                qs = qs.filter(student_visible=True)
                if user.formation_code:
                    qs = qs.filter(Q(formations__isnull=True) | Q(formations__code=user.formation_code)).distinct()
            self.fields['contact'].queryset = qs.order_by('full_name')
        if user and not user.is_prof_like:
            periods = PfmpPeriod.objects.filter(status='open')
            if user.formation_code:
                periods = periods.filter(Q(formations__isnull=True) | Q(formations__code=user.formation_code)).distinct()
            if user.class_name:
                periods = periods.filter(Q(class_names='') | Q(class_names__icontains=user.class_name)).distinct()
            self.fields['period'].queryset = periods.order_by('-start_date')
        else:
            self.fields['period'].queryset = PfmpPeriod.objects.exclude(status='archived').order_by('-start_date')


class StudentCompanyActionForm(forms.ModelForm):
    class Meta:
        model = StudentCompanyAction
        fields = ['action_type', 'contact', 'comment', 'status_after', 'next_action', 'next_action_date', 'attachment']
        widgets = {'next_action_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, search=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if search is not None:
            qs = search.company.contacts.filter(active=True)
            if user and not user.is_prof_like:
                qs = qs.filter(student_visible=True)
            self.fields['contact'].queryset = qs.order_by('full_name')
            if not self.initial.get('status_after'):
                self.initial['status_after'] = search.status


class CompanyImportForm(forms.Form):
    file = forms.FileField(label='Fichier XLSX entreprises/contacts')
    mode = forms.ChoiceField(choices=[
        ('simulation', 'Simulation sans écriture'),
        ('append_only', 'Ajout uniquement'),
        ('upsert', 'Ajout + mise à jour'),
        ('replace_all', 'Remplacement total entreprises/contacts'),
        ('delete_all_then_import', 'Suppression totale puis import'),
    ], initial='simulation')
    key = forms.ChoiceField(choices=[
        ('code_entreprise', 'code_entreprise'),
        ('siret', 'siret'),
        ('nom_code_postal_ville', 'nom + code postal + ville'),
    ], initial='code_entreprise')
    confirm = forms.CharField(required=False, help_text='Obligatoire pour les modes destructifs : CONFIRMER IMPORT DESTRUCTIF')


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = CompanyAnnouncement
        fields = ['company', 'title', 'announcement_type', 'formations', 'places', 'period_text', 'missions', 'expected_profile', 'mobility', 'requires_driving_license', 'requires_vehicle', 'public_transport_ok', 'deadline', 'status']
        widgets = {'deadline': forms.DateInput(attrs={'type': 'date'}), 'formations': forms.CheckboxSelectMultiple}
