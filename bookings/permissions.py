from rest_framework import permissions


class IsAuthorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        # allow admin (owner) to view content
        if request.user.is_superuser == True:
            return True

        # otherwise only author for edition purposes
        return request.user == obj.author


class IsAuthorOtherwiseViewOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        # allow admin (owner) and other users to view detail content
        if request.method in permissions.SAFE_METHODS:
            return True

        # otherwise only author for edition purposes
        return request.user == obj.author


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):

        # allow admin (owner) to view content
        if request.user.is_superuser == True:
            return True

        # otherwise only author for edition purposes
        return request.user == obj.reservation_owner
