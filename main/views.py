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
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .helper import calculate_world_statistics
from .models import *
from django.db.models import Sum, Avg

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


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Check if student has reset their password for the first time
        try:
            student = StudentProfile.objects.get(student=user)
        except StudentProfile.DoesNotExist:
            raise ValidationError(detail="Profile not yet created, please contact teacher to create.")
        if student.has_reset_password:
            token, created = Token.objects.get_or_create(user=user)
            login(request, user)
            data = UserSerializer(user).data
            data["token"] = token.key
        else:
            data = UserSerializer(user).data
            data["token"] = None
            data["error"] = "Please reset your password first."
        return Response(data)


class LogoutView(APIView):
    def get(self, request):
        user = request.user
        logout(request)
        return Response({"success": True, "user_id": user.id})


class ChangePasswordView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if request.data['password'] == request.data['new_password']:
            raise ValidationError(detail="New password can't be the same as old password.")

        user.set_password(request.data['new_password'])
        user.save()
        user.student_profile.has_reset_password = True
        user.student_profile.save()
        return Response({"success": True})


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
    """
    API for viewing leaderboard
    """

    def get(self, request):
        """
        Retrieves leaderboard, filtered optionally by world_id, user_id, limit, and offset.
        For each student, their total points, first_name, last_name, and rank are returned.
        :raises NotFound: if world_id is specified, and World with that world_id does not exist
        :raises NotFound: if user_id is specified, and User with that user_id does not exist
        :raises ParseError: if user_id is specified, and the user has not played in Campaign Mode yet or the user is not a Student
        :raises ParseError: if offset is specified, but it is invalid
        :raises ParseError: if limit is specified, but it is invalid
        """
        world_id = request.query_params.get("world_id")
        print(request.META)
        if world_id:  # get leaderboard of a particular world
            try:
                world = World.objects.get(id=world_id)
            except World.DoesNotExist:
                raise NotFound(detail="World with specified ID does not exist.")
            sections = Section.objects.filter(world_id=world)  # get sections in the world
        else:  # get overall leaderboard of campaign worlds
            campaign_worlds = World.objects.filter(is_custom_world=False)
            sections = Section.objects.filter(world__in=campaign_worlds)

        # get records of each question in the world(s)
        levels = Level.objects.filter(section__in=sections)
        student_records = QuestionRecord.objects.filter(level__in=levels)

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
                student = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise NotFound(detail="User with specified ID does not exist")
            student_exists = False
            for student_record in student_points:
                if student_record["user_id"] == student.id:
                    serializer = LeaderboardSerializer(student_record)
                    student_exists = True
                    break
            if not student_exists:
                raise ParseError(detail="This Student has not started playing Campaign Mode, or the User specified is not a Student.")
        else:
            # apply offset, if any
            offset = request.query_params.get("offset")
            if offset:
                try:
                    student_points = student_points[int(offset) - 1:]
                except (ValueError, AssertionError):
                    raise ParseError(detail="Invalid offsets specified")

            # apply limit, if any
            limit = request.query_params.get("limit")
            if limit:
                try:
                    student_points = student_points[:int(limit)]
                except (ValueError, AssertionError):
                    raise ParseError(detail="Invalid limit applied")

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
            raise NotFound("World with specified ID does not exist")

    def get(self, request, id):
        world = self.get_object(id)
        serializer = WorldSerializer(world)
        return Response(serializer.data)


class UserScore(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        user_points = gm.get_user_points_by_world(serializer.validated_data['world'])
        res = {
            "points": user_points,
        }
        return Response(res)


class QuestionDifficulty(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        user_difficulty = gm.get_qn_difficulty_by_world(serializer.validated_data['world'])
        if user_difficulty == "1":
            difficulty_text = "Easy"
        elif user_difficulty == "2":
            difficulty_text = "Normal"
        elif user_difficulty == "3":
            difficulty_text = "Hard"
        else:
            difficulty_text = "Unknown"

        res = {
            "difficulty_id": user_difficulty,
            "difficulty_text": difficulty_text,
        }
        return Response(res)


class QuestionView(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        serializer = WorldValidateSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        question_list, session_stats = gm.get_questions(serializer.validated_data['world'])
        res = {
            "questions": [],
            "score": session_stats[0],
            "correct_counter": session_stats[1]
        }
        for question in question_list:
            question_serializer = QuestionSerializer(question['question'])
            answers_serializer = AnswerWithoutCorrectShownSerializer(question["answers"], many=True)
            temp = {
                "question": question_serializer.data['question'],
                "answers": answers_serializer.data,
                "record_id": question['record_id'],
                "index": question['index'],
            }
            res["questions"].append(temp)

        return Response(res)


class CheckAnswerView(APIView):
    def post(self, request):
        user = request.user
        gm = GameManager(user)
        try:
            data = request.data["question_records"]
        except Exception:
            raise ValidationError(detail="Invalid input data.")

        question_answer_set = []
        for item in data:
            serializer = AnswerQuestionSerializer(data=item)
            serializer.is_valid(raise_exception=True)
            qr = serializer.validated_data['question_record']

            # Check ownership
            if qr.user != request.user:
                raise PermissionDenied(detail="You are not allowed to answer other people's question.")

            temp = {
                "question_record": serializer.validated_data['question_record'],
                "answer": serializer.validated_data['answer'],
            }
            question_answer_set.append(temp)

        res = gm.answer_questions(question_answer_set)

        return Response({"results": res})


class CustomQuestionView(APIView):
    """
    API for creating custom questions
    """
    def get(self, request):
        """
        Gets custom questions the user has created
        """
        questions = Question.objects.filter(created_by=request.user)
        world_id = request.query_params.get("world_id")
        if world_id:
            world = CustomWorld.objects.get(id=world_id)
            if world.created_by != request.user:
                raise PermissionDenied(detail="You do not have access to this Custom World")
            section = Section.objects.get(world_id=world_id)
            questions = questions.filter(section=section)
        serializer = CreateQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Allow user to create custom questions
        """
        serializer = CreateQuestionSerializer(data=request.data)
        if serializer.is_valid():
            section = Section.objects.get(id=request.data['section'])
            # check if this Section belongs to a Custom World, and if this Section has fewer than 12 questions
            # if both are true, then save
            number_of_questions_in_section = len(Question.objects.filter(section=section))
            if section.world.is_custom_world and number_of_questions_in_section < 12:
                serializer.save(created_by=request.user, difficulty=1, section=section)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class CustomQuestionListView(APIView):
    """
    API to get specific user created question
    """
    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, pk):
        """
        Check if question with specific ID exists
        """
        try:
            return Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            raise NotFound(detail="Invalid Question ID specified")

    def get(self, request, pk):
        """
        Get question with specific ID
        """
        question = self.get_object(pk)
        serializer = CreateQuestionSerializer(question)
        return Response(serializer.data)
        # if request.user == Question.objects.get(pk=pk).created_by:
        #     question = self.get_object(pk)
        #     serializer = CreateQuestionSerializer(question)
        #     return Response(serializer.data)
        # else:
        #     raise PermissionDenied(detail="You do not own this question")

    def put(self, request, pk):
        """
        Edit question with specific ID
        """
        question = self.get_object(pk)
        serializer = EditQuestionSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete question with specific ID
        """
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
        while True: # generate unique access_code
            access_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if access_code not in CustomWorld.objects.all().values_list("access_code", flat=True):
                data["access_code"] = access_code
                break
        serializer = CustomWorldSerializer(data=data)

        if serializer.is_valid():
            serializer.save()

            # make section
            created_world = World.objects.get(world_name=data["world_name"])
            section = Section.objects.create(world=created_world, sub_topic_name=created_world.world_name)

            # create Level
            for i in range(4):
                level_name = "Level %s" % (i + 1)
                Level.objects.create(section=section, level_name=level_name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomWorldDetails(APIView):
    permission_classes = [IsOwnerOrReadOnly]

    def get_custom_world(self, access_code, custom_world_type=None):
        try:
            custom_world = CustomWorld.objects.get(access_code=access_code)
            if custom_world_type == "assignment" and not Assignment.objects.filter(custom_world=custom_world).exists():
                raise ParseError(detail="Custom World exists but not as part of an Assignment")
            elif custom_world_type == "challenge" and Assignment.objects.filter(custom_world=custom_world).exists():
                raise ParseError(detail="Custom World exists but not as part of Challenge Mode")
            else:
                return CustomWorld.objects.get(access_code=access_code)
        except CustomWorld.DoesNotExist:
            raise NotFound(detail="Invalid access code specified")

    def get(self, request, access_code):
        custom_world_type = request.query_params.get("type")
        custom_world = self.get_custom_world(access_code, custom_world_type)
        serializer = CustomWorldSerializer(custom_world)
        return Response(serializer.data)

    def put(self, request, access_code):
        custom_world_type = request.query_params.get("type")
        custom_world = self.get_custom_world(access_code, custom_world_type)
        serializer = CustomWorldSerializer(custom_world, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, access_code):
        custom_world_type = request.query_params.get("type")
        custom_world = self.get_custom_world(access_code, custom_world_type)
        custom_world.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetPositionView(APIView):
    def get(self, request):
        user = request.user
        gm = GameManager(user)
        position_serializer = WorldValidateSerializer(data=request.GET)
        position_serializer.is_valid(raise_exception=True)

        position, has_completed_world = gm.get_user_position_in_world(
            position_serializer.validated_data['world'],
            check_completed=True,
        )

        res = {
            "world_id": position.section.world.id,
            "section_id": position.section.id,
            "level_id": position.id,
            "has_completed": has_completed_world,
        }
        return Response(res)


class CampaignStatisticsView(APIView):
    def get(self, request):
        """
        Retrieves the following statistics:
        - Per World in Campaign Mode, retrieve the average score (gained per Question in the Section) and total score per Section
        - Per Section, display each Question and the number of times it was answered correctly and incorrectly
        """
        campaign_mode_stats = []  # array of worlds and their stats
        campaign_worlds = World.objects.filter(is_custom_world=False)
        class_name = request.query_params.get("class")

        for world in campaign_worlds:
            campaign_mode_stats.append(calculate_world_statistics(world, class_name))

        context = {"campaign_mode_stats": campaign_mode_stats}
        if class_name:
            context["group"] = class_name
        else:
            context["group"] = "All"

        # create classes array for dropdown menu
        classes = ["All"]
        for class_group in Class.objects.all():
            classes.append(class_group.class_name)
        context["classes"] = classes

        return render(request, "main/campaign_statistics.html", context)


class AssignmentStatisticsView(APIView):
    """
    Retrieves the following statistics:
    - For an Assignment Custom World, retrieve the average score (gained per Question in the Section), total score,
    and for each Question, the number of times it was answered correctly and incorrectly
    - If a Class name was specified, return the above statistics but only specific to that Class
    """
    def get(self, request):
        access_code = request.query_params.get("access_code")
        class_name = request.query_params.get("class")

        # get list of assignment custom worlds and their access codes to let users choose
        # which statistics to view
        custom_worlds = [{"custom_world_name": "Choose an Assignment World", "access_code": ""}]
        teachers = User.objects.filter(is_staff=True, is_superuser=False)
        for custom_world in CustomWorld.objects.filter(created_by__in=teachers):
            custom_worlds.append({
                "custom_world_name": custom_world.world_name,
                "access_code": custom_world.access_code
            })
        context = {"custom_worlds": custom_worlds}

        # calculate stats for assignment custom world
        if access_code:
            custom_world = CustomWorld.objects.get(access_code=access_code)
            context["custom_world_stats"] = calculate_world_statistics(custom_world, class_name)

            # set current_assignment for displaying in dropdown menu
            context["current_custom_world"] = {
                "custom_world_name": custom_world.world_name,
                "access_code": access_code
            }

            # get list of classes that were assigned this assignment custom world
            classes = ["All"]
            assignments_with_this_custom_world = Assignment.objects.filter(custom_world=custom_world)
            for assignment in assignments_with_this_custom_world:
                classes.append(assignment.class_group.class_name)
            context["classes"] = classes

            # set current_class for displaying in dropdown menu
            if class_name:
                context["current_class"] = class_name
            else:
                context["current_class"] = "All"

        else:
            context["current_custom_world"] = {
                "custom_world_name": "All",
                "access_code": ""
            }

        return render(request, "main/assignment_statistics.html", context)
