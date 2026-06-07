
# Generated for LP Gestion Atelier EP Suite V0.3.4
from django.db import migrations, models
import django.db.models.deletion


def migrate_block_formations_to_classes(apps, schema_editor):
    CoreAtelierBlock = apps.get_model('core', 'CoreAtelierBlock')
    CoreClass = apps.get_model('core', 'CoreClass')
    for block in CoreAtelierBlock.objects.all():
        class_ids = []
        for formation in block.formations.all():
            class_ids.extend(CoreClass.objects.filter(formation=formation, active=True).values_list('id', flat=True))
        if class_ids:
            block.classes.set(CoreClass.objects.filter(id__in=class_ids))


class Migration(migrations.Migration):
    dependencies = [('core', '0009_atelier_blocks')]
    operations = [
        migrations.CreateModel(
            name='CoreWorkshopZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=100)),
            ],
            options={'ordering': ['order', 'code'], 'verbose_name': 'zone atelier centrale', 'verbose_name_plural': 'zones atelier centrales'},
        ),
        migrations.CreateModel(
            name='CoreWorkshopSubZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=64)),
                ('name', models.CharField(max_length=180)),
                ('description', models.TextField(blank=True)),
                ('active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=100)),
                ('zone', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subzones', to='core.coreworkshopzone')),
            ],
            options={'ordering': ['zone__code', 'order', 'code'], 'verbose_name': 'sous-zone atelier centrale', 'verbose_name_plural': 'sous-zones atelier centrales', 'unique_together': {('zone', 'code')}},
        ),
        migrations.AddField(
            model_name='coreatelierblock',
            name='classes',
            field=models.ManyToManyField(blank=True, related_name='atelier_blocks', to='core.coreclass'),
        ),
        migrations.RunPython(migrate_block_formations_to_classes, migrations.RunPython.noop),
    ]
