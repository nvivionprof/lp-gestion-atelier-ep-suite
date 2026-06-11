from django.contrib import admin
from .models import (
    Formation, PfmpUser, Company, CompanyContact, PfmpPeriod,
    StudentAssignment, StudentStep, CompanyAnnouncement, CompanyTag,
    StudentCompanySearch, StudentCompanyAction, ImportBatch
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name','city','postal_code','activity','status','student_visible','geocoding_status')
    search_fields = ('name','external_key','siret','city','postal_code','activity','domains_text')
    list_filter = ('status','student_visible','geocoding_status','formations','tags')
    filter_horizontal = ('formations','tags')


@admin.register(CompanyContact)
class CompanyContactAdmin(admin.ModelAdmin):
    list_display = ('full_name','company','email','contact_type','student_visible','teacher_visible','active','can_help_transport')
    search_fields = ('full_name','email','company__name','role','service')
    list_filter = ('contact_type','student_visible','teacher_visible','active','can_help_transport','use_personal_location_for_student_search')
    filter_horizontal = ('formations',)


@admin.register(StudentCompanySearch)
class StudentCompanySearchAdmin(admin.ModelAdmin):
    list_display = ('student','period','company','status','last_action_at','updated_at')
    search_fields = ('student__username','student__code','company__name','tags_text')
    list_filter = ('status','period')


@admin.register(StudentCompanyAction)
class StudentCompanyActionAdmin(admin.ModelAdmin):
    list_display = ('search','action_type','status_after','created_by','created_at','next_action_date')
    search_fields = ('search__company__name','search__student__username','comment','next_action')
    list_filter = ('action_type','status_after','created_at')


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ('file_name','mode','key_strategy','started_at','finished_at','created_count','updated_count','deleted_count','error_count')
    list_filter = ('mode','key_strategy')


admin.site.register(Formation)
admin.site.register(PfmpUser)
admin.site.register(PfmpPeriod)
admin.site.register(StudentAssignment)
admin.site.register(StudentStep)
admin.site.register(CompanyAnnouncement)
admin.site.register(CompanyTag)
