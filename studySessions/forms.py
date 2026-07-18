from django import forms
from .models import StudySession, SessionPost, SessionResource

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['title', 'description', 'duration_minutes']

class SessionPostForm(forms.ModelForm):
    class Meta:
        model = SessionPost
        fields = ['content']

class SessionResourceForm(forms.ModelForm):
    class Meta:
        model = SessionResource
        fields = ['resource_type', 'file', 'link_url', 'title']

    def clean(self):
        cleaned_data = super().clean()
        resource_type = cleaned_data.get('resource_type')
        file = cleaned_data.get('file')
        link_url = cleaned_data.get('link_url')

        if resource_type == 'file':
            if not file:
                self.add_error('file', 'This field is required for file resources.')
            if link_url:
                self.add_error('link_url', 'This field must be blank for file resources.')
        elif resource_type == 'link':
            if not link_url:
                self.add_error('link_url', 'This field is required for link resources.')
            if file:
                self.add_error('file', 'This field must be blank for link resources.')
        
        return cleaned_data