from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from main.GameManager import GameManager
from main.models import Question, Answer, Section, Level
from main.models import *
from main.validators import validate_username


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class LoginSerializer(serializers.Serializer):
    # email = serializers.EmailField()
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Incorrect email or password.')

        if not user.is_active:
            raise serializers.ValidationError('User is disabled.')

        return {'user': user}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'last_login',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'date_joined',
            'password'
        )
        read_only_fields = ('last_login', 'is_active', 'joined_at')
        extra_kwargs = {
            'password': {'required': True, 'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    @staticmethod
    def validate_email(value):
        return validate_username(value)

    def create(self, validated_data):
        return User.objects.create_user(
            validated_data.pop('email'),
            validated_data.pop('password'),
            **validated_data
        )


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.CharField(required=False)
    class Meta:
        model = Answer
        fields = '__all__'
        read_only_fields = ["is_correct"]

class AnswerWithoutCorrectShownSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer']


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


class GetQuestionByLevelIDSerializer(serializers.Serializer):
    level_id = serializers.IntegerField()

    def validate(self, attrs):
        level_id = attrs['level_id']
        try:
            level = Level.objects.get(id=level_id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Level ID not found.")

        return {"level": level}


class QuestionAnswerSerializer(serializers.Serializer):
    question = QuestionSerializer()
    answers = AnswerWithoutCorrectShownSerializer(many=True)



class LeaderboardSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    first_name = serializers.CharField(max_length=256)
    last_name = serializers.CharField(max_length=256)
    points = serializers.IntegerField()
    rank = serializers.IntegerField()


class SectionSerializer(serializers.ModelSerializer):
    levels = LevelSerializer(many=True, read_only=True)

    class Meta:
        model = Section
        fields = '__all__'


class WorldSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = World
        fields = '__all__'


class QuestionRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionRecord
        fields = '__all__'


class CheckAnswerSerializer(serializers.Serializer):
    answer_id = serializers.CharField()

    def validate(self, attrs):
        answer_id = attrs['answer_id']
        try:
            answer = Answer.objects.get(id=answer_id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Answer not found.")

        return {"answer": answer}

class CustomWorldSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = CustomWorld
        fields = '__all__'

class CreateQuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    section = serializers.CharField(required=False)
    difficulty = serializers.CharField(required=False)
    created_by = serializers.CharField(required=False)
    class Meta:
        model = Question
        fields = '__all__'

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        if len(answers_data) != 4:
            raise NotFound(detail="Invalid number of answers")
        question = Question.objects.create(**validated_data)
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        return question



class CustomWorldSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta:
        model = CustomWorld
        fields = '__all__'


# KIV if need
# class AssignmentSerializer(serializers.ModelSerializer):
#     custom_world = CustomWorldSerializer()
#
#     class Meta:
#         model = Assignment
#         fields = '__all__'
#
#     def create(self, validated_data):
#         custom_world_data = validated_data.pop("custom_world")
#         custom_world = CustomWorld.objects.create(**custom_world_data)
#         assignment = Assignment.objects.create(custom_world=custom_world, **validated_data)
#         return assignment


class WorldValidateSerializer(serializers.Serializer):
    world_id = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if 'world_id' not in attrs:
            world = None
        else:
            world_id = attrs['world_id']
            try:
                world = World.objects.get(id=world_id)
            except ObjectDoesNotExist:
                raise NotFound(detail="World does not exist")

        return {"world": world}