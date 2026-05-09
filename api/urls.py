from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path("auth/login/", views.LoginAPIView.as_view(), name="api_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api_refresh"),
    path("auth/google/", views.GoogleLoginAPIView.as_view(), name="api_google_login"),
    path("os/categorias/", views.OSCategoriasAPIView.as_view(), name="api_os_categorias"),
    path("os/", views.OSListaAPIView.as_view(), name="api_os_lista"),
    path("os/<int:pk>/", views.OSDetalheAPIView.as_view(), name="api_os_detalhe"),
]