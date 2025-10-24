from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import OrdemServico, AndamentoOS, AnexoOS

User = get_user_model()


class AndamentoOSInline(admin.TabularInline):
    model = AndamentoOS
    extra = 0
    readonly_fields = ("autor", "criado_em", "status_de", "status_para")
    can_delete = False


class AnexoOSInline(admin.TabularInline):
    model = AnexoOS
    extra = 0
    readonly_fields = ("enviado_por", "enviado_em")
    can_delete = False


class TecnicoAdminsFilter(admin.SimpleListFilter):
    title = "Técnico responsável"
    parameter_name = "tecnico_responsavel"

    def lookups(self, request, model_admin):
        admins_qs = User.objects.filter(
            Q(is_superuser=True) | Q(groups__name="admin")
        ).distinct().order_by("username")
        return [(u.pk, u.get_username()) for u in admins_qs]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tecnico_responsavel_id=self.value())
        return queryset


@admin.register(OrdemServico)
class OrdemServicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "loja",
        "solicitante",
        "tecnico_responsavel",
        "prioridade",
        "status",
        "data_abertura",
        "data_fechamento",
    )
    list_display_links = ("id", "loja")
    list_filter = ("status", "loja", "prioridade", TecnicoAdminsFilter, "data_abertura", "data_fechamento")
    search_fields = ("solicitante__username", "loja__nome", "descricao_problema")
    date_hierarchy = "data_abertura"
    ordering = ("-data_abertura",)
    inlines = [AndamentoOSInline, AnexoOSInline]

    actions = ["marcar_em_analise", "marcar_em_execucao", "finalizar_os", "cancelar_os"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.groups.filter(name="admin").exists():
            return qs
        return qs.filter(solicitante=request.user)

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name="admin").exists():
            return True
        return request.user.is_authenticated

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.groups.filter(name="admin").exists():
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.groups.filter(name="admin").exists()

    def _alterar_status_em_massa(self, request, queryset, novo_status, texto):
        sucesso, falha = 0, 0
        for os in queryset:
            try:
                os.mudar_status(novo_status, autor=request.user, texto_andamento=texto, visibilidade="INTERNO")
                sucesso += 1
            except Exception as e:
                falha += 1
        if sucesso:
            messages.success(request, _(f"{sucesso} OS(s) marcadas como {novo_status}."))
        if falha:
            messages.warning(request, _(f"{falha} OS(s) não puderam ser atualizadas."))

    @admin.action(description="Marcar como Em análise")
    def marcar_em_analise(self, request, queryset):
        self._alterar_status_em_massa(request, queryset, "EM_ANALISE", "Ação em massa: Em análise")

    @admin.action(description="Marcar como Em execução")
    def marcar_em_execucao(self, request, queryset):
        self._alterar_status_em_massa(request, queryset, "EM_EXECUCAO", "Ação em massa: Em execução")

    @admin.action(description="Finalizar OS")
    def finalizar_os(self, request, queryset):
        self._alterar_status_em_massa(request, queryset, "FINALIZADA", "Ação em massa: Finalizada")

    @admin.action(description="Cancelar OS")
    def cancelar_os(self, request, queryset):
        self._alterar_status_em_massa(request, queryset, "CANCELADA", "Ação em massa: Cancelada")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tecnico_responsavel":
            kwargs["queryset"] = User.objects.filter(
                Q(is_superuser=True) | Q(groups__name="admin")
            ).distinct().order_by("username")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
