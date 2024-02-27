from rest_framework import permissions


class IsOwnerOnly(permissions.BasePermission):
    """
    Кастомный класс разрешения, который разрешает доступ только владельцу объекта.
    """
    def has_object_permission(self, request, view, obj):
        try:
            return obj.email == request.user.email
        except AttributeError:
            return False


class OwnerOrReadOnly(permissions.BasePermission):
    message = ('Разрешено изменение/удаление только своего контента! '
               'Доступные методы: PATCH, DELETE.')

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.user == obj.author and request.method != "PUT"
                or request.method in permissions.SAFE_METHODS)


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS


class AllowAllPermission(permissions.BasePermission):
    """
    Разрешение, которое разрешает доступ для всех пользователей.
    """

    def has_permission(self, request, view):
        return True


class IsAuthorAdminOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        return (
            obj.author == request.user
            or request.user.is_superuser
        )