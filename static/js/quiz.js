/**
 * Enhanced Quiz Taking Interface for AI Quiz App
 * Compatible with both user and admin quiz systems
 */

class QuizManager {
    constructor() {
        this.currentQuestion = 1;
        this.totalQuestions = 0;
        this.timeRemaining = 0;
        this.quizStartTime = null;
        this.timerInterval = null;
        this.answers = {};
        this.timeWarningShown = false;
        this.autoSaveInterval = null;
        this.isPreviewMode = false;
        this.init();
    }

    init() {
        // Check if we're in preview mode (admin)
        this.isPreviewMode = document.body.classList.contains('preview-mode') || 
                           document.querySelector('.preview-banner') !== null;
        
        // Get quiz data from page
        this.extractQuizData();
        if (this.totalQuestions > 0) {
            this.setupQuiz();
            this.bindEvents();
            if (!this.isPreviewMode) {
                this.startTimer();
                this.setupAutoSave();
            }
            this.trackProgress();
        }
    }

    extractQuizData() {
        const questionsContainer = document.querySelector('.question-container, .questions-container');
        if (questionsContainer) {
            this.totalQuestions = questionsContainer.querySelectorAll('.question-card').length;
        }

        const timeElement = document.querySelector('[data-time-limit]');
        if (timeElement) {
            this.timeRemaining = parseInt(timeElement.dataset.timeLimit) * 60; // Convert to seconds
        } else {
            // Fallback: try to get from timer display
            const timerDisplay = document.getElementById('time-remaining');
            if (timerDisplay) {
                const timeText = timerDisplay.textContent.trim();
                const matches = timeText.match(/(\d+):(\d+)/);
                if (matches) {
                    this.timeRemaining = (parseInt(matches[1]) * 60) + parseInt(matches[2]);
                }
            }
        }
        
        this.quizStartTime = Date.now();
    }

    setupQuiz() {
        this.updateProgress();
        this.updateNavigation();
        this.loadSavedAnswers();
        this.createQuestionDots();
        this.enhanceAnswerChoices();
    }

    enhanceAnswerChoices() {
        const choices = document.querySelectorAll('.answer-choice');
        choices.forEach((choice, index) => {
            choice.style.animationDelay = `${index * 0.1}s`;
            choice.classList.add('fade-in-up');
            
            // Add ripple effect
            choice.addEventListener('click', (e) => {
                if (!this.isPreviewMode) {
                    this.createRipple(e, choice);
                }
            });
        });
    }

    createRipple(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(240, 147, 251, 0.6);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s ease-out;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }

    bindEvents() {
        // Navigation buttons
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        
        if (prevBtn) prevBtn.addEventListener('click', () => this.previousQuestion());
        if (nextBtn) nextBtn.addEventListener('click', () => this.nextQuestion());
        if (submitBtn) submitBtn.addEventListener('click', () => this.showSubmitModal());

        // Answer selection tracking
        document.addEventListener('change', (e) => {
            if (e.target.type === 'radio' && e.target.name.startsWith('question_')) {
                this.handleAnswerChange(e.target);
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Page visibility (pause timer when tab is hidden)
        if (!this.isPreviewMode) {
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.pauseTimer();
                } else {
                    this.resumeTimer();
                }
            });

            // Prevent accidental navigation
            window.addEventListener('beforeunload', (e) => {
                if (this.timerInterval) {
                    e.preventDefault();
                    e.returnValue = 'Are you sure you want to leave? Your quiz progress will be lost.';
                    return e.returnValue;
                }
            });
        }

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (this.timerInterval && !this.isPreviewMode) {
                e.preventDefault();
                if (confirm('Are you sure you want to leave the quiz? Your progress will be lost.')) {
                    this.endQuiz();
                    window.history.back();
                }
            }
        });

        // Enhanced choice selection
        this.setupChoiceInteractions();
    }

    setupChoiceInteractions() {
        const choices = document.querySelectorAll('.answer-choice');
        choices.forEach(choice => {
            choice.addEventListener('mouseenter', () => {
                if (!choice.classList.contains('selected')) {
                    choice.style.transform = 'translateX(5px) scale(1.01)';
                }
            });
            
            choice.addEventListener('mouseleave', () => {
                if (!choice.classList.contains('selected')) {
                    choice.style.transform = 'translateX(0) scale(1)';
                }
            });
        });
    }

    handleAnswerChange(input) {
        const questionId = input.name.replace('question_', '');
        const choiceId = input.value;
        
        // Store answer
        this.answers[questionId] = choiceId;
        
        // Update UI
        const questionCard = input.closest('.question-card');
        const choices = questionCard.querySelectorAll('.answer-choice');
        
        choices.forEach(choice => {
            choice.classList.remove('selected');
            choice.style.transform = 'translateX(0) scale(1)';
        });
        
        const selectedChoice = input.closest('.answer-choice');
        selectedChoice.classList.add('selected');
        selectedChoice.style.transform = 'translateX(15px) scale(1.03)';
        
        // Add visual feedback
        this.showAnswerFeedback(selectedChoice);
        
        // Update progress
        this.updateProgress();
        
        // Auto-save if not in preview mode
        if (!this.isPreviewMode) {
            this.autoSaveAnswer(questionId, choiceId);
        }
    }

    showAnswerFeedback(choice) {
        const feedback = document.createElement('div');
        feedback.className = 'answer-feedback';
        feedback.innerHTML = '<i class="fas fa-check"></i>';
        feedback.style.cssText = `
            position: absolute;
            top: 10px;
            right: 15px;
            color: var(--quiz-success);
            font-size: 1.2rem;
            animation: feedbackPulse 0.6s ease-out;
        `;
        
        choice.style.position = 'relative';
        choice.appendChild(feedback);
        
        setTimeout(() => feedback.remove(), 600);
    }

    startTimer() {
        if (this.timeRemaining <= 0 || this.isPreviewMode) return;
        
        this.updateTimerDisplay();
        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            // Show warning at 5 minutes
            if (this.timeRemaining === 300 && !this.timeWarningShown) {
                this.showTimeWarning();
                this.timeWarningShown = true;
            }
            
            // Auto-submit when time runs out
            if (this.timeRemaining <= 0) {
                this.timeUp();
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('time-remaining');
        if (!timerElement) return;
        
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        timerElement.textContent = display;
        
        // Add warning class when time is low
        const timerContainer = document.getElementById('timer');
        if (this.timeRemaining <= 300) { // 5 minutes
            timerContainer?.classList.add('warning');
        }
        
        // Add critical class when very low
        if (this.timeRemaining <= 60) { // 1 minute
            timerContainer?.classList.add('critical');
            // Add pulsing effect
            timerContainer.style.animation = 'pulse-timer 1s infinite';
        }
    }

    updateProgress() {
        const answeredCount = Object.keys(this.answers).length;
        const percentage = (answeredCount / this.totalQuestions) * 100;
        
        const progressBar = document.querySelector('.quiz-progress-bar');
        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        
        const progressText = document.getElementById('progress-text');
        if (progressText) {
            progressText.textContent = `${answeredCount} of ${this.totalQuestions} questions answered`;
        }
        
        // Update question dots
        this.updateQuestionDots();
    }

    createQuestionDots() {
        const dotsContainer = document.getElementById('question-dots');
        if (!dotsContainer) return;
        
        dotsContainer.innerHTML = '';
        for (let i = 1; i <= this.totalQuestions; i++) {
            const dot = document.createElement('div');
            dot.className = 'question-dot';
            dot.dataset.question = i;
            dot.addEventListener('click', () => this.goToQuestion(i));
            dotsContainer.appendChild(dot);
        }
    }

    updateQuestionDots() {
        const dots = document.querySelectorAll('.question-dot');
        dots.forEach((dot, index) => {
            const questionNum = index + 1;
            dot.classList.remove('answered', 'current');
            
            if (this.answers[questionNum]) {
                dot.classList.add('answered');
            }
            
            if (questionNum === this.currentQuestion) {
                dot.classList.add('current');
            }
        });
    }

    showTimeWarning() {
        this.showNotification('⏰ 5 minutes remaining!', 'warning', 5000);
        
        // Optional: Show modal warning
        if (confirm('⏰ Only 5 minutes remaining! Would you like to review your answers?')) {
            this.showAnswersReview();
        }
    }

    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `quiz-notification ${type}`;
        notification.innerHTML = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            animation: slideInRight 0.5s ease-out;
        `;
        
        // Set background color based on type
        const colors = {
            info: 'linear-gradient(135deg, var(--quiz-primary), var(--quiz-secondary))',
            warning: 'linear-gradient(135deg, #ff6b6b, #ffa726)',
            success: 'linear-gradient(135deg, var(--quiz-success), #20c997)',
            error: 'linear-gradient(135deg, #ff5252, #f44336)'
        };
        
        notification.style.background = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.5s ease-out';
            setTimeout(() => notification.remove(), 500);
        }, duration);
    }

    autoSaveAnswer(questionId, choiceId) {
        if (this.isPreviewMode) return;
        
        // Debounce auto-save
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveAnswerToServer(questionId, choiceId);
        }, 1000);
    }

    async saveAnswerToServer(questionId, choiceId) {
        try {
            const response = await fetch('/quiz/ajax/save-answer/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    attempt_id: this.getAttemptId(),
                    question_id: questionId,
                    answer: choiceId
                })
            });
            
            if (response.ok) {
                this.showSaveIndicator();
            }
        } catch (error) {
            console.warn('Auto-save failed:', error);
        }
    }

    showSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.innerHTML = '💾 Saved';
        indicator.className = 'save-indicator';
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(40, 167, 69, 0.9);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            z-index: 9999;
            animation: fadeInOut 2s ease-out;
        `;
        
        document.body.appendChild(indicator);
        setTimeout(() => indicator.remove(), 2000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    getAttemptId() {
        return document.querySelector('[data-attempt-id]')?.dataset.attemptId || '';
    }

    // Enhanced navigation methods
    nextQuestion() {
        if (this.currentQuestion < this.totalQuestions) {
            this.hideCurrentQuestion();
            this.currentQuestion++;
            this.showCurrentQuestion();
        }
        this.updateNavigation();
    }

    previousQuestion() {
        if (this.currentQuestion > 1) {
            this.hideCurrentQuestion();
            this.currentQuestion--;
            this.showCurrentQuestion();
        }
        this.updateNavigation();
    }

    goToQuestion(questionNum) {
        if (questionNum >= 1 && questionNum <= this.totalQuestions) {
            this.hideCurrentQuestion();
            this.currentQuestion = questionNum;
            this.showCurrentQuestion();
        }
        this.updateNavigation();
    }

    hideCurrentQuestion() {
        const currentCard = document.querySelector(`[data-question="${this.currentQuestion}"]`);
        if (currentCard) {
            currentCard.style.animation = 'slideOutLeft 0.3s ease-out';
            setTimeout(() => {
                currentCard.style.display = 'none';
            }, 300);
        }
    }

    showCurrentQuestion() {
        const targetCard = document.querySelector(`[data-question="${this.currentQuestion}"]`);
        if (targetCard) {
            targetCard.style.display = 'block';
            targetCard.style.animation = 'slideInRight 0.3s ease-out';
        }
    }

    updateNavigation() {
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');
        
        if (prevBtn) {
            prevBtn.disabled = this.currentQuestion === 1;
        }
        
        if (nextBtn) {
            nextBtn.style.display = this.currentQuestion === this.totalQuestions ? 'none' : 'inline-block';
        }
        
        if (submitBtn) {
            submitBtn.style.display = this.currentQuestion === this.totalQuestions ? 'inline-block' : 'none';
        }
    }

    // Utility methods
    pauseTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    resumeTimer() {
        if (!this.timerInterval && this.timeRemaining > 0 && !this.isPreviewMode) {
            this.startTimer();
        }
    }

    handleKeyboard(event) {
        if (this.isPreviewMode) return;
        
        switch(event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousQuestion();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextQuestion();
                break;
            case 'Enter':
                if (event.ctrlKey) {
                    event.preventDefault();
                    this.showSubmitModal();
                }
                break;
        }
    }

    showSubmitModal() {
        if (this.isPreviewMode) {
            alert('This is preview mode. The quiz cannot be submitted.');
            return;
        }
        
        const answeredCount = Object.keys(this.answers).length;
        const unansweredCount = this.totalQuestions - answeredCount;
        
        let message = `You have answered ${answeredCount} out of ${this.totalQuestions} questions.`;
        if (unansweredCount > 0) {
            message += `\n\n${unansweredCount} questions remain unanswered.`;
        }
        message += '\n\nAre you sure you want to submit your quiz?';
        
        if (confirm(message)) {
            this.submitQuiz();
        }
    }

    submitQuiz() {
        if (this.isPreviewMode) return;
        
        this.pauseTimer();
        const form = document.getElementById('quiz-form');
        if (form) {
            form.submit();
        }
    }

    timeUp() {
        this.pauseTimer();
        alert('⏰ Time is up! Your quiz will be submitted automatically.');
        this.submitQuiz();
    }

    loadSavedAnswers() {
        // Load any previously saved answers
        const savedAnswers = document.querySelectorAll('input[type="radio"]:checked');
        savedAnswers.forEach(input => {
            const questionId = input.name.replace('question_', '');
            this.answers[questionId] = input.value;
            
            const choice = input.closest('.answer-choice');
            if (choice) {
                choice.classList.add('selected');
            }
        });
    }

    trackProgress() {
        if (this.isPreviewMode) return;
        
        // Track time spent on each question
        this.questionStartTime = Date.now();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on a quiz page
    if (document.querySelector('.question-card') || document.querySelector('.quiz-container')) {
        new QuizManager();
    }
});

// Add required CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInOut {
        0%, 100% { opacity: 0; transform: translateY(20px); }
        20%, 80% { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideOutRight {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100%); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-100%); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideOutLeft {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(-100%); }
    }
    
    @keyframes ripple {
        to { transform: scale(4); opacity: 0; }
    }
    
    @keyframes feedbackPulse {
        0% { opacity: 0; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out both;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Export for use in other scripts
window.QuizManager = QuizManager;
