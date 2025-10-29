import os
import django
from datetime import date
import time

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'srvana.settings')
django.setup()

from api.models import UserType, User, ServiceCategory, Service, Order, Payment, Review, TechnicianAvailability, TechnicianSkill, ProjectOffer, Complaint, Media, VerificationDocument

def run_script():
    print("--- Starting Data Population Script ---")
    print("This script will create sample data in your main PostgreSQL database.")
    print("You can view this data in your DBMS after each step.")
    input("Press Enter to start creating UserTypes...")

    # Create UserTypes
    user_type_client, created = UserType.objects.get_or_create(user_type_name="Client")
    if created:
        print(f"Created UserType: {user_type_client.user_type_name}")
    else:
        print(f"UserType '{user_type_client.user_type_name}' already exists.")

    user_type_tech, created = UserType.objects.get_or_create(user_type_name="Technician")
    if created:
        print(f"Created UserType: {user_type_tech.user_type_name}")
    else:
        print(f"UserType '{user_type_tech.user_type_name}' already exists.")

    user_type_admin, created = UserType.objects.get_or_create(user_type_name="Admin")
    if created:
        print(f"Created UserType: {user_type_admin.user_type_name}")
    else:
        print(f"UserType '{user_type_admin.user_type_name}' already exists.")

    print("\nAll UserTypes:", UserType.objects.all())
    input("UserTypes created. Press Enter to continue to Users...")

    # Create Users
    user1, created = User.objects.get_or_create(
        email="alice.smith@example.com",
        defaults={
            "user_type": user_type_client,
            "first_name": "Alice",
            "last_name": "Smith",
            "password": "password123",
            "registration_date": date.today(),
            "username": "alicesmith",
            "account_status": "Active"
        }
    )
    if created:
        print(f"Created User: {user1.username}")
    else:
        print(f"User '{user1.username}' already exists.")

    user2, created = User.objects.get_or_create(
        email="bob.johnson@example.com",
        defaults={
            "user_type": user_type_tech,
            "first_name": "Bob",
            "last_name": "Johnson",
            "password": "password456",
            "registration_date": date.today(),
            "username": "bobjohnson",
            "account_status": "Active"
        }
    )
    if created:
        print(f"Created User: {user2.username}")
    else:
        print(f"User '{user2.username}' already exists.")

    user3, created = User.objects.get_or_create(
        email="charlie.admin@example.com",
        defaults={
            "user_type": user_type_admin,
            "first_name": "Charlie",
            "last_name": "Admin",
            "password": "adminpassword",
            "registration_date": date.today(),
            "username": "charlieadmin",
            "account_status": "Active"
        }
    )
    if created:
        print(f"Created User: {user3.username}")
    else:
        print(f"User '{user3.username}' already exists.")

    print("\nAll Users:", User.objects.all())
    input("Users created. Press Enter to continue to ServiceCategories...")

    # Create ServiceCategories
    cat1, created = ServiceCategory.objects.get_or_create(
        category_name="Electrical",
        defaults={"description": "Electrical services"}
    )
    if created:
        print(f"Created ServiceCategory: {cat1.category_name}")
    else:
        print(f"ServiceCategory '{cat1.category_name}' already exists.")

    cat2, created = ServiceCategory.objects.get_or_create(
        category_name="Plumbing",
        defaults={"description": "Plumbing services"}
    )
    if created:
        print(f"Created ServiceCategory: {cat2.category_name}")
    else:
        print(f"ServiceCategory '{cat2.category_name}' already exists.")

    print("\nAll ServiceCategories:", ServiceCategory.objects.all())
    input("ServiceCategories created. Press Enter to continue to Services...")

    # Create Services
    service1, created = Service.objects.get_or_create(
        service_name="Wiring Repair",
        defaults={
            "category": cat1,
            "description": "Repairing faulty wiring",
            "service_type": "Repair",
            "base_inspection_fee": 75.00
        }
    )
    if created:
        print(f"Created Service: {service1.service_name}")
    else:
        print(f"Service '{service1.service_name}' already exists.")

    service2, created = Service.objects.get_or_create(
        service_name="Pipe Leak Fix",
        defaults={
            "category": cat2,
            "description": "Fixing leaky pipes",
            "service_type": "Repair",
            "base_inspection_fee": 60.00
        }
    )
    if created:
        print(f"Created Service: {service2.service_name}")
    else:
        print(f"Service '{service2.service_name}' already exists.")

    print("\nAll Services:", Service.objects.all())
    input("Services created. Press Enter to continue to Orders...")

    # Create Orders
    order1, created = Order.objects.get_or_create(
        client_user=user1,
        service=service1,
        defaults={
            "technician_user": user2,
            "order_type": "Scheduled",
            "problem_description": "Light fixture not working",
            "requested_location": "456 Oak Ave",
            "scheduled_date": date.today(),
            "scheduled_time_start": "10:00",
            "scheduled_time_end": "11:00",
            "order_status": "Assigned",
            "creation_timestamp": date.today()
        }
    )
    if created:
        print(f"Created Order: {order1.order_id}")
    else:
        print(f"Order '{order1.order_id}' already exists.")

    print("\nAll Orders:", Order.objects.all())
    input("Orders created. Press Enter to continue to Payments...")

    # Create Payments
    payment1, created = Payment.objects.get_or_create(
        order=order1,
        client_user=user1,
        transaction_id="TXN12345",
        defaults={
            "payment_method": "Credit Card",
            "amount": 150.00,
            "payment_date": date.today(),
            "payment_status": "Completed",
            "is_deposit": True
        }
    )
    if created:
        print(f"Created Payment: {payment1.payment_id}")
    else:
        print(f"Payment '{payment1.payment_id}' already exists.")

    print("\nAll Payments:", Payment.objects.all())
    input("Payments created. Press Enter to continue to Reviews...")

    # Create Reviews
    review1, created = Review.objects.get_or_create(
        order=order1,
        client_user=user1,
        technician_user=user2,
        defaults={
            "rating": 5,
            "comment": "Excellent service!",
            "review_date": date.today()
        }
    )
    if created:
        print(f"Created Review: {review1.review_id}")
    else:
        print(f"Review '{review1.review_id}' already exists.")

    print("\nAll Reviews:", Review.objects.all())
    input("Reviews created. Press Enter to continue to TechnicianAvailability...")

    # Create TechnicianAvailability
    tech_avail1, created = TechnicianAvailability.objects.get_or_create(
        technician_user=user2,
        day_of_week="Monday",
        start_time="09:00",
        end_time="17:00",
        defaults={"is_available": True}
    )
    if created:
        print(f"Created TechnicianAvailability: {tech_avail1.availability_id}")
    else:
        print(f"TechnicianAvailability '{tech_avail1.availability_id}' already exists.")

    print("\nAll TechnicianAvailability:", TechnicianAvailability.objects.all())
    input("TechnicianAvailability created. Press Enter to continue to TechnicianSkill...")

    # Create TechnicianSkill
    tech_skill1, created = TechnicianSkill.objects.get_or_create(
        technician_user=user2,
        service=service1,
        defaults={"experience_level": "Expert"}
    )
    if created:
        print(f"Created TechnicianSkill: {tech_skill1.technician_user.username} - {tech_skill1.service.service_name}")
    else:
        print(f"TechnicianSkill '{tech_skill1.technician_user.username} - {tech_skill1.service.service_name}' already exists.")

    print("\nAll TechnicianSkills:", TechnicianSkill.objects.all())
    input("TechnicianSkills created. Press Enter to continue to ProjectOffer...")

    # Create ProjectOffer
    offer1, created = ProjectOffer.objects.get_or_create(
        order=order1,
        technician_user=user2,
        defaults={
            "proposed_price": 120.00,
            "estimated_completion_time": "2 hours",
            "offer_date": date.today(),
            "offer_status": "Accepted"
        }
    )
    if created:
        print(f"Created ProjectOffer: {offer1.offer_id}")
    else:
        print(f"ProjectOffer '{offer1.offer_id}' already exists.")

    print("\nAll ProjectOffers:", ProjectOffer.objects.all())
    input("ProjectOffers created. Press Enter to continue to Complaint...")

    # Create Complaint
    complaint1, created = Complaint.objects.get_or_create(
        order=order1,
        client_user=user1,
        defaults={
            "complaint_details": "Technician was late.",
            "submission_date": date.today(),
            "status": "Pending",
            "technician_user": user2 # Assuming technician is involved in complaint
        }
    )
    if created:
        print(f"Created Complaint: {complaint1.complaint_id}")
    else:
        print(f"Complaint '{complaint1.complaint_id}' already exists.")

    print("\nAll Complaints:", Complaint.objects.all())
    input("Complaints created. Press Enter to continue to Media...")

    # Create Media
    media1, created = Media.objects.get_or_create(
        order=order1,
        media_url="http://example.com/image1.jpg",
        defaults={
            "media_type": "image",
            "upload_date": date.today(),
            "client_user": user1 # Assuming client uploaded media
        }
    )
    if created:
        print(f"Created Media: {media1.media_id}")
    else:
        print(f"Media '{media1.media_id}' already exists.")

    print("\nAll Media:", Media.objects.all())
    input("Media created. Press Enter to continue to VerificationDocument...")

    # Create VerificationDocument
    doc1, created = VerificationDocument.objects.get_or_create(
        technician_user=user2,
        document_type="ID Card",
        document_url="http://example.com/id_card.pdf",
        defaults={
            "upload_date": date.today(),
            "verification_status": "Approved"
        }
    )
    if created:
        print(f"Created VerificationDocument: {doc1.doc_id}")
    else:
        print(f"VerificationDocument '{doc1.doc_id}' already exists.")

    print("\nAll VerificationDocuments:", VerificationDocument.objects.all())
    input("VerificationDocuments created. Press Enter to finish the script.")

    print("--- Data Population Script Finished ---")

if __name__ == '__main__':
    run_script()
