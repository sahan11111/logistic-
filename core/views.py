from rest_framework.viewsets import GenericViewSet,ModelViewSet
from rest_framework.mixins import *
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from .serializers import *
from django.contrib.auth import get_user_model, authenticate
from rest_framework.exceptions import PermissionDenied
from rest_framework.authtoken.models import Token
from .models import *
from .permissions import *
from rest_framework.decorators import action 
from django.shortcuts import get_object_or_404

User = get_user_model()

from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from drf_yasg.utils import swagger_auto_schema
from .models import *
from .serializers import *
from .permissions import *
from .utils import calculate_distance


class UserViewSet(GenericViewSet,CreateModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    # This view is for user verification
    @swagger_auto_schema(
        methods=['put'],
        request_body=UserVerificationSerializer
    )
    @action(methods=['put'],detail=False)
    def verification(self, request):
        user = get_object_or_404(User, email=request.data.get('email'))
        serializer = UserVerificationSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'details':'User has been successfully verified.'
        })
    def get_permissions(self):
        if self.action in ['create', 'login', 'verification']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        if self.action == 'login':
            return UserLoginSerializer
        return super().get_serializer_class()
    
    @action(detail=False, methods=['get'], url_path='detail', permission_classes=[IsAuthenticated])
    def user_detail(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def list_users(self, request):
        user = request.user
        if not user.groups.filter(name="Admin").exists():
            return Response({'detail': 'You do not have permission to view this.'}, status=403)
        
        users = self.get_queryset()
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        role = serializer.validated_data.get('role')

        # ✅ authenticate with email (USERNAME_FIELD)
        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({"error": "Invalid email or password"}, status=400)

        if user.role != role:
            return Response({"error": "Role mismatch"}, status=400)

        if not user.is_active:
            raise PermissionDenied("OTP verification incomplete. Please verify your email to activate the account.")

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "groups": list(user.groups.values_list("name", flat=True)),
            "token": token.key,
        })

class OrderViewSet(GenericViewSet, CreateModelMixin, ListModelMixin):
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class DriverShipmentViewSet(GenericViewSet, ListModelMixin):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self):
        return Shipment.objects.filter(driver=self.request.user)


class ShipmentAdminViewSet(GenericViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=True, methods=['patch'])
    def auto_assign_driver(self, request, pk=None):
        shipment = self.get_object()
        order = shipment.order

        drivers = User.objects.filter(
            role='driver',
            is_available=True,
            current_latitude__isnull=False,
            current_longitude__isnull=False
        )

        if not drivers.exists():
            return Response({"error": "No available drivers"}, status=400)

        driver = min(
            drivers,
            key=lambda d: calculate_distance(
                order.pickup_latitude,
                order.pickup_longitude,
                d.current_latitude,
                d.current_longitude
            )
        )

        shipment.driver = driver
        shipment.status = 'assigned'
        shipment.assigned_at = now()
        shipment.save()

        driver.is_available = False
        driver.save()

        return Response({"message": "Driver assigned", "driver": driver.username})


class AdminDashboardViewSet(GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.Serializer  # swagger-safe

    def list(self, request):
        return Response({
            "users": User.objects.count(),
            "orders": Order.objects.count(),
            "shipments": Shipment.objects.count(),
            "drivers": User.objects.filter(role='driver').count(),
            "warehouses": Warehouse.objects.count(),
        })

class DriverShipmentViewSet(GenericViewSet, ListModelMixin):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self):
        return Shipment.objects.filter(driver=self.request.user)
    
class DriverLocationViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated, IsDriver]

    @action(detail=False, methods=["post"])
    def update_location(self, request):
        user = request.user

        user.current_latitude = request.data.get("latitude")
        user.current_longitude = request.data.get("longitude")
        user.is_available = True
        user.save()

        return Response({"message": "Location updated"})

class DriverShipmentActionViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated, IsDriver]
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer

    @action(detail=True, methods=["post"])
    def pickup(self, request, pk=None):
        shipment = self.get_object()

        if shipment.status != "assigned":
            return Response({"error": "Invalid state"}, status=400)

        shipment.status = "in_transit"
        shipment.picked_at = now()
        shipment.generate_delivery_otp()
        shipment.save()

        return Response({"message": "Shipment picked"})

    @action(detail=True, methods=["post"])
    def deliver(self, request, pk=None):
        shipment = self.get_object()
        otp = request.data.get("otp")

        if otp != shipment.delivery_otp:
            return Response({"error": "Invalid OTP"}, status=400)

        shipment.status = "delivered"
        shipment.delivered_at = now()
        shipment.save()

        shipment.driver.is_available = True
        shipment.driver.save()

        return Response({"message": "Order delivered"})

class AdminChartViewSet(GenericViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.Serializer

    @action(detail=False, methods=["get"])
    def orders(self, request):
        return Response({
            "pending": Order.objects.filter(status="pending").count(),
            "delivered": Order.objects.filter(status="delivered").count(),
        })

    @action(detail=False, methods=["get"])
    def shipments(self, request):
        return Response({
            "assigned": Shipment.objects.filter(status="assigned").count(),
            "in_transit": Shipment.objects.filter(status="in_transit").count(),
            "delivered": Shipment.objects.filter(status="delivered").count(),
        })

    @action(detail=False, methods=["get"])
    def users(self, request):
        return Response({
            "customers": User.objects.filter(role="customer").count(),
            "drivers": User.objects.filter(role="driver").count(),
            "admins": User.objects.filter(role="admin").count(),
        })

class CustomerOrderHistoryViewSet(GenericViewSet, ListModelMixin):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')
    
class DriverOrderHistoryViewSet(GenericViewSet, ListModelMixin):
    serializer_class = ShipmentSerializer
    permission_classes = [IsAuthenticated, IsDriver]

    def get_queryset(self):
        return Shipment.objects.filter(
            driver=self.request.user,
            status="delivered"
        ).order_by('-delivered_at')

class AdminOrderHistoryViewSet(GenericViewSet, ListModelMixin):
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]
    queryset = Order.objects.all().order_by('-created_at')
