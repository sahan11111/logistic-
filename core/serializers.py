
from rest_framework import serializers
from .models import *
from .utils import calculate_distance
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    role=serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone',  'role' ,'password', 'confirm_password']
        extra_kwargs = {'id': {'read_only': True}}
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role=validated_data.pop('role')
        user=models.User.objects.create_user(**validated_data, role=role)
        user.role=role
        user.is_active = False  # Inactive until email verification
        
        user.otp=str(generate_otp())
        user.save()
        
        send_mail(
            subject='User activation',
            message=f'Your OTP is {user.otp} for {user.email}',
            from_email=settings.SENDER_EMAIL_USER,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        return user
        
class UserVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255)
    
    def update(self, user, validated_data):
        otp = validated_data.get('otp')
        email = validated_data.get('email')
        
        if otp == user.otp and email == user.email:
            user.is_active = True
            user.otp = None
            user.save()
        else:
            raise serializers.ValidationError({
                'otp': 'Invalid otp or email'
            })

        return user       


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'token',
            'customer',
            'customer_name',
            'warehouse',
            'warehouse_name',
            'pickup_address',
            'dropoff_address',
            'package_weight',
            'package_details',
            'created_at',
            'status'
        ]
        read_only_fields = ['token', 'created_at', 'status']




class OrderCreateSerializer(serializers.ModelSerializer):
    warehouse = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Order
        fields = [
            'customer',
            'pickup_address',
            'dropoff_address',
            'package_weight',
            'package_details',
            'pickup_latitude',
            'pickup_longitude',
            'warehouse',  # Optional (manual selection)
        ]

    def validate(self, data):
        if not data.get("warehouse"):
            lat, lon = data.get("pickup_latitude"), data.get("pickup_longitude")
            if lat is None or lon is None:
                raise serializers.ValidationError("Latitude & longitude required")

            warehouses = Warehouse.objects.all()
            if not warehouses.exists():
                raise serializers.ValidationError("No warehouses available")

            data["warehouse"] = min(
                warehouses,
                key=lambda w: calculate_distance(lat, lon, w.latitude, w.longitude)
            )
        return data

    def create(self, validated_data):
        return Order.objects.create(**validated_data)

    
class ShipmentSerializer(serializers.ModelSerializer):
    order_token = serializers.CharField(source='order.token', read_only=True)
    customer = serializers.CharField(source='order.customer.username', read_only=True)
    driver_name = serializers.CharField(source='driver.username', read_only=True)
    class Meta:
        model = Shipment
        fields = [
            'id',
            'order',
            'order_token',
            'customer',
            'driver',
            'vehicle',
            'assigned_at',
            'delivered_at',
            'status'
        ]
        
class InvoiceSerializer(serializers.ModelSerializer):
    order_token = serializers.CharField(source="order.token", read_only=True)
    customer = serializers.CharField(source="order.customer.username", read_only=True)
    

    class Meta:
        model = Invoice
        fields = [
            "invoice_number",
            "order_token",
            "customer",
            "amount",
            "generated_at"
        ]
