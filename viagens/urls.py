from django.urls import path
from . import views

app_name = "viagens"

urlpatterns = [
    path("nova/", views.criar_viagem, name="viagem_nova"),
    path("nova/", views.criar_viagem, name="nova"),
    path("nova/<int:os_id>/", views.criar_viagem, name="viagem_nova_os"),
    path("<int:pk>/", views.detalhe_viagem, name="viagem_detalhe"),
    path("<int:pk>/", views.detalhe_viagem, name="detalhe"),
]
