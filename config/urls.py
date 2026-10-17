from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from apps.portal import views as v

urlpatterns = [
    path("", v.landing, name="landing"),
    path("health/", v.health, name="health"),
    path("admin/", admin.site.urls),
    path("signup/", v.signup, name="signup"),
    path("login/", v.signin, name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("verify/<str:token>/", v.verify, name="verify"),
    path(
        "password-reset/",
        v.limited(auth.PasswordResetView.as_view(template_name="registration/password_reset_form.html")),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        auth.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("info/<str:page>/", v.legal, name="legal"),
    path("workspace/", v.workspace, name="workspace"),
    path("business/new/", v.business_new, name="business_new"),
    path("b/<uuid:business_id>/switch/", v.switch, name="switch"),
    path("b/<uuid:business_id>/", v.dashboard, name="dashboard"),
    path("b/<uuid:business_id>/business/", v.my_business, name="my_business"),
    path("b/<uuid:business_id>/recurring/new/", v.recurring_add, name="recurring_add"),
    path("b/<uuid:business_id>/recurring/<int:pk>/disable/", v.recurring_disable, name="recurring_disable"),
    path("b/<uuid:business_id>/transaction/new/", v.transaction_edit, name="transaction_new"),
    path("b/<uuid:business_id>/transaction/<int:pk>/", v.transaction_edit, name="transaction_edit"),
    path("b/<uuid:business_id>/transaction/<int:pk>/archive/", v.transaction_archive, name="transaction_archive"),
    path("b/<uuid:business_id>/upload/", v.upload, name="upload"),
    path("b/<uuid:business_id>/import/<int:pk>/confirm/", v.import_confirm, name="import_confirm"),
    path("b/<uuid:business_id>/planning/", v.planning, name="planning"),
    path("b/<uuid:business_id>/advisor/", v.advisor, name="advisor"),
    path("b/<uuid:business_id>/reports/", v.reports, name="reports"),
    path("api/b/<uuid:business_id>/summary/", v.api_summary, name="api_summary"),
]
