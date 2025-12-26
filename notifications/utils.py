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

def get_notification_frontend_url(notification):
    """
    Generate the appropriate frontend URL for a notification based on notification type and context.
    
    Args:
        notification: Notification instance
        
    Returns:
        str: Relative frontend URL path
    """
    notification_type = notification.notification_type
    
    # Use match statement for switch-case pattern with individual cases
    match notification_type:
        case 'order_created':
            # Client created order - show in orders-offers
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'new_project_available':
            # New project available - technicians see in orders-offers
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/projects/{order_id}'
            else:
                return '/projects'
        
        case 'new_offer':
            # Offer accepted - show order details
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
            
        case 'offer_accepted':
            # Offer accepted - show order details
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'job_started':
            # Job started - show order details
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'job_done':
            # Job done - show order details for fund release
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'funds_released':
            return f'/dashboard/financials'
        
        case 'order_cancelled':
            # Order cancelled - check if user is the assigned technician
            if notification.related_order:
                order_id = notification.related_order.order_id
                # Check if the user is the assigned technician of the order
                if notification.user == notification.related_order.technician_user:
                    return f'/dashboard/tasks/{order_id}'
                else:
                    return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'offer_declined':
            # Offer declined - show in orders-offers
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/tasks/{order_id}'
            else:
                return '/dashboard/tasks'
        
        case 'offer_rejected':
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/projects/{order_id}'
            else:
                return '/projects'
        
        case 'client_offer_rejected':
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
        
        case 'client_offer_accepted':
            # Client offer accepted - show in client-offers
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
                    
        case 'direct_offer_accepted_by_tech':
            # Direct offer accepted - show in client-offers
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            else:
                return '/dashboard/orders-offers'
                    
        case 'dispute_initiated':
            # Dispute initiated - show dispute details
            if notification.related_dispute and notification.related_dispute.order:
                order_id = notification.related_dispute.order.order_id
                return f'/dashboard/disputes/{order_id}'
            else:
                return '/dashboard/disputes'
        
        case 'dispute_resolved':
            # Dispute resolved - show dispute details
            if notification.related_dispute and notification.related_dispute.order:
                order_id = notification.related_dispute.order.order_id
                return f'/dashboard/disputes/{order_id}'
            else:
                return '/dashboard/disputes'
        
        case 'dispute_response':
            # Dispute response - show dispute details
            if notification.related_dispute and notification.related_dispute.order:
                order_id = notification.related_dispute.order.order_id
                return f'/dashboard/disputes/{order_id}'
            else:
                return '/dashboard/disputes'
        
        case 'review':
            # Review created - show in reviews
            return '/dashboard/reviews'
        
        case 'dispute_new':
            # New dispute - admins see in admin-overview
            if notification.related_dispute and notification.related_dispute.order:
                order_id = notification.related_dispute.order.order_id
                return f'/dashboard/disputes/{order_id}'
            else:
                return '/dashboard/disputes'
                    
        case 'system_error':
            # System error - admins see in admin-overview
            return '/dashboard/admin-overview'
        
        case 'funds_auto_released':
            # Auto-release successful - show in orders-offers
            return f'/dashboard/financials'
        
        case 'auto_release_failed':
            # Auto-release failed - show in orders-offers
            return f'/dashboard/financials'
        
        case 'message':
            # Message notification - show in messages
            return '/dashboard/messages'
        case 'new_direct_offer':
            # Message notification - show in messages
            return '/dashboard/client-offers'
        
        case _:
            # Fallback to related entity logic for unknown notification types
            if notification.related_order:
                order_id = notification.related_order.order_id
                return f'/dashboard/orders-offers/view/{order_id}'
            
            if notification.related_offer:
                return '/dashboard/orders-offers'
            
            if notification.related_dispute:
                order_id = notification.related_dispute.order.order_id if notification.related_dispute.order else ''
                return f'/dashboard/disputes/{order_id}'
            
            if notification.related_review:
                return '/dashboard/reviews'
            
            # Final default fallback
            return '/dashboard/orders-offers'
