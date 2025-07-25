from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied


def sales_access_required(function):
    """this function is a decorator used to authorize if a user has sales access"""

    def wrap(request, *args, **kwargs):
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user.has_sales_access
        ):
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap


def marketing_access_required(function):
    """this function is a decorator used to authorize if a user has marketing access"""

    def wrap(request, *args, **kwargs):
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user.has_marketing_access
        ):
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap


class SalesAccessRequiredMixin(AccessMixin):
    """Mixin used to authorize if a user has sales access"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user.has_sales_access
        ):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class MarketingAccessRequiredMixin(AccessMixin):
    """Mixin used to authorize if a user has marketing access"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        if (
            request.user.role == "ADMIN"
            or request.user.is_superuser
            or request.user.has_marketing_access
        ):
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


def admin_login_required(function):
    """this function is a decorator used to authorize if a user is admin"""

    def wrap(request, *args, **kwargs):
        if request.user.role == "ADMIN" or request.user.is_superuser:
            return function(request, *args, **kwargs)
        raise PermissionDenied

    return wrap


# New Role-Based Access Control


def role_required(*roles):
    """Decorator to check if user has one of the required roles"""

    def decorator(function):
        def wrap(request, *args, **kwargs):
            # Get user's profile to check role
            if hasattr(request, "profile") and request.profile:
                user_role = request.profile.role
            else:
                # Fallback - get the first active profile for the user
                from common.models import Profile

                profile = Profile.objects.filter(
                    user=request.user, is_active=True
                ).first()
                if not profile:
                    raise PermissionDenied("No active profile found for user.")
                user_role = profile.role

            if user_role in roles or request.user.is_superuser:
                return function(request, *args, **kwargs)
            raise PermissionDenied("You don't have permission to access this resource.")

        return wrap

    return decorator


def admin_required(function):
    """Decorator for Admin-only access"""
    return role_required("ADMIN")(function)


def admin_manager_required(function):
    """Decorator for Admin or Manager access"""
    return role_required("ADMIN", "MANAGER")(function)


class RoleRequiredMixin(LoginRequiredMixin):
    """Base mixin for role-based access control"""

    required_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Get user's profile to check role
        if hasattr(request, "profile") and request.profile:
            user_role = request.profile.role
        else:
            # Fallback - get the first active profile for the user
            from common.models import Profile

            profile = Profile.objects.filter(user=request.user, is_active=True).first()
            if not profile:
                raise PermissionDenied("No active profile found for user.")
            user_role = profile.role

        if user_role not in self.required_roles and not request.user.is_superuser:
            raise PermissionDenied("You don't have permission to access this resource.")

        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(RoleRequiredMixin):
    required_roles = ["ADMIN"]


class AdminManagerRequiredMixin(RoleRequiredMixin):
    required_roles = ["ADMIN", "MANAGER"]


class AllRolesRequiredMixin(RoleRequiredMixin):
    required_roles = ["ADMIN", "MANAGER", "USER"]


class OwnershipMixin:
    """Mixin to filter objects based on ownership for users"""

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get user's profile to check role
        if hasattr(self.request, "profile") and self.request.profile:
            profile = self.request.profile
        else:
            # Fallback - get the first active profile for the user
            from common.models import Profile

            profile = Profile.objects.filter(
                user=self.request.user, is_active=True
            ).first()
            if not profile:
                return queryset.none()

        # Admin and Manager can see all records
        if profile.is_admin_role() or profile.is_manager_role():
            return queryset
        elif profile.is_user_role():
            # Users can only see their own records for certain models
            model_name = queryset.model.__name__.lower()

            # For Company and Contact models, all users can see all records
            if model_name in ["companyprofile", "contact"]:
                return queryset

            # For other models, users can only see their assigned records
            if hasattr(queryset.model, "assigned_to"):
                return queryset.filter(assigned_to=profile)
            elif hasattr(queryset.model, "created_by"):
                return queryset.filter(created_by=profile)

        return queryset


# DRF Permission Classes
class IsAdminRole(BasePermission):
    """Permission class for Admin role only"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if hasattr(request, "profile") and request.profile:
            return request.profile.is_admin_role()

        # Fallback
        from common.models import Profile

        profile = Profile.objects.filter(user=request.user, is_active=True).first()
        return profile and profile.is_admin_role()


class IsAdminOrManagerRole(BasePermission):
    """Permission class for Admin or Manager roles"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if hasattr(request, "profile") and request.profile:
            return request.profile.is_admin_role() or request.profile.is_manager_role()

        # Fallback
        from common.models import Profile

        profile = Profile.objects.filter(user=request.user, is_active=True).first()
        return profile and (profile.is_admin_role() or profile.is_manager_role())


class IsOwnerOrAdminOrManager(BasePermission):
    """Permission class for ownership-based access with admin/manager override"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if hasattr(request, "profile") and request.profile:
            profile = request.profile
        else:
            from common.models import Profile

            profile = Profile.objects.filter(user=request.user, is_active=True).first()
            if not profile:
                return False

        # Admin and Manager have full access
        if profile.is_admin_role() or profile.is_manager_role():
            return True

        # Users can only access their own objects
        if hasattr(obj, "assigned_to"):
            return profile in obj.assigned_to.all()
        elif hasattr(obj, "created_by"):
            return obj.created_by == profile

        return False


class CanViewAllCompaniesContacts(BasePermission):
    """All authenticated users can view companies and contacts"""

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated
