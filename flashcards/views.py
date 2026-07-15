from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from groups.models import StudyGroup
from .models import FlashcardDeck, Flashcard
from .forms import DeckForm

@login_required
def deck_list(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    decks = FlashcardDeck.objects.filter(group=group)
    return render(request, 'flashcards/deck_list.html', {'group': group, 'decks': decks})

@login_required
def create_deck(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    CardFormSet = inlineformset_factory(FlashcardDeck, Flashcard, fields=('front', 'back'), extra=1, can_delete=True)

    if request.method == 'POST':
        form = DeckForm(request.POST)
        if form.is_valid():
            deck = form.save(commit=False)
            deck.group = group
            deck.created_by = request.user
            deck.save()
            formset = CardFormSet(request.POST, instance=deck)
            if formset.is_valid():
                formset.save()
                return redirect('flashcards:deck_detail', group_id=group.id, deck_id=deck.id)
    else:
        form = DeckForm()
        formset = CardFormSet(instance=FlashcardDeck())
    return render(request, 'flashcards/deck_form.html', {'group': group, 'form': form, 'formset': formset})

@login_required
def edit_deck(request, group_id, deck_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    deck = get_object_or_404(FlashcardDeck, id=deck_id, group=group)
    CardFormSet = inlineformset_factory(FlashcardDeck, Flashcard, fields=('front', 'back'), extra=1, can_delete=True)

    if request.method == 'POST':
        form = DeckForm(request.POST, instance=deck)
        formset = CardFormSet(request.POST, instance=deck)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('flashcards:deck_detail', group_id=group.id, deck_id=deck.id)
    else:
        form = DeckForm(instance=deck)
        formset = CardFormSet(instance=deck)
    return render(request, 'flashcards/deck_form.html', {'group': group, 'form': form, 'formset': formset, 'deck': deck})

@login_required
def deck_detail(request, group_id, deck_id):
    deck = get_object_or_404(FlashcardDeck, id=deck_id, group_id=group_id)
    return render(request, 'flashcards/deck_detail.html', {'deck': deck})

@login_required
def play_deck(request, group_id, deck_id):
    deck = get_object_or_404(FlashcardDeck.objects.prefetch_related('cards'), id=deck_id, group_id=group_id)
    cards = list(deck.cards.values('id', 'front', 'back'))
    return render(request, 'flashcards/play.html', {'deck': deck, 'cards_json': cards})