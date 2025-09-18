from django.contrib import admin
from .models import Categoria, Produto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "unidade", "fabricante", "modelo", "estoque_minimo", "ativo")
    list_filter = ("categoria", "ativo")
    search_fields = ("nome", "modelo", "fabricante")
