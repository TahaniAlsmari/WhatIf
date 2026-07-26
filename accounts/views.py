from django.shortcuts import render, redirect
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
)
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


def register_view(request):
    if request.user.is_authenticated:
        return redirect("landing")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        username = request.POST.get("username", "").strip()

        if username and User.objects.filter(
            username__iexact=username
        ).exists():
            form.add_error(
                "username",
                "اسم المستخدم مستخدم بالفعل، اختاري اسمًا آخر.",
            )

        elif form.is_valid():
            user = form.save()

            login(request, user)

            return redirect("landing")

    else:
        form = UserCreationForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("landing")

    if request.method == "POST":
        form = AuthenticationForm(
            request=request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()

            login(request, user)

            return redirect("landing")

    else:
        form = AuthenticationForm(
            request=request
        )

    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
        },
    )


@login_required
def logout_view(request):
    logout(request)

    return redirect("login")
