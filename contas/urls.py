from django.urls import path
from . import views

app_name = "contas"  # <- importante para usar 'contas:login' etc.

urlpatterns = [
    path("registrar/", views.registrar, name="registrar"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
