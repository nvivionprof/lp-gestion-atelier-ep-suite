from django.contrib import admin
from .models import (
    SystemUser, Formation, Niveau, SchoolClass, WorkshopZone, WorkshopSubZone, EducationalSystem, DocumentCategory,
    SystemDocument, DefaultCheckTemplate, CheckItem, ReservationGroup, Reservation, WorkSession, CheckResponse, SystemAnomaly, TemporarySystemPermission
)


@admin.register(SystemUser)
class SystemUserAdmin(admin.ModelAdmin):
    list_display = ('code', 'username', 'last_name', 'first_name', 'formation_code', 'class_name', 'role_principal', 'active')
    search_fields = ('code', 'username', 'last_name', 'first_name', 'class_name')
    list_filter = ('active', 'role_principal', 'formation_code')


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'active')
    search_fields = ('code', 'nom')


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('nom', 'formation', 'formation_code', 'school_year', 'active')
    list_filter = ('active', 'formation_code')
    search_fields = ('nom', 'formation_code')


@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'ordre', 'active')
    list_editable = ('ordre', 'active')


class SubZoneInline(admin.TabularInline):
    model = WorkshopSubZone
    extra = 0


@admin.register(WorkshopZone)
class WorkshopZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'responsable', 'active', 'ordre_affichage')
    inlines = [SubZoneInline]


@admin.register(WorkshopSubZone)
class WorkshopSubZoneAdmin(admin.ModelAdmin):
    list_display = ('zone', 'code', 'nom', 'active')
    list_filter = ('zone', 'active')


class DocumentInline(admin.TabularInline):
    model = SystemDocument
    extra = 0


class CheckItemInline(admin.TabularInline):
    model = CheckItem
    extra = 0


@admin.register(EducationalSystem)
class EducationalSystemAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'zone', 'sous_zone', 'statut', 'professeur_referent', 'actif')
    search_fields = ('code', 'designation', 'description')
    list_filter = ('statut', 'zone', 'formations', 'niveaux', 'actif')
    filter_horizontal = ('formations', 'niveaux')
    inlines = [DocumentInline, CheckItemInline]


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'ordre', 'active')
    list_editable = ('ordre', 'active')


@admin.register(SystemDocument)
class SystemDocumentAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'categorie', 'titre', 'type_document', 'version', 'visible_students', 'teacher_only', 'actif')
    search_fields = ('titre', 'systeme__code', 'systeme__designation')
    list_filter = ('categorie', 'type_document', 'visible_students', 'teacher_only', 'actif')


@admin.register(DefaultCheckTemplate)
class DefaultCheckTemplateAdmin(admin.ModelAdmin):
    # V0.3.8b : Django interdit d'utiliser le premier champ de list_display
    # comme list_editable. On garde ordre éditable mais on rend libelle cliquable.
    list_display = ('ordre', 'libelle', 'phase', 'expected_response', 'obligatoire', 'bloquant_si_non', 'active')
    list_display_links = ('libelle',)
    list_filter = ('phase', 'expected_response', 'obligatoire', 'bloquant_si_non', 'active')
    search_fields = ('libelle', 'aide')
    list_editable = ('ordre', 'active')


@admin.register(CheckItem)
class CheckItemAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'ordre', 'libelle', 'phase', 'type_reponse', 'obligatoire', 'bloquant_si_non', 'actif')
    list_filter = ('phase', 'type_reponse', 'obligatoire', 'actif')


@admin.register(TemporarySystemPermission)
class TemporarySystemPermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_debut', 'date_fin', 'can_create', 'can_edit', 'active', 'granted_by')
    list_filter = ('active', 'can_create', 'can_edit', 'date_debut', 'date_fin')
    search_fields = ('user__code', 'user__username', 'user__last_name', 'user__first_name', 'reason')
    filter_horizontal = ('zones', 'systems')


@admin.register(ReservationGroup)
class ReservationGroupAdmin(admin.ModelAdmin):
    list_display = ('titre', 'reservation_mode', 'classe_ou_groupe', 'date_debut', 'date_fin', 'statut')
    list_filter = ('reservation_mode', 'statut', 'block', 'classe')
    search_fields = ('titre', 'classe_ou_groupe', 'sequence_title', 'tp_titre')
    filter_horizontal = ('slots',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'date_debut', 'date_fin', 'professeur', 'classe_ou_groupe', 'statut')
    list_filter = ('statut', 'formation', 'niveau', 'systeme__zone')
    search_fields = ('systeme__code', 'systeme__designation', 'classe_ou_groupe', 'tp_code', 'tp_titre')


class CheckResponseInline(admin.TabularInline):
    model = CheckResponse
    extra = 0


@admin.register(WorkSession)
class WorkSessionAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'utilisateur', 'formation', 'niveau', 'classe_ou_groupe', 'date_prise', 'date_restitution', 'statut')
    list_filter = ('statut', 'formation', 'niveau', 'systeme__zone')
    inlines = [CheckResponseInline]


@admin.register(SystemAnomaly)
class SystemAnomalyAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'titre', 'gravite', 'statut', 'signalee_par', 'created_at')
    list_filter = ('gravite', 'statut', 'systeme__zone')
    search_fields = ('titre', 'description', 'systeme__code', 'systeme__designation')

# V0.3.3 — System Manager avancé
try:
    from .models import WorkshopBlock, WorkshopBlockSlot, SystemTPAssociation, SystemSafetyLink, MaintenanceIntervention, MaintenanceCheckLine, MaintenanceDrawingZone, SystemChangeLog

    class WorkshopBlockSlotInline(admin.TabularInline):
        model = WorkshopBlockSlot
        extra = 0

    @admin.register(WorkshopBlock)
    class WorkshopBlockAdmin(admin.ModelAdmin):
        list_display = ('code', 'nom', 'active')
        filter_horizontal = ('classes', 'formations', 'niveaux')
        inlines = [WorkshopBlockSlotInline]

    @admin.register(SystemTPAssociation)
    class SystemTPAssociationAdmin(admin.ModelAdmin):
        list_display = ('systeme', 'tp_code', 'tp_titre', 'formation', 'niveau', 'source', 'active')
        list_filter = ('source', 'formation', 'niveau', 'active')
        search_fields = ('tp_code', 'tp_titre', 'systeme__code')

    @admin.register(SystemSafetyLink)
    class SystemSafetyLinkAdmin(admin.ModelAdmin):
        list_display = ('systeme', 'titre', 'safety_object_type', 'niveau_risque', 'consignation_requise', 'source', 'active')
        list_filter = ('safety_object_type', 'consignation_requise', 'source', 'active')
        search_fields = ('titre', 'systeme__code')

    class MaintenanceCheckLineInline(admin.TabularInline):
        model = MaintenanceCheckLine
        extra = 0

    class MaintenanceDrawingZoneInline(admin.TabularInline):
        model = MaintenanceDrawingZone
        extra = 0

    @admin.register(MaintenanceIntervention)
    class MaintenanceInterventionAdmin(admin.ModelAdmin):
        list_display = ('reference', 'systeme', 'type_action', 'statut', 'executant_nom', 'created_at')
        list_filter = ('type_action', 'statut', 'systeme__zone')
        search_fields = ('reference', 'systeme__code', 'executant_nom')
        inlines = [MaintenanceCheckLineInline, MaintenanceDrawingZoneInline]

    @admin.register(SystemChangeLog)
    class SystemChangeLogAdmin(admin.ModelAdmin):
        list_display = ('systeme', 'type_changement', 'titre', 'version_avant', 'version_apres', 'date_effet')
        list_filter = ('type_changement', 'systeme__zone')
        search_fields = ('titre', 'description', 'systeme__code')
except admin.sites.AlreadyRegistered:
    pass
