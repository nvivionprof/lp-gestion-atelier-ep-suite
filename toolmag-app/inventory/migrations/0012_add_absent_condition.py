# Generated for ToolMag V27: add the "Absent" component status.
from django.db import migrations, models

CONDITION_CHOICES = [
    ('new', 'Neuf'),
    ('good', 'Bon état'),
    ('normal_wear', 'Usure normale'),
    ('watch', 'À surveiller'),
    ('damaged', 'Abîmé'),
    ('incomplete', 'Incomplet'),
    ('dangerous', 'Dangereux'),
    ('absent', 'Absent'),
]


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_equipmentdocument'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='current_condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='component',
            name='default_condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='loan',
            name='condition_out',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='loan',
            name='condition_return',
            field=models.CharField(blank=True, choices=CONDITION_CHOICES, max_length=30),
        ),
        migrations.AlterField(
            model_name='componentcheck',
            name='condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='userinventory',
            name='global_condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='userinventoryitem',
            name='condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
        migrations.AlterField(
            model_name='repairlog',
            name='resulting_condition',
            field=models.CharField(choices=CONDITION_CHOICES, default='good', max_length=30),
        ),
    ]
