// Theme Switcher Functionality
class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getSystemTheme();
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.setupEventListeners();
        this.updateThemeIndicators();
    }
    
    getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    getStoredTheme() {
        return localStorage.getItem('quiz-app-theme');
    }
    
    storeTheme(theme) {
        localStorage.setItem('quiz-app-theme', theme);
    }
    
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        this.storeTheme(theme);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme }
        }));
    }
    
    updateMetaThemeColor(theme) {
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
            const color = theme === 'dark' ? '#0f172a' : '#ffffff';
            metaThemeColor.setAttribute('content', color);
        }
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        this.updateThemeIndicators();
        this.saveThemePreference(newTheme);
    }
    
    updateThemeIndicators() {
        const themeText = document.getElementById('theme-text');
        if (themeText) {
            themeText.textContent = this.currentTheme === 'dark' ? 'Switch to Light' : 'Switch to Dark';
        }
        
        // Update theme toggle buttons
        const themeToggles = document.querySelectorAll('.theme-toggle');
        themeToggles.forEach(toggle => {
            const icon = toggle.querySelector('i');
            if (icon) {
                icon.className = this.currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        });
    }
    
    async saveThemePreference(theme) {
        try {
            // Save to server if user is authenticated
            if (window.location.pathname !== '/login/' && window.location.pathname !== '/register/') {
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                if (csrfToken) {
                    await fetch('/accounts/settings/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': csrfToken
                        },
                        body: `theme_preference=${theme}&update_theme_only=1`
                    });
                }
            }
        } catch (error) {
            console.warn('Could not save theme preference to server:', error);
        }
    }
    
    setupEventListeners() {
        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addListener((e) => {
            if (!this.getStoredTheme()) {
                this.applyTheme(e.matches ? 'dark' : 'light');
                this.updateThemeIndicators();
            }
        });
        
        // Listen for storage changes (sync across tabs)
        window.addEventListener('storage', (e) => {
            if (e.key === 'quiz-app-theme' && e.newValue !== this.currentTheme) {
                this.applyTheme(e.newValue);
                this.updateThemeIndicators();
            }
        });
    }
}

// Theme transition effect
function addThemeTransition() {
    const style = document.createElement('style');
    style.textContent = `
        * {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
        }
    `;
    document.head.appendChild(style);
    
    // Remove transition after theme change
    setTimeout(() => {
        document.head.removeChild(style);
    }, 300);
}

// Global theme toggle function
function toggleTheme() {
    addThemeTransition();
    window.themeManager.toggleTheme();
    
    // Update 3D background if it exists
    if (window.backgroundAnimation) {
        window.backgroundAnimation.updateTheme(window.themeManager.currentTheme);
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    
    // Add keyboard shortcut for theme toggle (Ctrl/Cmd + Shift + T)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggleTheme();
        }
    });
    
    // Auto theme switching based on time (optional)
    if (localStorage.getItem('quiz-app-auto-theme') === 'true') {
        const hour = new Date().getHours();
        const shouldUseDarkTheme = hour < 6 || hour > 18;
        const autoTheme = shouldUseDarkTheme ? 'dark' : 'light';
        
        if (autoTheme !== window.themeManager.currentTheme) {
            window.themeManager.applyTheme(autoTheme);
        }
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeManager, toggleTheme };
}
