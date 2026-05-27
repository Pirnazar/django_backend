from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'superadmin')

class IsAdminOrManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['superadmin', 'admin', 'manager']
        )

class IsOperatorOrHigher(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['superadmin', 'admin', 'manager', 'operator']
        )

class IsClientOrStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
            
        if request.user.role == 'client':
            # Клиентам разрешены только безопасные методы (чтение)
            return request.method in permissions.SAFE_METHODS
            
        return request.user.role in ['superadmin', 'admin', 'manager', 'operator', 'warehouse']
