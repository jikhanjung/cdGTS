from django.urls import path

from . import views

urlpatterns = [
    path("auth/whoami/", views.whoami, name="whoami"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
]
