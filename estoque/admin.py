from django.contrib import admin
from django.utils.html import format_html
from django.db.models import F  # << IMPORTANTE
from .models import Categoria, Produto


class NivelEstoqueFilter(admin.SimpleListFilter):
    title = "nível de estoque"
    parameter_name = "nivel_estoque"

    def lookups(self, request, model_admin):
        return [
            ("baixo", "Abaixo do mínimo"),
            ("ok", "Dentro do mínimo"),
            ("zerado", "Zerado"),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val == "baixo":
            return queryset.filter(quantidade__lt=F("estoque_minimo"))
        if val == "ok":
            return queryset.filter(quantidade__gte=F("estoque_minimo"))
        if val == "zerado":
            return queryset.filter(quantidade=0)
        return queryset  # sem filtro


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "nome", "categoria", "unidade",
        "quantidade_colored", "estoque_minimo",
        "fabricante", "modelo", "ativo"
    )
    list_filter = ("categoria", "ativo", NivelEstoqueFilter)  # << usa o filtro acima
    search_fields = ("nome", "modelo", "fabricante")

    def quantidade_colored(self, obj):
        if obj.quantidade < obj.estoque_minimo:
            return format_html('<span style="color:red;font-weight:bold;">{}</span>', obj.quantidade)
        return obj.quantidade

    quantidade_colored.short_description = "Quantidade"
