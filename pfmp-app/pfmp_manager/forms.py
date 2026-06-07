from django import forms
from .models import Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep, CompanyAnnouncement


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'activity', 'address', 'postal_code', 'city',
            'latitude', 'longitude',
            'phone', 'email', 'website', 'formations', 'transport_access',
            'student_visible_notes', 'internal_comment', 'safety_notes',
            'global_rating', 'status'
        ]
        widgets = {
            'formations': forms.CheckboxSelectMultiple,
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'ex. 48.006110'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'ex. 0.199556'}),
        }
        help_texts = {
            'latitude': 'Coordonnée GPS en degrés décimaux. Nécessaire pour l’affichage sur la carte PFMP.',
            'longitude': 'Coordonnée GPS en degrés décimaux. Nécessaire pour le filtrage par distance.',
        }


class CompanyContactForm(forms.ModelForm):
    class Meta:
        model = CompanyContact
        fields = ['full_name', 'role', 'service', 'email', 'phone', 'contact_type', 'visibility', 'formations', 'active', 'note']
        widgets = {'formations': forms.CheckboxSelectMultiple}


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


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = CompanyAnnouncement
        fields = ['company', 'title', 'announcement_type', 'formations', 'places', 'period_text', 'missions', 'expected_profile', 'mobility', 'requires_driving_license', 'requires_vehicle', 'public_transport_ok', 'deadline', 'status']
        widgets = {'deadline': forms.DateInput(attrs={'type': 'date'}), 'formations': forms.CheckboxSelectMultiple}
