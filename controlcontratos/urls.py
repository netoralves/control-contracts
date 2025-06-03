from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from contracts import views as contracts_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Autenticação
    path("login/", contracts_views.login_view, name="login"),
    path("logout/", contracts_views.logout_view, name="logout"),
    # path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    # path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"),
        name="password_reset",
    ),
    path(
        "password_reset_done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="auth/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="auth/password_change.html"
        ),
        name="password_change",
    ),
    path(
        "password_change_done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="auth/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # Apps
    path("", include("contracts.urls")),  # Suas rotas da aplicação
]
