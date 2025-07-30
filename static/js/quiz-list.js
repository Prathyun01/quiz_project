/**
 * Quiz List Management
 * Handles filtering, pagination, search, and quiz card interactions
 */

class QuizListManager {
    constructor() {
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.currentFilters = {};
        this.searchTimeout = null;
        this.quizCards = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.setupSearch();
        this.setupFilters();
        this.setupPagination();
        this.enhanceQuizCards();
        this.setupInfiniteScroll();
    }

    bindEvents() {
        // Search input
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
        }

        // Filter dropdowns
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', (e) => this.handleFilterChange(e.target.name, e.target.value));
        });

        // Clear filters button
        const clearFiltersBtn = document.querySelector('.clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Sort options
        const sortSelect = document.querySelector('select[name="sort"]');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => this.handleSort(e.target.value));
        }

        // View toggle (grid/list)
        const viewToggle = document.querySelectorAll('.view-toggle');
        viewToggle.forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleView(e.target.dataset.view));
        });
    }

    setupSearch() {
        const searchContainer = document.querySelector('.search-container');
        if (searchContainer) {
            // Add search suggestions
            const suggestionsDiv = document.createElement('div');
            suggestionsDiv.className = 'search-suggestions';
            suggestionsDiv.style.display = 'none';
            searchContainer.appendChild(suggestionsDiv);
        }
    }

    handleSearch(query) {
        clearTimeout(this.searchTimeout);
        
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 300); // Debounce search
    }

    performSearch(query) {
        const quizCards = document.querySelectorAll('.quiz-card');
        let visibleCount = 0;

        quizCards.forEach(card => {
            const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
            const description = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
            const category = card.querySelector('.category-badge')?.textContent.toLowerCase() || '';
            
            const matches = title.includes(query.toLowerCase()) || 
                          description.includes(query.toLowerCase()) || 
                          category.includes(query.toLowerCase());

            if (matches || query === '') {
                this.showCard(card);
                visibleCount++;
            } else {
                this.hideCard(card);
            }
        });

        this.updateResultsCount(visibleCount);
        this.updateNoResultsMessage(visibleCount === 0 && query !== '');
    }

    showCard(card) {
        card.style.display = 'block';
        card.style.animation = 'fadeInUp 0.5s ease-out';
    }

    hideCard(card) {
        card.style.animation = 'fadeOutDown 0.3s ease-out';
        setTimeout(() => {
            card.style.display = 'none';
        }, 300);
    }

    handleFilterChange(filterName, filterValue) {
        this.currentFilters[filterName] = filterValue;
        this.applyFilters();
    }

    applyFilters() {
        const quizCards = document.querySelectorAll('.quiz-card');
        let visibleCount = 0;

        quizCards.forEach(card => {
            let shouldShow = true;

            // Apply each filter
            Object.entries(this.currentFilters).forEach(([filterName, filterValue]) => {
                if (filterValue && filterValue !== '') {
                    const cardValue = this.getCardFilterValue(card, filterName);
                    if (cardValue !== filterValue) {
                        shouldShow = false;
                    }
                }
            });

            if (shouldShow) {
                this.showCard(card);
                visibleCount++;
            } else {
                this.hideCard(card);
            }
        });

        this.updateResultsCount(visibleCount);
        this.updateFiltersDisplay();
    }

    getCardFilterValue(card, filterName) {
        switch (filterName) {
            case 'category':
                return card.querySelector('.category-badge')?.dataset.category || '';
            case 'difficulty':
                return card.querySelector('.difficulty-badge')?.dataset.difficulty || '';
            case 'ai_provider':
                return card.querySelector('.provider-badge')?.dataset.provider || '';
            default:
                return '';
        }
    }

    clearFilters() {
        this.currentFilters = {};
        
        // Reset all filter selects
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.value = '';
        });

        // Clear search
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.value = '';
        }

        // Show all cards
        const quizCards = document.querySelectorAll('.quiz-card');
        quizCards.forEach(card => this.showCard(card));

        this.updateResultsCount(quizCards.length);
        this.updateFiltersDisplay();
    }

    handleSort(sortValue) {
        const container = document.querySelector('.quiz-grid, .quiz-list');
        if (!container) return;

        const cards = Array.from(container.querySelectorAll('.quiz-card'));
        
        cards.sort((a, b) => {
            switch (sortValue) {
                case 'newest':
                    return this.getCardDate(b) - this.getCardDate(a);
                case 'oldest':
                    return this.getCardDate(a) - this.getCardDate(b);
                case 'title':
                    return this.getCardTitle(a).localeCompare(this.getCardTitle(b));
                case 'difficulty':
                    return this.getDifficultyOrder(this.getCardDifficulty(a)) - 
                           this.getDifficultyOrder(this.getCardDifficulty(b));
                case 'popular':
                    return this.getCardPopularity(b) - this.getCardPopularity(a);
                default:
                    return 0;
            }
        });

        // Animate sorting
        container.style.opacity = '0.5';
        setTimeout(() => {
            cards.forEach(card => container.appendChild(card));
            container.style.opacity = '1';
        }, 200);
    }

    getCardDate(card) {
        const dateEl = card.querySelector('.card-date');
        return dateEl ? new Date(dateEl.dataset.date).getTime() : 0;
    }

    getCardTitle(card) {
        return card.querySelector('.card-title')?.textContent || '';
    }

    getCardDifficulty(card) {
        return card.querySelector('.difficulty-badge')?.dataset.difficulty || '';
    }

    getDifficultyOrder(difficulty) {
        const order = { easy: 1, medium: 2, hard: 3 };
        return order[difficulty] || 0;
    }

    getCardPopularity(card) {
        const attemptsEl = card.querySelector('.attempts-count');
        return attemptsEl ? parseInt(attemptsEl.textContent) : 0;
    }

    toggleView(viewType) {
        const container = document.querySelector('.quiz-grid, .quiz-list');
        if (!container) return;

        container.className = viewType === 'grid' ? 'quiz-grid row' : 'quiz-list';
        
        // Update toggle buttons
        document.querySelectorAll('.view-toggle').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewType}"]`).classList.add('active');

        // Save preference
        localStorage.setItem('quiz-list-view', viewType);
    }

    enhanceQuizCards() {
        const cards = document.querySelectorAll('.quiz-card');
        
        cards.forEach((card, index) => {
            // Add hover effects
            this.addCardHoverEffects(card);
            
            // Add intersection observer for animations
            this.observeCard(card, index);
            
            // Add quick actions
            this.addQuickActions(card);
        });
    }

    addCardHoverEffects(card) {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px) scale(1.02)';
            card.style.boxShadow = '0 20px 40px rgba(0,0,0,0.15)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0) scale(1)';
            card.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
        });
    }

    observeCard(card, index) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.classList.add('animate-in');
                    }, index * 100);
                }
            });
        }, { threshold: 0.1 });

        observer.observe(card);
    }

    addQuickActions(card) {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'quick-actions';
        actionsDiv.innerHTML = `
            <button class="quick-action-btn preview-btn" title="Quick Preview">
                <i class="fas fa-eye"></i>
            </button>
            <button class="quick-action-btn favorite-btn" title="Add to Favorites">
                <i class="fas fa-heart"></i>
            </button>
            <button class="quick-action-btn share-btn" title="Share Quiz">
                <i class="fas fa-share"></i>
            </button>
        `;

        card.appendChild(actionsDiv);

        // Bind quick action events
        this.bindQuickActionEvents(card, actionsDiv);
    }

    bindQuickActionEvents(card, actionsDiv) {
        const previewBtn = actionsDiv.querySelector('.preview-btn');
        const favoriteBtn = actionsDiv.querySelector('.favorite-btn');
        const shareBtn = actionsDiv.querySelector('.share-btn');

        if (previewBtn) {
            previewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showQuickPreview(card);
            });
        }

        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleFavorite(card, favoriteBtn);
            });
        }

        if (shareBtn) {
            shareBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.shareQuiz(card);
            });
        }
    }

    showQuickPreview(card) {
        const quizTitle = card.querySelector('.card-title')?.textContent || '';
        const quizDescription = card.querySelector('.card-text')?.textContent || '';
        const quizId = card.dataset.quizId;

        const modal = document.createElement('div');
        modal.className = 'quiz-preview-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h5>${quizTitle}</h5>
                    <button class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <p>${quizDescription}</p>
                    <div class="preview-actions">
                        <a href="/quiz/${quizId}/" class="btn btn-primary">Take Quiz</a>
                        <a href="/quiz/${quizId}/details/" class="btn btn-outline-secondary">View Details</a>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal events
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.remove();
        });
        modal.querySelector('.close-btn').addEventListener('click', () => modal.remove());
    }

    toggleFavorite(card, btn) {
        const isFavorited = btn.classList.contains('favorited');
        
        if (isFavorited) {
            btn.classList.remove('favorited');
            btn.innerHTML = '<i class="fas fa-heart"></i>';
            btn.title = 'Add to Favorites';
        } else {
            btn.classList.add('favorited');
            btn.innerHTML = '<i class="fas fa-heart text-danger"></i>';
            btn.title = 'Remove from Favorites';
        }

        // Save to localStorage or send to server
        const quizId = card.dataset.quizId;
        this.saveFavoriteStatus(quizId, !isFavorited);
    }

    shareQuiz(card) {
        const quizTitle = card.querySelector('.card-title')?.textContent || '';
        const quizUrl = window.location.origin + card.querySelector('.btn-primary')?.getAttribute('href');

        if (navigator.share) {
            navigator.share({
                title: quizTitle,
                text: 'Check out this quiz!',
                url: quizUrl
            });
        } else {
            // Fallback: copy to clipboard
            navigator.clipboard.writeText(quizUrl).then(() => {
                this.showNotification('Quiz link copied to clipboard!', 'success');
            });
        }
    }

    setupInfiniteScroll() {
        let loading = false;
        
        window.addEventListener('scroll', () => {
            if (loading) return;
            
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 1000) {
                loading = true;
                this.loadMoreQuizzes().then(() => {
                    loading = false;
                });
            }
        });
    }

    async loadMoreQuizzes() {
        // Implementation for loading more quizzes via AJAX
        const nextPage = this.currentPage + 1;
        
        try {
            const response = await fetch(`/quiz/ajax/load-more/?page=${nextPage}`);
            const data = await response.json();
            
            if (data.success && data.quizzes) {
                this.appendQuizzes(data.quizzes);
                this.currentPage = nextPage;
            }
        } catch (error) {
            console.error('Failed to load more quizzes:', error);
        }
    }

    appendQuizzes(quizzes) {
        const container = document.querySelector('.quiz-grid, .quiz-list');
        if (!container) return;

        quizzes.forEach(quiz => {
            const quizCard = this.createQuizCard(quiz);
            container.appendChild(quizCard);
            this.enhanceQuizCard(quizCard);
        });
    }

    updateResultsCount(count) {
        const countEl = document.querySelector('.results-count');
        if (countEl) {
            countEl.textContent = `${count} quiz${count !== 1 ? 'es' : ''} found`;
        }
    }

    updateNoResultsMessage(show) {
        let noResultsEl = document.querySelector('.no-results-message');
        
        if (show && !noResultsEl) {
            noResultsEl = document.createElement('div');
            noResultsEl.className = 'no-results-message text-center py-5';
            noResultsEl.innerHTML = `
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h4>No quizzes found</h4>
                <p class="text-muted">Try adjusting your search criteria or filters.</p>
            `;
            document.querySelector('.quiz-container').appendChild(noResultsEl);
        } else if (!show && noResultsEl) {
            noResultsEl.remove();
        }
    }

    saveFavoriteStatus(quizId, isFavorited) {
        // Save to localStorage
        const favorites = JSON.parse(localStorage.getItem('quiz-favorites') || '[]');
        
        if (isFavorited) {
            if (!favorites.includes(quizId)) {
                favorites.push(quizId);
            }
        } else {
            const index = favorites.indexOf(quizId);
            if (index > -1) {
                favorites.splice(index, 1);
            }
        }
        
        localStorage.setItem('quiz-favorites', JSON.stringify(favorites));
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
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
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        
        notification.style.backgroundColor = colors[type] || colors.info;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.quiz-grid, .quiz-list')) {
        new QuizListManager();
    }
});

// Export for use in other scripts
window.QuizListManager = QuizListManager;
