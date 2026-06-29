from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('display_manager.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL.replace(settings.FORCE_SCRIPT_NAME, '', 1), document_root=settings.MEDIA_ROOT)
