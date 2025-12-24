from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = DefaultRouter()
# Users
router.register("users", UserViewSet, basename="users")

# Orders (customers)
router.register("orders", OrderViewSet, basename="orders")

# Shipments (admin)
router.register("admin/shipments", ShipmentAdminViewSet, basename="admin-shipments")

# Shipments (driver view)
router.register("driver/shipments", DriverShipmentViewSet, basename="driver-shipments")

# Admin Dashboard
router.register("admin/dashboard", AdminDashboardViewSet, basename="admin-dashboard")
urlpatterns = [
    path('', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),

]