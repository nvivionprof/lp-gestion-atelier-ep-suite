from django.contrib import admin
from django.utils.html import format_html
from .models import AuthorizedTerminal, Category, Component, ComponentCheck, Competence, CompetenceMapping, EnrollmentHistory, Equipment, EquipmentDocument, EvaluationRecord, Formation, SchoolClass, InterventionLog, Loan, Location, LockerOpenLog, LockerSettings, MaterialEditGrant, PedagogicalSession, Person, RepairLog, SessionRoleAssignment, UserInventory, UserInventoryItem


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'referential_name', 'active')
    list_filter = ('active',)
    search_fields = ('code', 'name', 'referential_name')


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'formation', 'active')
    list_filter = ('formation', 'active')
    search_fields = ('name', 'formation__code', 'formation__name')


class EquipmentDocumentInline(admin.TabularInline):
    model = EquipmentDocument
    extra = 1
    fields = ('title', 'document_type', 'file', 'description', 'active', 'sort_order')


class ComponentInline(admin.TabularInline):
    model = Component
    extra = 1
    fields = ('name', 'required', 'expected_quantity', 'default_condition', 'photo', 'photo_preview', 'sort_order')
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" style="height:48px; max-width:80px; object-fit:contain;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Aperçu'


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'description', 'equipment_type', 'category', 'status', 'current_condition', 'location', 'photo_preview')
    list_filter = ('equipment_type', 'status', 'category', 'location', 'sensitive', 'secure_storage')
    search_fields = ('code', 'name', 'description', 'brand', 'model', 'serial_number', 'location__name', 'category__name')
    readonly_fields = ('photo_preview',)
    fieldsets = (
        ('Identification', {'fields': ('code', 'name', 'description', 'equipment_type', 'category', 'brand', 'model', 'serial_number')}),
        ('État et localisation', {'fields': ('location', 'status', 'current_condition', 'sensitive', 'display_on_public_screen')}),
        ('Armoire sécurisée', {'fields': ('secure_storage', 'secure_cabinet', 'secure_locker'), 'description': 'Ne renseigner que le numéro d’armoire et de casier. Aucune URL de contrôleur ne doit être stockée sur la fiche matériel.'}),
        ('Inventaire', {'fields': ('inventory_required_out', 'inventory_required_return')}),
        ('Photo et notes', {'fields': ('photo', 'photo_preview', 'notes')}),
    )
    inlines = [ComponentInline, EquipmentDocumentInline]

    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" style="height:70px; max-width:120px; object-fit:contain;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Aperçu photo'


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    search_fields = ('code', 'first_name', 'last_name', 'username', 'email', 'rfid_uid')
    list_display = ('code', 'first_name', 'last_name', 'username', 'role', 'formation', 'class_name', 'group_name', 'active', 'archived')
    list_filter = ('role', 'active', 'archived', 'formation', 'class_name', 'group_name')
    fieldsets = (
        ('Identité', {'fields': ('code', 'first_name', 'last_name', 'username', 'email')}),
        ('Scolarité', {'fields': ('formation', 'class_name', 'group_name', 'level', 'department')}),
        ('Droits ToolMag', {'fields': ('role', 'allowed_roles', 'active', 'archived', 'rfid_uid')}),
    )


@admin.register(EnrollmentHistory)
class EnrollmentHistoryAdmin(admin.ModelAdmin):
    list_display = ('person', 'event_type', 'school_year', 'old_formation', 'new_formation', 'old_class_name', 'new_class_name', 'created_at')
    list_filter = ('event_type', 'school_year', 'new_formation', 'new_class_name')
    search_fields = ('person__code', 'person__last_name', 'person__first_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'borrower', 'checkout_storekeeper', 'checked_out_at', 'due_at', 'status')
    list_filter = ('status', 'condition_out', 'condition_return')
    search_fields = ('equipment__code', 'equipment__name', 'borrower__last_name')



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')



@admin.register(EquipmentDocument)
class EquipmentDocumentAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'title', 'document_type', 'active', 'sort_order')
    list_filter = ('document_type', 'active', 'equipment__category')
    search_fields = ('equipment__code', 'equipment__name', 'title', 'description')
    autocomplete_fields = ('equipment',)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'name', 'required', 'expected_quantity', 'default_condition', 'photo_preview', 'sort_order')
    list_filter = ('required', 'default_condition', 'equipment__category')
    search_fields = ('equipment__code', 'equipment__name', 'name')
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        if obj and obj.photo:
            return format_html('<img src="{}" style="height:60px; max-width:100px; object-fit:contain;" />', obj.photo.url)
        return '-'
    photo_preview.short_description = 'Aperçu photo'



@admin.register(ComponentCheck)
class ComponentCheckAdmin(admin.ModelAdmin):
    list_display = ('loan', 'component', 'check_type', 'present', 'quantity', 'condition', 'checked_by', 'checked_by_role')
    list_filter = ('check_type', 'present', 'condition', 'checked_by_role')
    search_fields = ('loan__equipment__code', 'loan__borrower__last_name', 'component__name', 'checked_by__last_name')



@admin.register(InterventionLog)
class InterventionLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'storekeeper', 'intervention_at', 'intervention_type', 'result', 'resulting_condition')
    list_filter = ('intervention_type', 'result', 'resulting_condition', 'intervention_at')
    search_fields = ('equipment__code', 'equipment__name', 'equipment__description', 'storekeeper__code', 'storekeeper__last_name', 'finding', 'action_done', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('equipment', 'storekeeper')


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'storekeeper', 'repaired_at', 'repair_type', 'result', 'resulting_condition')
    list_filter = ('repair_type', 'result', 'resulting_condition', 'repaired_at')
    search_fields = ('equipment__code', 'equipment__name', 'storekeeper__code', 'storekeeper__last_name', 'diagnosis', 'action_done', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('equipment', 'storekeeper')


class UserInventoryItemInline(admin.TabularInline):
    model = UserInventoryItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('component', 'present', 'quantity', 'condition', 'comment')
    autocomplete_fields = ('component',)


@admin.register(UserInventory)
class UserInventoryAdmin(admin.ModelAdmin):
    list_display = ('submitted_at', 'equipment', 'borrower', 'inventory_type', 'status', 'applied_by', 'applied_at')
    list_filter = ('inventory_type', 'status', 'equipment__category')
    search_fields = ('equipment__code', 'equipment__name', 'borrower__code', 'borrower__last_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('equipment', 'loan', 'borrower', 'applied_by')
    inlines = [UserInventoryItemInline]


@admin.register(UserInventoryItem)
class UserInventoryItemAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'component', 'present', 'quantity', 'condition')
    list_filter = ('present', 'condition', 'inventory__inventory_type', 'inventory__status')
    search_fields = ('inventory__equipment__code', 'component__name', 'inventory__borrower__last_name')
    autocomplete_fields = ('inventory', 'component')


@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('formation', 'code', 'title', 'block', 'unit', 'active')
    list_filter = ('formation', 'active', 'block')
    search_fields = ('code', 'title', 'description')


class SessionRoleAssignmentInline(admin.TabularInline):
    model = SessionRoleAssignment
    extra = 1
    fields = ('person', 'role', 'comment')
    autocomplete_fields = ('person',)


@admin.register(PedagogicalSession)
class PedagogicalSessionAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'formation', 'class_name', 'group_name', 'active')
    list_filter = ('formation', 'active', 'date', 'class_name')
    search_fields = ('title', 'objectives', 'class_name', 'group_name')
    filter_horizontal = ('targeted_competences',)
    inlines = [SessionRoleAssignmentInline]


@admin.register(SessionRoleAssignment)
class SessionRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('session', 'person', 'role')
    list_filter = ('role', 'session__formation', 'session__class_name')
    search_fields = ('session__title', 'person__code', 'person__last_name', 'person__first_name')
    autocomplete_fields = ('session', 'person')


@admin.register(CompetenceMapping)
class CompetenceMappingAdmin(admin.ModelAdmin):
    list_display = ('formation', 'action_type', 'role', 'competence', 'weight', 'active')
    list_filter = ('formation', 'action_type', 'role', 'active')
    search_fields = ('competence__code', 'competence__title', 'criterion')


@admin.register(EvaluationRecord)
class EvaluationRecordAdmin(admin.ModelAdmin):
    list_display = ('person', 'competence', 'session', 'role', 'proposed_level', 'validated_level', 'evidence_count', 'source')
    list_filter = ('competence__formation', 'role', 'source', 'proposed_level', 'validated_level')
    search_fields = ('person__code', 'person__last_name', 'person__first_name', 'competence__code', 'comment')
    autocomplete_fields = ('session', 'person', 'competence', 'validated_by')


@admin.register(LockerSettings)
class LockerSettingsAdmin(admin.ModelAdmin):
    list_display = ('module_enabled', 'require_authorized_terminal', 'require_allowed_public_ip', 'script_timeout_seconds', 'updated_at')
    fieldsets = (
        ('Activation du module', {'fields': ('module_enabled',)}),
        ('Sécurité ouverture casier', {'fields': ('require_authorized_terminal', 'require_allowed_public_ip', 'allowed_public_ips')}),
        ('Forçage super admin', {'fields': ('allow_superadmin_force_without_terminal', 'allow_superadmin_force_without_ip')}),
        ('Script serveur', {'fields': ('script_timeout_seconds',)}),
    )

    def has_add_permission(self, request):
        return not LockerSettings.objects.exists()


@admin.register(AuthorizedTerminal)
class AuthorizedTerminalAdmin(admin.ModelAdmin):
    list_display = ('name', 'terminal_type', 'can_open_lockers', 'active', 'last_seen_at', 'last_ip', 'created_by')
    list_filter = ('terminal_type', 'can_open_lockers', 'active')
    search_fields = ('name', 'last_ip', 'created_by__last_name', 'created_by__first_name')
    readonly_fields = ('token', 'last_seen_at', 'last_ip', 'user_agent', 'created_at', 'updated_at')


@admin.register(LockerOpenLog)
class LockerOpenLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'cabinet', 'locker', 'equipment', 'storekeeper', 'terminal', 'context', 'success', 'refused', 'client_ip')
    list_filter = ('context', 'success', 'refused', 'cabinet')
    search_fields = ('cabinet', 'locker', 'equipment__code', 'equipment__name', 'storekeeper__code', 'storekeeper__last_name', 'refusal_reason')
    readonly_fields = ('created_at', 'updated_at', 'equipment', 'storekeeper', 'terminal', 'cabinet', 'locker', 'context', 'success', 'refused', 'refusal_reason', 'payload', 'controller_response', 'client_ip', 'user_agent')


@admin.register(MaterialEditGrant)
class MaterialEditGrantAdmin(admin.ModelAdmin):
    list_display = ('formation', 'class_name', 'group_name', 'start_date', 'end_date', 'active', 'can_create_equipment', 'can_edit_equipment', 'can_edit_components', 'granted_by')
    list_filter = ('active', 'formation', 'class_name', 'group_name', 'can_create_equipment', 'can_edit_equipment')
    search_fields = ('formation__code', 'formation__name', 'class_name', 'group_name', 'comment', 'granted_by__code', 'granted_by__last_name')
    autocomplete_fields = ('formation', 'granted_by')


admin.site.site_header = 'Administration ToolMag'
admin.site.site_title = 'ToolMag'
admin.site.index_title = 'Gestion ToolMag'
