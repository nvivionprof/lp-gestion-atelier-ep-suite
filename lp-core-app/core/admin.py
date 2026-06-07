from django.contrib import admin
from .models import (
    CoreFormation, CoreClass, CoreWorkshopZone, CoreWorkshopSubZone, CoreUser, CoreAuditLog,
    CoreStore, CoreUserStoreAccess, CoreCertification, CoreRightDefinition, CoreCertificationType, CoreUserDocument, RgpdPolicySettings, BackupPolicySettings,
    PublicSuiteSettings, UploadedUpdatePackage, SuiteMaintenanceJob, CoreModuleAccessRule,
)


@admin.register(CoreFormation)
class CoreFormationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'active')
    search_fields = ('code', 'name')


@admin.register(CoreClass)
class CoreClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'formation', 'school_year', 'active')
    search_fields = ('name', 'formation__code')


class CoreWorkshopSubZoneInline(admin.TabularInline):
    model = CoreWorkshopSubZone
    extra = 0


@admin.register(CoreWorkshopZone)
class CoreWorkshopZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'active', 'order')
    list_editable = ('active', 'order')
    search_fields = ('code', 'name')
    inlines = [CoreWorkshopSubZoneInline]


@admin.register(CoreWorkshopSubZone)
class CoreWorkshopSubZoneAdmin(admin.ModelAdmin):
    list_display = ('zone', 'code', 'name', 'active', 'order')
    list_filter = ('zone', 'active')
    search_fields = ('code', 'name')


@admin.register(CoreUser)
class CoreUserAdmin(admin.ModelAdmin):
    list_display = ('code', 'username', 'last_name', 'first_name', 'class_name', 'role_principal', 'active')
    list_filter = ('role_principal', 'active', 'class_name', 'formation')
    search_fields = ('code', 'username', 'last_name', 'first_name', 'class_name')


@admin.register(CoreStore)
class CoreStoreAdmin(admin.ModelAdmin):
    list_display = ('module', 'code', 'nom', 'active')
    list_filter = ('module', 'active')
    search_fields = ('code', 'nom')


@admin.register(CoreUserStoreAccess)
class CoreUserStoreAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'store', 'active')
    list_filter = ('store__module', 'active')
    search_fields = ('user__code', 'user__last_name', 'store__code')


@admin.register(CoreCertification)
class CoreCertificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_certification', 'niveau', 'date_obtention', 'date_fin_validite', 'actif')
    list_filter = ('type_certification', 'actif')
    search_fields = ('user__code', 'user__last_name', 'niveau')


@admin.register(CoreRightDefinition)
class CoreRightDefinitionAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'module', 'active')
    list_filter = ('module', 'active')
    search_fields = ('code', 'label')


@admin.register(CoreCertificationType)
class CoreCertificationTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'active')
    list_filter = ('active',)
    search_fields = ('code', 'label')


@admin.register(CoreUserDocument)
class CoreUserDocumentAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'type_document', 'title', 'uploaded_by')
    list_filter = ('type_document',)
    search_fields = ('user__code', 'user__last_name', 'title')


@admin.register(RgpdPolicySettings)
class RgpdPolicySettingsAdmin(admin.ModelAdmin):
    list_display = ('technical_logs_retention', 'backup_retention_days', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BackupPolicySettings)
class BackupPolicySettingsAdmin(admin.ModelAdmin):
    list_display = ('automatic_enabled', 'daily_hour', 'daily_minute', 'daily_retention_days', 'pre_upgrade_required', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CoreAuditLog)
class CoreAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'target')
    search_fields = ('action', 'target', 'details')


@admin.register(PublicSuiteSettings)
class PublicSuiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('public_domain', 'public_scheme', 'exposure_mode', 'challenge_method', 'enable_https', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UploadedUpdatePackage)
class UploadedUpdatePackageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'original_filename', 'detected_version', 'status', 'size_bytes', 'uploaded_by')
    list_filter = ('status',)
    search_fields = ('original_filename', 'stored_filename', 'detected_version', 'sha256')
    readonly_fields = ('created_at', 'updated_at', 'sha256', 'stored_path', 'manifest')


@admin.register(SuiteMaintenanceJob)
class SuiteMaintenanceJobAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'status', 'agent_job_id', 'requested_by')
    list_filter = ('action', 'status')
    search_fields = ('agent_job_id', 'result_message', 'log_tail')
    readonly_fields = ('created_at', 'updated_at', 'result_message', 'log_tail')


@admin.register(CoreModuleAccessRule)
class CoreModuleAccessRuleAdmin(admin.ModelAdmin):
    list_display = ('module', 'target_type', 'target_value', 'active', 'updated_at')
    list_filter = ('module', 'target_type', 'active')
    search_fields = ('target_value', 'comment')

# V0.3.3 — Blocs atelier
try:
    from .models import CoreAtelierBlock, CoreAtelierBlockSlot

    class CoreAtelierBlockSlotInline(admin.TabularInline):
        model = CoreAtelierBlockSlot
        extra = 0

    @admin.register(CoreAtelierBlock)
    class CoreAtelierBlockAdmin(admin.ModelAdmin):
        list_display = ('code', 'name', 'active')
        search_fields = ('code', 'name')
        list_filter = ('active',)
        filter_horizontal = ('classes', 'formations')
        inlines = [CoreAtelierBlockSlotInline]
except admin.sites.AlreadyRegistered:
    pass
