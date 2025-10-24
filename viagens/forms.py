from typing import Optional, Union
from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware, is_naive

from estoque.models import Loja
from ordens.models import OrdemServico
from .models import Viagem

User = get_user_model()


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        super().__init__(**kwargs)


class ViagemForm(forms.ModelForm):
    class Meta:
        model = Viagem
        fields = [
            "referencia_os",
            "origem",
            "destino",
            "responsavel",
            "veiculo",
            "data_partida",
            "data_retorno",
            "status",
            "motivo",
            "observacoes",
        ]
        widgets = {
            "data_partida": DateTimeLocalInput(attrs={"class": "input"}),
            "data_retorno": DateTimeLocalInput(attrs={"class": "input"}),
            "motivo": forms.TextInput(attrs={"placeholder": ""}),
            "observacoes": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "referencia_os": "Referência OS",
            "origem": "Origem",
            "destino": "Destino",
            "responsavel": "Responsável",
            "veiculo": "Veículo",
            "data_partida": "Data partida",
            "data_retorno": "Data retorno",
            "status": "Status",
            "motivo": "Motivo",
            "observacoes": "Observações",
        }

    def __init__(self, *args, **kwargs):
        user: Optional[User] = kwargs.pop("user", None)
        os_id: Optional[Union[int, str]] = kwargs.pop("os_id", None)
        super().__init__(*args, **kwargs)

        self.fields["origem"].queryset = Loja.objects.all().order_by("nome")
        self.fields["destino"].queryset = Loja.objects.all().order_by("nome")
        self.fields["responsavel"].queryset = User.objects.filter(is_active=True).order_by("username")

        # Sugerir origem = central
        try:
            central = Loja.objects.filter(is_central=True).first()
            if central and not self.instance.pk and not self.initial.get("origem"):
                self.fields["origem"].initial = central.pk
        except Exception:
            pass

        # Descobrir a OS (por instancia, por os_id ou por initial)
        os_obj: Optional[OrdemServico] = None
        if getattr(self.instance, "referencia_os_id", None):
            os_obj = self.instance.referencia_os
        elif os_id:
            try:
                os_obj = OrdemServico.objects.select_related("loja").get(pk=int(os_id))
            except (ValueError, OrdemServico.DoesNotExist):
                os_obj = None
        elif isinstance(self.initial.get("referencia_os"), OrdemServico):
            os_obj = self.initial["referencia_os"]

        # Preencher destino = loja da OS e selecionar a OS por padrão
        if os_obj:
            if not self.initial.get("referencia_os"):
                self.fields["referencia_os"].initial = os_obj.pk
            if not self.initial.get("destino"):
                self.fields["destino"].initial = getattr(os_obj, "loja_id", None)

        # Responsável padrão = usuário atual
        if user and not self.instance.pk and not self.initial.get("responsavel"):
            self.fields["responsavel"].initial = getattr(user, "id", None)

    # Validações coerentes com o admin do django
    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("data_partida")
        end = cleaned.get("data_retorno")

        # Caso o navegador envie string, converte corretamente
        if isinstance(start, str):
            try:
                start = datetime.fromisoformat(start)
                if is_naive(start):
                    start = make_aware(start)
                cleaned["data_partida"] = start
            except Exception:
                pass

        if isinstance(end, str):
            try:
                end = datetime.fromisoformat(end)
                if is_naive(end):
                    end = make_aware(end)
                cleaned["data_retorno"] = end
            except Exception:
                pass

        # Regra: retorno não pode ser antes da partida
        if start and end and end < start:
            self.add_error("data_retorno", "Data de retorno não pode ser anterior à data de partida.")

        # Regra: origem e destino diferentes
        origem = cleaned.get("origem")
        destino = cleaned.get("destino")
        if origem and destino and origem == destino:
            self.add_error("destino", "Origem e destino devem ser diferentes.")

        return cleaned
