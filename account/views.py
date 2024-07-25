from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer, FollowUserSerializer, UserProfileSerializer, UserProfileUpdateSerializer
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
import os
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_bytes, smart_str, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .serializers import RegistrationSerializer, EmailVerificationSerializer, RegisterPersonalInfoSerializer, LoginSerializer
from django.http import HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import Util
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
import jwt
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, APIException
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils.http import urlsafe_base64_encode

class UserListAPIView(APIView):
    @swagger_auto_schema(
        tags=['Users'],
        operation_description="This endpoint is for getting a list of all users.",
        responses={
            200: UserSerializer(many=True),
            401: "Unauthorized. User not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="This endpoint enables users search for users by username.",
        manual_parameters=[
            openapi.Parameter('search_query', openapi.IN_QUERY, description="Search query string for username.",
                              type=openapi.TYPE_STRING),
        ],
        responses={
            200: UserSerializer(many=True),
            400: "Bad request. Invalid input data.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request):
        search_query = request.data.get('search_query', None)
        if search_query:
            users = User.objects.filter(username__icontains=search_query)
        else:
            users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

class MyPageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="This endpoint is for getting current user's profile data including recipes which was posted.",
        responses={200: UserProfileSerializer()},
    )

    def get(self, request, *args, **kwargs):
        try:
            profile = User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            return Response({'data': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        profile_info = UserProfileSerializer(profile)
        content = {"Profile Info": profile_info.data}
        return Response(content, status=status.HTTP_200_OK)
class MyPageUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="This endpoint is for updating current user's profile data.",
        responses={200: UserProfileUpdateSerializer()},
    )

    def put(self, request, *args, **kwargs):
        try:
            user = request.user
            serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'data': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class FollowUserAPIView(APIView):
    permission_classes = [IsAuthenticated,]
    @swagger_auto_schema(
        tags=['Users'],
        operation_description="This endpoint is for following a user.",
        responses={
            200: "User followed successfully.",
            400: "Bad request. Invalid input data.",
            404: "User not found.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            following_user = User.objects.all().get(id=kwargs['user_id'])
        except:
            return Response({'data': 'Page not found'}, status=status.HTTP_404_NOT_FOUND)

        follower = request.user

        if follower == following_user:
            return Response({"message": "You can't follow yourself"}, status=status.HTTP_400_BAD_REQUEST)

        if follower in following_user.follow.all():
            return Response({"message": "You are already following this user"}, status=status.HTTP_400_BAD_REQUEST)

        following_user.follow.add(follower)
        follower.following.add(following_user)

        return Response({"message": "You are now following this user"}, status=status.HTTP_201_CREATED)

class UnfollowUserAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    @swagger_auto_schema(
        tags=['Users'],
        operation_description="Unfollow a user.",
        responses={
            200: "User unfollowed successfully.",
            400: "Bad request. Invalid input data.",
            404: "User not found.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            following_user = User.objects.get(id=kwargs['user_id'])
        except:
            return Response({'data': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        follower = request.user

        if follower == following_user:
            return Response({"message": "You can't unfollow yourself"}, status=status.HTTP_400_BAD_REQUEST)

        if follower not in following_user.follow.all():
            return Response({"message": "You are not following this user"}, status=status.HTTP_400_BAD_REQUEST)
        following_user.follow.remove(follower)
        follower.following.remove(following_user)

        return Response({"message": "You have unfollowed this user"}, status=status.HTTP_200_OK)

class CustomRedirect(HttpResponseRedirect):
    allowed_schemes = [os.environ.get('APP_SCHEME'), 'http', 'https']

class RegisterEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegistrationSerializer

    @swagger_auto_schema(
        request_body=RegistrationSerializer,
        responses={201: 'User registered successfully', 400: 'Invalid data'},
        operation_description="This endpoint allows a user to register an account. "
                              "A verification email with a link is sent to the provided email address."
    )

    def post(self, request):
        serializer = self.serializer_class(data=request.data) # создание экземляра класса сериализатора
        serializer.is_valid(raise_exception=True)
        user = serializer.save() #

        token = RefreshToken.for_user(user) # создание нового токена доступа для конкретного пользователя
        token_payload = {'email': user.email} # создает словарь, который будет содержать информацию , которая будет добавлена к токену
        token['email'] = user.email  # значение адрес электронной почты
        token['payload'] = token_payload # значение дополнительных данных
        token = str(token.access_token) # преобразует объект токена в строку

        current_site = get_current_site(request).domain  # получение домена нашего сайта, на котором работает приложение
        relative_link = reverse('email-verify') # позволяет получить url адрес
        absurl = 'http://' + current_site + relative_link + "?token=" + token
        email_body = 'Hi ' + ' Use the link below to verify your email \n' + absurl
        data = {'email_body': email_body, 'to_email': user.email, 'email_subject': 'Verify your email'}

        try:
            Util.send_email(data)
        except Exception as e:
            print(f"Failed to send verification email to {user.email}: {e}")
            return Response({'message': 'Failed to send verification email.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        token_payload = {'email': user.email}

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class VerifyEmail(APIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="The verification token.")
        ],
        responses={200: 'Email verified successfully', 400: 'Invalid token'}
    )
    def get(self, request):
        token = request.GET.get('token')
        User = get_user_model()  # Получение модели пользователя

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['user_id']
            email = payload['email']
            user = User.objects.get(id=user_id, email=email)
            if not user:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            if not user.is_verified:
                user.is_verified = True
                user.save()

            return redirect(reverse('register-personal-info') + f'?email={email}')
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Activation link has expired'}, status=status.HTTP_400_BAD_REQUEST)
        except (jwt.exceptions.DecodeError, User.DoesNotExist):
            return Response({'error': 'Invalid activation link'}, status=status.HTTP_400_BAD_REQUEST)

class RegisterPersonalInfoView(APIView):
    serializer_class = RegisterPersonalInfoSerializer
    permission_classes = [AllowAny,]

    @swagger_auto_schema(
        tags=['Registration'],
        operation_description="After registration, once we have confirmed our account by mail, we ask the user to enter their personal information",
        request_body=RegisterPersonalInfoSerializer,
        responses={
            200: "Successfully updated user's personal information.",
            400: "Bad request, email mismatch or serializer errors.",
            404: "User not found."
        }
    )

    def put(self, request):
        User = get_user_model()
        user_email = request.GET.get('email')
        user_email = user_email.rstrip('/')
        email_field = request.data.get('email')

        if not user_email or not email_field or user_email != email_field:
            return Response({'error': 'Email mismatch'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email_field)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_400_NOT_FOUND)

        serializer = RegisterPersonalInfoSerializer(user, data=request.data) # используетася для обновления объектов в сериализаторе
        if serializer.is_valid():
            serializer.save()

            return Response(data={"email": user_email}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):

    serializer_class = LoginSerializer
    permission_classes = [AllowAny,]

    @swagger_auto_schema(
        tags=['Authorization'],
        operation_description="Endpoint for user login. Returns a new access token and refresh token.",
        request_body=LoginSerializer,
        responses={
            200: "Successful login. Returns the user's email and tokens.",
            400: "Bad request. Invalid input.",
            401: "Unauthorized. Invalid credentials.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)