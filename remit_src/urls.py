from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.http import HttpResponse


def home(request):
    return HttpResponse("Hello, I'm Django. Welcome!")

urlpatterns = [
    path("", home, name="home"),
    path("api/agent/", include("agent_api.urls")),
    path("api/remit/", include("remit_api.urls")),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
