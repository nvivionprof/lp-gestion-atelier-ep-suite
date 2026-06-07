from django.contrib import admin
from .models import *

@admin.register(TpUser)
class TpUserAdmin(admin.ModelAdmin):
    list_display = ('code', 'username', 'last_name', 'first_name', 'class_name', 'formation_code', 'role_principal', 'active')
    search_fields = ('code', 'username', 'last_name', 'first_name', 'class_name')
    list_filter = ('active', 'role_principal', 'formation_code')

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'active')
    search_fields = ('code', 'nom')

@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'ordre', 'active')

admin.site.register(FormationNiveau)
admin.site.register(ZoneApprentissage)
admin.site.register(ThemeGeneral)
admin.site.register(ThemeSecondaire)
admin.site.register(TypeTP)
admin.site.register(SystemePedagogiqueRef)
admin.site.register(Referentiel)
admin.site.register(BlocCompetence)
admin.site.register(Competence)
admin.site.register(SousCompetence)
admin.site.register(ActiviteReferentiel)
admin.site.register(TacheReferentiel)

class TPDocumentInline(admin.TabularInline):
    model = TPDocument
    extra = 0

class TPCompetenceInline(admin.TabularInline):
    model = TPCompetence
    extra = 0

class TPSystemeInline(admin.TabularInline):
    model = TPSysteme
    extra = 0

@admin.register(TP)
class TPAdmin(admin.ModelAdmin):
    list_display = ('code', 'titre', 'formation_principale', 'zone_apprentissage', 'theme_secondaire', 'temps_estime_minutes', 'statut', 'version')
    search_fields = ('code', 'titre', 'resume_apprentissages')
    list_filter = ('statut', 'formation_principale', 'zone_apprentissage', 'theme_general', 'theme_secondaire')
    inlines = [TPDocumentInline, TPCompetenceInline, TPSystemeInline]

admin.site.register(TPFormationNiveau)
admin.site.register(TPPrerequis)
admin.site.register(TPSuivant)
admin.site.register(TPDocument)
admin.site.register(SerieTP)
admin.site.register(SerieTPItem)
admin.site.register(SequencePedagogique)
admin.site.register(SequenceTP)
admin.site.register(ParcoursEleveTP)
admin.site.register(TraceEleveTP)
admin.site.register(EvaluationCompetenceTP)

for m in [PoleActivite, UniteCertificative, BlocUnite, SavoirAssocie, CompetenceSavoir, CritereEvaluation, IndicateurEvaluation, TacheCompetence, TPTache, TPSavoir, TPCritere, TPContributionPermission]:
    try:
        admin.site.register(m)
    except admin.sites.AlreadyRegistered:
        pass

# TP Manager V2
for m in [BacDiplome, BacPole, BacUnite, BacCompetence, BacBloc, BacBlocCompetence,
          BacChampTP, BacChampTPOption, BacActivite, BacTache, BacTacheCompetence,
          BacCompetenceCritere, BacAttitudeProfessionnelle, BacCompetenceAttitude,
          CompetencePivot, TPV2, TPV2ChampValeur, TPV2ActiviteOfficielle,
          TPV2TacheOfficielle, TPV2CompetenceOfficielle, TPV2CritereOfficiel,
          TPV2AttitudeOfficielle, TPV2CritereReussite, TPV2CritereEvaluationFinale,
          TPV2Document, TPV2LinkedBlock, TPV2LinkedTPItem, TPV2CriterionLibrary,
          TPV2ResourceGroup, TPV2ResourceItem, TPV2TransferRule]:
    try:
        admin.site.register(m)
    except admin.sites.AlreadyRegistered:
        pass


# Admin autocomplete support for Evaluation Manager
# These models are used in autocomplete_fields by evaluation_manager.admin.
# Django requires their ModelAdmin to define search_fields.
for _model in [BacCompetence, BacCompetenceCritere, TPV2]:
    try:
        admin.site.unregister(_model)
    except admin.sites.NotRegistered:
        pass

@admin.register(BacCompetence)
class BacCompetenceOfficialAdmin(admin.ModelAdmin):
    # BacCompetence n'a pas de champ ordre dans les versions 2.8.x/2.9.x.
    # Garder uniquement les champs réellement présents évite le crash Django admin.E108.
    list_display = ('diplome', 'code', 'libelle_officiel', 'selectable_bac')
    list_filter = ('diplome', 'selectable_bac')
    search_fields = ('code', 'libelle_officiel', 'diplome__code', 'diplome__nom')
    ordering = ('diplome__code', 'code')

@admin.register(BacCompetenceCritere)
class BacCompetenceCritereOfficialAdmin(admin.ModelAdmin):
    list_display = ('competence', 'code', 'libelle_officiel', 'ordre')
    list_filter = ('competence__diplome', 'competence')
    search_fields = (
        'code',
        'libelle_officiel',
        'competence__code',
        'competence__libelle_officiel',
        'competence__diplome__code',
    )
    ordering = ('competence__diplome__code', 'competence__code', 'ordre', 'code')

@admin.register(TPV2)
class TPV2OfficialAdmin(admin.ModelAdmin):
    # Noms de champs réels du modèle TPV2 : niveau_classe et domaine_principal.
    # created_at/updated_at viennent de TimeStampedModel.
    list_display = ('code', 'titre', 'diplome', 'niveau_classe', 'domaine_principal', 'sous_theme', 'usage_pedagogique', 'statut', 'updated_at')
    list_filter = ('diplome', 'niveau_classe', 'domaine_principal', 'usage_pedagogique', 'statut')
    search_fields = ('code', 'titre', 'domaine_principal', 'sous_theme', 'resume_eleve', 'diplome__code')
    ordering = ('diplome__code', 'code')
