from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Only owner can edit
    Others can only read
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for all requests (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions for only owner
        return obj == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission: Only owner can access
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission: Admin or owner can access
    """

    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user and request.user.is_staff:
            return True

        # Owners have full access only with their object
        return obj == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission: Staff can edit, others can only read
    """

    def has_permission(self, request, view):
        # Read permissions for all requests
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions for only staff
        return request.user and request.user.is_staff


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission: Only user who was verified email has permission
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user had profile and verified?
        if hasattr(request.user, 'profile'):
            return request.user.profile.email_verified

        return False

    message = "You must verify your email before performing this action."


class IsPublicProfile(permissions.BasePermission):
    """
    Custom permission: Chỉ cho phép xem public profiles
    """

    def has_object_permission(self, request, view, obj):
        # Owner luôn có quyền xem profile của mình
        if obj == request.user:
            return True

        # Staff có thể xem tất cả profiles
        if request.user and request.user.is_staff:
            return True

        # Check nếu profile là public
        if hasattr(obj, 'profile'):
            return obj.profile.is_public

        return False


class CanDeleteAccount(permissions.BasePermission):
    """
    Custom permission: Chỉ owner hoặc superuser mới có thể xóa account
    """

    def has_object_permission(self, request, view, obj):
        # Superuser có thể xóa bất kỳ account nào
        if request.user and request.user.is_superuser:
            return True

        # User chỉ có thể xóa account của mình
        return obj == request.user


class IsActiveUser(permissions.BasePermission):
    """
    Custom permission: Chỉ active users mới có quyền
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active

    message = "Your account is inactive. Please contact support."
