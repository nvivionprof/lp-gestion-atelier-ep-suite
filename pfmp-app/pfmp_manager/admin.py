from django.contrib import admin
from .models import Formation, PfmpUser, Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep, CompanyAnnouncement
for m in [Formation, PfmpUser, Company, CompanyContact, PfmpPeriod, StudentAssignment, StudentStep, CompanyAnnouncement]: admin.site.register(m)
