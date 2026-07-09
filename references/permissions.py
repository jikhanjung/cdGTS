from rest_framework import permissions


class ReferenceAccessPermission(permissions.BasePermission):
    """
    Global shared registry:
      - read: public,
      - create: any authenticated user,
      - edit/delete: staff or the entry's `created_by` (creator).
    (Deletion of a *cited* reference is additionally blocked in the view.)
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        u = request.user
        return bool(u and u.is_authenticated and (u.is_staff or obj.created_by_id == u.id))
