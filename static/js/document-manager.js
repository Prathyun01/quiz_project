class DocumentManager {
    constructor() {
        this.favorites = new Set();
        this.ratings = new Map();
        this.init();
    }

    init() {
        this.loadUserFavorites();
        this.setupEventListeners();
        this.animateCards();
    }

    loadUserFavorites() {
        // Load user's favorite documents
        const favoriteButtons = document.querySelectorAll('[data-favorite]');
        favoriteButtons.forEach(button => {
            const docId = button.dataset.documentId;
            if (button.classList.contains('favorited')) {
                this.favorites.add(docId);
            }
        });
    }

    setupEventListeners() {
        // File type filter
        const fileTypeFilters = document.querySelectorAll('[data-file-type]');
        fileTypeFilters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                e.preventDefault();
                this.filterByFileType(filter.dataset.fileType);
            });
        });

        // Sort options
        const sortSelect = document.getElementById('sort-documents');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortDocuments(e.target.value);
            });
        }

        // Search functionality
        const searchInput = document.getElementById('document-search');
        if (searchInput) {
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.searchDocuments(e.target.value);
                }, 500);
            });
        }
    }

    animateCards() {
        const cards = document.querySelectorAll('.document-card');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, { threshold: 0.1 });

        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = `opacity 0.6s ease ${index * 0.05}s, transform 0.6s ease ${index * 0.05}s`;
            observer.observe(card);
        });
    }

    filterByFileType(fileType) {
        const cards = document.querySelectorAll('.document-card');
        cards.forEach(card => {
            const cardFileType = card.dataset.fileType;
            if (fileType === 'all' || cardFileType === fileType) {
                card.style.display = 'block';
                card.style.animation = 'fadeIn 0.5s ease';
            } else {
                card.style.display = 'none';
            }
        });
    }

    sortDocuments(sortBy) {
        const container = document.querySelector('.documents-grid');
        const cards = Array.from(container.querySelectorAll('.document-card'));
        
        cards.sort((a, b) => {
            switch (sortBy) {
                case 'name':
                    return a.dataset.title.localeCompare(b.dataset.title);
                case 'date':
                    return new Date(b.dataset.date) - new Date(a.dataset.date);
                case 'downloads':
                    return parseInt(b.dataset.downloads) - parseInt(a.dataset.downloads);
                case 'rating':
                    return parseFloat(b.dataset.rating) - parseFloat(a.dataset.rating);
                default:
                    return 0;
            }
        });
        
        cards.forEach(card => container.appendChild(card));
    }

    searchDocuments(query) {
        const cards = document.querySelectorAll('.document-card');
        const searchTerm = query.toLowerCase();
        
        cards.forEach(card => {
            const title = card.dataset.title.toLowerCase();
            const category = card.dataset.category.toLowerCase();
            const tags = card.dataset.tags.toLowerCase();
            
            if (title.includes(searchTerm) || 
                category.includes(searchTerm) || 
                tags.includes(searchTerm)) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    async toggleFavorite(documentId, element) {
        try {
            const response = await fetch('/documents/ajax/toggle-favorite/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ document_id: documentId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const icon = element.querySelector('i');
                if (data.action === 'added') {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    element.classList.add('favorited');
                    this.favorites.add(documentId);
                } else {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    element.classList.remove('favorited');
                    this.favorites.delete(documentId);
                }
                
                this.showNotification(
                    data.action === 'added' ? 'Added to favorites!' : 'Removed from favorites!',
                    'success'
                );
            }
        } catch (error) {
            this.showNotification('Failed to update favorites', 'error');
        }
    }

    async rateDocument(documentId, rating) {
        try {
            const response = await fetch('/documents/ajax/rate-document/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ 
                    document_id: documentId, 
                    rating: rating 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.ratings.set(documentId, rating);
                this.updateStarRating(documentId, rating);
                this.showNotification('Rating submitted successfully!', 'success');
            }
        } catch (error) {
            this.showNotification('Failed to submit rating', 'error');
        }
    }

    updateStarRating(documentId, rating) {
        const stars = document.querySelectorAll(`[data-document-id="${documentId}"] .star`);
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    new DocumentManager();
});
