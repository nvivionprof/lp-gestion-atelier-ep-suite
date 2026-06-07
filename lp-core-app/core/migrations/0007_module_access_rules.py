# Generated manually for LP Gestion Atelier Suite — Bêta V0.0.1
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_coreuser_force_password_change_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoreModuleAccessRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('module', models.CharField(choices=[('toolmag', 'ToolMag'), ('safety', 'Safety Manager'), ('pedashop', 'PedaShop'), ('system', 'System Manager'), ('tpmanager', 'TP Manager')], max_length=40)),
                ('target_type', models.CharField(choices=[('role', 'Fonction / rôle'), ('class', 'Classe'), ('formation', 'Formation'), ('group', 'Groupe'), ('user', 'Utilisateur / élève'), ('right', 'Droit LP Core')], max_length=20)),
                ('target_value', models.CharField(help_text='Valeur exacte : eleve, 1MELEC, MELEC, groupe A, USR-0001, TOOLMAG_VIEW...', max_length=120)),
                ('active', models.BooleanField(default=True)),
                ('comment', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'verbose_name': 'Règle accès module',
                'verbose_name_plural': 'Règles accès modules',
                'ordering': ['module', 'target_type', 'target_value'],
                'unique_together': {('module', 'target_type', 'target_value')},
            },
        ),
    ]
