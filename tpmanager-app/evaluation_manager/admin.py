from django.contrib import admin
from .models import EvalActivity, EvalCriterionResult, EvalBilanIntermediaire, EvalBilanCompetence


class EvalCriterionResultInline(admin.TabularInline):
    model = EvalCriterionResult
    extra = 0
    autocomplete_fields = ['critere']


@admin.register(EvalActivity)
class EvalActivityAdmin(admin.ModelAdmin):
    list_display = ['code_eval', 'eleve', 'tp', 'date_activite', 'statut', 'absent', 'a_refaire', 'tp_note', 'note_calculee']
    list_filter = ['statut', 'absent', 'a_refaire', 'formation_code', 'classe', 'tp_note']
    search_fields = [
        'code_eval',
        'intitule',
        'eleve__first_name',
        'eleve__last_name',
        'eleve__code',
        'tp__code',
        'tp__titre',
    ]
    autocomplete_fields = ['eleve', 'tp', 'evaluateur']
    inlines = [EvalCriterionResultInline]


@admin.register(EvalCriterionResult)
class EvalCriterionResultAdmin(admin.ModelAdmin):
    list_display = ['activity', 'critere', 'auto_niveau', 'prof_niveau', 'pourcentage', 'a_refaire']
    list_filter = ['prof_niveau', 'auto_niveau', 'a_refaire']
    search_fields = [
        'activity__code_eval',
        'activity__intitule',
        'activity__eleve__last_name',
        'activity__eleve__first_name',
        'critere__libelle_officiel',
        'critere__competence__code',
        'critere__competence__libelle_officiel',
    ]
    autocomplete_fields = ['activity', 'critere']


class EvalBilanCompetenceInline(admin.TabularInline):
    model = EvalBilanCompetence
    extra = 0
    autocomplete_fields = ['competence']


@admin.register(EvalBilanIntermediaire)
class EvalBilanIntermediaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'eleve', 'type_bilan', 'date_bilan', 'verrouille']
    list_filter = ['type_bilan', 'verrouille', 'formation_code', 'classe']
    search_fields = [
        'nom',
        'eleve__first_name',
        'eleve__last_name',
        'eleve__code',
    ]
    autocomplete_fields = ['eleve', 'validateur']
    inlines = [EvalBilanCompetenceInline]


@admin.register(EvalBilanCompetence)
class EvalBilanCompetenceAdmin(admin.ModelAdmin):
    list_display = ['bilan', 'competence', 'niveau', 'date_validation']
    list_filter = ['niveau', 'competence__diplome__code']
    search_fields = [
        'bilan__nom',
        'bilan__eleve__last_name',
        'bilan__eleve__first_name',
        'competence__code',
        'competence__libelle_officiel',
    ]
    autocomplete_fields = ['bilan', 'competence']
