from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Obrigatório. Insira um endereço de email válido.")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            group, _ = Group.objects.get_or_create(name="user")
            user.groups.add(group)
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Nome de usuário")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
