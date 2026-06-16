from django.urls import path
from . import views

urlpatterns = [
    path('', views.root_view, name='root'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.profile_view, name='view_profile'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('search/', views.user_search, name='user_search'),
    path('api/user_search/', views.api_user_search, name='api_user_search'),
    path('friends/', views.friends_list, name='friends_list'),
    path('friend-requests/', views.friend_requests_list, name='friend_requests_list'),
    path('friend_request/send/<str:to_user_username>/', views.send_friend_request, name='send_friend_request'),
    path('friend_request/accept/<str:from_user_username>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend_request/reject/<str:from_user_username>/', views.reject_friend_request, name='reject_friend_request'),
    path('unfriend/<str:username>/', views.unfriend_user, name='unfriend_user'),
    path('block/<str:username>/', views.block_user, name='block_user'),
]
