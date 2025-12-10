from django.urls import path
from . import views

app_name = "relatorios"

urlpatterns = [
    path("viagens/", views.relatorio_viagens, name="viagens"),

    path("os/", views.rel_os, name="os"),
    path("os.csv", views.rel_os_csv, name="os_csv"),
    path("os.pdf", views.rel_os_pdf, name="os_pdf"),

    path("problemas/", views.rel_problemas, name="problemas"),
    path("problemas.csv", views.rel_problemas_csv, name="problemas_csv"),
]
