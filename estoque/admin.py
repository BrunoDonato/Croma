from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F, Sum, Q, Count
from django.db.models.functions import Coalesce

from .models import Categoria, Produto, Loja, SaldoEstoque


class MinimoCentralFilter(admin.SimpleListFilter):
    title = "mínimo (Central)"
    parameter_name = "min_central"

    def lookups(self, request, model_admin):
        return [
            ("baixo", "Abaixo do mínimo (Central)"),
            ("ok", "Dentro do mínimo (Central)"),
            ("zerado_central", "Central zerado"),
        ]

    # Anota o saldo do CENTRAL por produto
    def queryset(self, request, queryset):
        qs = queryset.annotate(
            saldo_central=Coalesce(
                Sum("saldos__quantidade", filter=Q(saldos__loja__is_central=True)),
                0,
            )
        )
        val = self.value()
        if val == "baixo":
            return qs.filter(saldo_central__lt=F("estoque_minimo"))
        if val == "ok":
            return qs.filter(saldo_central__gte=F("estoque_minimo"))
        if val == "zerado_central":
            return qs.filter(saldo_central=0)
        return qs


# Inlines
class SaldoComSaldoInline(admin.TabularInline):
    model = SaldoEstoque
    extra = 0
    fields = ("produto", "quantidade")
    autocomplete_fields = ("produto",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(quantidade__gt=0).select_related("produto")


class SaldoInline(admin.TabularInline):
    model = SaldoEstoque
    extra = 1
    min_num = 0
    autocomplete_fields = ("loja",)


# Admins

@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ("nome", "endereco", "ativa", "is_central", "itens_com_saldo")
    list_filter = ("ativa", "is_central")
    search_fields = ("nome", "endereco")
    inlines = [SaldoComSaldoInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Conta quantos produtos com quantidade > 0 existem por loja (só para a coluna)
        return qs.annotate(
            _itens=Count("saldos", filter=Q(saldos__quantidade__gt=0), distinct=True)
        )

    @admin.display(description="Itens com saldo")
    def itens_com_saldo(self, obj):
        return obj._itens or 0


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome", "categoria", "unidade",
        "saldo_central_colored",  # saldo apenas do Central
        "estoque_minimo",         # mínimo do Central
        "estoque_total",          # soma de todas as lojas
        "fabricante", "modelo", "ativo",
    )
    list_filter = ("categoria", "ativo", MinimoCentralFilter)
    search_fields = ("nome", "modelo", "fabricante")
    inlines = [SaldoInline]

    def saldo_central_val(self, obj):
        return obj.saldos.filter(loja__is_central=True).aggregate(
            t=Coalesce(Sum("quantidade"), 0)
        )["t"]

    def saldo_central_colored(self, obj):
        sc = self.saldo_central_val(obj)
        if sc < obj.estoque_minimo:
            return format_html('<span style="color:red;font-weight:bold;">{}</span>', sc)
        return sc
    saldo_central_colored.short_description = "Saldo no Central"

    def estoque_total(self, obj):
        return obj.saldos.aggregate(t=Coalesce(Sum("quantidade"), 0))["t"]
    estoque_total.short_description = "Total (todas as lojas)"


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(SaldoEstoque)
class SaldoEstoqueAdmin(admin.ModelAdmin):
    list_display = ("produto", "loja", "quantidade")
    list_filter = ("loja", "produto__categoria")
    search_fields = ("produto__nome", "produto__modelo", "produto__fabricante", "loja__nome")
    autocomplete_fields = ("produto", "loja")
