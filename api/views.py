from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"erro": "Informe usuário e senha."},
                status=400
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"erro": "Usuário ou senha inválidos."},
                status=401
            )

        if not user.is_active:
            return Response(
                {"erro": "Usuário inativo."},
                status=403
            )

        refresh = RefreshToken.for_user(user)
        perfil = getattr(user, "perfil", None)
        loja = None
        if perfil and perfil.loja:
            loja = {
                "id": perfil.loja.id,
                "nome": perfil.loja.nome,
            }

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "usuario": {
                "id": user.id,
                "username": user.username,
                "nome": user.get_full_name() or user.username,
                "email": user.email,
                "is_admin": user.is_superuser or user.groups.filter(name="admin").exists(),
                "loja": loja,
            }
        })


class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("id_token")

        if not token:
            return Response(
                {"erro": "Token não informado."},
                status=400
            )

        try:
            info = id_token.verify_firebase_token(
                token,
                google_requests.Request()
            )
            email = info.get("email")
            nome = info.get("name", email)

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": nome.split()[0] if nome else "",
                }
            )

            refresh = RefreshToken.for_user(user)
            perfil = getattr(user, "perfil", None)
            loja = None
            if perfil and perfil.loja:
                loja = {
                    "id": perfil.loja.id,
                    "nome": perfil.loja.nome,
                }

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "usuario": {
                    "id": user.id,
                    "username": user.username,
                    "nome": user.get_full_name() or user.username,
                    "email": user.email,
                    "is_admin": user.is_superuser or user.groups.filter(name="admin").exists(),
                    "loja": loja,
                }
            })

        except Exception as e:
            return Response(
                {"erro": "Token inválido.", "detalhe": str(e)},
                status=401
            )