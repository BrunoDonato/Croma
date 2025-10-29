from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib.auth import views as auth_views
from django.urls import reverse

from .forms import RegistroForm, LoginForm
from .decorators import admin_required

from datetime import timedelta
from django.db.models import Count
from ordens.models import OrdemServico, AndamentoOS
from viagens.models import Viagem


# Checa se é admin
def is_admin(user):
    return user.is_superuser or user.groups.filter(name="admin").exists()

# Tela de Login personalizada
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
