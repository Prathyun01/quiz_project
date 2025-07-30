class MessagingManager {
    constructor() {
        this.socket = null;
        this.conversationId = null;
        this.currentUser = null;
        this.typingUsers = new Set();
        this.messageQueue = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    initialize(conversationId, userId) {
        this.conversationId = conversationId;
        this.currentUser = userId;
        this.connectWebSocket();
        this.bindEvents();
    }

    connectWebSocket() {
        if (this.socket) {
            this.socket.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.conversationId}/`;

        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.processMessageQueue();
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
            
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connectWebSocket();
            }, delay);
        }
    }

    sendMessage(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            this.messageQueue.push(data);
        }
    }

    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'chat_message':
                this.displayMessage(data.message);
                break;
            case 'typing_indicator':
                this.handleTypingIndicator(data);
                break;
            case 'user_status':
                this.updateUserStatus(data);
                break;
            case 'message_reaction':
                this.updateReactions(data);
                break;
        }
    }

    displayMessage(message) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageElement = this.createMessageElement(message);
        messagesContainer.appendChild(messageElement);
        this.scrollToBottom();

        // Play sound for incoming messages
        if (message.sender_id !== this.currentUser) {
            this.playNotificationSound();
        }
    }

    createMessageElement(message) {
        const div = document.createElement('div');
        div.className = `message-bubble ${message.sender_id === this.currentUser ? 'message-sent' : 'message-received'}`;
        div.dataset.messageId = message.id;
        
        div.innerHTML = `
            <div class="message-content">${this.formatMessageContent(message.content)}</div>
            <div class="message-time">${this.formatTime(message.created_at)}</div>
        `;
        
        return div;
    }

    formatMessageContent(content) {
        return content.replace(/\n/g, '<br>');
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    handleTypingIndicator(data) {
        if (data.is_typing) {
            this.typingUsers.add(data.username);
        } else {
            this.typingUsers.delete(data.username);
        }
        this.updateTypingDisplay();
    }

    updateTypingDisplay() {
        const indicator = document.getElementById('typing-indicator');
        
        if (this.typingUsers.size > 0) {
            const usersList = Array.from(this.typingUsers);
            let text = '';
            
            if (usersList.length === 1) {
                text = `${usersList[0]} is typing`;
            } else if (usersList.length === 2) {
                text = `${usersList[0]} and ${usersList[1]} are typing`;
            } else {
                text = `${usersList.length} people are typing`;
            }
            
            indicator.querySelector('.typing-user').textContent = text;
            indicator.style.display = 'flex';
        } else {
            indicator.style.display = 'none';
        }
    }

    scrollToBottom() {
        const container = document.getElementById('chat-messages');
        container.scrollTop = container.scrollHeight;
    }

    playNotificationSound() {
        try {
            const audio = new Audio('/static/sounds/message.mp3');
            audio.volume = 0.3;
            audio.play();
        } catch (e) {
            // Ignore audio errors
        }
    }

    bindEvents() {
        // Message form submission
        const form = document.getElementById('message-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleMessageSubmit();
            });
        }

        // Typing indicators
        const input = document.getElementById('message-input');
        if (input) {
            let typingTimer;
            let isTyping = false;

            input.addEventListener('input', () => {
                if (!isTyping) {
                    isTyping = true;
                    this.sendMessage({
                        type: 'typing',
                        is_typing: true
                    });
                }

                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    isTyping = false;
                    this.sendMessage({
                        type: 'typing',
                        is_typing: false
                    });
                }, 2000);
            });
        }
    }

    handleMessageSubmit() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();
        
        if (content) {
            this.sendMessage({
                type: 'chat_message',
                content: content
            });
            input.value = '';
        }
    }
}
