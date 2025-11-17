from django.core.management.base import BaseCommand
from users.models import UserType

class Command(BaseCommand):
    help = 'Populates the UserType model with client, technician, and admin if they do not exist.'

    def handle(self, *args, **options):
        user_types = ['client', 'technician', 'admin']
        for utype in user_types:
            obj, created = UserType.objects.get_or_create(user_type_name=utype)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created UserType: {utype}'))
            else:
                self.stdout.write(self.style.WARNING(f'UserType already exists: {utype}'))

        # Optional: Remove any other user types if they exist
        # For now, we'll just ensure the required ones are present.
        # If strict enforcement is needed, we would add logic here to delete other types.
