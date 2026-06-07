from django.contrib import admin
from .models import (
    SafetyUser, SafetyZone, WorkUnit, RiskFamily, RiskAssessment, PreventionAction, SafetyEvent, EventFact,
    CauseAnalysis, FiveWhyLine, IshikawaCause, CauseTreeNode, CauseTreeLink, SafetyDocument, DUERPVersion
)


@admin.register(SafetyUser)
class SafetyUserAdmin(admin.ModelAdmin):
    list_display = ('code', 'username', 'last_name', 'first_name', 'class_name', 'role_principal', 'active', 'synced_at')
    list_filter = ('active', 'role_principal', 'formation_code', 'class_name')
    search_fields = ('code', 'username', 'last_name', 'first_name', 'class_name')
    readonly_fields = ('core_user_id', 'synced_at', 'created_at', 'updated_at')


@admin.register(SafetyZone)
class SafetyZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type_zone', 'actif', 'ordre_affichage')
    list_filter = ('type_zone', 'actif')
    search_fields = ('code', 'nom')


@admin.register(WorkUnit)
class WorkUnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'zone', 'responsable', 'actif')
    list_filter = ('actif', 'zone')
    search_fields = ('code', 'nom')


@admin.register(RiskFamily)
class RiskFamilyAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'actif')
    search_fields = ('code', 'nom')


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'unite_travail', 'famille_risque', 'gravite', 'frequence', 'priorite_calculee', 'statut')
    list_filter = ('priorite_calculee', 'statut', 'famille_risque')
    search_fields = ('code', 'danger', 'situation_dangereuse')
    readonly_fields = ('niveau_calcule', 'priorite_calculee', 'priorite_libelle')


@admin.register(PreventionAction)
class PreventionActionAdmin(admin.ModelAdmin):
    list_display = ('code', 'titre', 'origine', 'responsable', 'priorite', 'echeance', 'statut')
    list_filter = ('origine', 'type_action', 'statut', 'priorite')
    search_fields = ('code', 'titre', 'description')


@admin.register(SafetyEvent)
class SafetyEventAdmin(admin.ModelAdmin):
    list_display = ('code', 'type_evenement', 'date', 'zone', 'personne_concernee', 'avec_arret', 'statut_analyse')
    list_filter = ('type_evenement', 'avec_arret', 'statut_analyse', 'zone')
    search_fields = ('code', 'description_courte', 'recit_detaille')


admin.site.register(EventFact)
admin.site.register(CauseAnalysis)
admin.site.register(FiveWhyLine)
admin.site.register(IshikawaCause)
admin.site.register(CauseTreeNode)
admin.site.register(CauseTreeLink)
admin.site.register(SafetyDocument)
admin.site.register(DUERPVersion)
