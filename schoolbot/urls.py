from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf.urls.static import static


def index(request):
    return HttpResponse("Welcome to Yuksalish School Bot API")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bot.urls')),
path('favicon.ico', lambda x: HttpResponse(status=204)),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)