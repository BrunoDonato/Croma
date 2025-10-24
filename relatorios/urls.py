from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    path("viagens/", views.relatorio_viagens, name="viagens"),
]
