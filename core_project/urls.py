"""core_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from allauth.account.views import confirm_email
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import PasswordResetConfirmView, PasswordResetView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from . import main_api_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth", include("rest_framework.urls")),  # login
    re_path(
        r"^api/registrationaccount-confirm-email/", VerifyEmailView.as_view(), name="account_email_verification_sent"
    ),
    re_path(
        r"^api/registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        VerifyEmailView.as_view(),
        name="account_confirm_email",
    ),
    path("account/api/password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path(
        "account/api/password_reset_confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("api/dj-rest-auth/", include("dj_rest_auth.urls")),
    path("api/registration/", include("dj_rest_auth.registration.urls")),  # registration
    path("api/", main_api_view.api_root),  # main view api / starting point
    path("accounts/", include("accounts.urls")),
    # path("accounts/", include("django.contrib.auth.urls")),
    path("bookings/", include("bookings.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]

# to allow images to be viewable
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
