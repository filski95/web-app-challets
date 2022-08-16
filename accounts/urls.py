from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from .views import SignUpView
from .views_api import AdminUsersList, UserDetail, UsersList

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("users/", UsersList.as_view(), name="users_list"),
    path("admin_users/", AdminUsersList.as_view(), name="users_list"),
    path("users/<slug:slug>", UserDetail.as_view(), name="user_detail"),
]

# formats available in urls .. .api / .json will yield different layout
urlpatterns = format_suffix_patterns(urlpatterns)
