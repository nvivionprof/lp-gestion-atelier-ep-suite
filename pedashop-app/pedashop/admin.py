from django.contrib import admin
from .models import (
    Article, Bon, BonHistorique, DemandeAchat, Emplacement, LigneBon, LigneDemandeAchat,
    LigneProjectionPedagogique, LigneReservation, Magasin, MouvementStock, PedaShopUser,
    ProjectionPedagogique, Reclamation, Reservation, RetourAttendu, StockAlert,
    StockArticleMagasin, SupplierConsultation, SupplierConsultationLine,
)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('reference_interne', 'designation', 'fabricant', 'categorie', 'marche', 'substituable', 'archive')
    search_fields = ('reference_interne', 'designation', 'reference_fabricant', 'code_ean', 'fabricant', 'marche')
    list_filter = ('categorie', 'sous_categorie', 'fabricant', 'substituable', 'archive')


@admin.register(StockArticleMagasin)
class StockArticleMagasinAdmin(admin.ModelAdmin):
    list_display = ('article', 'magasin', 'stock_reel', 'stock_minimum', 'stock_reserve_demande', 'stock_reserve_projection', 'stock_en_preparation', 'stock_temporairement_sorti', 'stock_hs')
    list_filter = ('magasin',)
    search_fields = ('article__reference_interne', 'article__designation', 'article__fabricant')


for model in [
    PedaShopUser, Magasin, Emplacement, Bon, LigneBon, Reservation, LigneReservation,
    MouvementStock, DemandeAchat, LigneDemandeAchat, ProjectionPedagogique,
    LigneProjectionPedagogique, RetourAttendu, Reclamation, BonHistorique, StockAlert,
    SupplierConsultation, SupplierConsultationLine,
]:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
