from rest_framework.permissions import BasePermission


class IsSeller(BasePermission):
    """Sellers and admins only. Anonymous users get 401, buyers get 403."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_seller)


class IsBuyer(BasePermission):
    """Only buyers can use the cart and checkout."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "buyer")


class IsAdminRole(BasePermission):
    """Admin portal only. Anonymous gets 401, everyone else who is not an admin gets 403."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "admin")
