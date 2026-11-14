import django
from django.apps import apps
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps import views
from django.urls import include, path
from oscar.views import handler403, handler404, handler500
from citas import vista_reservar_cita, vista_panel_barbero
from apps.sitemaps import base_sitemaps

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include(django.conf.urls.i18n)),
    path('sitemap.xml', views.index, {'sitemaps': base_sitemaps}),
    path('sitemap-<slug:section>.xml', views.sitemap, {'sitemaps': base_sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # Ruta directa de citas y panel sin prefijo de idioma
    path('citas/', vista_reservar_cita, name='reservar_cita'),
    path('panel-barbero/', vista_panel_barbero, name='panel_barbero_directo'),
]

# Rutas con prefijo de idioma (/es/, /en-gb/) - Priorizamos Citas en la página principal
urlpatterns += i18n_patterns(
    path('', vista_reservar_cita, name='home_citas'),
    path('citas/', vista_reservar_cita, name='reservar_cita_i18n'),
    path('panel-barbero/', vista_panel_barbero, name='panel_barbero'),
    path('', include(apps.get_app_config('oscar').urls[0])),
)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('403', handler403, {'exception': Exception()}),
        path('404', handler404, {'exception': Exception()}),
        path('500', handler500),
        path('__debug__/', include(debug_toolbar.urls)),
    ]