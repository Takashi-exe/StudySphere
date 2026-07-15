from django.contrib import admin
from .models import FlashcardDeck, Flashcard

class FlashcardInline(admin.TabularInline):
    model = Flashcard
    extra = 1

@admin.register(FlashcardDeck)
class FlashcardDeckAdmin(admin.ModelAdmin):
    inlines = [FlashcardInline]
    list_display = ('title', 'group', 'created_by', 'created_at')
    list_filter = ('group', 'created_by')
    search_fields = ('title',)