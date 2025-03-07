from rest_framework import serializers
from .models import User
from recipes.models import Recipe
from recipes.serializers import RecipeSerializer
from rest_framework import serializers
from django.contrib import auth
from .models import User
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class UserProfileSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()

    def get_recipes(self, user):
        recipes = Recipe.objects.filter(author=user)
        serializer = RecipeSerializer(recipes, many=True)
        return serializer.data

    class Meta:
        model = User
        fields = ('username', 'bio', 'image', 'first_name', 'last_name', 'recipes')



class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'bio', 'image', 'first_name', 'last_name']


class FollowUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'follow']

    def update(self, instance, validated_data):
        follower_user_id = validated_data.get('follow')
        if follower_user_id:
            followed_user = User.objects.get(id=follower_user_id)
            if followed_user != instance:
                instance.following.remove(followed_user)
            else:
                instance.following.add(followed_user)
        return instance


class RegisterEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email']

class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = ['token']


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=255)
    password = serializers.CharField(max_length=15, min_length=8, write_only=True)
    password_confirm = serializers.CharField(max_length=15, min_length=8, write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(**validated_data)

class RegisterPersonalInfoSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    birth_date = serializers.DateField()
    email = serializers.EmailField(required=True)

    def update(self, instance, validated_data):
        try:
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)
            instance.birth_date = validated_data.get('birth_date', instance.birth_date)
            instance.email = validated_data.get('email', instance.email)
            instance.save()
        except AttributeError:
            pass
        return instance


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=16, min_length=8, write_only=True
    )
    token = serializers.SerializerMethodField()

    def get_token(self, obj):
        user = User.objects.get(email=obj['email'])
        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }

    class Meta:
        model = User
        fields = ['email', 'password', 'token']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Пользователя не существует, попробуй снова')

        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

        return {
            'email': user.email,
            'tokens': user.tokens,
        }

