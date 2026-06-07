# Generated for ToolMag V11
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_person_must_change_password_person_password_hash'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentcheck',
            name='checked_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='component_checks_done', to='inventory.person'),
        ),
        migrations.AddField(
            model_name='componentcheck',
            name='checked_by_role',
            field=models.CharField(blank=True, help_text='Fonction active au moment de l’inventaire : utilisateur ou magasinier', max_length=30),
        ),
    ]
