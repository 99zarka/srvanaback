from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Update num_jobs_completed and overall_rating for all existing users'

    def handle(self, *args, **options):
        self.stdout.write('Updating user statistics...')
        
        # Get all technician users
        technicians = User.objects.filter(user_type__user_type_name='technician')
        
        updated_count = 0
        for technician in technicians:
            old_jobs = technician.num_jobs_completed
            old_rating = technician.overall_rating
            
            # Update the statistics
            technician.update_stats()
            
            # Check if values changed
            if (technician.num_jobs_completed != old_jobs or 
                technician.overall_rating != old_rating):
                updated_count += 1
                
                # Log changes for verification
                self.stdout.write(
                    f'Updated user {technician.email}: '
                    f'Jobs {old_jobs} -> {technician.num_jobs_completed}, '
                    f'Rating {old_rating} -> {technician.overall_rating}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} technician users'
            )
        )
