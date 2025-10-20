from django.db import models

class UserType(models.Model):
    user_type_id = models.AutoField(primary_key=True)
    user_type_name = models.CharField(max_length=255, unique=True, null=False, blank=False)

    class Meta:
        db_table = 'USER_TYPE' # Explicitly set table name to match SQL

    def __str__(self):
        return self.user_type_name

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_type = models.ForeignKey(UserType, on_delete=models.CASCADE, null=False, blank=False)
    first_name = models.CharField(max_length=255, null=False, blank=False)
    last_name = models.CharField(max_length=255, null=False, blank=False)
    email = models.CharField(max_length=255, unique=True, null=False, blank=False)
    phone_number = models.CharField(max_length=255, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=False, blank=False)
    address = models.TextField(null=True, blank=True)
    account_status = models.CharField(max_length=255, null=True, blank=True)
    registration_date = models.DateField(null=False, blank=False)
    last_login_date = models.DateField(null=True, blank=True)
    notification_preferences = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    profile_picture = models.CharField(max_length=255, null=True, blank=True)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True) # Assuming rating is between 0-5
    num_jobs_completed = models.IntegerField(null=True, blank=True)
    average_response_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Assuming time in minutes/hours
    verification_status = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True, null=True, blank=True)
    access_level = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'USER' # Explicitly set table name to match SQL

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
