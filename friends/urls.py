from django.urls import path
from .views import FriendListView

app_name = 'friends'

urlpatterns = [
    path('', FriendListView.as_view(), name='friend_list'),
]