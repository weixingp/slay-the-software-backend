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
from main.permissions import IsOwnerOrReadOnly
import random, string


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


class LeaderboardView(APIView):

    def get(self, request):
        world_id = request.query_params.get("world_id")
        print(request.META)
        if world_id:  # get leaderboard of a particular world
            try:
                world_id = int(world_id)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            sections = Section.objects.filter(world_id=world_id)  # get sections in the world
            section_ids = [section.id for section in sections]  # extract section ids
            level_ids = []
            for section_id in section_ids:
                levels = Level.objects.filter(section_id=section_id)  # get levels in the section
                level_ids += [level.id for level in levels]  # extract level ids
            student_records = QuestionRecord.objects.filter(
                level_id__in=level_ids)  # extract level records which fall in level_ids
        else:  # get overall leaderboard
            student_records = QuestionRecord.objects.all()

        # sum up points for each student and sort in desc order
        student_points = student_records.values('user_id', 'user__first_name', 'user__last_name') \
            .annotate(points=Sum('points_change')).order_by('points').reverse()

        # do cleaning of queryset
        for i in range(1, len(student_points) + 1):
            student = student_points[i - 1]
            student["first_name"] = student.pop("user__first_name")
            student["last_name"] = student.pop("user__last_name")
            student["rank"] = i

        # if user_id specified, return only the ranking of that user
        # don't need to apply offset/limit in this case
        user_id = request.query_params.get("user_id")
        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            student_exists = False
            for student in student_points:
                if student["user_id"] == int(user_id):
                    serializer = LeaderboardSerializer(student)
                    student_exists = True
                    break
            if not student_exists:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            # apply offset, if any
            offset = request.query_params.get("offset")
            if offset:
                try:
                    student_points = student_points[int(offset) - 1:]
                except (ValueError, AssertionError):
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            # apply limit, if any
            limit = request.query_params.get("limit")
            if limit:
                try:
                    student_points = student_points[:int(limit)]
                except (ValueError, AssertionError):
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            serializer = LeaderboardSerializer(student_points, many=True)

        return Response(serializer.data)


class WorldView(APIView):

    def get(self, request):
        worlds = World.objects.filter(is_custom_world=False)
        serializer = WorldSerializer(worlds, many=True)
        return Response(serializer.data)


class WorldDetails(APIView):

    def get_object(self, id):
        try:
            return World.objects.get(id=id)
        except World.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, id):
        world = self.get_object(id)
        if isinstance(world, Response):  # custom_world not found
            return world
        serializer = WorldSerializer(world)
        return Response(serializer.data)


class QuestionView(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        question_list = gm.get_questions(serializer.validated_data['world'])
        res = {
            "questions": [],
        }
        for question in question_list:
            question_serializer = QuestionSerializer(question['question'])
            answers_serializer = AnswerWithoutCorrectShownSerializer(question["answers"], many=True)
            temp = {
                "question": question_serializer.data['question'],
                "answers": answers_serializer.data,
                "record_id": question['record_id']
            }
            res["questions"].append(temp)

        return Response(res)


class CheckAnswerView(APIView):
    def post(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        check_answer_serializer = CheckAnswerSerializer(data=request.data)
        check_answer_serializer.is_valid(raise_exception=True)
        answer = check_answer_serializer.validated_data['answer']

        is_correct, points_change = gm.check_answer_in_world(serializer.validated_data['world'], answer)
        res = {
            "is_correct": is_correct,
            "points_change": points_change,
        }
        return Response(res)


class CustomQuestionView(APIView):
    def get(self, request):
        questions = Question.objects.filter(created_by=request.user)
        serializer = CreateQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            section = Section.objects.get(id=request.data['section'])
            # check if this Section belongs to a Custom World, and if this Section has fewer than 10 questions
            # if both are true, then save
            number_of_questions_in_section = len(Question.objects.filter(section=section))
            if section.world.is_custom_world and number_of_questions_in_section < 10:
                serializer.save(created_by=request.user, difficulty=1, section=section)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class CustomQuestionListView(APIView):

    def get_object(self, pk):
        try:
            return Question.objects.get(pk=pk)
        except Question.objects.get(pk=pk):
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        if request.user == Question.objects.get(pk=pk).created_by:
            question = self.get_object(pk)
            serializer = CreateQuestionSerializer(question)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk):
        if request.user == Question.objects.get(pk=pk).created_by:
            question = self.get_object(pk)
            serializer = CreateQuestionSerializer(question, data=request.data, partial=True)
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

    def get_user(self, id):
        return User.objects.get(id=id)

    def get(self, request):
        user = self.get_user(request.user.id)
        user_custom_worlds = CustomWorld.objects.filter(created_by=user)
        serializer = CustomWorldSerializer(user_custom_worlds, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        print(data)
        data["created_by"] = self.get_user(request.user.id).id
        data["is_custom_world"] = True
        data["access_code"] = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        serializer = CustomWorldSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            # make section
            created_world = World.objects.get(world_name=data["world_name"])
            section = Section.objects.create(world=created_world, sub_topic_name=created_world.world_name)

            # create Level
            for i in range(10):
                level_name = "Level %s" % (i + 1)
                Level.objects.create(section=section, level_name=level_name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomWorldDetails(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, access_code):
        try:
            return CustomWorld.objects.get(access_code=access_code)
        except CustomWorld.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, access_code):
        custom_world = self.get_object(access_code)
        if isinstance(custom_world, Response):  # custom_world not found
            return custom_world
        serializer = CustomWorldSerializer(custom_world)
        return Response(serializer.data)

    def put(self, request, access_code):
        custom_world = self.get_object(access_code)
        if isinstance(custom_world, Response):  # custom_world not found
            return custom_world

        serializer = CustomWorldSerializer(custom_world, data=request.data, partial=True)
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


class EditAnswerView(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get_answer(self, id):
        try:
            return Answer.objects.get(id=id)
        except Answer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, id):
        answer = self.get_answer(id)
        if isinstance(answer, Response):
            return answer

        serializer = AnswerSerializer(answer)
        return Response(serializer.data)

    def put(self, request, id):
        answer = self.get_answer(id)
        if isinstance(answer, Response):
            return answer

        serializer = AnswerSerializer(answer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# KIV if need
# class AssignmentView(APIView):
#
#     def get(self, request):
#         assignments = Assignment.objects.all()
#         serializer = AssignmentSerializer(assignments)
#         return Response(serializer.data)
#
#     def post(self, request):
#         serializer = CreateQuestionSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(created_by=request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
