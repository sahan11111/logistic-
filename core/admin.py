from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('role', 'is_active', 'is_staff')