# Generated for LP Gestion Atelier EP Suite V0.3.3
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('core', '0008_backup_policy_settings')]
    operations = [
        migrations.CreateModel(name='CoreAtelierBlock', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('code', models.CharField(max_length=80, unique=True)), ('name', models.CharField(max_length=180)), ('description', models.TextField(blank=True)), ('active', models.BooleanField(default=True)), ('formations', models.ManyToManyField(blank=True, related_name='atelier_blocks', to='core.coreformation'))], options={'ordering': ['code'], 'verbose_name': 'bloc atelier', 'verbose_name_plural': 'blocs atelier'}),
        migrations.CreateModel(name='CoreAtelierBlockSlot', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('day_of_week', models.PositiveSmallIntegerField(choices=[(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi')])), ('label', models.CharField(blank=True, help_text='Ex. lundi matin, jeudi après-midi', max_length=120)), ('start_time', models.TimeField()), ('end_time', models.TimeField()), ('active', models.BooleanField(default=True)), ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='core.coreatelierblock'))], options={'ordering': ['block__code', 'day_of_week', 'start_time'], 'verbose_name': 'créneau bloc atelier', 'verbose_name_plural': 'créneaux blocs atelier', 'unique_together': {('block', 'day_of_week', 'start_time', 'end_time')}}),
    ]
