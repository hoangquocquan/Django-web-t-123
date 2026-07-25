"""URL của module Accounts/Auth."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.accounts_home, name="home"),
    path("api/login/", views.login_api, name="api-login"),
    path("api/logout/", views.logout_api, name="api-logout"),
    path("api/users/", views.users_api, name="api-users"),
    path("api/sessions/", views.sessions_api, name="api-sessions"),
    path("api/forgot-password/", views.forgot_password_api, name="api-forgot-password"),
    path("api/reset-password/", views.reset_password_api, name="api-reset-password"),
    path("api/change-password/", views.change_password_api, name="api-change-password"),
    path("api/users/<int:admin_id>/status/", views.account_status_api, name="api-user-status"),
]
