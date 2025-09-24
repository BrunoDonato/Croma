from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Obrigatório. Insira um endereço de email válido.")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Nome de usuário")
    password = forms.CharField(label="Senha", widget=forms.PasswordInput)
        