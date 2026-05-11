import requests as req
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ordens.models import OrdemServico, AndamentoOS, CategoriaProblema
from estoque.models import Loja
from django.db.models import Count
from datetime import timedelta
from django.db.models import Avg, F, ExpressionWrapper, DurationField

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"erro": "Informe usuário e senha."}, status=400)

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response({"erro": "Usuário ou senha inválidos."}, status=401)

        if not user.is_active:
            return Response({"erro": "Usuário inativo."}, status=403)

        refresh = RefreshToken.for_user(user)
        perfil = getattr(user, "perfil", None)
        loja = None
        if perfil and perfil.loja:
            loja = {"id": perfil.loja.id, "nome": perfil.loja.nome}

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
        access_token = request.data.get("id_token")

        if not access_token:
            return Response({"erro": "Token não informado."}, status=400)

        try:
            google_response = req.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            info = google_response.json()

            if "error" in info:
                return Response({"erro": "Token inválido."}, status=401)

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
                loja = {"id": perfil.loja.id, "nome": perfil.loja.nome}

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
            return Response({"erro": "Erro ao validar token.", "detalhe": str(e)}, status=401)


def serializar_os(os):
    return {
        "id": os.id,
        "loja": {"id": os.loja.id, "nome": os.loja.nome} if os.loja else None,
        "solicitante": os.solicitante.get_full_name() or os.solicitante.username,
        "tecnico_responsavel": (
            os.tecnico_responsavel.get_full_name() or os.tecnico_responsavel.username
        ) if os.tecnico_responsavel else None,
        "categoria": os.categoria.nome if os.categoria else None,
        "descricao_problema": os.descricao_problema,
        "prioridade": os.prioridade,
        "status": os.status,
        "observacoes": os.observacoes,
        "solucao": os.solucao,
        "motivo_cancelamento": os.motivo_cancelamento,
        "custo_total": str(os.custo_total) if os.custo_total else None,
        "data_abertura": os.data_abertura.isoformat(),
        "data_fechamento": os.data_fechamento.isoformat() if os.data_fechamento else None,
    }


class OSListaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_superuser or user.groups.filter(name="admin").exists()

        if is_admin:
            ordens = OrdemServico.objects.select_related(
                "loja", "solicitante", "tecnico_responsavel", "categoria"
            ).order_by("-data_abertura")
        else:
            ordens = OrdemServico.objects.filter(
                tecnico_responsavel=user
            ).select_related(
                "loja", "solicitante", "tecnico_responsavel", "categoria"
            ).order_by("-data_abertura")

        return Response([serializar_os(os) for os in ordens])

    def post(self, request):
        user = request.user
        data = request.data

        descricao = data.get("descricao_problema")
        if not descricao:
            return Response({"erro": "Descrição do problema é obrigatória."}, status=400)

        perfil = getattr(user, "perfil", None)
        loja_id = data.get("loja_id") or (perfil.loja_id if perfil else None)
        if not loja_id:
            return Response({"erro": "Loja não identificada."}, status=400)

        loja = get_object_or_404(Loja, pk=loja_id)
        categoria_id = data.get("categoria_id")
        categoria = get_object_or_404(CategoriaProblema, pk=categoria_id) if categoria_id else None

        os = OrdemServico.objects.create(
            loja=loja,
            solicitante=user,
            descricao_problema=descricao,
            prioridade=data.get("prioridade", "MEDIA"),
            categoria=categoria,
            observacoes=data.get("observacoes", ""),
        )

        return Response(serializar_os(os), status=201)


class OSDetalheAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        is_admin = user.is_superuser or user.groups.filter(name="admin").exists()
        os = get_object_or_404(
            OrdemServico.objects.select_related("loja", "solicitante", "tecnico_responsavel", "categoria"),
            pk=pk
        )

        if not (is_admin or os.solicitante == user or os.tecnico_responsavel == user):
            return Response({"erro": "Acesso negado."}, status=403)

        return Response(serializar_os(os))

    def put(self, request, pk):
        user = request.user
        is_admin = user.is_superuser or user.groups.filter(name="admin").exists()
        os = get_object_or_404(OrdemServico, pk=pk)

        if not (is_admin or os.tecnico_responsavel == user):
            return Response({"erro": "Acesso negado."}, status=403)

        data = request.data
        novo_status = data.get("status")

        if novo_status and novo_status != os.status:
            if novo_status == "FINALIZADA":
                solucao = data.get("solucao", os.solucao)
                if not solucao.strip():
                    return Response({"erro": "Informe a solução antes de finalizar."}, status=400)
                os.solucao = solucao

            if novo_status == "CANCELADA":
                motivo = data.get("motivo_cancelamento", os.motivo_cancelamento)
                if not motivo.strip():
                    return Response({"erro": "Informe o motivo do cancelamento."}, status=400)
                os.motivo_cancelamento = motivo

            try:
                os.mudar_status(
                    novo_status,
                    autor=user,
                    texto_andamento=data.get("texto_andamento", ""),
                )
            except OrdemServico.TransicaoInvalida as e:
                return Response({"erro": str(e)}, status=400)
            except OrdemServico.CamposObrigatorios as e:
                return Response({"erro": str(e)}, status=400)

        if "observacoes" in data:
            os.observacoes = data["observacoes"]
        if "solucao" in data:
            os.solucao = data["solucao"]
        if "custo_total" in data:
            os.custo_total = data["custo_total"]

        os.save()
        return Response(serializar_os(os))

    def delete(self, request, pk):
        user = request.user
        is_admin = user.is_superuser or user.groups.filter(name="admin").exists()

        if not is_admin:
            return Response({"erro": "Apenas administradores podem excluir OS."}, status=403)

        os = get_object_or_404(OrdemServico, pk=pk)
        os.delete()
        return Response({"mensagem": "OS excluída com sucesso."}, status=200)


class OSCategoriasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categorias = CategoriaProblema.objects.filter(ativo=True).values("id", "nome")
        return Response(list(categorias))

class LojasAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        lojas = Loja.objects.all().values("id", "nome")
        return Response(list(lojas))

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_superuser or user.groups.filter(name="admin").exists()
        agora = timezone.now()
        inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if is_admin:
            qs = OrdemServico.objects.all()
        else:
            qs = OrdemServico.objects.filter(tecnico_responsavel=user)

        kpi_abertas = qs.filter(status="ABERTA").count()
        kpi_execucao = qs.filter(status="EM_EXECUCAO").count()
        kpi_finalizadas_mes = qs.filter(
            status="FINALIZADA",
            data_fechamento__gte=inicio_mes
        ).count()
        kpi_atrasadas = qs.filter(
            status__in=["ABERTA", "EM_ANALISE", "EM_EXECUCAO"],
            data_abertura__lt=agora - timedelta(days=3)
        ).count()

        dist_status = list(
            qs.values("status").annotate(total=Count("id")).order_by()
        )

        dur_expr = ExpressionWrapper(
            F("data_fechamento") - F("data_abertura"),
            output_field=DurationField()
        )
        mttr_qs = qs.filter(
            status="FINALIZADA",
            data_fechamento__gte=inicio_mes
        ).annotate(dur=dur_expr).aggregate(media=Avg("dur"))

        mttr_horas = None
        if mttr_qs["media"]:
            total_sec = mttr_qs["media"].total_seconds()
            mttr_horas = round(total_sec / 3600.0, 1)

        return Response({
            "kpi_abertas": kpi_abertas,
            "kpi_execucao": kpi_execucao,
            "kpi_finalizadas_mes": kpi_finalizadas_mes,
            "kpi_atrasadas": kpi_atrasadas,
            "mttr_horas": mttr_horas,
            "dist_status": dist_status,
        })