from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        login_url = reverse("contas:login")
        if not request.user.is_authenticated:
            return redirect(f"{login_url}?expired=1&next={request.get_full_path()}")
        if not (request.user.is_superuser or request.user.groups.filter(name="admin").exists()):
            return redirect(f"{login_url}?denied=1")
        return view_func(request, *args, **kwargs)
    return _wrapped
