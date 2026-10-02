from rest_framework import permissions


class IsGovernmentOfficer(permissions.BasePermission):
    """Only allows Government role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'GOVERNMENT')


class IsStartup(permissions.BasePermission):
    """Only allows Startup role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'STARTUP')


class IsExpert(permissions.BasePermission):
    """Only allows Expert role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'EXPERT')


class IsAdmin(permissions.BasePermission):
    """Only allows Admin role."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')


class IsGovernmentOrReadOnly(permissions.BasePermission):
    """Read-only for anyone; write only for Government."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == 'GOVERNMENT')
