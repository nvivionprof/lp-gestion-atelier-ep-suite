from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_public_settings_pfmp_port'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicsuitesettings',
            name='local_public_host',
            field=models.CharField(default='localhost:9000', help_text='Adresse utilisée sur le serveur ou en test local, par exemple localhost:9000.', max_length=255),
        ),
        migrations.AddField(
            model_name='publicsuitesettings',
            name='network_public_host',
            field=models.CharField(blank=True, default='', help_text='Adresse réseau interne, par exemple 192.168.101.19:9000 ou lp-suite.local:9000.', max_length=255),
        ),
        migrations.AddField(
            model_name='publicsuitesettings',
            name='external_public_domain',
            field=models.CharField(blank=True, default='', help_text='Domaine extérieur, par exemple stjoseph-lpsuite.duckdns.org.', max_length=255),
        ),
        migrations.AlterField(
            model_name='publicsuitesettings',
            name='exposure_mode',
            field=models.CharField(choices=[('local', 'Local — ce poste / localhost'), ('network', 'Réseau local — adresse IP ou nom DNS interne'), ('domain', 'Domaine extérieur — DuckDNS / nom public'), ('reverse_proxy', 'Ancien mode — passerelle unique / chemins publics')], default='local', max_length=40),
        ),
    ]
