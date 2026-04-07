from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


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

        # Busca o perfil para retornar a loja do técnico
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