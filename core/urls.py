"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from contas.views import is_admin
from django.conf import settings
from django.conf.urls.static import static

def home_router(request):
    if not request.user.is_authenticated:
        return redirect("contas:login")
    if is_admin(request.user):
        return redirect("contas:dashboard")
    return redirect("ordens:os_nova")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("contas/", include(("contas.urls", "contas"), namespace="contas")),
    path("os/", include(("ordens.urls", "ordens"), namespace="ordens")),
    path("viagens/", include(("viagens.urls", "viagens"), namespace="viagens")),
    path("relatorios/", include(("relatorios.urls", "relatorios"), namespace="relatorios")),
    path("", home_router, name="home"),
    path("estoque/", include(("estoque.urls", "estoque"), namespace="estoque")),
    path("prestadores/", include("prestadores.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Erro 403 (Acesso negado)
handler403 = "contas.views.error_403"

