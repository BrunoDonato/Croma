from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.urls import reverse

from .forms import RegistroForm
from .decorators import admin_required

from datetime import timedelta
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Sum, Q
from django.db.models.functions import TruncDate, Coalesce
from ordens.models import OrdemServico, AndamentoOS
from viagens.models import Viagem
from estoque.models import Produto


# Checa se é admin
def is_admin(user):
    return user.is_superuser or user.groups.filter(name="admin").exists()


# Tela de Login
class CustomLoginView(auth_views.LoginView):
    MAX_ATTEMPTS = 5
    LOCK_SECONDS = 300

    def dispatch(self, request, *args, **kwargs):
        lock_until = request.session.get("login_lock_until")
        if lock_until:
            now_ts = timezone.now().timestamp()
            if now_ts < lock_until:
                remaining = int(lock_until - now_ts)
                messages.error(request, f"Tentativas bloqueadas. Tente novamente em {remaining} segundos.")
                return self.render_to_response(self.get_context_data())
            else:
                request.session.pop("login_lock_until", None)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        attempts = self.request.session.get("login_attempts", 0) + 1
        if attempts >= self.MAX_ATTEMPTS:
            lock_until = timezone.now().timestamp() + self.LOCK_SECONDS
            self.request.session["login_lock_until"] = lock_until
            self.request.session["login_attempts"] = 0
            messages.error(self.request, f"Muitas tentativas inválidas. Tente novamente em {self.LOCK_SECONDS} segundos.")
        else:
            self.request.session["login_attempts"] = attempts
            remaining = self.MAX_ATTEMPTS - attempts
            messages.error(self.request, f"Login inválido. Você ainda tem {remaining} tentativa(s).")
        self.request.session.modified = True
        return super().form_invalid(form)

    def form_valid(self, form):
        self.request.session.pop("login_attempts", None)
        self.request.session.pop("login_lock_until", None)
        self.request.session.modified = True
        return super().form_valid(form)

    # Redireciona conforme o tipo de usuário
    def get_success_url(self):
        if is_admin(self.request.user):
            return reverse("contas:dashboard")
        return reverse("ordens:os_nova")


# Dashboard (apenas admin)
@login_required(login_url="contas:login")
def dashboard(request):
    if not is_admin(request.user):
        return redirect("ordens:os_nova")

    # KPIs e listas do dashboard
    agora = timezone.now()
    inicio_mes = agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    kpi_abertas = OrdemServico.objects.filter(status="ABERTA").count()
    kpi_execucao = OrdemServico.objects.filter(status="EM_EXECUCAO").count()
    kpi_finalizadas_mes = OrdemServico.objects.filter(
        status="FINALIZADA",
        data_fechamento__gte=inicio_mes
    ).count()
    kpi_atrasadas = OrdemServico.objects.filter(
        status__in=["ABERTA", "EM_ANALISE", "EM_EXECUCAO"],
        data_abertura__lt=agora - timedelta(days=3)
    ).count()

    sem_tecnico = (
        OrdemServico.objects
        .filter(tecnico_responsavel__isnull=True)
        .select_related("loja", "solicitante")
        .order_by("-data_abertura")[:10]
    )
    analise_atraso = (
        OrdemServico.objects
        .filter(status="EM_ANALISE", data_abertura__lt=agora - timedelta(days=3))
        .select_related("loja", "solicitante", "tecnico_responsavel")
        .order_by("data_abertura")[:10]
    )
    viagens_proximas = (
        Viagem.objects
        .filter(
            data_partida__date__gte=agora.date(),
            data_partida__date__lte=(agora + timedelta(days=1)).date()
        )
        .select_related("origem", "destino", "responsavel")
        .order_by("data_partida")[:10]
    )

    dist_status_qs = (
        OrdemServico.objects
        .values("status")
        .annotate(total=Count("id"))
        .order_by()
    )
    STATUS_LABELS = {
        "ABERTA": "Aberta",
        "EM_ANALISE": "Em análise",
        "EM_EXECUCAO": "Em execução",
        "FINALIZADA": "Finalizada",
        "CANCELADA": "Cancelada",
    }
    chart_labels = [STATUS_LABELS.get(item["status"], item["status"]) for item in dist_status_qs]
    chart_values = [item["total"] for item in dist_status_qs]

    atividade = (
        AndamentoOS.objects
        .select_related("os", "autor")
        .order_by("-criado_em")[:10]
    )

    context = {
        "kpi_abertas": kpi_abertas,
        "kpi_execucao": kpi_execucao,
        "kpi_finalizadas_mes": kpi_finalizadas_mes,
        "kpi_atrasadas": kpi_atrasadas,
        "sem_tecnico": sem_tecnico,
        "analise_atraso": analise_atraso,
        "viagens_proximas": viagens_proximas,
        "chart_labels": chart_labels,
        "chart_values": chart_values,
        "atividade": atividade,
    }

    # Análises do Dashboard
    inicio_janela = agora - timedelta(days=29)

    # Série temporal
    abertas_por_dia = (
        OrdemServico.objects.filter(data_abertura__date__gte=inicio_janela.date())
        .annotate(dia=TruncDate("data_abertura"))
        .values("dia").annotate(total=Count("id")).order_by("dia")
    )
    finalizadas_por_dia = (
        OrdemServico.objects.filter(status="FINALIZADA", data_fechamento__date__gte=inicio_janela.date())
        .annotate(dia=TruncDate("data_fechamento"))
        .values("dia").annotate(total=Count("id")).order_by("dia")
    )

    dias = []
    cur = inicio_janela.date()
    while cur <= agora.date():
        dias.append(cur.isoformat())
        cur += timedelta(days=1)

    map_abertas = {r["dia"].isoformat(): r["total"] for r in abertas_por_dia}
    map_final = {r["dia"].isoformat(): r["total"] for r in finalizadas_por_dia}
    serie_abertas = [map_abertas.get(d, 0) for d in dias]
    serie_final = [map_final.get(d, 0) for d in dias]

    # Ranking por loja
    ranking_lojas = (
        OrdemServico.objects.filter(status__in=["ABERTA", "EM_ANALISE", "EM_EXECUCAO"])
        .values("loja__nome").annotate(total=Count("id")).order_by("-total")[:5]
    )
    ranking_labels = [r["loja__nome"] for r in ranking_lojas]
    ranking_values = [r["total"] for r in ranking_lojas]

    # Distribuição por prioridade
    prio = (
        OrdemServico.objects.values("prioridade").annotate(total=Count("id")).order_by()
    )
    PRIO_LABELS = {"BAIXA": "Baixa", "MEDIA": "Média", "ALTA": "Alta", "CRITICA": "Crítica"}
    prio_labels = [PRIO_LABELS.get(x["prioridade"], x["prioridade"]) for x in prio]
    prio_values = [x["total"] for x in prio]

    # MTTR médio do mês (em horas)
    dur_expr = ExpressionWrapper(F("data_fechamento") - F("data_abertura"), output_field=DurationField())
    mttr_qs = (
        OrdemServico.objects.filter(status="FINALIZADA", data_fechamento__gte=inicio_mes)
        .annotate(dur=dur_expr).aggregate(media=Avg("dur"))
    )
    mttr_horas = None
    if mttr_qs["media"]:
        total_sec = mttr_qs["media"].total_seconds()
        mttr_horas = round(total_sec / 3600.0, 1)

    # Situação geral do Estoque Central
    produtos_central = (
        Produto.objects.filter(ativo=True)
        .annotate(
            central_qtd=Coalesce(
                Sum(
                    "saldos__quantidade",
                    filter=Q(saldos__loja__is_central=True)
                ),
                0
            )
        )
    )

    estoque_abaixo = produtos_central.filter(
        central_qtd__lt=F("estoque_minimo"),
        central_qtd__gt=0
    ).count()

    estoque_ok = produtos_central.filter(
        central_qtd__gte=F("estoque_minimo"),
        central_qtd__gt=0
    ).count()

    estoque_zerado = produtos_central.filter(
        central_qtd=0
    ).count()

    estoque_labels = ["Dentro do mínimo", "Abaixo do mínimo", "Zerado no Central"]
    estoque_values = [estoque_ok, estoque_abaixo, estoque_zerado]

    context.update({
        "serie_dias": dias,
        "serie_abertas": serie_abertas,
        "serie_final": serie_final,
        "ranking_labels": ranking_labels,
        "ranking_values": ranking_values,
        "prio_labels": prio_labels,
        "prio_values": prio_values,
        "mttr_horas": mttr_horas,
        "estoque_labels": estoque_labels,
        "estoque_values": estoque_values,
    })

    return render(request, "contas/dashboard.html", context)


# Cadastro de usuário (apenas admin)
@user_passes_test(is_admin)
def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuário cadastrado com sucesso.")
            return redirect("contas:registrar")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = RegistroForm()
    return render(request, "contas/registrar.html", {"form": form})


# Área admin
@admin_required
def admin_area(request):
    return render(request, "contas/admin_area.html")


# 403 (acesso negado)
def error_403(request, exception=None):
    return render(request, "403.html", status=403)
