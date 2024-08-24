from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS, AllowAny


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Allow all read-only actions for any user
        if request.method in SAFE_METHODS:
            return True

        # Only allow authenticated users for non-safe methods (e.g., POST, PUT, DELETE)
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Allow all read-only actions for any user
        if request.method in SAFE_METHODS:
            return True

        # Only the author of the object can modify it
        return obj.author == request.user