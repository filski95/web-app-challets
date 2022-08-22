from core_project import main_api_view
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import SignUpView
from .views_api import AdminUsersList, CustomAuthToken, UserDetail, UsersListCreate

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    # api
    path("", main_api_view.api_root),
    path("users/", UsersListCreate.as_view(), name="users_list"),
    path("admin_users/", AdminUsersList.as_view(), name="admin_list"),
    path("users/<slug:slug>", UserDetail.as_view(), name="user_detail"),
    path("api-token-auth/", CustomAuthToken.as_view()),
]


# formats available in urls .. .api / .json will yield different layout
urlpatterns = format_suffix_patterns(urlpatterns)
