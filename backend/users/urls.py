from django.urls import path

from . import api


app_name = "users"

urlpatterns = [
    path("login/", api.login, name="login"),
    path("logout/", api.logout, name="logout"),
    path("me/", api.profile, name="profile"),
    path("change-password/", api.change_password, name="change-password"),
    path(
        "notification-preferences/",
        api.notification_preferences,
        name="notification-preferences",
    ),
    path("password-reset/", api.password_reset, name="password-reset"),
    path(
        "password-reset/confirm/",
        api.password_reset_confirm,
        name="password-reset-confirm",
    ),
    path("centers/", api.centers, name="centers"),
]
