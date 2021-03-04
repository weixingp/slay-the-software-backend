from django.conf.global_settings import AUTHENTICATION_BACKENDS
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render
from pytz import unicode
from rest_framework import viewsets, authentication, exceptions
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from .models import *
from django.db.models import Sum

from main.serializers import *


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


# not tested yet
class LeaderboardView(APIView):

    def get(self, request):
        if request.world_id: # get leaderboard of a particular world
            sections = Section.objects.filter(world_id = request.world_id) # get sections in the world
            section_ids = [section.id for section in sections] # extract section ids
            level_ids = []
            for section_id in section_ids:
                levels = Level.objects.filter(section_id=section_id)  # get levels in the section
                level_ids += [level.id for level in levels] # extract level ids
            student_records = QuestionRecord.objects.get(level_id__in=level_ids) # extract level records which fall in level_ids
        else: # get overall leaderboard
            student_records = QuestionRecord.objects.all()

        # sum up points for each student and sort in desc order
        student_points = student_records.values('user_id').annotate(points=Sum('points_gained')).order_by('points').reverse()

        if request.offset:
            student_points = student_points[request.offset:]
        if request.limit:
            student_points = student_points[:request.limit]

        serializer = LeaderboardSerializer(data=student_points, many=True)
        return Response(serializer.data)


class WorldView(APIView):

    def get_object(self, id):
        try:
            return World.objects.get(id=id)
        except World.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request):
        worlds = World.objects.all()
        serializer = WorldSerializer(worlds)
        return Response(serializer.data)

    # not sure if overloading works
    def get(self, request, id):
        world = self.get_object(id)
        serializer = WorldSerializer(world)
        return Response(serializer.data)

class QuestionView(APIView):
    def get(self, request):
        user = request.user

        return Response({"success": True, "user_id": user.id})