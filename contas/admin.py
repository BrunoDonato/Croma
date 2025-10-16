from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("user", "loja")
    list_filter = ("loja",)
    search_fields = ("user__username", "user__email")

class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = "Perfil"

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
