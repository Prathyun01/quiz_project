/**
 * Quiz Timer Management
 * Handles countdown timer, auto-save, and time-based quiz submission
 */

class QuizTimer {
    constructor(timeLimit, attemptId, autoSubmitCallback) {
        this.timeLimit = timeLimit; // in seconds
        this.timeRemaining = timeLimit;
        this.attemptId = attemptId;
        this.autoSubmitCallback = autoSubmitCallback;
        this.timerInterval = null;
        this.isPaused = false;
        this.warningShown = false;
        this.criticalWarningShown = false;
        this.init();
    }

    init() {
        this.createTimerElements();
        this.bindEvents();
        this.updateDisplay();
        this.start();
    }

    createTimerElements() {
        // Create floating timer widget if it doesn't exist
        if (!document.getElementById('quiz-timer-widget')) {
            const timerWidget = document.createElement('div');
            timerWidget.id = 'quiz-timer-widget';
            timerWidget.className = 'quiz-timer-widget';
            timerWidget.innerHTML = `
                <div class="timer-content">
                    <div class="timer-icon">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="timer-display">
                        <span id="timer-minutes">00</span>:<span id="timer-seconds">00</span>
                    </div>
                    <div class="timer-progress">
                        <div class="timer-progress-bar" id="timer-progress-bar"></div>
                    </div>
                    <div class="timer-controls">
                        <button id="timer-pause" class="timer-btn" title="Pause Timer">
                            <i class="fas fa-pause"></i>
                        </button>
                        <button id="timer-info" class="timer-btn" title="Timer Info">
                            <i class="fas fa-info"></i>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(timerWidget);
        }
    }

    bindEvents() {
        // Pause/Resume button
        const pauseBtn = document.getElementById('timer-pause');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.togglePause());
        }

        // Info button
        const infoBtn = document.getElementById('timer-info');
        if (infoBtn) {
            infoBtn.addEventListener('click', () => this.showTimeInfo());
        }

        // Page visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });

        // Prevent accidental page close
        window.addEventListener('beforeunload', (e) => {
            if (this.timerInterval && this.timeRemaining > 0) {
                e.preventDefault();
                e.returnValue = 'Quiz in progress. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    start() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        this.timerInterval = setInterval(() => {
            if (!this.isPaused) {
                this.tick();
            }
        }, 1000);

        this.updatePauseButton();
    }

    tick() {
        this.timeRemaining--;
        this.updateDisplay();
        this.checkWarnings();
        
        if (this.timeRemaining <= 0) {
            this.timeUp();
        }
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        
        const minutesEl = document.getElementById('timer-minutes');
        const secondsEl = document.getElementById('timer-seconds');
        const progressBar = document.getElementById('timer-progress-bar');
        
        if (minutesEl) minutesEl.textContent = minutes.toString().padStart(2, '0');
        if (secondsEl) secondsEl.textContent = seconds.toString().padStart(2, '0');
        
        // Update progress bar
        if (progressBar) {
            const percentage = (this.timeRemaining / this.timeLimit) * 100;
            progressBar.style.width = percentage + '%';
            
            // Change colors based on time remaining
            if (percentage <= 10) {
                progressBar.className = 'timer-progress-bar critical';
            } else if (percentage <= 25) {
                progressBar.className = 'timer-progress-bar warning';
            } else {
                progressBar.className = 'timer-progress-bar normal';
            }
        }

        // Update widget appearance
        const widget = document.getElementById('quiz-timer-widget');
        if (widget) {
            widget.classList.remove('warning', 'critical');
            if (this.timeRemaining <= 60) {
                widget.classList.add('critical');
            } else if (this.timeRemaining <= 300) {
                widget.classList.add('warning');
            }
        }
    }

    checkWarnings() {
        // 5 minute warning
        if (this.timeRemaining === 300 && !this.warningShown) {
            this.showWarning('5 minutes remaining!', 'warning');
            this.warningShown = true;
        }
        
        // 1 minute critical warning
        if (this.timeRemaining === 60 && !this.criticalWarningShown) {
            this.showWarning('Only 1 minute left!', 'critical');
            this.criticalWarningShown = true;
        }

        // Final 10 seconds countdown
        if (this.timeRemaining <= 10 && this.timeRemaining > 0) {
            this.showCountdown(this.timeRemaining);
        }
    }

    showWarning(message, type) {
        const notification = document.createElement('div');
        notification.className = `timer-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
        
        // Manual dismiss
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    showCountdown(seconds) {
        const countdown = document.createElement('div');
        countdown.className = 'timer-countdown';
        countdown.textContent = seconds;
        countdown.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 4rem;
            font-weight: bold;
            color: #ff4757;
            z-index: 10000;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            animation: countdownPulse 1s ease-out;
        `;
        
        document.body.appendChild(countdown);
        setTimeout(() => countdown.remove(), 1000);
    }

    togglePause() {
        this.isPaused = !this.isPaused;
        this.updatePauseButton();
        
        if (this.isPaused) {
            this.showNotification('Timer paused', 'info');
        } else {
            this.showNotification('Timer resumed', 'info');
        }
    }

    updatePauseButton() {
        const pauseBtn = document.getElementById('timer-pause');
        if (pauseBtn) {
            const icon = pauseBtn.querySelector('i');
            if (this.isPaused) {
                icon.className = 'fas fa-play';
                pauseBtn.title = 'Resume Timer';
            } else {
                icon.className = 'fas fa-pause';
                pauseBtn.title = 'Pause Timer';
            }
        }
    }

    showTimeInfo() {
        const elapsed = this.timeLimit - this.timeRemaining;
        const elapsedMinutes = Math.floor(elapsed / 60);
        const elapsedSeconds = elapsed % 60;
        const remainingMinutes = Math.floor(this.timeRemaining / 60);
        const remainingSeconds = this.timeRemaining % 60;
        
        const info = `
            Time Information:
            • Elapsed: ${elapsedMinutes}:${elapsedSeconds.toString().padStart(2, '0')}
            • Remaining: ${remainingMinutes}:${remainingSeconds.toString().padStart(2, '0')}
            • Total: ${Math.floor(this.timeLimit / 60)}:${(this.timeLimit % 60).toString().padStart(2, '0')}
        `;
        
        alert(info);
    }

    handlePageHidden() {
        // Log the time when page becomes hidden
        this.hiddenTime = Date.now();
    }

    handlePageVisible() {
        // Adjust timer if page was hidden for too long
        if (this.hiddenTime) {
            const hiddenDuration = Math.floor((Date.now() - this.hiddenTime) / 1000);
            if (hiddenDuration > 5) { // More than 5 seconds hidden
                this.showNotification(`Page was hidden for ${hiddenDuration}s`, 'warning');
            }
            this.hiddenTime = null;
        }
    }

    timeUp() {
        clearInterval(this.timerInterval);
        this.timerInterval = null;
        
        // Show time up notification
        this.showNotification('Time is up! Quiz will be submitted automatically.', 'critical');
        
        // Auto-submit after 3 seconds
        setTimeout(() => {
            if (this.autoSubmitCallback) {
                this.autoSubmitCallback();
            }
        }, 3000);
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `quiz-notification ${type}`;
        notification.innerHTML = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
        `;
        
        const colors = {
            info: '#3498db',
            warning: '#f39c12',
            critical: '#e74c3c'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    destroy() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        
        const widget = document.getElementById('quiz-timer-widget');
        if (widget) {
            widget.remove();
        }
    }
}

// Export for use in other scripts
window.QuizTimer = QuizTimer;
