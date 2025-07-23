class ChatbotInterface {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.init();
    }

    init() {
        this.sessionId = document.querySelector('.chat-container')?.dataset.sessionId;
        if (this.sessionId) {
            this.setupWebSocket();
        }
        this.setupEventListeners();
        this.setupQuickActions();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chatbot/${this.sessionId}/`;
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('Chatbot WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };

        this.socket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleWebSocketMessage(data);
        };

        this.socket.onclose = () => {
            console.log('Chatbot WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                const delay = Math.pow(2, this.reconnectAttempts) * 1000;
                setTimeout(() => this.setupWebSocket(), delay);
                this.reconnectAttempts++;
            }
        };

        this.socket.onerror = (error) => {
            console.error('Chatbot WebSocket error:', error);
        };
    }

    setupEventListeners() {
        const chatForm = document.getElementById('chat-form');
        const chatInput = document.getElementById('chat-input');

        if (chatForm) {
            chatForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            chatInput.addEventListener('input', () => {
                chatInput.style.height = 'auto';
                chatInput.style.height = chatInput.scrollHeight + 'px';
            });

            let typingTimer;
            chatInput.addEventListener('input', () => {
                if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({
                        'type': 'typing',
                        'is_typing': true
                    }));
                    
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(() => {
                        this.socket.send(JSON.stringify({
                            'type': 'typing',
                            'is_typing': false
                        }));
                    }, 1000);
                }
            });
        }

        document.getElementById('new-session-btn')?.addEventListener('click', () => {
            this.createNewSession();
        });

        document.getElementById('clear-chat-btn')?.addEventListener('click', () => {
            this.clearChat();
        });
    }

    setupQuickActions() {
        const quickActions = document.querySelectorAll('.quick-action-btn');
        quickActions.forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.dataset.prompt;
                document.getElementById('chat-input').value = prompt;
                this.sendMessage();
            });
        });
    }

    sendMessage() {
        const chatInput = document.getElementById('chat-input');
        const providerSelect = document.getElementById('ai-provider');
        const message = chatInput.value.trim();

        if (!message) return;

        const provider = providerSelect?.value || 'perplexity';

        this.addMessageToChat(message, 'user');
        chatInput.value = '';
        chatInput.style.height = 'auto';

        this.showTypingIndicator();

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                'type': 'chat_message',
                'message': message,
                'provider': provider
            }));
        } else {
            console.log('Sending via HTTP fallback');
            this.sendMessageHTTP(message, provider);
        }
    }

    async sendMessageHTTP(message, provider) {
        console.log('Sending HTTP request:', { session_id: this.sessionId, message, provider });
        
        try {
            const response = await fetch(`/chatbot/ajax/send-message/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({ 
                    session_id: this.sessionId,
                    message: message, 
                    provider: provider 
                })
            });

            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('Response data:', data);
            
            this.hideTypingIndicator();

            if (data.success) {
                this.addMessageToChat(data.bot_response.content, 'bot', data.bot_response);
            } else {
                console.error('API error:', data.error);
                this.addMessageToChat(`Error: ${data.error}`, 'bot');
                if (data.error.includes('Rate limit')) {
                    this.showError('Rate limit exceeded. Please wait before sending another message.');
                }
            }
        } catch (error) {
            console.error('Fetch error:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('Network error. Please try again.', 'bot');
        }
    }

    handleWebSocketMessage(data) {
        if (data.type === 'chat_response') {
            this.hideTypingIndicator();
            this.addMessageToChat(data.bot_response.content, 'bot', data.bot_response);
        } else if (data.type === 'typing_indicator') {
            // Handle typing indicators
        } else if (data.type === 'error') {
            this.hideTypingIndicator();
            this.showError(data.message);
        }
    }

    addMessageToChat(content, type, metadata = null) {
        const chatMessages = document.getElementById('chat-messages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
        const timestamp = new Date().toLocaleTimeString();
        let modelInfo = '';
        
        if (type === 'bot' && metadata) {
            const processingTime = metadata.processing_time ? ` (${metadata.processing_time.toFixed(2)}s)` : '';
            modelInfo = `<div class="message-meta text-muted mt-1">
                <small>via ${metadata.model || 'AI'}${processingTime} • ${timestamp}</small>
            </div>`;
        }

        messageDiv.innerHTML = `
            <div class="message-bubble d-flex ${type === 'user' ? 'flex-row-reverse' : ''}">
                ${type === 'bot' ? '<div class="ai-avatar-small me-2"><i class="fas fa-robot"></i></div>' : ''}
                <div class="message-content">
                    <div class="message-text">${this.formatMessage(content)}</div>
                    ${type === 'user' ? `<div class="message-meta text-muted mt-1"><small>${timestamp}</small></div>` : modelInfo}
                    ${type === 'bot' ? this.createMessageActions(metadata?.id) : ''}
                </div>
                ${type === 'user' ? '<div class="ai-avatar-small ms-2"><i class="fas fa-user"></i></div>' : ''}
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px)';
        setTimeout(() => {
            messageDiv.style.transition = 'all 0.3s ease';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0)';
        }, 100);
    }

    formatMessage(content) {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    createMessageActions(messageId) {
        if (!messageId) return '';
        
        return `
            <div class="message-actions mt-2">
                <button class="btn btn-sm btn-outline-light copy-btn" onclick="copyMessage(this)">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="rateResponse('${messageId}', true)">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="rateResponse('${messageId}', false)">
                    <i class="fas fa-thumbs-down"></i>
                </button>
            </div>
        `;
    }

    showTypingIndicator() {
        const existingIndicator = document.getElementById('typing-indicator');
        if (existingIndicator) return;

        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'chat-message bot-message';
        typingDiv.innerHTML = `
            <div class="message-bubble d-flex">
                <div class="ai-avatar-small me-2"><i class="fas fa-robot"></i></div>
                <div class="message-content">
                    <div class="typing-animation">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = connected ? 'text-success' : 'text-warning';
            statusElement.textContent = connected ? 'Connected' : 'Reconnecting...';
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-warning alert-dismissible fade show';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.chat-interface');
        container.insertBefore(errorDiv, container.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    createNewSession() {
        window.location.href = '/chatbot/new-session/?type=general';
    }

    clearChat() {
        if (confirm('Are you sure you want to clear this chat session?')) {
            window.location.href = '/chatbot/new-session/';
        }
    }
}

function copyMessage(button) {
    const messageText = button.closest('.message-content').querySelector('.message-text').innerText;
    navigator.clipboard.writeText(messageText).then(() => {
        showSuccess('Message copied to clipboard!');
    });
}

function newChatSession() {
    window.location.href = '/chatbot/new-session/?type=general';
}

function loadSession(sessionId) {
    window.location.href = `/chatbot/load-session/${sessionId}/`;
}

function clearChat() {
    if (confirm('Are you sure you want to clear this chat session?')) {
        window.location.href = '/chatbot/new-session/';
    }
}

async function rateResponse(messageId, isHelpful) {
    try {
        const response = await fetch('/chatbot/ajax/rate-response/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                message_id: messageId,
                is_helpful: isHelpful
            })
        });

        const data = await response.json();
        if (data.success) {
            showSuccess('Thank you for your feedback!');
        }
    } catch (error) {
        console.error('Error rating response:', error);
    }
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.chat-interface');
    container.insertBefore(successDiv, container.firstChild);
    
    setTimeout(() => {
        successDiv.remove();
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatbotInterface();
});
