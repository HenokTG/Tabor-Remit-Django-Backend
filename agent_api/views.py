from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.generics import ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import AgentProfile
from .serializers import AgentProfileUpdateSerializer, CustomAgentSerializer


class UserRegistrationAPIView(ListCreateAPIView):

    permission_classes = [AllowAny]
    serializer_class = CustomAgentSerializer
    queryset = AgentProfile.objects.all()

    def post(self, request, format='json'):
        serializer = CustomAgentSerializer(data=request.data)
         
        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileViewSet(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = AgentProfileUpdateSerializer

    def get_object(self, queryset=None, **kwargs):
        user = self.kwargs.get('pk')

        return get_object_or_404(AgentProfile, agent_name=user)

    def get_queryset(self):
       return AgentProfile.objects.all()

    def update(self, request, format=None, *args, **kwargs):

        instance = self.get_object()
        serializer = self.serializer_class(instance, data=request.data, context={
                                           'request': request}, partial=True)

        if serializer.is_valid(raise_exception=True):
            profile = serializer.save()
            if profile:
                return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


