document.addEventListener('DOMContentLoaded', () => {
    const gameContainer = document.getElementById('game-container');
    if (!gameContainer) return;

    const progressBar = document.getElementById('progress-bar').firstElementChild;
    const progressText = document.getElementById('progress-text');
    const cardContainer = document.querySelector('.flip-card');
    const cardInner = document.querySelector('.flip-card-inner');
    const cardFront = document.querySelector('.flip-card-front');
    const cardBack = document.querySelector('.flip-card-back');
    const controls = document.getElementById('controls');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const gotItBtn = document.getElementById('got-it-btn');
    const endScreen = document.getElementById('end-screen');
    const scoreEl = document.getElementById('score');
    const totalEl = document.getElementById('total');
    const accuracyEl = document.getElementById('accuracy');
    const missedList = document.getElementById('missed-list');
    const retryMissedBtn = document.getElementById('retry-missed-btn');
    const studyAgainBtn = document.getElementById('study-again-btn');
    const ariaLiveRegion = document.getElementById('aria-live-region');

    let currentCards = [];
    let currentIndex = 0;
    let correctCount = 0;
    let missedCards = [];
    let isFlipped = false;

    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    function startGame(cardsToStudy) {
        currentCards = shuffle([...cardsToStudy]);
        currentIndex = 0;
        correctCount = 0;
        missedCards = [];
        isFlipped = false;
        endScreen.classList.add('hidden');
        gameContainer.querySelector('#progress-bar').classList.remove('hidden');
        progressText.classList.remove('hidden');
        cardContainer.classList.remove('hidden');
        controls.classList.add('hidden');
        showNextCard();
    }

    function showNextCard() {
        if (currentIndex >= currentCards.length) {
            showEndScreen();
            return;
        }
        isFlipped = false;
        cardInner.classList.remove('flipped');
        const card = currentCards[currentIndex];
        cardFront.textContent = card.front;
        cardBack.textContent = card.back;
        updateProgressBar();
        ariaLiveRegion.textContent = `Showing front of card ${currentIndex + 1}.`;
    }

    function flipCard() {
        if (isFlipped) return;
        isFlipped = true;
        cardInner.classList.add('flipped');
        controls.classList.remove('hidden');
        ariaLiveRegion.textContent = `Showing back of card.`;
    }

    function handleGrade(isCorrect) {
        if (isCorrect) {
            correctCount++;
        } else {
            missedCards.push(currentCards[currentIndex]);
        }
        currentIndex++;
        controls.classList.add('hidden');
        showNextCard();
    }

    function updateProgressBar() {
        const percent = ((currentIndex + 1) / currentCards.length) * 100;
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${currentIndex + 1} / ${currentCards.length}`;
    }

    function showEndScreen() {
        gameContainer.querySelector('#progress-bar').classList.add('hidden');
        progressText.classList.add('hidden');
        cardContainer.classList.add('hidden');
        endScreen.classList.remove('hidden');
        scoreEl.textContent = correctCount;
        totalEl.textContent = currentCards.length;
        const accuracy = currentCards.length > 0 ? Math.round((correctCount / currentCards.length) * 100) : 0;
        accuracyEl.textContent = accuracy;
        missedList.innerHTML = '';
        if (missedCards.length > 0) {
            missedCards.forEach(card => {
                const li = document.createElement('li');
                li.className = 'text-sm text-[#958EA0]';
                li.textContent = card.front;
                missedList.appendChild(li);
            });
            document.getElementById('missed-cards').style.display = 'block';
            retryMissedBtn.style.display = 'block';
        } else {
            document.getElementById('missed-cards').style.display = 'none';
            retryMissedBtn.style.display = 'none';
        }
    }

    cardContainer.addEventListener('click', flipCard);
    tryAgainBtn.addEventListener('click', () => handleGrade(false));
    gotItBtn.addEventListener('click', () => handleGrade(true));
    retryMissedBtn.addEventListener('click', () => startGame(missedCards));
    studyAgainBtn.addEventListener('click', () => startGame(cards));

    document.addEventListener('keydown', (e) => {
        if (endScreen.classList.contains('hidden')) {
            if (e.code === 'Space' || e.code === 'Enter') {
                flipCard();
            } else if (isFlipped) {
                if (e.code === 'Digit1' || e.code === 'ArrowLeft') {
                    handleGrade(false);
                } else if (e.code === 'Digit2' || e.code === 'ArrowRight') {
                    handleGrade(true);
                }
            }
        }
    });

    startGame(cards);
});