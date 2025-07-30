/**
 * Admin Quiz Management JavaScript
 * Handles dynamic forms, validation, and UI interactions
 */

class AdminQuizManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupFormValidation();
        this.setupDynamicForms();
        this.setupUIEnhancements();
        this.setupConfirmations();
        this.initializeTooltips();
    }

    setupFormValidation() {
        // Quiz form validation
        const quizForms = document.querySelectorAll('.quiz-form');
        quizForms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateQuizForm(e, form));
        });

        // Question form validation
        const questionForms = document.querySelectorAll('.question-form');
        questionForms.forEach(form => {
            form.addEventListener('submit', (e) => this.validateQuestionForm(e, form));
        });
    }

    validateQuizForm(event, form) {
        const title = form.querySelector('input[name="title"]');
        const description = form.querySelector('textarea[name="description"]');
        const timeLimit = form.querySelector('input[name="time_limit"]');

        let isValid = true;
        let errors = [];

        // Title validation
        if (!title.value.trim() || title.value.length < 5) {
            errors.push('Quiz title must be at least 5 characters long');
            this.highlightField(title, 'error');
            isValid = false;
        } else {
            this.highlightField(title, 'success');
        }

        // Description validation
        if (!description.value.trim() || description.value.length < 20) {
            errors.push('Quiz description must be at least 20 characters long');
            this.highlightField(description, 'error');
            isValid = false;
        } else {
            this.highlightField(description, 'success');
        }

        // Time limit validation
        if (timeLimit.value < 5 || timeLimit.value > 180) {
            errors.push('Time limit must be between 5 and 180 minutes');
            this.highlightField(timeLimit, 'error');
            isValid = false;
        } else {
            this.highlightField(timeLimit, 'success');
        }

        if (!isValid) {
            event.preventDefault();
            this.showValidationErrors(errors);
        } else {
            this.showSubmissionLoader(form);
        }
    }

    validateQuestionForm(event, form) {
        const questionText = form.querySelector('textarea[name="question_text"]');
        const choices = form.querySelectorAll('input[name*="choice_text"]');
        const correctAnswers = form.querySelectorAll('input[name*="is_correct"]:checked');

        let isValid = true;
        let errors = [];

        // Question text validation
        if (!questionText.value.trim() || questionText.value.length < 10) {
            errors.push('Question text must be at least 10 characters long');
            this.highlightField(questionText, 'error');
            isValid = false;
        } else {
            this.highlightField(questionText, 'success');
        }

        // Choices validation
        let validChoices = 0;
        choices.forEach(choice => {
            if (choice.value.trim()) {
                validChoices++;
                this.highlightField(choice, 'success');
            } else {
                this.highlightField(choice, 'error');
            }
        });

        if (validChoices < 2) {
            errors.push('At least 2 answer choices are required');
            isValid = false;
        }

        // Correct answer validation
        if (correctAnswers.length === 0) {
            errors.push('At least one correct answer must be selected');
            isValid = false;
        }

        if (!isValid) {
            event.preventDefault();
            this.showValidationErrors(errors);
        } else {
            this.showSubmissionLoader(form);
        }
    }

    setupDynamicForms() {
        // Dynamic choice addition
        const addChoiceButtons = document.querySelectorAll('.add-choice-btn');
        addChoiceButtons.forEach(btn => {
            btn.addEventListener('click', () => this.addChoiceField());
        });

        // Choice deletion
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-choice')) {
                this.deleteChoiceField(e.target);
            }
        });

        // Slug generation
        const nameFields = document.querySelectorAll('input[name="name"]');
        nameFields.forEach(field => {
            field.addEventListener('input', (e) => {
                const slugField = document.querySelector('input[name="slug"]');
                if (slugField) {
                    slugField.value = this.generateSlug(e.target.value);
                }
            });
        });
    }

    addChoiceField() {
        const choiceContainer = document.getElementById('choice-formset');
        const totalForms = document.querySelector('input[name$="TOTAL_FORMS"]');
        const formIndex = parseInt(totalForms.value);

        const choiceHtml = `
            <div class="choice-editor" data-form-index="${formIndex}">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h6><i class="fas fa-circle"></i> Choice ${formIndex + 1}</h6>
                    <button type="button" class="btn btn-sm btn-outline-danger delete-choice">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
                
                <div class="row">
                    <div class="col-md-8">
                        <label for="id_form-${formIndex}-choice_text">Choice text:</label>
                        <input type="text" name="form-${formIndex}-choice_text" 
                               class="form-control" id="id_form-${formIndex}-choice_text"
                               required>
                    </div>
                    <div class="col-md-2">
                        <label for="id_form-${formIndex}-order">Order:</label>
                        <input type="number" name="form-${formIndex}-order" 
                               class="form-control" id="id_form-${formIndex}-order" 
                               value="${formIndex + 1}">
                    </div>
                    <div class="col-md-2">
                        <div class="form-check mt-4">
                            <input type="checkbox" name="form-${formIndex}-is_correct" 
                                   class="form-check-input" id="id_form-${formIndex}-is_correct">
                            <label class="form-check-label" for="id_form-${formIndex}-is_correct">
                                Correct Answer
                            </label>
                        </div>
                    </div>
                </div>
                
                <div class="mt-3">
                    <label for="id_form-${formIndex}-explanation">Explanation:</label>
                    <textarea name="form-${formIndex}-explanation" class="form-control" 
                              id="id_form-${formIndex}-explanation" rows="2"></textarea>
                </div>
                
                <input type="hidden" name="form-${formIndex}-id" id="id_form-${formIndex}-id">
            </div>
        `;

        choiceContainer.insertAdjacentHTML('beforeend', choiceHtml);
        totalForms.value = formIndex + 1;

        // Animate new choice
        const newChoice = choiceContainer.lastElementChild;
        newChoice.style.opacity = '0';
        newChoice.style.transform = 'translateY(20px)';
        setTimeout(() => {
            newChoice.style.transition = 'all 0.3s ease';
            newChoice.style.opacity = '1';
            newChoice.style.transform = 'translateY(0)';
        }, 10);
    }

    deleteChoiceField(button) {
        const choiceDiv = button.closest('.choice-editor');
        const deleteCheckbox = choiceDiv.querySelector('input[name$="-DELETE"]');

        if (deleteCheckbox) {
            // Mark for deletion
            deleteCheckbox.checked = true;
            choiceDiv.classList.add('to-delete');
            button.innerHTML = '<i class="fas fa-undo"></i> Undo';
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-outline-warning');
            button.onclick = () => this.undoDeleteChoice(button);
        } else {
            // Remove from DOM with animation
            choiceDiv.style.transition = 'all 0.3s ease';
            choiceDiv.style.opacity = '0';
            choiceDiv.style.transform = 'translateX(-100%)';
            setTimeout(() => choiceDiv.remove(), 300);
        }
    }

    undoDeleteChoice(button) {
        const choiceDiv = button.closest('.choice-editor');
        const deleteCheckbox = choiceDiv.querySelector('input[name$="-DELETE"]');

        deleteCheckbox.checked = false;
        choiceDiv.classList.remove('to-delete');
        button.innerHTML = '<i class="fas fa-trash"></i> Delete';
        button.classList.remove('btn-outline-warning');
        button.classList.add('btn-outline-danger');
        button.onclick = () => this.deleteChoiceField(button);
    }

    setupUIEnhancements() {
        // Animate cards on scroll
        this.setupScrollAnimations();
        
        // Setup tooltips
        this.initializeTooltips();
        
        // Setup color picker enhancements
        this.setupColorPickers();
        
        // Setup file upload previews
        this.setupFilePreview();
    }

    setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        const animatedElements = document.querySelectorAll('.stat-card, .quick-action-card, .quiz-management-card');
        animatedElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
            element.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
            observer.observe(element);
        });
    }

    setupColorPickers() {
        const colorInputs = document.querySelectorAll('input[type="color"]');
        colorInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const preview = document.querySelector('.color-preview');
                if (preview) {
                    preview.style.backgroundColor = e.target.value;
                }
            });
        });
    }

    setupFilePreview() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file && file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        let preview = document.querySelector('.image-preview');
                        if (!preview) {
                            preview = document.createElement('div');
                            preview.className = 'image-preview mt-3';
                            input.parentNode.appendChild(preview);
                        }
                        preview.innerHTML = `
                            <img src="${e.target.result}" 
                                 style="max-width: 200px; max-height: 200px; border-radius: 10px;" 
                                 alt="Preview">
                        `;
                    };
                    reader.readAsDataURL(file);
                }
            });
        });
    }

    setupConfirmations() {
        // Delete confirmations
        const deleteButtons = document.querySelectorAll('.btn-danger[href*="delete"]');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });

        // Publish confirmations
        const publishButtons = document.querySelectorAll('.publish-btn');
        publishButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.textContent.includes('Publish') ? 'publish' : 'unpublish';
                if (!confirm(`Are you sure you want to ${action} this quiz?`)) {
                    e.preventDefault();
                }
            });
        });
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Utility methods
    highlightField(field, type) {
        field.classList.remove('is-valid', 'is-invalid');
        if (type === 'success') {
            field.classList.add('is-valid');
        } else if (type === 'error') {
            field.classList.add('is-invalid');
        }
    }

    showValidationErrors(errors) {
        const errorContainer = document.createElement('div');
        errorContainer.className = 'alert alert-danger alert-dismissible fade show';
        errorContainer.innerHTML = `
            <h6><i class="fas fa-exclamation-triangle"></i> Please fix the following errors:</h6>
            <ul class="mb-0">
                ${errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const form = document.querySelector('.form-container-admin');
        form.insertBefore(errorContainer, form.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            errorContainer.remove();
        }, 5000);
    }

    showSubmissionLoader(form) {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            const originalText = submitBtn.innerHTML || submitBtn.value;
            submitBtn.disabled = true;
            
            if (submitBtn.tagName === 'BUTTON') {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            } else {
                submitBtn.value = 'Processing...';
            }
            
            // Restore button after 10 seconds (failsafe)
            setTimeout(() => {
                submitBtn.disabled = false;
                if (submitBtn.tagName === 'BUTTON') {
                    submitBtn.innerHTML = originalText;
                } else {
                    submitBtn.value = originalText;
                }
            }, 10000);
        }
    }

    generateSlug(text) {
        return text
            .toLowerCase()
            .replace(/[^a-z0-9 -]/g, '')
            .replace(/\s+/g, '-')
            .replace(/-+/g, '-')
            .trim('-');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminQuizManager();
});

// Export for use in other scripts
window.AdminQuizManager = AdminQuizManager;
