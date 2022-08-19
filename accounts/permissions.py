from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions


class IsUserAccountOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        if type(request.user) == AnonymousUser:
            return False

        if obj.id == request.user.id or request.user.is_admin:
            return True
        return False
