from django import forms

from .models import DisplayLayout, DisplayMedia, DisplayQRCodeAction, DisplayScreen, DisplayZoneItem


class DisplayScreenForm(forms.ModelForm):
    class Meta:
        model = DisplayScreen
        fields = ['name', 'location', 'active_layout', 'is_active']


class DisplayLayoutForm(forms.ModelForm):
    class Meta:
        model = DisplayLayout
        fields = ['name', 'description', 'column_position', 'target_width', 'target_height', 'is_active']


class DisplayMediaForm(forms.ModelForm):
    class Meta:
        model = DisplayMedia
        fields = ['name', 'media_type', 'image', 'web_url', 'default_duration_seconds', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex. Logo atelier, consigne sécurité, planning PFMP'}),
            'media_type': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'web_url': forms.URLInput(attrs={'placeholder': 'https://...'}),
            'default_duration_seconds': forms.NumberInput(attrs={'min': 1, 'max': 3600}),
        }

    def clean(self):
        cleaned = super().clean()
        media_type = cleaned.get('media_type')
        image = cleaned.get('image')
        web_url = cleaned.get('web_url')
        if media_type == DisplayMedia.TYPE_IMAGE and not image and not getattr(self.instance, 'image', None):
            self.add_error('image', 'Ajoute une image pour un média de type image.')
        if media_type == DisplayMedia.TYPE_WEB and not web_url:
            self.add_error('web_url', 'Ajoute une URL pour un média de type page web.')
        return cleaned


class DisplayZoneItemForm(forms.ModelForm):
    class Meta:
        model = DisplayZoneItem
        fields = ['zone', 'media', 'order', 'duration_seconds', 'is_active']


class DisplayQRCodeActionForm(forms.ModelForm):
    class Meta:
        model = DisplayQRCodeAction
        fields = ['name', 'action', 'target_screen', 'target_zone', 'duration_seconds', 'is_active', 'expires_at']
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
