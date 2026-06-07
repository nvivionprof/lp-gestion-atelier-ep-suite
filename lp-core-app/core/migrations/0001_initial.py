# Generated for LP Gestion Atelier EP Suite
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='CoreFormation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=160)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='CoreUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=64, unique=True)),
                ('username', models.CharField(max_length=120, unique=True)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('class_name', models.CharField(blank=True, max_length=80)),
                ('group_name', models.CharField(blank=True, max_length=80)),
                ('role_principal', models.CharField(choices=[('utilisateur', 'Utilisateur'), ('eleve', 'Élève'), ('magasinier', 'Magasinier'), ('professeur', 'Professeur'), ('responsable', 'Responsable'), ('admin', 'Administrateur'), ('lecture_seule', 'Lecture seule')], default='utilisateur', max_length=50)),
                ('rights', models.CharField(blank=True, help_text='Droits séparés par ;', max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('school_year', models.CharField(blank=True, max_length=20)),
                ('password_hash', models.CharField(blank=True, max_length=255)),
                ('initial_password_for_sync', models.CharField(blank=True, help_text='Mot de passe initial, réservé à la synchronisation locale', max_length=80)),
                ('source', models.CharField(blank=True, default='manual', max_length=80)),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='core.coreformation')),
            ],
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.CreateModel(
            name='CoreClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=80)),
                ('school_year', models.CharField(blank=True, max_length=20)),
                ('active', models.BooleanField(default=True)),
                ('formation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='classes', to='core.coreformation')),
            ],
            options={'ordering': ['formation__code', 'name'], 'unique_together': {('formation', 'name', 'school_year')}},
        ),
        migrations.CreateModel(
            name='CoreAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(max_length=200)),
                ('target', models.CharField(blank=True, max_length=200)),
                ('details', models.TextField(blank=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.coreuser')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
