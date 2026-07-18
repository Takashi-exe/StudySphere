from django import forms
from .models import FlashcardDeck

class DeckForm(forms.ModelForm):
    class Meta:
        model = FlashcardDeck
        fields = ['title', 'description']