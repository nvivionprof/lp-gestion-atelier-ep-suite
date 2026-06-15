from django import forms
from .models import TLSConfig


class TLSConfigForm(forms.ModelForm):
    duckdns_token = forms.CharField(
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Token DuckDNS. Ne doit jamais être stocké en clair dans GitHub.",
    )

    class Meta:
        model = TLSConfig
        fields = [
            "mode",
            "external_public_domain",
            "public_domain",
            "duckdns_domain",
            "duckdns_full_domain",
            "tls_email",
            "acme_dns_sleep",
        ]


class ManualCertificateUploadForm(forms.Form):
    fullchain = forms.FileField(label="fullchain.pem")
    privkey = forms.FileField(label="privkey.pem")
