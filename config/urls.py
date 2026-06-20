from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok", "version": "228"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", health),
    path("api/", include("catalog.urls")),
]
