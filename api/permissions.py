from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from users.models import User

class IsClientUser(permissions.BasePermission):
    """
    Custom permission to only allow clients to access certain objects.
    Includes technicians (they can be customers too).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_type = request.user.user_type.user_type_name
        return user_type in ['client', 'technician']

class IsTechnicianUser(permissions.BasePermission):
    """
    Custom permission to only allow technicians to access certain objects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'technician'

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admins to access certain objects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin'

class IsClientOrTechnicianUser(permissions.BasePermission):
    """
    Custom permission to allow clients or technicians to access certain objects.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_type_name = request.user.user_type.user_type_name
        return user_type_name == 'client' or user_type_name == 'technician'

class IsAdminOrTechnicianUser(permissions.BasePermission):
    """
    Custom permission to allow admins or technicians to access certain objects.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        user_type_name = request.user.user_type.user_type_name
        return user_type_name == 'admin' or user_type_name == 'technician'

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    Assumes the object has an 'owner' attribute or is a User object.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        
        # For User objects, check against user_id
        if isinstance(obj, User):
            return obj.user_id == request.user.user_id
        
        # For other objects, assume an 'owner' attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False # Default to false if no owner attribute or not a User object

class IsConversationParticipantOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation or admins to access it.
    Assumes the object is either a Conversation or has a 'conversation' attribute with a 'participants' ManyToManyField.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        
        if hasattr(obj, 'participants'): # For Conversation objects
            return request.user in obj.participants.all()
        elif hasattr(obj, 'conversation') and hasattr(obj.conversation, 'participants'): # For Message objects
            return request.user in obj.conversation.participants.all()
        return False

class IsClientOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the client owner of an object or admins to access it.
    Assumes the object has a 'client_user' attribute which is a User, or an 'order' attribute with a 'client_user' attribute.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        
        if hasattr(obj, 'client_user'):
            return obj.client_user == request.user
        elif hasattr(obj, 'order') and hasattr(obj.order, 'client_user'):
            return obj.order.client_user == request.user
        raise PermissionDenied("You do not have permission to access this object.")

class IsTechnicianOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the technician owner of an object or admins to access it.
    Assumes the object has a 'technician' attribute which is a User.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        if hasattr(obj, 'technician_user'):
            return obj.technician_user == request.user
        raise PermissionDenied("You do not have permission to access this object.")

class IsUserOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the user owner of an object or admins to access it.
    Assumes the object has a 'user' attribute which is a User.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        if hasattr(obj, 'user'):
            if obj.user == request.user:
                return True
        elif hasattr(obj, 'reporter'):
            if obj.reporter == request.user:
                return True
        raise PermissionDenied("You do not have permission to access this object.")

class IsMessageSenderOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the sender of a message or admins to access it.
    Assumes the object has a 'sender' attribute which is a User.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        return obj.sender == request.user

class IsReviewOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the client who made the review or admins to access it.
    Assumes the object has a 'client_user' attribute which is a User.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        if hasattr(obj, 'reviewer'):
            return obj.reviewer == request.user
        raise PermissionDenied("You do not have permission to access this object.")

class IsReviewTechnicianOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow the technician who received the review or admins to access it.
    Assumes the object has a 'technician' attribute which is a User.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated and request.user.user_type.user_type_name == 'admin':
            return True
        if hasattr(obj, 'technician') and obj.technician == request.user:
            return True
        if hasattr(obj, 'reviewer') and obj.reviewer == request.user:
            return True
        raise PermissionDenied("You do not have permission to access this object.")

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS or
            request.user and
            request.user.is_authenticated
        )
