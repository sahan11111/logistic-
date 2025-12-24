from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('role', 'is_active', 'is_staff')
    

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "warehouse", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("token",)

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "driver", "status", "assigned_at")

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude")