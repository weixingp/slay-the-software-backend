from django.conf.global_settings import AUTHENTICATION_BACKENDS
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render
from pytz import unicode
from rest_framework import viewsets, authentication, exceptions
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from main.serializers import UserSerializer, GroupSerializer, LoginSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


# Function-based view example
@api_view(['GET'])
def hello_world(request):
    return Response({"message": "Hello, world!"})


# Class-based view example
class HelloWorld2(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)


class CsrfExemptSessionAuthentication(authentication.SessionAuthentication):
    def enforce_csrf(self, request):
        return


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (TokenAuthentication, )

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        login(request, user)
        data = UserSerializer(user).data
        data["token"] = token.key
        return Response(data)


class LogoutView(APIView):
    def get(self, request):
        user = request.user
        logout(request)
        return Response({"success": True, "user_id": user.id})


class RegisterView(CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        user = serializer.save()
        user.backend = AUTHENTICATION_BACKENDS[0]
        login(self.request, user)


class UserView(RetrieveAPIView):
    serializer_class = UserSerializer
    lookup_field = 'pk'

    def get_object(self, *args, **kwargs):
        return self.request.user


class QuestionView(APIView):
    def get(self, request):
        user = request.user
        

        return Response({"success": True, "user_id": user.id})