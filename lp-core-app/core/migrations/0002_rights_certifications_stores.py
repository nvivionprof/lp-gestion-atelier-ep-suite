# Generated for LP Gestion Atelier EP Suite V2.1
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoreStore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=60)),
                ('nom', models.CharField(max_length=160)),
                ('module', models.CharField(choices=[('pedashop', 'PedaShop'), ('toolmag', 'ToolMag'), ('inventory', 'Inventory'), ('other', 'Autre')], default='pedashop', max_length=40)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['module', 'code'], 'unique_together': {('module', 'code')}},
        ),
        migrations.CreateModel(
            name='CoreCertification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('type_certification', models.CharField(choices=[('SST', 'SST'), ('HABILITATION_ELEC', 'Habilitation électrique'), ('B0', 'B0'), ('B1V', 'B1V'), ('BR', 'BR'), ('BC', 'BC'), ('R407', 'R407'), ('R408', 'R408'), ('CACES', 'CACES'), ('TRAVAIL_HAUTEUR', 'Travail en hauteur'), ('ECHAF', 'Échafaudage'), ('FLUIDE_FRIGO', 'Fluide frigorigène'), ('AUTRE', 'Autre')], max_length=80)),
                ('niveau', models.CharField(blank=True, max_length=120)),
                ('date_obtention', models.DateField(blank=True, null=True)),
                ('date_fin_validite', models.DateField(blank=True, null=True)),
                ('actif', models.BooleanField(default=True)),
                ('document', models.FileField(blank=True, null=True, upload_to='core/certifications/')),
                ('commentaire', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='certifications', to='core.coreuser')),
            ],
            options={'ordering': ['user__last_name', 'type_certification', '-date_fin_validite']},
        ),
        migrations.CreateModel(
            name='CoreUserStoreAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('active', models.BooleanField(default=True)),
                ('comment', models.CharField(blank=True, max_length=255)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_accesses', to='core.corestore')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='store_accesses', to='core.coreuser')),
            ],
            options={'ordering': ['user__last_name', 'store__module', 'store__code'], 'unique_together': {('user', 'store')}},
        ),
    ]
