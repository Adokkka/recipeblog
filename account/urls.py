from django.urls import path
from .views import RegisterEmailView, VerifyEmail, RegisterPersonalInfoView, LoginAPIView, UserListAPIView, FollowUserAPIView, UnfollowUserAPIView, MyPageAPIView, MyPageUpdateAPIView
from rest_framework_simplejwt.views import (
    TokenRefreshView
)

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),
    path('email-verify/', VerifyEmail.as_view(), name='email-verify'),
    path('register/email/', RegisterEmailView.as_view(), name='email-verification'),
    path('register/personal-info/', RegisterPersonalInfoView.as_view(), name='register-personal-info'),
    path('users/', UserListAPIView.as_view(), name='user-list'),
    path('users/int:user_id/follow/', FollowUserAPIView.as_view(), name='follow_user'),
    path('users/int:user_id/unfollow/', UnfollowUserAPIView.as_view(), name='unfollow_user'),
    path('mypage/', MyPageAPIView.as_view(), name='mypage'),
    path('my-page/update', MyPageUpdateAPIView.as_view(), name='my-page-update'),
]