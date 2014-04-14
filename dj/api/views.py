from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from api.serializers import CSPSerializer

from main.models import Client, Show, Episode

class CSPViewSet(viewsets.ModelViewSet):
    """
    API endpoint that dumps Client->Show->Episode: Presenter Name(s)
    """
    queryset = Client.objects.all()
    serializer_class = CSPSerializer


