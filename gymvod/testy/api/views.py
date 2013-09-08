from rest_framework import viewsets
from django.contrib.auth.models import User, Group

import testy.api.serializers
import testy.models

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = testy.api.serializers.UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = testy.api.serializers.GroupSerializer

class TestViewSet(viewsets.ModelViewSet):
    
    queryset = testy.models.Test.objects.all()
    serializer_class = testy.api.serializers.TestSerializer
