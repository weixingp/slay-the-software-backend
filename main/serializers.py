from abc import ABC

from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from rest_framework import serializers

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
    class Meta:
        model = Answer
        fields = '__all__'


class GetQuestionByLevelIDSerializer(serializers.Serializer):
    level_id = serializers.IntegerField()

    def get_question(self):
        pass

    def get_answers(self):
        raise serializers.Rel


class LeaderboardSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    points = serializers.IntegerField()


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'


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

