import json

from django.conf.global_settings import AUTHENTICATION_BACKENDS
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render
from pytz import unicode
from rest_framework import viewsets, authentication, exceptions
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
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
    authentication_classes = (TokenAuthentication,)

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
        if request.world_id:  # get leaderboard of a particular world
            sections = Section.objects.filter(world_id=request.world_id)  # get sections in the world
            section_ids = [section.id for section in sections]  # extract section ids
            level_ids = []
            for section_id in section_ids:
                levels = Level.objects.filter(section_id=section_id)  # get levels in the section
                level_ids += [level.id for level in levels]  # extract level ids
            student_records = QuestionRecord.objects.get(
                level_id__in=level_ids)  # extract level records which fall in level_ids
        else:  # get overall leaderboard
            student_records = QuestionRecord.objects.all()

        # sum up points for each student and sort in desc order
        student_points = student_records.values('user_id').annotate(points=Sum('points_gained')).order_by(
            'points').reverse()

        if request.offset:
            student_points = student_points[request.offset:]
        if request.limit:
            student_points = student_points[:request.limit]

        serializer = LeaderboardSerializer(data=student_points, many=True)
        return Response(serializer.data)


class WorldView(APIView):

    def get(self, request):
        worlds = World.objects.all()
        serializer = WorldSerializer(worlds)
        return Response(serializer.data)


class WorldDetails(APIView):

    def get_object(self, id):
        try:
            return World.objects.get(id=id)
        except World.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, id):
        world = self.get_object(id)
        serializer = WorldSerializer(world)
        return Response(serializer.data)


class QuestionView(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        question, answers, record = gm.get_question_answer_in_main_world(serializer.validated_data['world'])
        question_serializer = QuestionSerializer(question)
        answers_serializer = AnswerWithoutCorrectShownSerializer(answers, many=True)
        # question_record_serializer = QuestionRecordSerializer(record)
        res = {
            "question": question_serializer.data['question'],
            "answers": answers_serializer.data,
            "record_id": record.id
        }
        return Response(res)


class CheckAnswerView(APIView):
    def post(self, request):
        user = request.user
        gm = GameManager(user)

        check_answer_serializer = CheckAnswerSerializer(data=request.data)
        check_answer_serializer.is_valid(raise_exception=True)
        answer = check_answer_serializer.validated_data['answer']

        is_correct, points_change = gm.check_answer_in_main_world(answer)
        res = {
            "is_correct": is_correct,
            "points_change": points_change,
        }
        return Response(res)


class CreateQuestionView(APIView):
    def get(self, request):
        questions = Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class QuestionListView(APIView):

    def get_object(self, pk):
        try:
            return Question.objects.get(pk=pk)
        except Question.objects.get(pk=pk):
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        if request.user == Question.objects.get(pk=pk).created_by:
            question = self.get_object(pk)
            serializer = QuestionSerializer(question)
            return Response(serializer.data)

    def put(self, request, pk):
        if request.user == Question.objects.get(pk=pk).created_by:
            question = self.get_object(pk)
            serializer = QuestionSerializer(question, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        if request.user == Question.objects.get(pk=pk).created_by:
            question = self.get_object(pk)
            question.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomWorldView(APIView):

    def get(self, request):
        user = User.objects.get(id=request.user.id)
        user_custom_worlds = CustomWorld.objects.filter(created_by=user)
        serializer = CustomWorldSerializer(user_custom_worlds)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomWorldSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomWorldDetails(APIView):

    def get_object(self, access_code):
        try:
            return CustomWorld.objects.get(access_code=access_code)
        except CustomWorld.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, access_code):
        custom_world = self.get_object(access_code)
        serializer = CustomWorldSerializer(custom_world)
        return Response(serializer.data)

    def put(self, request, access_code):
        custom_world = self.get_object(access_code)
        serializer = CustomWorldSerializer(custom_world, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, access_code):
        custom_world = self.get_object(access_code)
        custom_world.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetPositionView(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        position_serializer = WorldValidateSerializer(data=request.GET)
        position_serializer.is_valid(raise_exception=True)
        position = gm.get_user_position_in_world(position_serializer.validated_data['world'])
        res = {
            "world_id": position.section.world.id,
            "section_id": position.section.id,
            "level_id": position.id
        }
        return Response(res)
