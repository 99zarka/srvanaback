from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

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
        user = self.model(email=email, **extra_fields)
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
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, null=False, blank=False, default=1)
    first_name = models.CharField(max_length=255, null=False, blank=False)
    last_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.CharField(max_length=255, unique=True, null=False, blank=False)
    phone_number = models.CharField(max_length=255, unique=True, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    account_status = models.CharField(max_length=255, null=True, blank=True)
    registration_date = models.DateTimeField(null=False, blank=False, default=timezone.now, editable=False)
    last_login_date = models.DateTimeField(null=True, blank=True)
    notification_preferences = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.CharField(max_length=255, null=True, blank=True)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True) # Assuming rating is between 0-5
    num_jobs_completed = models.IntegerField(null=True, blank=True)
    average_response_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Assuming time in minutes/hours
    verification_status = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    access_level = models.CharField(max_length=255, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type', 'registration_date']

    class Meta:
        db_table = 'USER' # Explicitly set table name to match SQL

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name
