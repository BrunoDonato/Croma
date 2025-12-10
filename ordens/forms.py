from typing import Optional

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.forms import ModelChoiceField

from .models import OrdemServico, AndamentoOS, AnexoOS, CategoriaProblema

User = get_user_model()


# Abrir OS
class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ["loja", "descricao_problema", "prioridade", "observacoes"]
        labels = {
            "loja": "Loja",
            "descricao_problema": "Descrição do problema",
            "prioridade": "Prioridade",
            "observacoes": "Observações (opcional)",
        }
        widgets = {
            "descricao_problema": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Detalhe o problema, sintomas, quando ocorre, etc."
            }),
            "observacoes": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Informações adicionais (opcional)"
            }),
        }

    def __init__(self, *args, **kwargs):
        user: Optional[User] = kwargs.pop("user", None)  # <-- tipado e opcional
        super().__init__(*args, **kwargs)

        # Campo obrigatório
        self.fields["descricao_problema"].required = True

        # Checa admin com segurança mesmo se user=None
        is_admin = bool(
            user and (
                getattr(user, "is_superuser", False) or
                (hasattr(user, "groups") and user.groups.filter(name="admin").exists())
            )
        )

        # Usuário comum não escolhe a loja manualmente
        if user and not is_admin:
            self.fields["loja"].widget = forms.HiddenInput()

            # Se houver perfil com loja vinculada, usa como initial
            loja_id = getattr(getattr(user, "perfil", None), "loja_id", None)
            if loja_id:
                self.fields["loja"].initial = loja_id
            else:
                # Evita alert: só acessa .queryset se for ModelChoiceField
                field = self.fields.get("loja")
                if isinstance(field, ModelChoiceField):
                    field.queryset = field.queryset.none()
                else:
                    # fallback: recria como ModelChoiceField vazio
                    from estoque.models import Loja
                    self.fields["loja"] = ModelChoiceField(queryset=Loja.objects.none(), widget=forms.HiddenInput())


# Comentários / Andamentos
class AndamentoForm(forms.ModelForm):
    class Meta:
        model = AndamentoOS
        fields = ("texto", "visibilidade")
        labels = {
            "texto": "Comentário",
            "visibilidade": "Visibilidade",
        }
        widgets = {
            "texto": forms.Textarea(attrs={"rows": 3, "placeholder": "Descreva o andamento..."}),
        }


# Anexos
class AnexoForm(forms.ModelForm):
    class Meta:
        model = AnexoOS
        fields = ("arquivo",)
        labels = {
            "arquivo": "Arquivo",
        }


# Finalizar OS
class FinalizarForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ("solucao", "custo_total")
        labels = {
            "solucao": "Solução aplicada",
            "custo_total": "Custo total (opcional)",
        }
        widgets = {
            "solucao": forms.Textarea(attrs={"rows": 4, "placeholder": "Descreva a solução aplicada..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solução é obrigatória para finalizar
        self.fields["solucao"].required = True


# Cancelar OS
class CancelarForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ("motivo_cancelamento",)
        labels = {
            "motivo_cancelamento": "Motivo do cancelamento",
        }
        widgets = {
            "motivo_cancelamento": forms.Textarea(attrs={"rows": 3, "placeholder": "Explique por que a OS será cancelada..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # É obrigatório ter um motivo para cancelar a minha OS
        self.fields["motivo_cancelamento"].required = True


# Atribuir Técnico / Prioridade / Categoria
class AtribuirTecnicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ("tecnico_responsavel", "prioridade", "categoria")
        labels = {
            "tecnico_responsavel": "Técnico responsável",
            "prioridade": "Prioridade",
            "categoria": "Categoria do problema",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        admins_qs = User.objects.filter(Q(is_superuser=True) | Q(groups__name="admin")).distinct().order_by("username")
        self.fields["tecnico_responsavel"].queryset = admins_qs
        self.fields["tecnico_responsavel"].required = False

        # adiciona as categorias ativas
        self.fields["categoria"].queryset = CategoriaProblema.objects.filter(ativo=True).order_by("nome")
        self.fields["categoria"].required = False

    def clean_tecnico_responsavel(self):
        u = self.cleaned_data.get("tecnico_responsavel")
        if u is None:
            return None  # permitir sem responsável
        if not (u.is_superuser or u.groups.filter(name="admin").exists()):
            raise forms.ValidationError("Apenas administradores podem ser técnicos responsáveis.")
        return u
