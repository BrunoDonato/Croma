from django import forms
from .models import OrdemServico

class OrdemServicoForm(forms.ModelForm):
    class Meta:
        model = OrdemServico
        fields = ["loja", "descricao_problema", "prioridade", "observacoes"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields["loja"].widget = forms.HiddenInput()
            if hasattr(user, "perfil") and user.perfil and user.perfil.loja_id:
                self.fields["loja"].initial = user.perfil.loja_id
            else:
                self.fields["loja"].queryset = self.fields["loja"].queryset.none()
