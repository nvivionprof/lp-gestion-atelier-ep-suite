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
        labels = {
            'external_key': 'Clé d’import',
            'name': 'Nom de l’entreprise',
            'student_visible': 'Visible par les élèves',
            'status': 'Statut',
            'activity': 'Activité principale',
            'source_activity': 'Activité source',
            'domains_text': 'Domaines / formations concernés',
            'subdomains_text': 'Sous-domaines / spécialités',
            'tags': 'Tags',
            'siret': 'SIRET',
            'naf_ape': 'Code NAF / APE',
            'address': 'Adresse',
            'postal_code': 'Code postal',
            'city': 'Ville',
            'country': 'Pays',
            'full_address': 'Adresse complète',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'geocoding_status': 'Statut du géocodage',
            'osm_search_url': 'Lien de recherche OpenStreetMap',
            'phone': 'Téléphone entreprise',
            'email': 'Adresse mail générale',
            'website': 'Site web',
            'formations': 'Formations concernées',
            'transport_access': 'Accès / transport',
            'student_visible_notes': 'Notes visibles par les élèves',
            'internal_comment': 'Commentaire interne',
            'safety_notes': 'Notes sécurité',
            'global_rating': 'Notation globale',
        }
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
        labels = {
            'external_key': 'Clé d’import',
            'name': 'Nom de l’entreprise',
            'student_visible': 'Visible par les élèves',
            'status': 'Statut',
            'activity': 'Activité principale',
            'source_activity': 'Activité source',
            'domains_text': 'Domaines / formations concernés',
            'subdomains_text': 'Sous-domaines / spécialités',
            'tags': 'Tags',
            'siret': 'SIRET',
            'naf_ape': 'Code NAF / APE',
            'address': 'Adresse',
            'postal_code': 'Code postal',
            'city': 'Ville',
            'country': 'Pays',
            'full_address': 'Adresse complète',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'geocoding_status': 'Statut du géocodage',
            'osm_search_url': 'Lien de recherche OpenStreetMap',
            'phone': 'Téléphone entreprise',
            'email': 'Adresse mail générale',
            'website': 'Site web',
            'formations': 'Formations concernées',
            'transport_access': 'Accès / transport',
            'student_visible_notes': 'Notes visibles par les élèves',
            'internal_comment': 'Commentaire interne',
            'safety_notes': 'Notes sécurité',
            'global_rating': 'Notation globale',
        }
        labels = {
            'full_name': 'Nom du contact',
            'role': 'Fonction',
            'service': 'Service',
            'email': 'Adresse mail',
            'phone': 'Téléphone fixe',
            'mobile_phone': 'Téléphone mobile',
            'contact_type': 'Type de contact',
            'visibility': 'Visibilité générale',
            'student_visible': 'Contact visible par les élèves',
            'teacher_visible': 'Contact visible par les professeurs',
            'formations': 'Formations concernées',
            'active': 'Contact actif',
            'can_help_transport': 'Peut aider au transport d’un stagiaire',
            'personal_address': 'Adresse personnelle du contact',
            'personal_postal_code': 'Code postal personnel',
            'personal_city': 'Ville personnelle',
            'personal_latitude': 'Latitude personnelle',
            'personal_longitude': 'Longitude personnelle',
            'use_personal_location_for_student_search': 'Utiliser cette adresse comme point de proximité',
            'note': 'Commentaire interne',
        }
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
        labels = {
            'title': 'Intitulé de la période',
            'start_date': 'Date de début',
            'end_date': 'Date de fin',
            'search_deadline': 'Date limite de recherche',
            'formations': 'Formations concernées',
            'class_names': 'Classes concernées',
            'referent': 'Référent',
            'status': 'Statut',
            'notes': 'Notes',
        }
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
    first_next_action = forms.CharField(max_length=180, required=False, label='Prochaine action à prévoir')
    first_next_action_date = forms.DateField(required=False, label='Date prévue de la prochaine action', widget=forms.DateInput(attrs={'type': 'date'}))
    class Meta:
        model = StudentCompanySearch
        fields = ['period', 'contact', 'tags_text']
        labels = {
            'period': 'Période PFMP concernée',
            'contact': 'Contact utilisé',
            'tags_text': 'Tags de suivi',
        }
        help_texts = {
            'tags_text': 'Tags séparés par des points-virgules, par exemple : prioritaire; à relancer; proche domicile',
        }

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
        labels = {
            'action_type': 'Type d’action',
            'contact': 'Contact utilisé',
            'comment': 'Commentaire',
            'status_after': 'État après cette action',
            'next_action': 'Prochaine action à prévoir',
            'next_action_date': 'Date prévue de la prochaine action',
            'attachment': 'Pièce jointe',
        }
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
    mode = forms.ChoiceField(label='Mode d’import', choices=[
        ('simulation', 'Simulation sans écriture'),
        ('append_only', 'Ajout uniquement'),
        ('upsert', 'Ajout + mise à jour'),
        ('replace_all', 'Remplacement total entreprises/contacts'),
        ('delete_all_then_import', 'Suppression totale puis import'),
    ], initial='simulation')
    key = forms.ChoiceField(label='Clé de rapprochement', choices=[
        ('code_entreprise', 'code_entreprise'),
        ('siret', 'siret'),
        ('nom_code_postal_ville', 'nom + code postal + ville'),
    ], initial='code_entreprise')
    confirm = forms.CharField(label='Confirmation import destructif', required=False, help_text='Obligatoire pour les modes destructifs : CONFIRMER IMPORT DESTRUCTIF')


class GeocodeCompaniesForm(forms.Form):
    mode = forms.ChoiceField(
        label='Mode de géocodage',
        choices=[
            ('missing', 'Géocoder seulement les entreprises sans coordonnées'),
            ('retry_failed', 'Relancer les échecs et ambiguïtés'),
            ('force', 'Forcer le recalcul de toutes les entreprises'),
        ],
        initial='missing',
    )
    limit = forms.IntegerField(
        label='Nombre maximum à traiter',
        required=False,
        min_value=1,
        help_text='Laisser vide pour traiter toutes les entreprises concernées.',
    )
    include_contacts = forms.BooleanField(
        label='Inclure les contacts autorisés comme point de proximité',
        required=False,
        help_text='Ne géocode que les contacts avec l’option “utiliser cette adresse comme point de proximité”. Les adresses restent masquées aux élèves.',
    )
    dry_run = forms.BooleanField(
        label='Simulation sans écriture',
        required=False,
        initial=False,
    )



class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = CompanyAnnouncement
        fields = ['company', 'title', 'announcement_type', 'formations', 'places', 'period_text', 'missions', 'expected_profile', 'mobility', 'requires_driving_license', 'requires_vehicle', 'public_transport_ok', 'deadline', 'status']
        widgets = {'deadline': forms.DateInput(attrs={'type': 'date'}), 'formations': forms.CheckboxSelectMultiple}
