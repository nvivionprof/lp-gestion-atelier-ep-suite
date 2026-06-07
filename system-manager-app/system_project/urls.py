from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('', include('system_manager.urls')),
    path('admin/', admin.site.urls),
]
# Avec APP_URL_PREFIX=/system, Nginx retire le préfixe avant proxy_pass.
# Les liens publics restent /system/media/..., mais Django reçoit /media/...
# Cette route corrige l'affichage des photos et l'ouverture des documents.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
