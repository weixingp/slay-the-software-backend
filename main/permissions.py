from rest_framework import permissions
from main.models import Question, User

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to read it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        try:
            return obj.created_by == request.user
        except AttributeError: # Answer has no created_by attribute
            # get User who created the Question that this Answer belongs to
            user = obj.question.created_by
            return user == request.user
