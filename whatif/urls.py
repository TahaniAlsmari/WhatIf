from django.contrib import admin
from django.urls import path, include

from accounts.views import login_view
from ml_app import views as ml_views


urlpatterns = [
    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "home/",
        ml_views.landing_view,
        name="landing"
    ),

    path(
        "dashboard/",
        ml_views.home_view,
        name="dashboard"
    ),

    path(
        "ml/",
        include("ml_app.urls")
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "",
        login_view,
        name="login"
    ),
]
