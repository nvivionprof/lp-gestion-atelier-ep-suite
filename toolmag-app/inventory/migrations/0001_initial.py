# Generated manually for ToolMag starter
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={'verbose_name_plural': 'Categories'},
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=32, unique=True)),
                ('first_name', models.CharField(max_length=80)),
                ('last_name', models.CharField(max_length=80)),
                ('role', models.CharField(choices=[('user', 'Utilisateur'), ('storekeeper', 'Magasinier'), ('admin', 'Administrateur')], default='user', max_length=20)),
                ('department', models.CharField(blank=True, max_length=120)),
                ('rfid_uid', models.CharField(blank=True, max_length=120)),
                ('active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=160)),
                ('equipment_type', models.CharField(choices=[('simple', 'Matériel simple'), ('kit', 'Matériel composé / kit'), ('consumable', 'Consommable')], default='simple', max_length=20)),
                ('brand', models.CharField(blank=True, max_length=120)),
                ('model', models.CharField(blank=True, max_length=120)),
                ('serial_number', models.CharField(blank=True, max_length=120)),
                ('status', models.CharField(choices=[('available', 'Disponible'), ('out', 'Sorti'), ('late', 'En retard'), ('maintenance', 'Maintenance'), ('incomplete', 'Incomplet'), ('out_of_service', 'Hors service'), ('lost', 'Perdu')], default='available', max_length=30)),
                ('current_condition', models.CharField(choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux')], default='good', max_length=30)),
                ('inventory_required_out', models.BooleanField(default=False)),
                ('inventory_required_return', models.BooleanField(default=False)),
                ('sensitive', models.BooleanField(default=False)),
                ('display_on_public_screen', models.BooleanField(default=True)),
                ('photo', models.ImageField(blank=True, upload_to='equipment/')),
                ('notes', models.TextField(blank=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.category')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventory.location')),
            ],
            options={'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=160)),
                ('required', models.BooleanField(default=True)),
                ('expected_quantity', models.PositiveIntegerField(default=1)),
                ('default_condition', models.CharField(choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux')], default='good', max_length=30)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='inventory.equipment')),
            ],
            options={'ordering': ['sort_order', 'name'], 'unique_together': {('equipment', 'name')}},
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('checked_out_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('due_at', models.DateTimeField(blank=True, null=True)),
                ('condition_out', models.CharField(choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux')], default='good', max_length=30)),
                ('comment_out', models.TextField(blank=True)),
                ('returned_at', models.DateTimeField(blank=True, null=True)),
                ('condition_return', models.CharField(blank=True, choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux')], max_length=30)),
                ('comment_return', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('open', 'En cours'), ('closed', 'Clôturé'), ('problem', 'Clôturé avec anomalie')], default='open', max_length=20)),
                ('borrower', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='borrowed_loans', to='inventory.person')),
                ('checkout_storekeeper', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='checkout_loans', to='inventory.person')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loans', to='inventory.equipment')),
                ('return_storekeeper', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='return_loans', to='inventory.person')),
            ],
            options={'ordering': ['-checked_out_at']},
        ),
        migrations.CreateModel(
            name='ComponentCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('check_type', models.CharField(choices=[('out', 'Sortie'), ('return', 'Retour')], max_length=10)),
                ('present', models.BooleanField(default=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('condition', models.CharField(choices=[('new', 'Neuf'), ('good', 'Bon état'), ('normal_wear', 'Usure normale'), ('watch', 'À surveiller'), ('damaged', 'Abîmé'), ('incomplete', 'Incomplet'), ('dangerous', 'Dangereux')], default='good', max_length=30)),
                ('comment', models.CharField(blank=True, max_length=255)),
                ('component', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventory.component')),
                ('loan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='component_checks', to='inventory.loan')),
            ],
            options={'ordering': ['component__sort_order', 'component__name'], 'unique_together': {('loan', 'component', 'check_type')}},
        ),
    ]
