from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('create/', views.create_group, name='create_group'),
    path('<uuid:group_id>/', views.group_detail, name='group_detail'),
    path('join/<uuid:invite_code>/', views.join_group, name='join_group'),
    path('<uuid:group_id>/upload/', views.upload_resource, name='upload_resource'),
    path('<uuid:group_id>/leave/', views.leave_group, name='leave_group'),
    path('<uuid:group_id>/members/add/', views.add_member, name='add_member'),
    path('<uuid:group_id>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('<uuid:group_id>/members/<int:user_id>/promote/', views.promote_member, name='promote_member'),
    path('<uuid:group_id>/members/<int:user_id>/demote/', views.demote_member, name='demote_member'),
]