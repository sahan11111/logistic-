import math
from rest_framework import serializers
from .models import Order, Warehouse ,Shipment
from django.utils import calculate_distance
from django.contrib.auth import get_user_model
User = get_user_model()
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'role',
            'phone'
        ]

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data.get('email'),
            role=validated_data['role'],
            phone=validated_data.get('phone')
        )
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


def calculate_distance(lat1, lon1, lat2, lon2):
    # Earth radius (KM)
    R = 6371  

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = math.sin(d_lat/2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(d_lon/2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

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
        # If warehouse not provided, we auto assign
        if not data.get("warehouse"):

            lat = data.get("pickup_latitude")
            lon = data.get("pickup_longitude")

            if lat is None or lon is None:
                raise serializers.ValidationError(
                    "Pickup latitude & longitude required for auto warehouse selection."
                )

            warehouses = Warehouse.objects.all()

            # Find nearest warehouse
            nearest = min(
                warehouses,
                key=lambda w: calculate_distance(
                    lat, lon, w.latitude, w.longitude
                )
            )

            data["warehouse"] = nearest

        return data

    def create(self, validated_data):
        return Order.objects.create(**validated_data)

    
class ShipmentSerializer(serializers.ModelSerializer):
    order_token = serializers.CharField(source='order.token', read_only=True)
    customer = serializers.CharField(source='order.customer.username', read_only=True)

    class Meta:
        model = Shipment
        fields = [
            'id',
            'order',
            'order_token',
            'driver',
            'vehicle',
            'assigned_at',
            'delivered_at',
            'status'
        ]