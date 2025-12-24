# Create your models here.
import random
import string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from .utils import generate_otp, otp_expiry_time

class User(AbstractUser):
    ROLE_CHOICES = (('customer','Customer'),('driver','Driver'),('admin','Admin'))
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_available = models.BooleanField(default=False)  # driver availability
    # driver current lat/lon (optional)
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'customer'}
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.SET_NULL, null=True)

    # NEW FIELD (unique token for each order)
    token = models.CharField(max_length=20, unique=True, db_index=True, blank=True)

    pickup_address = models.TextField()
    dropoff_address = models.TextField()
    package_weight = models.FloatField()
    package_details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="pending")
    pickup_latitude = models.FloatField(null=True, blank=True)
    pickup_longitude = models.FloatField(null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)

    def generate_token(self):
        # Example: NCM-ABC123
        prefix = "NCM"  # Nepal Can Move (customizable)
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{random_part}"

    def __str__(self):
        return f"Order {self.id} - {self.token}"
    
class Vehicle(models.Model):
    driver = models.OneToOneField(User, on_delete=models.CASCADE,
                                  limit_choices_to={'role': 'driver'})
    vehicle_type = models.CharField(max_length=50)   # Bike, Van, Truck
    plate_number = models.CharField(max_length=20)
    model = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.vehicle_type} - {self.plate_number}"

class Shipment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver = models.ForeignKey(User, null=True, blank=True,
                               limit_choices_to={'role': 'driver'}, on_delete=models.SET_NULL)
    vehicle = models.ForeignKey('Vehicle', null=True, blank=True, on_delete=models.SET_NULL)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('assigned', 'Assigned'),
            ('in_transit', 'In Transit'),
            ('delivered', 'Delivered'),
        ]
    )
    pickup_otp = models.CharField(max_length=10, null=True, blank=True)
    pickup_otp_expires = models.DateTimeField(null=True, blank=True)
    delivery_otp = models.CharField(max_length=10, null=True, blank=True)
    delivery_otp_expires = models.DateTimeField(null=True, blank=True)

    def generate_pickup_otp(self, minutes_valid=10):
        from django.utils import generate_otp, otp_expiry_time
        self.pickup_otp = generate_otp()
        self.pickup_otp_expires = otp_expiry_time(minutes_valid)
        self.save(update_fields=['pickup_otp','pickup_otp_expires'])
        return self.pickup_otp

    def generate_delivery_otp(self, minutes_valid=30):
        from django.utils import generate_otp, otp_expiry_time
        self.delivery_otp = generate_otp()
        self.delivery_otp_expires = otp_expiry_time(minutes_valid)
        self.save(update_fields=['delivery_otp','delivery_otp_expires'])
        return self.delivery_otp

    def verify_pickup_otp(self, code):
        if self.pickup_otp and self.pickup_otp_expires and timezone.now() <= self.pickup_otp_expires:
            return self.pickup_otp == code
        return False

    def verify_delivery_otp(self, code):
        if self.delivery_otp and self.delivery_otp_expires and timezone.now() <= self.delivery_otp_expires:
            return self.delivery_otp == code
        return False


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=30, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number
