from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from api.views import redirect_to_original

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_code>/', redirect_to_original, name='short_link_redirect'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)