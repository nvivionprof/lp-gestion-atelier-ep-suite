# Compatibilité avec les installations où une migration 0003 a été générée localement.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedashop', '0002_pedashop_v17_workflows_alerts')]
    operations = [
        migrations.AlterField(
            model_name='article',
            name='reference_interne',
            field=models.CharField(help_text='Code produit PedaShop, unique et bloquant à l’import.', max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='bon',
            name='type_bon',
            field=models.CharField(choices=[('demande_eleve', 'Demande élève'), ('demande_prof', 'Demande professeur'), ('preparation', 'Bon de préparation'), ('enlevement', 'Bon d’enlèvement'), ('comptoir', 'Bon comptoir'), ('retour', 'Bon de retour'), ('transfert', 'Transfert'), ('etat_stock', 'État de stock')], default='demande_eleve', max_length=30),
        ),
    ]
