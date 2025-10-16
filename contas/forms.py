from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Group
from contas.models import Perfil
from estoque.models import Loja

User = get_user_model()

class RegistroForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", required=False, max_length=150)
    last_name = forms.CharField(label="Sobrenome", required=False, max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    loja = forms.ModelChoiceField(label="Loja do Usuário", queryset=Loja.objects.order_by("nome"), required=True)
    grupo = forms.ChoiceField(
        label="Grupo de Permissão",
        choices=(("user", "Usuário"), ("admin", "Admin")),
        required=True,
        initial="user",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2", "loja", "grupo"]

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        return u.lower()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")

        grupo_nome = self.cleaned_data["grupo"]
        user.is_staff = (grupo_nome == "admin")
        user.is_active = True

        if commit:
            user.save()
            grupo_obj, _ = Group.objects.get_or_create(name=grupo_nome)
            user.groups.set([grupo_obj])
            loja = self.cleaned_data["loja"]
            Perfil.objects.update_or_create(user=user, defaults={"loja": loja})
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Nome de usuário")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
