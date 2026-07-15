from django.urls import path
from . import views

app_name = 'flashcards'

urlpatterns = [
    path('groups/<uuid:group_id>/flashcards/', views.deck_list, name='deck_list'),
    path('groups/<uuid:group_id>/flashcards/create/', views.create_deck, name='create_deck'),
    path('groups/<uuid:group_id>/flashcards/<uuid:deck_id>/', views.deck_detail, name='deck_detail'),
    path('groups/<uuid:group_id>/flashcards/<uuid:deck_id>/play/', views.play_deck, name='play_deck'),
    path('groups/<uuid:group_id>/flashcards/<uuid:deck_id>/edit/', views.edit_deck, name='edit_deck'),
]