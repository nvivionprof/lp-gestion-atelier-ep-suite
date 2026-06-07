from django.contrib import admin
from .models import *


class SeqSequenceFormationInline(admin.TabularInline):
    model = SeqSequenceFormation
    extra = 0


class SeqPresenceWaveInline(admin.TabularInline):
    model = SeqPresenceWave
    extra = 0


class SeqSessionInline(admin.TabularInline):
    model = SeqSession
    extra = 0


class SeqAssignmentInline(admin.TabularInline):
    model = SeqAssignment
    extra = 0


@admin.register(SeqSequence)
class SeqSequenceAdmin(admin.ModelAdmin):
    list_display = ('code', 'titre', 'date_debut', 'nb_semaines', 'zone_principale', 'coloration', 'statut', 'auto_inscription_libre')
    list_filter = ('statut', 'coloration', 'zone_principale', 'auto_inscription_libre', 'sequence_modele')
    search_fields = ('code', 'titre', 'description', 'axe_principal')
    filter_horizontal = ('professeurs', 'zones', 'slots')
    inlines = [SeqSequenceFormationInline, SeqPresenceWaveInline, SeqSessionInline]


@admin.register(SeqColoration)
class SeqColorationAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'statut', 'active')
    list_filter = ('statut', 'active')
    search_fields = ('code', 'nom', 'description')


@admin.register(SeqZone)
class SeqZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'capacite_max', 'active')
    search_fields = ('code', 'nom', 'description')
    list_filter = ('active',)
    filter_horizontal = ('systemes',)


@admin.register(SeqWeeklySlot)
class SeqWeeklySlotAdmin(admin.ModelAdmin):
    list_display = ('code', 'day', 'half_day', 'active')
    list_filter = ('day', 'half_day', 'active')


class SeqRotationFormationInline(admin.TabularInline):
    model = SeqRotationFormation
    extra = 0


@admin.register(SeqRotationBlock)
class SeqRotationBlockAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'active')
    search_fields = ('code', 'nom', 'description')
    filter_horizontal = ('slots', 'zones', 'professeurs')
    inlines = [SeqRotationFormationInline]


@admin.register(SeqPresenceWave)
class SeqPresenceWaveAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'nom', 'formation_code', 'classe', 'type_presence', 'semaine_debut', 'duree_semaines')
    list_filter = ('type_presence', 'formation_code', 'classe')
    search_fields = ('nom', 'formation_code', 'classe', 'sequence__code', 'sequence__titre')
    filter_horizontal = ('eleves',)


@admin.register(SeqStudentGroup)
class SeqStudentGroupAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'nom', 'type_groupe', 'formation_dominante', 'ordre', 'parcours_libre')
    list_filter = ('type_groupe', 'formation_dominante', 'parcours_libre')
    search_fields = ('nom', 'sequence__code', 'sequence__titre')


@admin.register(SeqStudentGroupMember)
class SeqStudentGroupMemberAdmin(admin.ModelAdmin):
    list_display = ('group', 'eleve', 'role', 'ordre')
    search_fields = ('group__nom', 'eleve__code', 'eleve__last_name', 'eleve__first_name')


@admin.register(SeqSession)
class SeqSessionAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'numero', 'semaine', 'date', 'slot', 'titre')
    list_filter = ('semaine', 'slot')
    search_fields = ('sequence__code', 'sequence__titre', 'titre')
    inlines = [SeqAssignmentInline]


@admin.register(SeqAssignment)
class SeqAssignmentAdmin(admin.ModelAdmin):
    list_display = ('session', 'group', 'eleve_individuel', 'tp', 'systeme', 'mode', 'status', 'tp_note')
    list_filter = ('mode', 'status', 'tp_note', 'zone')
    search_fields = ('session__sequence__code', 'group__nom', 'eleve_individuel__code', 'tp__code', 'tp__titre', 'systeme__code')


@admin.register(SeqSystemBooking)
class SeqSystemBookingAdmin(admin.ModelAdmin):
    list_display = ('systeme', 'session', 'sequence', 'status', 'source')
    list_filter = ('status', 'source')
    search_fields = ('systeme__code', 'sequence__code', 'session__titre')


@admin.register(SeqFreeChoiceRequest)
class SeqFreeChoiceRequestAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'session', 'eleve', 'tp', 'systeme', 'status')
    list_filter = ('status',)
    search_fields = ('eleve__code', 'eleve__last_name', 'tp__code', 'tp__titre', 'sequence__code')
