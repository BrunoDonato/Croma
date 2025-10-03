from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import views as auth_views

from .forms import RegistroForm, LoginForm
from .decorators import admin_required

class CustomLoginView(auth_views.LoginView):
    MAX_ATTEMPTS = 5
    LOCK_SECONDS = 300

    def dispatch(self, request, *args, **kwargs):
        lock_until = request.session.get('login_lock_until')
        if lock_until:
            now_ts = timezone.now().timestamp()
            if now_ts < lock_until:
                remaining = int(lock_until - now_ts)
                messages.error(request, f"Tentativas bloqueadas. Tente novamente em {remaining} segundos.")
                return self.render_to_response(self.get_context_data())
            else:
                request.session.pop('login_lock_until', None)
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        attempts = self.request.session.get('login_attempts', 0) + 1
        if attempts >= self.MAX_ATTEMPTS:
            lock_until = timezone.now().timestamp() + self.LOCK_SECONDS
            self.request.session['login_lock_until'] = lock_until
            self.request.session['login_attempts'] = 0
            messages.error(self.request, f"Muitas tentativas inválidas. Tente novamente em {self.LOCK_SECONDS} segundos.")
        else:
            self.request.session['login_attempts'] = attempts
            remaining = self.MAX_ATTEMPTS - attempts
            messages.error(self.request, f"Login inválido. Você ainda tem {remaining} tentativa(s).")
        self.request.session.modified = True
        return super().form_invalid(form)

    def form_valid(self, form):
        self.request.session.pop('login_attempts', None)
        self.request.session.pop('login_lock_until', None)
        self.request.session.modified = True
        return super().form_valid(form)

def registrar(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Conta criada com sucesso! Faça login.")
            return redirect("contas:login")
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = RegistroForm()
    return render(request, "contas/registrar.html", {"form": form})

@login_required(login_url="contas:login")
def dashboard(request):
    return render(request, "contas/dashboard.html")

@admin_required
def admin_area(request):
    return render(request, "contas/admin_area.html")

def error_403(request, exception=None):
    return render(request, "403.html", status=403)
