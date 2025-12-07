from .models import Notification
from users.models import User
from orders.models import Order, ProjectOffer # Import ProjectOffer
from users.models import User
from disputes.models import Dispute # Import Dispute model

def create_notification(user, notification_type, title, message, related_order=None, related_offer=None, related_dispute=None):
    """
    Helper function to create a new notification.
    """
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_order=related_order,
        related_offer=related_offer, # Add related_offer field
        related_dispute=related_dispute # Add related_dispute field
    )
