# PedaShop V2.0 : accès public, magasins visibles, retours détaillés.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('pedashop', '0003_alter_article_reference_interne_and_more')]
    operations = [
        migrations.AddField(
            model_name='pedashopuser',
            name='magasins_visibles',
            field=models.ManyToManyField(blank=True, help_text='Magasins consultables par cet utilisateur. Vide = tous les magasins actifs.', related_name='utilisateurs_visibles', to='pedashop.magasin'),
        ),
        migrations.AddField(
            model_name='stockarticlemagasin',
            name='stock_perdu',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='lignebon',
            name='quantite_usee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='lignebon',
            name='quantite_hs',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='lignebon',
            name='quantite_perdue',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='retourattendu',
            name='quantite_usee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='retourattendu',
            name='quantite_cassee',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='retourattendu',
            name='quantite_perdue',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
