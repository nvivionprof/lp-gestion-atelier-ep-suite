from django import forms
from .models import (Category, Component, Competence, EquipmentDocument, EvaluationRecord, Equipment, Formation,
    InterventionLog, Loan, Location, MaterialEditGrant, PedagogicalSession, Person, RepairLog)


STOREKEEPER_ROLES = [Person.Role.STOREKEEPER, Person.Role.RESPONSIBLE, Person.Role.ADMIN]


def global_condition_choices():
    """États utilisables pour l'état global d'un matériel.
    Le statut 'Absent' est réservé aux lignes de composants.
    """
    return [(value, label) for value, label in Equipment.Condition.choices if value != Equipment.Condition.ABSENT]


def find_active_person_by_code(code):
    if not code:
        return None
    return Person.objects.filter(code=code, active=True, archived=False).first()


def is_storekeeper(person):
    return bool(person and person.has_role(*STOREKEEPER_ROLES))


class StorekeeperSessionForm(forms.Form):
    storekeeper_code = forms.CharField(label='Code magasinier')
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        code = (cleaned.get('storekeeper_code') or '').strip()
        password = cleaned.get('password') or ''
        person = find_active_person_by_code(code)
        if not is_storekeeper(person):
            raise forms.ValidationError('Magasinier introuvable, inactif ou non autorisé. Vérifie le rôle principal ou les rôles autorisés.')
        if not person.check_password(password):
            raise forms.ValidationError('Mot de passe incorrect.')
        cleaned['storekeeper'] = person
        cleaned['storekeeper_code'] = code
        return cleaned


class UserSessionForm(forms.Form):
    borrower_code = forms.CharField(label='Code utilisateur / emprunteur')
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        code = (cleaned.get('borrower_code') or '').strip()
        password = cleaned.get('password') or ''
        person = find_active_person_by_code(code)
        if not person:
            raise forms.ValidationError('Utilisateur introuvable, inactif ou archivé.')
        if not person.check_password(password):
            raise forms.ValidationError('Mot de passe incorrect.')
        cleaned['borrower'] = person
        cleaned['borrower_code'] = code
        return cleaned


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(label='Mot de passe actuel', widget=forms.PasswordInput)
    new_password = forms.CharField(label='Nouveau mot de passe', min_length=6, widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirmation', min_length=6, widget=forms.PasswordInput)

    def __init__(self, *args, person=None, **kwargs):
        self.person = person
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        if self.person and not self.person.check_password(cleaned.get('current_password') or ''):
            raise forms.ValidationError('Mot de passe actuel incorrect.')
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('La confirmation ne correspond pas au nouveau mot de passe.')
        return cleaned


class ResetPasswordForm(forms.Form):
    person_code = forms.CharField(label='Code utilisateur')
    new_password = forms.CharField(label='Nouveau mot de passe', min_length=6, widget=forms.PasswordInput)
    force_change = forms.BooleanField(label='Forcer le changement au prochain usage', required=False, initial=True)

    def __init__(self, *args, selected_person_code=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['person_code'].widget.attrs.update({
            'autocomplete': 'off',
            'autocapitalize': 'characters',
            'spellcheck': 'false',
        })
        if selected_person_code and not self.is_bound:
            self.fields['person_code'].initial = selected_person_code
            self.fields['person_code'].help_text = (
                "Code repris depuis la fiche utilisateur sélectionnée. Vérifier avant validation."
            )

    def clean_person_code(self):
        code = self.cleaned_data['person_code'].strip()
        person = find_active_person_by_code(code)
        if not person:
            raise forms.ValidationError('Utilisateur introuvable, inactif ou archivé.')
        self.cleaned_data['person'] = person
        return code


class CheckoutForm(forms.Form):
    equipment_code = forms.CharField(label='Code matériel')
    borrower_code = forms.CharField(label='Code utilisateur')
    storekeeper_code = forms.CharField(label='Code magasinier', required=False)
    due_at = forms.DateTimeField(label='Retour prévu', required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    condition_out = forms.ChoiceField(label='État de sortie', choices=global_condition_choices)
    comment_out = forms.CharField(label='Commentaire sortie', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, current_storekeeper=None, current_borrower=None, **kwargs):
        self.current_storekeeper = current_storekeeper
        self.current_borrower = current_borrower
        super().__init__(*args, **kwargs)
        if current_storekeeper:
            self.fields['storekeeper_code'].initial = current_storekeeper.code
            self.fields['storekeeper_code'].widget.attrs.update({'readonly': 'readonly'})
            self.fields['storekeeper_code'].help_text = f'Magasinier connecté : {current_storekeeper.first_name} {current_storekeeper.last_name}'
        if current_borrower:
            self.fields['borrower_code'].initial = current_borrower.code
            self.fields['borrower_code'].widget.attrs.update({'readonly': 'readonly'})
            self.fields['borrower_code'].help_text = f'Emprunteur connecté : {current_borrower.first_name} {current_borrower.last_name}'

    def clean(self):
        cleaned = super().clean()
        equipment_code = cleaned.get('equipment_code')
        borrower_code = cleaned.get('borrower_code') or (self.current_borrower.code if self.current_borrower else '')
        storekeeper_code = cleaned.get('storekeeper_code') or (self.current_storekeeper.code if self.current_storekeeper else '')
        if equipment_code:
            try:
                equipment = Equipment.objects.get(code=equipment_code)
            except Equipment.DoesNotExist:
                raise forms.ValidationError('Matériel introuvable.')
            if equipment.status not in [Equipment.Status.AVAILABLE, Equipment.Status.INCOMPLETE]:
                raise forms.ValidationError('Ce matériel n’est pas disponible pour une sortie.')
            cleaned['equipment'] = equipment
        borrower = self.current_borrower or find_active_person_by_code(borrower_code)
        if not borrower:
            raise forms.ValidationError('Emprunteur introuvable ou inactif. Connecte un emprunteur ou donne un code utilisateur valide.')
        cleaned['borrower'] = borrower
        cleaned['borrower_code'] = borrower.code
        storekeeper = self.current_storekeeper or find_active_person_by_code(storekeeper_code)
        if not is_storekeeper(storekeeper):
            raise forms.ValidationError('Magasinier introuvable ou inactif. Connecte un magasinier ou donne un code ayant le rôle MAGASINIER/RESPONSABLE/ADMIN.')
        cleaned['storekeeper'] = storekeeper
        cleaned['storekeeper_code'] = storekeeper.code
        return cleaned


class ReturnForm(forms.Form):
    equipment_code = forms.CharField(label='Code matériel')
    storekeeper_code = forms.CharField(label='Code magasinier', required=False)
    condition_return = forms.ChoiceField(label='État de retour', choices=global_condition_choices)
    action = forms.ChoiceField(label='Action', choices=[
        ('available', 'Remettre disponible'),
        ('incomplete', 'Disponible mais incomplet'),
        ('maintenance', 'Envoyer en maintenance'),
        ('out_of_service', 'Bloquer / hors service'),
    ])
    comment_return = forms.CharField(label='Commentaire retour', required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, current_storekeeper=None, **kwargs):
        self.current_storekeeper = current_storekeeper
        super().__init__(*args, **kwargs)
        if current_storekeeper:
            self.fields['storekeeper_code'].initial = current_storekeeper.code
            self.fields['storekeeper_code'].widget.attrs.update({'readonly': 'readonly'})
            self.fields['storekeeper_code'].help_text = f'Magasinier connecté : {current_storekeeper.first_name} {current_storekeeper.last_name}'

    def clean(self):
        cleaned = super().clean()
        equipment_code = cleaned.get('equipment_code')
        storekeeper_code = cleaned.get('storekeeper_code') or (self.current_storekeeper.code if self.current_storekeeper else '')
        if equipment_code:
            try:
                equipment = Equipment.objects.get(code=equipment_code)
                loan = Loan.objects.get(equipment=equipment, status=Loan.LoanStatus.OPEN)
            except Equipment.DoesNotExist:
                raise forms.ValidationError('Matériel introuvable.')
            except Loan.DoesNotExist:
                raise forms.ValidationError('Aucune sortie en cours pour ce matériel.')
            cleaned['equipment'] = equipment
            cleaned['loan'] = loan
        storekeeper = self.current_storekeeper or find_active_person_by_code(storekeeper_code)
        if not is_storekeeper(storekeeper):
            raise forms.ValidationError('Magasinier introuvable ou inactif. Connecte un magasinier ou donne un code ayant le rôle MAGASINIER/RESPONSABLE/ADMIN.')
        cleaned['storekeeper'] = storekeeper
        cleaned['storekeeper_code'] = storekeeper.code
        return cleaned


class RepairForm(forms.ModelForm):
    class Meta:
        model = RepairLog
        fields = ['repair_type', 'diagnosis', 'action_done', 'parts_replaced', 'result', 'resulting_condition', 'comment']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'action_done': forms.Textarea(attrs={'rows': 3}),
            'parts_replaced': forms.Textarea(attrs={'rows': 2}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resulting_condition'].choices = global_condition_choices()

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get('diagnosis') or cleaned.get('action_done') or cleaned.get('comment')):
            raise forms.ValidationError('Renseigne au moins le diagnostic, l’action réalisée ou le commentaire du bon de réparation.')
        return cleaned


class InterventionForm(forms.ModelForm):
    class Meta:
        model = InterventionLog
        fields = ['intervention_type', 'finding', 'action_done', 'result', 'resulting_condition', 'comment']
        widgets = {
            'finding': forms.Textarea(attrs={'rows': 3}),
            'action_done': forms.Textarea(attrs={'rows': 3}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resulting_condition'].choices = global_condition_choices()

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get('finding') or cleaned.get('action_done') or cleaned.get('comment')):
            raise forms.ValidationError('Renseigne au moins le constat, l’action réalisée ou le commentaire du bon d’intervention.')
        return cleaned



class PersonCreateForm(forms.ModelForm):
    temporary_password = forms.CharField(label='Mot de passe provisoire', min_length=6, widget=forms.PasswordInput, required=True)
    force_change = forms.BooleanField(label='Forcer le changement au prochain login', required=False, initial=True)

    class Meta:
        model = Person
        fields = ['code', 'first_name', 'last_name', 'username', 'email', 'formation', 'class_name', 'group_name', 'level', 'department', 'role', 'allowed_roles', 'rfid_uid', 'active', 'archived']
        labels = {
            'code': 'Code utilisateur',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'username': 'Identifiant',
            'class_name': 'Classe',
            'group_name': 'Groupe',
            'level': 'Niveau',
            'role': 'Rôle principal',
            'allowed_roles': 'Rôles autorisés',
        }

    def save(self, commit=True):
        person = super().save(commit=False)
        person.set_password(self.cleaned_data['temporary_password'])
        person.must_change_password = self.cleaned_data.get('force_change', True)
        if commit:
            person.save()
        return person



class EquipmentDuplicateForm(forms.Form):
    """Prépare la duplication contrôlée d'un matériel composé ou d'un modèle.

    Le formulaire impose une prévisualisation avant validation définitive.
    """
    new_name = forms.CharField(label='Nom du nouveau matériel', max_length=160)
    new_code = forms.CharField(
        label='Nouveau code inventaire',
        max_length=32,
        required=False,
        help_text='Laisser vide pour générer automatiquement un code disponible.',
    )
    copy_components = forms.BooleanField(label='Copier la structure des composants attendus', required=False, initial=True)
    copy_documents = forms.BooleanField(label='Copier les documents modèles / consignes', required=False, initial=True)
    copy_photo = forms.BooleanField(label='Réutiliser la photo modèle', required=False, initial=False)
    copy_storage = forms.BooleanField(
        label='Copier emplacement / armoire / casier',
        required=False,
        initial=False,
        help_text='À éviter si le nouveau matériel physique ira dans un autre casier.',
    )
    confirm_creation = forms.BooleanField(label='Je confirme la création du nouveau matériel indépendant', required=False)

class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ['code', 'name', 'description', 'equipment_type', 'category', 'brand', 'model', 'serial_number', 'location', 'status', 'current_condition', 'inventory_required_out', 'inventory_required_return', 'sensitive', 'display_on_public_screen', 'secure_storage', 'secure_cabinet', 'secure_locker', 'photo', 'notes']
        labels = {
            'code': 'Code matériel',
            'name': 'Nom',
            'description': 'Descriptif matériel',
            'equipment_type': 'Type',
            'serial_number': 'N° série',
            'location': 'Emplacement',
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'photo': forms.ClearableFileInput(attrs={'accept': 'image/*', 'data-camera-upload': '1'}),
        }


class ComponentEditForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = ['name', 'required', 'expected_quantity', 'default_condition', 'photo', 'sort_order']
        labels = {'name': 'Composant', 'required': 'Présent normalement', 'expected_quantity': 'Qté', 'default_condition': 'Statut', 'sort_order': 'Ordre'}
        widgets = {'photo': forms.ClearableFileInput(attrs={'accept': 'image/*', 'data-camera-upload': '1'})}


class EquipmentDocumentEditForm(forms.ModelForm):
    class Meta:
        model = EquipmentDocument
        fields = ['title', 'document_type', 'file', 'description', 'active', 'sort_order']
        labels = {'title': 'Titre', 'document_type': 'Type', 'file': 'Fichier', 'description': 'Description', 'sort_order': 'Ordre'}
        widgets = {'description': forms.Textarea(attrs={'rows': 2})}


class MaterialEditGrantForm(forms.ModelForm):
    class Meta:
        model = MaterialEditGrant
        fields = ['formation', 'class_name', 'group_name', 'start_date', 'end_date', 'active', 'can_create_equipment', 'can_edit_equipment', 'can_add_photo', 'can_add_document', 'can_edit_components', 'can_edit_location', 'can_edit_description', 'can_generate_qr', 'comment']
        labels = {
            'class_name': 'Classe',
            'group_name': 'Groupe',
            'start_date': 'Date début',
            'end_date': 'Date fin',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 2}),
        }


class UserImportForm(forms.Form):
    file = forms.FileField(label='Fichier Excel .xlsx')
    apply_changes = forms.BooleanField(label='Appliquer les changements après analyse', required=False)


class PromotionFilterForm(forms.Form):
    formation = forms.ModelChoiceField(label='Formation source', queryset=Formation.objects.filter(active=True), required=False)
    class_name = forms.CharField(label='Classe source', required=False)
    group_name = forms.CharField(label='Groupe source', required=False)


class PromotionActionForm(forms.Form):
    ACTION_CHOICES = [
        ('promote', 'Monter au niveau supérieur'),
        ('repeat', 'Redoublement / maintien dans la classe'),
        ('transfer', 'Changement de filière'),
        ('change_group', 'Changer classe / groupe'),
        ('deactivate', 'Désactiver'),
        ('archive', 'Archiver'),
        ('delete_if_no_history', 'Supprimer seulement si aucun historique'),
    ]
    selected = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, required=False)
    action = forms.ChoiceField(label='Action', choices=ACTION_CHOICES)
    new_formation = forms.ModelChoiceField(label='Nouvelle formation', queryset=Formation.objects.filter(active=True), required=False)
    new_class_name = forms.CharField(label='Nouvelle classe', required=False)
    new_group_name = forms.CharField(label='Nouveau groupe', required=False)
    school_year = forms.CharField(label='Année scolaire', required=False, help_text='Exemple : 2026-2027')
    comment = forms.CharField(label='Commentaire', required=False, widget=forms.Textarea(attrs={'rows': 2}))
    apply_changes = forms.BooleanField(label='Appliquer réellement', required=False)



class EvaluationFilterForm(forms.Form):
    formation = forms.ModelChoiceField(label='Formation', queryset=Formation.objects.filter(active=True), required=False)
    class_name = forms.CharField(label='Classe', required=False)
    group_name = forms.CharField(label='Groupe', required=False)
    person = forms.ModelChoiceField(label='Élève', queryset=Person.objects.filter(active=True, archived=False), required=False)
    session = forms.ModelChoiceField(label='Séance', queryset=PedagogicalSession.objects.filter(active=True), required=False)
    date_from = forms.DateField(label='Du', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(label='Au', required=False, widget=forms.DateInput(attrs={'type': 'date'}))


class PedagogicalSessionForm(forms.ModelForm):
    class Meta:
        model = PedagogicalSession
        fields = ['title', 'date', 'formation', 'class_name', 'group_name', 'school_year', 'objectives', 'targeted_competences', 'active']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'objectives': forms.Textarea(attrs={'rows': 3}),
            'targeted_competences': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['targeted_competences'].queryset = Competence.objects.filter(active=True).select_related('formation')


class EvaluationValidationForm(forms.Form):
    validated_level = forms.ChoiceField(label='Niveau validé', choices=[('', '— non validé —'), ('0', '0 - Non observé'), ('1', '1 - Avec aide importante'), ('2', '2 - Avec aide légère'), ('3', '3 - Autonomie'), ('4', '4 - Autonomie + rigueur/initiative')], required=False)
    comment = forms.CharField(label='Commentaire professeur', required=False, widget=forms.Textarea(attrs={'rows': 2}))


class TerminalRegistrationForm(forms.Form):
    name = forms.CharField(label='Nom du terminal', max_length=120, help_text='Exemple : Tablette magasin atelier 1')
    terminal_type = forms.ChoiceField(label='Type', choices=[('tablet', 'Tablette'), ('pc', 'PC'), ('display', 'Affichage dynamique'), ('other', 'Autre')])
    can_open_lockers = forms.BooleanField(label='Autoriser ce terminal à ouvrir les casiers', required=False, initial=True)


class ForceLockerForm(forms.Form):
    cabinet = forms.CharField(label='Numéro d’armoire', max_length=50)
    locker = forms.CharField(label='Numéro de casier', max_length=50)
    context = forms.ChoiceField(label='Contexte', choices=[('force', 'Forçage super admin'), ('maintenance', 'Maintenance / contrôle')])
    reason = forms.CharField(label='Motif du forçage', required=True, widget=forms.Textarea(attrs={'rows': 3}))


class ManualBackupForm(forms.Form):
    note = forms.CharField(label='Commentaire sauvegarde manuelle', required=False, widget=forms.TextInput(attrs={'placeholder': 'Ex. avant import élèves / fin de période'}))


class RestoreBackupForm(forms.Form):
    backup_name = forms.CharField(widget=forms.HiddenInput)
    confirmation = forms.CharField(label='Confirmation', help_text='Tapez RESTAURER pour confirmer la restauration.')

    def clean_confirmation(self):
        value = (self.cleaned_data.get('confirmation') or '').strip()
        if value != 'RESTAURER':
            raise forms.ValidationError('Confirmation incorrecte. Tapez exactement RESTAURER.')
        return value
