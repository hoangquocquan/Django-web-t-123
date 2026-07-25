"""Cấu hình Django Admin cho Common/System."""

from django.contrib import admin

from .models import CmsBanner, CmsMenuItem, CmsPage, EnterpriseEvent, JobQueue, Notification

admin.site.register(CmsPage)
admin.site.register(CmsMenuItem)
admin.site.register(CmsBanner)
admin.site.register(EnterpriseEvent)
admin.site.register(JobQueue)
admin.site.register(Notification)
