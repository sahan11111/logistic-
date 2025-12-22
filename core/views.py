from django.shortcuts import render
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from .serializers import *
User = get_user_model()

# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    
    def get_queryset(self):
        return User.objects.all().filter(is_active=True)
    
    def perform_create(self, serializer):
        serializer.save()