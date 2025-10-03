from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "contas"

urlpatterns = [
    path("login/",  auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page=reverse_lazy("contas:login")), name="logout"), # Logout, POST redireciona para a tela de login 
    path("dashboard/", views.dashboard, name="dashboard"),
    path("registrar/", views.registrar, name="registrar"), # Se usar o cadastro
    path("admin-area/", views.admin_area, name="admin_area"), # Area restrita para administradores
]
