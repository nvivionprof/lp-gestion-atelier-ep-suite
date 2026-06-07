from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def seed_teacher_corrections_category(apps, schema_editor):
    DocumentCategory = apps.get_model('system_manager', 'DocumentCategory')
    root = DocumentCategory.objects.filter(section_code='05', parent__isnull=True).order_by('ordre', 'id').first()
    if root:
        DocumentCategory.objects.get_or_create(
            code='05_CORRECTIONS_PROF',
            defaults={
                'nom': 'Corrections professeurs',
                'parent': root,
                'section_code': '05',
                'ordre': 900,
                'active': True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('system_manager', '0003_v034_reservation_admin_classes_zones'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemdocument',
            name='parent_document',
            field=models.ForeignKey(blank=True, help_text='Version précédente ou document remplacé.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='versions', to='system_manager.systemdocument'),
        ),
        migrations.AddField(
            model_name='systemdocument',
            name='teacher_only',
            field=models.BooleanField(default=False, verbose_name='Correction / contenu professeur uniquement'),
        ),
        migrations.AddField(
            model_name='systemdocument',
            name='visible_students',
            field=models.BooleanField(default=True, verbose_name='Visible élèves'),
        ),
        migrations.CreateModel(
            name='TemporarySystemPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('date_debut', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_fin', models.DateTimeField()),
                ('can_create', models.BooleanField(default=False, verbose_name='Peut créer des systèmes')),
                ('can_edit', models.BooleanField(default=True, verbose_name='Peut modifier des systèmes')),
                ('reason', models.TextField(blank=True, verbose_name='Motif / activité')),
                ('active', models.BooleanField(default=True)),
                ('granted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='temporary_permissions_granted', to='system_manager.systemuser')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temporary_system_permissions', to='system_manager.systemuser')),
            ],
            options={
                'verbose_name': 'droit temporaire système',
                'verbose_name_plural': 'droits temporaires systèmes',
                'ordering': ['-date_debut', 'user__last_name', 'user__first_name'],
            },
        ),
        migrations.AddField(
            model_name='temporarysystempermission',
            name='systems',
            field=models.ManyToManyField(blank=True, related_name='temporary_permissions', to='system_manager.educationalsystem'),
        ),
        migrations.AddField(
            model_name='temporarysystempermission',
            name='zones',
            field=models.ManyToManyField(blank=True, related_name='temporary_permissions', to='system_manager.workshopzone'),
        ),
        migrations.RunPython(seed_teacher_corrections_category, migrations.RunPython.noop),
    ]
