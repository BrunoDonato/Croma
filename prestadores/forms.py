from django import forms
from .models import PrestadorServico, OrdemExterna


class PrestadorServicoForm(forms.ModelForm):
    class Meta:
        model = PrestadorServico
        fields = [
            "nome",
            "telefone",
            "email",
            "cidade",
            "tipo_servico",
            "ativo",
        ]


class OrdemExternaForm(forms.ModelForm):
    class Meta:
        model = OrdemExterna
        fields = [
            "loja",
            "prestador",
            "os_interna",
            "equipamento",
            "numero_serie",
            "descricao_defeito",
            "status",
            "prioridade",
            "data_envio",
            "data_previsao_retorno",
            "data_retorno",
            "numero_os_prestador",
            "valor_orcado",
            "valor_aprovado",
            "observacoes",
        ]
        widgets = {
            "descricao_defeito": forms.Textarea(attrs={"rows": 3}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
            "data_envio": forms.DateInput(attrs={"type": "date"}),
            "data_previsao_retorno": forms.DateInput(attrs={"type": "date"}),
            "data_retorno": forms.DateInput(attrs={"type": "date"}),
        }
