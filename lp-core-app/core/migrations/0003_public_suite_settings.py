# Generated manually for LP Gestion Atelier EP Suite V2.4
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_rights_certifications_stores'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicSuiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('public_domain', models.CharField(default='localhost:9000', max_length=255)),
                ('public_scheme', models.CharField(choices=[('http', 'HTTP'), ('https', 'HTTPS')], default='https', max_length=10)),
                ('exposure_mode', models.CharField(choices=[('reverse_proxy', 'Passerelle unique / chemins publics')], default='reverse_proxy', max_length=40)),
                ('challenge_method', models.CharField(choices=[('dns_duckdns', 'DNS-01 via DuckDNS'), ('http_01', 'HTTP-01 via passerelle HTTP')], default='dns_duckdns', max_length=40)),
                ('letsencrypt_email', models.EmailField(blank=True, max_length=254)),
                ('duckdns_token', models.CharField(blank=True, help_text='Token DuckDNS, requis uniquement pour le challenge DNS-01.', max_length=255)),
                ('enable_https', models.BooleanField(default=True)),
                ('lp_core_port', models.PositiveIntegerField(default=9000)),
                ('toolmag_port', models.PositiveIntegerField(default=9001)),
                ('safety_port', models.PositiveIntegerField(default=9002)),
                ('pedashop_port', models.PositiveIntegerField(default=9003)),
                ('system_manager_port', models.PositiveIntegerField(default=9004)),
                ('tpmanager_port', models.PositiveIntegerField(default=9005)),
                ('ssl_cert_file', models.CharField(default='/ssl/fullchain.pem', max_length=255)),
                ('ssl_key_file', models.CharField(default='/ssl/privkey.pem', max_length=255)),
            ],
            options={
                'verbose_name': 'Paramètres publics de la suite',
                'verbose_name_plural': 'Paramètres publics de la suite',
            },
        ),
    ]
