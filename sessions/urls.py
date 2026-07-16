from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    path('groups/<uuid:group_id>/sessions/create/', views.create_session, name='create_session'),
    path('sessions/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('sessions/<uuid:session_id>/close/', views.close_session, name='close_session'),
    path('sessions/post/<uuid:post_id>/comment/', views.add_comment, name='add_comment'),
    path('groups/<uuid:group_id>/sessions/', views.session_history, name='session_history'),
]