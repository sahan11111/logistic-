
from rest_framework import serializers
from .models import *
from .utils import calculate_distance
from django.contrib.auth import get_user_model
User = get_user_model()
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password', 'role']

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
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
