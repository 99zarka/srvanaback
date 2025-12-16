from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from cloudinary.models import CloudinaryField # Import CloudinaryField
from django.db.models import Avg, Count, Q

class UserType(models.Model):
    user_type_id = models.AutoField(primary_key=True)
    user_type_name = models.CharField(max_length=255, unique=True, null=False, blank=False)

    class Meta:
        db_table = 'USER_TYPE' # Explicitly set table name to match SQL

    def __str__(self):
        return self.user_type_name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        # Convert empty username to None to avoid unique constraint violation for empty strings
        if 'username' in extra_fields and extra_fields['username'] == '':
            extra_fields['username'] = None

        # Determine user_type: prioritize direct object, then user_type_name string, then default
        user_type_obj = extra_fields.pop('user_type', None) # Pop UserType object if directly provided
        if not user_type_obj:
            user_type_name = extra_fields.pop('user_type_name', 'client')
            try:
                user_type_obj = UserType.objects.get(user_type_name=user_type_name)
            except UserType.DoesNotExist:
                user_type_obj = UserType.objects.create(user_type_name=user_type_name)

        user = self.model(email=email, user_type=user_type_obj, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, null=False, blank=False)
    first_name = models.CharField(max_length=255, null=False, blank=False)
    last_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.CharField(max_length=255, unique=True, null=False, blank=False)
    phone_number = models.CharField(max_length=255, unique=True, null=True, blank=True) # Re-added unique=True
    address = models.TextField(null=True, blank=True)
    account_status = models.CharField(max_length=255, null=True, blank=True)
    registration_date = models.DateTimeField(null=False, blank=False, default=timezone.now, editable=False)
    last_login_date = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_photo = CloudinaryField('profile_photos', null=True, blank=True) # Use CloudinaryField
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True) # Assuming rating is between 0-5
    num_jobs_completed = models.IntegerField(null=True, blank=True)
    average_response_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Assuming time in minutes/hours
    verification_status = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    access_level = models.CharField(max_length=255, null=True, blank=True)

    # Balance fields
    available_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    in_escrow_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Technician specific fields
    specialization = models.CharField(max_length=255, null=True, blank=True)
    skills_text = models.TextField(null=True, blank=True) # Renamed from skills to avoid conflict with TechnicianSkill reverse relation
    experience_years = models.IntegerField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Removed 'user_type' as it has a default

    class Meta:
        db_table = 'USER' # Explicitly set table name to match SQL

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

    def calculate_num_jobs_completed(self):
        """Calculate the number of completed jobs for this user (technician)."""
        from orders.models import Order
        return Order.objects.filter(
            technician_user=self,
            order_status='COMPLETED'
        ).count()

    def calculate_overall_rating(self):
        """Calculate the overall rating based on all reviews received."""
        from reviews.models import Review
        avg_rating = Review.objects.filter(
            technician=self
        ).aggregate(avg=Avg('rating'))['avg']
        return avg_rating if avg_rating is not None else None

    def update_stats(self):
        """Update both num_jobs_completed and overall_rating fields."""
        self.num_jobs_completed = self.calculate_num_jobs_completed()
        self.overall_rating = self.calculate_overall_rating()
        self.save(update_fields=['num_jobs_completed', 'overall_rating'])
