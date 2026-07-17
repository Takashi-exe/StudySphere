from django.urls import path
from . import views

app_name = 'studySessions'

urlpatterns = [
    path('', views.study_sessions_view, name='study_sessions'),
    path('session_detail/<uuid:session_id>/', views.session_detail, name='session_detail'),
    path('close_session/<uuid:session_id>/', views.close_session, name='close_session'),
    path('start/<uuid:group_id>/', views.start_session, name='start_session'),
    path('history/<uuid:group_id>/', views.session_history, name='session_history'),
]