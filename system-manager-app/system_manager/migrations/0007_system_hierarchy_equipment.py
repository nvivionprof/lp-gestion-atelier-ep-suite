from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('system_manager', '0006_v038_calendar_default_checks_sync_downloads')]
    operations = [
        migrations.AlterField(
            model_name='documentcategory',
            name='section_code',
            field=models.CharField(
                blank=True,
                choices=[
                    ('01', '01 - Présentation - CCTP - Analyse fonctionnelle'),
                    ('02', '02 - Plans, schémas et notes de calcul'),
                    ('03', '03 - Documentations techniques'),
                    ('04', '04 - Programmes'),
                    ('05', '05 - TP / TD associés'),
                    ('06', '06 - Sécurité / risques / consignation'),
                    ('07', '07 - Maintenance / dépannage'),
                    ('08', '08 - Historique des modifications'),
                ],
                max_length=2,
            ),
        ),
        migrations.AlterField(model_name='reservation', name='block_code', field=models.CharField(blank=True, max_length=80)),
        migrations.AlterField(model_name='reservation', name='block_name', field=models.CharField(blank=True, max_length=180)),
        migrations.AlterField(model_name='reservation', name='slot_label', field=models.CharField(blank=True, max_length=120)),
        migrations.AlterField(model_name='reservation', name='sequence_code', field=models.CharField(blank=True, max_length=80)),
        migrations.AlterField(model_name='reservation', name='sequence_title', field=models.CharField(blank=True, max_length=220)),
        migrations.AddField(
            model_name='educationalsystem',
            name='parent_system',
            field=models.ForeignKey(
                blank=True,
                help_text='Laisser vide pour un système principal. Un sous-système partage sa documentation.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='subsystems',
                to='system_manager.educationalsystem',
                verbose_name='Système principal',
            ),
        ),
        migrations.CreateModel(
            name='SystemEquipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(blank=True, max_length=80)),
                ('designation', models.CharField(max_length=220)),
                ('type_equipement', models.CharField(blank=True, max_length=120)),
                ('marque', models.CharField(blank=True, max_length=120)),
                ('modele', models.CharField(blank=True, max_length=120)),
                ('numero_serie', models.CharField(blank=True, max_length=160)),
                ('quantite', models.PositiveIntegerField(default=1)),
                ('toolmag_code', models.CharField(blank=True, help_text='Code métier ToolMag facultatif. Aucun lien SQL direct entre les deux bases.', max_length=80)),
                ('description', models.TextField(blank=True)),
                ('ordre', models.PositiveIntegerField(default=100)),
                ('actif', models.BooleanField(default=True)),
                ('systeme', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipment_items', to='system_manager.educationalsystem')),
            ],
            options={
                'ordering': ['ordre', 'code', 'designation'],
                'unique_together': {('systeme', 'code')},
                'verbose_name': 'équipement de système',
                'verbose_name_plural': 'équipements de systèmes',
            },
        ),
    ]
