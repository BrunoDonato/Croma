from django.urls import path
from . import views

app_name = "estoque"

urlpatterns = [
    path("", views.estoque_home, name="home"),
    path("exportar-csv/", views.estoque_exportar_csv, name="exportar_csv"),
    path("movimentar/", views.movimentacao_form, name="movimentar"),
]
