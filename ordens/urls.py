from django.urls import path
from . import views

app_name = "ordens"

urlpatterns = [
    # Criação OS
    path("nova/", views.criar_os, name="os_nova"),
    path("sucesso/", views.os_sucesso, name="os_sucesso"),

    # Listagem OS
    path("listar/", views.listar_os, name="os_listar"),          # Visão do admin
    path("minhas/", views.os_minhas, name="os_minhas"),          # Solicitações do usuário

    # Detalhes e interações
    path("<int:pk>/", views.detalhe_os, name="os_detalhe"),

    # Ações relacionadas à OS específica
    path("<int:pk>/comentario/", views.os_comentario, name="os_comentario"),
    path("<int:pk>/anexo/", views.os_anexo, name="os_anexo"),
    path("<int:pk>/acao/", views.os_acao_status, name="os_acao_status"),
    path("<int:pk>/atribuir/", views.os_atribuir, name="os_atribuir"),
]
