from django.contrib import admin

from .models import (
    DisplayCommand,
    DisplayLayout,
    DisplayMedia,
    DisplayQRCodeAction,
    DisplayScreen,
    DisplayZone,
    DisplayZoneItem,
)


class DisplayZoneItemInline(admin.TabularInline):
    model = DisplayZoneItem
    extra = 1


class DisplayZoneInline(admin.TabularInline):
    model = DisplayZone
    extra = 0


@admin.register(DisplayLayout)
class DisplayLayoutAdmin(admin.ModelAdmin):
    list_display = ('name', 'column_position', 'target_width', 'target_height', 'is_active')
    list_filter = ('column_position', 'is_active')
    search_fields = ('name',)
    inlines = [DisplayZoneInline]


@admin.register(DisplayZone)
class DisplayZoneAdmin(admin.ModelAdmin):
    list_display = ('layout', 'name', 'order')
    list_filter = ('name',)
    inlines = [DisplayZoneItemInline]


@admin.register(DisplayMedia)
class DisplayMediaAdmin(admin.ModelAdmin):
    list_display = ('name', 'media_type', 'default_duration_seconds', 'is_active')
    list_filter = ('media_type', 'is_active')
    search_fields = ('name', 'web_url')


@admin.register(DisplayScreen)
class DisplayScreenAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'status', 'last_contact', 'active_layout', 'is_active')
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'location', 'association_code', 'player_token')
    readonly_fields = ('association_code', 'player_token', 'last_contact', 'ip_address')


@admin.register(DisplayQRCodeAction)
class DisplayQRCodeActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'action', 'target_screen', 'duration_seconds', 'is_active', 'use_count')
    list_filter = ('action', 'is_active')
    search_fields = ('name', 'token')
    readonly_fields = ('token', 'use_count')


@admin.register(DisplayCommand)
class DisplayCommandAdmin(admin.ModelAdmin):
    list_display = ('screen', 'action', 'status', 'created_at', 'executed_at')
    list_filter = ('action', 'status')
    search_fields = ('screen__name', 'result')
    readonly_fields = ('created_at', 'sent_at', 'executed_at')
