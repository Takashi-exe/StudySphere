from django import forms
from .models import StudySession, SessionPost

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['title', 'description', 'duration_minutes']

class SessionPostForm(forms.ModelForm):
    class Meta:
        model = SessionPost
        fields = ['content']