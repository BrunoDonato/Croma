from django.urls import path
from . import views

app_name = "ordens"

urlpatterns = [
    path("nova/", views.criar_os, name="os_nova"),
    path("sucesso/", views.os_sucesso, name="os_sucesso"),
]
