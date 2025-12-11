from django.urls import path
from . import views

app_name = "prestadores"

urlpatterns = [
    path("ordens-externas/", views.ordem_externa_lista, name="ordem_externa_lista"),
    path("ordens-externas/nova/", views.ordem_externa_nova, name="ordem_externa_nova"),
    path("ordens-externas/<int:pk>/", views.ordem_externa_detalhe, name="ordem_externa_detalhe"),
    path("contatos/", views.contatos_lista, name="contatos_lista"),
]
