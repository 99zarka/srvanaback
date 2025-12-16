from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from orders.models import Order
from users.models import User
from decimal import Decimal # Import Decimal for precise calculations
from transactions.models import Transaction
from notifications.utils import create_notification
from notifications.arabic_translations import ARABIC_NOTIFICATIONS

class Command(BaseCommand):
    help = 'Checks for orders past their auto_release_date and automatically releases funds to technicians.'

    def handle(self, *args, **options):
        self.stdout.write("Starting auto-release check...")
        
        now = timezone.now()
        
        # Find orders that are in 'awaiting_release' and past their auto_release_date
        orders_to_auto_release = Order.objects.filter(
            order_status='awaiting_release',
            auto_release_date__lte=now
        ).select_for_update() # Lock these orders to prevent race conditions

        processed_count = 0
        for order in orders_to_auto_release:
            try:
                with db_transaction.atomic():
                    # Refresh from DB to get the latest state and ensure lock is active
                    order.refresh_from_db()

                    # Double check status inside the atomic block
                    if order.order_status != 'awaiting_release':
                        self.stdout.write(self.style.WARNING(f"Order {order.order_id} was already processed or changed status. Skipping auto-release."))
                        continue

                    client_user = order.client_user
                    technician_user = order.technician_user
                    amount_to_release = Decimal(str(order.final_price)) # Ensure it's a Decimal object

                    if not technician_user:
                        self.stdout.write(self.style.ERROR(f"Order {order.order_id} has no assigned technician. Cannot auto-release funds."))
                        create_notification(
                            user=client_user,
                            notification_type='auto_release_failed',
                            title=ARABIC_NOTIFICATIONS['auto_release_failed_title'],
                            message=ARABIC_NOTIFICATIONS['auto_release_failed_message'].format(order_id=order.order_id),
                            related_order=order
                        )
                        continue

                    client_user.refresh_from_db()
                    technician_user.refresh_from_db()

                    if client_user.in_escrow_balance < amount_to_release:
                        self.stdout.write(self.style.ERROR(f"Order {order.order_id}: Insufficient escrow funds ({client_user.in_escrow_balance}) to release {amount_to_release}."))
                        create_notification(
                            user=client_user,
                            notification_type='auto_release_failed',
                            title=ARABIC_NOTIFICATIONS['auto_release_failed_title'],
                            message=ARABIC_NOTIFICATIONS['auto_release_failed_message'].format(order_id=order.order_id),
                            related_order=order
                        )
                        continue
                    
                    # Move funds from client's in_escrow_balance to technician's pending_balance
                    client_user.in_escrow_balance -= amount_to_release
                    client_user.save(update_fields=['in_escrow_balance'])

                    technician_user.pending_balance += amount_to_release
                    technician_user.save(update_fields=['pending_balance'])

                    # Create an escrow release transaction
                    Transaction.objects.create(
                        user=client_user,
                        related_user=technician_user,
                        order=order,
                        transaction_type='escrow_release',
                        amount=amount_to_release,
                        status='completed',
                        currency='USD',
                        # description field removed as it does not exist in Transaction model
                    )

                    # Update the order status to completed and set job_completion_timestamp
                    order.order_status = 'completed'
                    order.job_completion_timestamp = timezone.now()
                    order.save(update_fields=['order_status', 'job_completion_timestamp'])

                    # Notify technician and client
                    create_notification(
                        user=technician_user,
                        notification_type='funds_auto_released',
                        title=ARABIC_NOTIFICATIONS['funds_auto_released_title'],
                        message=ARABIC_NOTIFICATIONS['funds_auto_released_message'].format(order_id=order.order_id),
                        related_order=order
                    )
                    create_notification(
                        user=client_user,
                        notification_type='funds_auto_released',
                        title=ARABIC_NOTIFICATIONS['funds_auto_released_title'],
                        message=ARABIC_NOTIFICATIONS['funds_auto_released_to_tech_message'].format(order_id=order.order_id, technician_name=technician_user.get_full_name()),
                        related_order=order
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f"Successfully auto-released funds for order {order.order_id}."))
                    processed_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing order {order.order_id} for auto-release: {e}"))
                # Optionally notify admin about the error
                admins = User.objects.filter(user_type__user_type_name='admin')
                for admin_user in admins:
                    create_notification(
                        user=admin_user,
                        notification_type='system_error',
                        title=ARABIC_NOTIFICATIONS['system_error_title'],
                        message=ARABIC_NOTIFICATIONS['system_error_message'].format(order_id=order.order_id, error=str(e)),
                        related_order=order
                    )

        self.stdout.write(self.style.SUCCESS(f"Auto-release check completed. Processed {processed_count} orders."))
