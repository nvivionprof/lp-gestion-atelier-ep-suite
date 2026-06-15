from django.conf import settings
from django.db import models
from django.utils import timezone


class TLSConfig(models.Model):
    MODE_DISABLED = "disabled"
    MODE_MANUAL = "manual"
    MODE_DUCKDNS = "duckdns-acme"
    MODE_SELFSIGNED = "selfsigned"

    MODE_CHOICES = [
        (MODE_DISABLED, "HTTP seulement"),
        (MODE_MANUAL, "Certificat manuel établissement"),
        (MODE_DUCKDNS, "DuckDNS + Let's Encrypt DNS-01"),
        (MODE_SELFSIGNED, "Auto-signé test local"),
    ]

    mode = models.CharField(max_length=32, choices=MODE_CHOICES, default=MODE_MANUAL)
    external_public_domain = models.CharField(max_length=255, blank=True)
    public_domain = models.CharField(max_length=255, blank=True)
    duckdns_domain = models.CharField(max_length=128, blank=True)
    duckdns_full_domain = models.CharField(max_length=255, blank=True)
    tls_email = models.EmailField(blank=True)
    acme_dns_sleep = models.PositiveIntegerField(default=120)
    cert_path = models.CharField(max_length=500, default="./certs/manual/fullchain.pem")
    key_path = models.CharField(max_length=500, default="./certs/manual/privkey.pem")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration TLS"
        verbose_name_plural = "Configurations TLS"
        permissions = [
            ("core_tls_view", "Voir la configuration TLS"),
            ("core_tls_manage_manual", "Gérer les certificats manuels"),
            ("core_tls_manage_duckdns", "Gérer DuckDNS ACME"),
            ("core_tls_run_operations", "Exécuter les opérations TLS"),
        ]

    def __str__(self):
        return f"TLS {self.mode} — {self.external_public_domain or 'non configuré'}"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class TLSOperationLog(models.Model):
    ACTION_CHOICES = [
        ("status", "Statut"),
        ("manual-install", "Installation manuelle"),
        ("duckdns-issue", "Génération DuckDNS"),
        ("duckdns-renew", "Renouvellement DuckDNS"),
        ("selfsigned", "Auto-signé"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64, choices=ACTION_CHOICES)
    success = models.BooleanField(default=False)
    output = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    remote_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} — {self.action} — {'OK' if self.success else 'KO'}"
