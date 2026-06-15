# Migration modèle pour intégration dans LP Core.
# À adapter au nom réel de l'app LP Core avant application.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='TLSConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('disabled', 'HTTP seulement'), ('manual', 'Certificat manuel établissement'), ('duckdns-acme', "DuckDNS + Let's Encrypt DNS-01"), ('selfsigned', 'Auto-signé test local')], default='manual', max_length=32)),
                ('external_public_domain', models.CharField(blank=True, max_length=255)),
                ('public_domain', models.CharField(blank=True, max_length=255)),
                ('duckdns_domain', models.CharField(blank=True, max_length=128)),
                ('duckdns_full_domain', models.CharField(blank=True, max_length=255)),
                ('tls_email', models.EmailField(blank=True, max_length=254)),
                ('acme_dns_sleep', models.PositiveIntegerField(default=120)),
                ('cert_path', models.CharField(default='./certs/manual/fullchain.pem', max_length=500)),
                ('key_path', models.CharField(default='./certs/manual/privkey.pem', max_length=500)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuration TLS',
                'verbose_name_plural': 'Configurations TLS',
                'permissions': [('core_tls_view', 'Voir la configuration TLS'), ('core_tls_manage_manual', 'Gérer les certificats manuels'), ('core_tls_manage_duckdns', 'Gérer DuckDNS ACME'), ('core_tls_run_operations', 'Exécuter les opérations TLS')],
            },
        ),
        migrations.CreateModel(
            name='TLSOperationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('status', 'Statut'), ('manual-install', 'Installation manuelle'), ('duckdns-issue', 'Génération DuckDNS'), ('duckdns-renew', 'Renouvellement DuckDNS'), ('selfsigned', 'Auto-signé')], max_length=64)),
                ('success', models.BooleanField(default=False)),
                ('output', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('remote_ip', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
