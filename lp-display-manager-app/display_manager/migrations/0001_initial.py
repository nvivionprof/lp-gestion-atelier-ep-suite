# Generated for LP Display Manager v0.1-bootstrap
import display_manager.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='DisplayLayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('column_position', models.CharField(choices=[('right', 'Miniatures à droite'), ('left', 'Miniatures à gauche')], default='right', max_length=10, verbose_name='Position colonne')),
                ('target_width', models.PositiveIntegerField(default=1920, verbose_name='Largeur cible')),
                ('target_height', models.PositiveIntegerField(default=1080, verbose_name='Hauteur cible')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Layout', 'verbose_name_plural': 'Layouts', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='DisplayMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom')),
                ('media_type', models.CharField(choices=[('image', 'Image'), ('web', 'Page web')], max_length=20, verbose_name='Type')),
                ('image', models.ImageField(blank=True, null=True, upload_to='display/images/', verbose_name='Image')),
                ('web_url', models.URLField(blank=True, verbose_name='URL web')),
                ('default_duration_seconds', models.PositiveIntegerField(default=15, verbose_name='Durée par défaut')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Média', 'verbose_name_plural': 'Médias', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='DisplayScreen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom')),
                ('location', models.CharField(blank=True, max_length=150, verbose_name='Lieu')),
                ('association_code', models.CharField(default=display_manager.models.make_code, max_length=16, unique=True, verbose_name='Code association')),
                ('player_token', models.CharField(default=display_manager.models.make_token, max_length=64, unique=True, verbose_name='Token player')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('last_contact', models.DateTimeField(blank=True, null=True, verbose_name='Dernier contact')),
                ('status', models.CharField(choices=[('online', 'En ligne'), ('offline', 'Hors ligne'), ('unknown', 'Inconnu')], default='unknown', max_length=20, verbose_name='Statut')),
                ('agent_version', models.CharField(blank=True, max_length=50, verbose_name='Version agent')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('active_layout', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='screens', to='display_manager.displaylayout')),
            ],
            options={'verbose_name': 'Écran', 'verbose_name_plural': 'Écrans', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='DisplayZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('main', 'Zone centrale'), ('thumb1', 'Miniature 1'), ('thumb2', 'Miniature 2'), ('thumb3', 'Miniature 3')], max_length=20, verbose_name='Zone')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('layout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zones', to='display_manager.displaylayout')),
            ],
            options={'verbose_name': 'Zone', 'verbose_name_plural': 'Zones', 'ordering': ['order', 'name'], 'unique_together': {('layout', 'name')}},
        ),
        migrations.CreateModel(
            name='DisplayQRCodeAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nom')),
                ('token', models.CharField(default=display_manager.models.make_token, max_length=64, unique=True, verbose_name='Token QR')),
                ('action', models.CharField(choices=[('freeze', 'Figer l’affichage'), ('resume', 'Reprendre l’affichage')], max_length=30, verbose_name='Action')),
                ('target_zone', models.CharField(default='all', max_length=20, verbose_name='Zone cible')),
                ('duration_seconds', models.PositiveIntegerField(default=60, verbose_name='Durée')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expiration')),
                ('use_count', models.PositiveIntegerField(default=0, verbose_name='Utilisations')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('target_screen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='qr_actions', to='display_manager.displayscreen')),
            ],
            options={'verbose_name': 'QR action', 'verbose_name_plural': 'QR actions', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='DisplayCommand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('freeze', 'Figer'), ('resume', 'Reprendre'), ('reload', 'Recharger')], max_length=30, verbose_name='Action')),
                ('payload', models.JSONField(blank=True, default=dict, verbose_name='Payload')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('sent', 'Envoyée'), ('done', 'Terminée'), ('failed', 'Échec')], default='pending', max_length=20, verbose_name='Statut')),
                ('result', models.TextField(blank=True, verbose_name='Résultat')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('screen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commands', to='display_manager.displayscreen')),
            ],
            options={'verbose_name': 'Commande player', 'verbose_name_plural': 'Commandes player', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='DisplayZoneItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordre')),
                ('duration_seconds', models.PositiveIntegerField(default=15, verbose_name='Durée')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='zone_items', to='display_manager.displaymedia')),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='display_manager.displayzone')),
            ],
            options={'verbose_name': 'Élément de zone', 'verbose_name_plural': 'Éléments de zone', 'ordering': ['order', 'id']},
        ),
    ]
