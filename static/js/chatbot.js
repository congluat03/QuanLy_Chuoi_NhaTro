class ChatbotManager {
    constructor() {
        this.isOpen = false;
        this.conversationHistory = [];
        this.isTyping = false;
        this.apiUrl = '/api/chatbot/';
        
        this.init();
    }
    
    init() {
        this.createChatbotHTML();
        this.attachEventListeners();
        this.loadConversationHistory();
    }
    
    createChatbotHTML() {
        const chatbotHTML = `
            <div class="chatbot-container">
                <!-- Chatbot Button -->
                <button class="chatbot-button" id="chatbot-toggle">
                    <span id="chatbot-icon">💬</span>
                </button>
                
                <!-- Chatbot Window -->
                <div class="chatbot-window" id="chatbot-window">
                    <!-- Header -->
                    <div class="chatbot-header">
                        <button class="chatbot-close" id="chatbot-close">&times;</button>
                        <h3>🤖 Trợ lý AI</h3>
                        <p>Hỗ trợ tìm phòng & quản lý nhà trọ</p>
                    </div>
                    
                    <!-- Messages Container -->
                    <div class="chatbot-messages" id="chatbot-messages">
                        <div class="welcome-message">
                            <div class="welcome-icon">🏠</div>
                            <p><strong>Xin chào!</strong></p>
                            <p>Tôi là trợ lý AI của website Quản lý Nhà Trọ. Tôi có thể giúp bạn:</p>
                            <ul style="text-align: left; margin-top: 10px;">
                                <li>Tìm kiếm phòng trọ phù hợp</li>
                                <li>Hướng dẫn đặt phòng</li>
                                <li>Tra cứu thông tin hợp đồng</li>
                                <li>Giải đáp các thắc mắc</li>
                            </ul>
                            <p style="margin-top: 10px;"><em>Hãy nhập tin nhắn để bắt đầu!</em></p>
                        </div>
                    </div>
                    
                    <!-- Input Container -->
                    <div class="chatbot-input-container">
                        <div class="chatbot-input-wrapper">
                            <input 
                                type="text" 
                                class="chatbot-input" 
                                id="chatbot-input" 
                                placeholder="Nhập tin nhắn của bạn..."
                                maxlength="500"
                            >
                            <button class="chatbot-send" id="chatbot-send" disabled>
                                <span>➤</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Thêm HTML vào cuối body
        document.body.insertAdjacentHTML('beforeend', chatbotHTML);
    }
    
    attachEventListeners() {
        const toggleBtn = document.getElementById('chatbot-toggle');
        const closeBtn = document.getElementById('chatbot-close');
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send');
        
        // Toggle chatbot
        toggleBtn.addEventListener('click', () => this.toggleChatbot());
        closeBtn.addEventListener('click', () => this.closeChatbot());
        
        // Input events
        input.addEventListener('input', () => this.handleInputChange());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Send button
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            const chatbotContainer = document.querySelector('.chatbot-container');
            if (!chatbotContainer.contains(e.target) && this.isOpen) {
                this.closeChatbot();
            }
        });
        
        // Prevent closing when clicking inside chatbot window
        document.getElementById('chatbot-window').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    toggleChatbot() {
        if (this.isOpen) {
            this.closeChatbot();
        } else {
            this.openChatbot();
        }
    }
    
    openChatbot() {
        const window = document.getElementById('chatbot-window');
        const button = document.getElementById('chatbot-toggle');
        const icon = document.getElementById('chatbot-icon');
        
        window.classList.add('active');
        button.classList.add('active');
        // Change icon to close
        icon.innerHTML = `
            <svg class="w-6 h-6 transition-all duration-300 rotate-90" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
        `;
        this.isOpen = true;
        
        // Focus input with smooth delay
        setTimeout(() => {
            document.getElementById('chatbot-input').focus();
        }, 200);
    }
    
    closeChatbot() {
        const window = document.getElementById('chatbot-window');
        const button = document.getElementById('chatbot-toggle');
        const icon = document.getElementById('chatbot-icon');
        
        window.classList.remove('active');
        button.classList.remove('active');
        // Change back to chat icon
        icon.innerHTML = `
            <svg class="w-7 h-7 transition-all duration-300" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clip-rule="evenodd" />
            </svg>
        `;
        this.isOpen = false;
    }
    
    handleInputChange() {
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send');
        
        if (input.value.trim().length > 0) {
            sendBtn.disabled = false;
            sendBtn.style.opacity = '1';
            sendBtn.style.transform = 'scale(1)';
            sendBtn.innerHTML = `
                <svg class="w-5 h-5 transition-transform duration-200" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
                </svg>
            `;
        } else {
            sendBtn.disabled = true;
            sendBtn.style.opacity = '0.5';
            sendBtn.style.transform = 'scale(0.95)';
            sendBtn.innerHTML = `
                <svg class="w-5 h-5 transition-transform duration-200" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clip-rule="evenodd" />
                </svg>
            `;
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('chatbot-input');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        document.getElementById('chatbot-send').disabled = true;
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to API
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    message: message,
                    history: this.conversationHistory.slice(-10) // Gửi 10 tin nhắn gần nhất
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            if (data.success) {
                this.addMessage(data.message, 'bot');
                
                // Update conversation history
                this.conversationHistory.push({
                    user: message,
                    ai: data.message,
                    timestamp: Date.now()
                });
                
                // Save to localStorage
                this.saveConversationHistory();
            } else {
                this.addMessage(data.message || 'Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này.', 'bot', true);
            }
        } catch (error) {
            console.error('Chatbot error:', error);
            this.hideTypingIndicator();
            this.addMessage('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.', 'bot', true);
        }
    }
    
    addMessage(text, type, isError = false) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        
        // Remove welcome message if exists
        if (welcomeMessage) {
            welcomeMessage.style.opacity = '0';
            welcomeMessage.style.transform = 'translateY(-20px) scale(0.95)';
            setTimeout(() => welcomeMessage.remove(), 300);
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} new ${isError ? 'error' : ''}`;
        
        if (type === 'bot' && !isError) {
            messageDiv.innerHTML = this.formatMessage(text);
        } else {
            messageDiv.textContent = text;
        }
        
        // Add subtle entrance animation
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(20px) scale(0.95)';
        messagesContainer.appendChild(messageDiv);
        
        // Trigger animation
        requestAnimationFrame(() => {
            messageDiv.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            messageDiv.style.opacity = '1';
            messageDiv.style.transform = 'translateY(0) scale(1)';
        });
        
        // Scroll to bottom with smooth behavior
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
        
        // Remove 'new' class after animation
        setTimeout(() => {
            messageDiv.classList.remove('new');
            messageDiv.style.transform = '';
            messageDiv.style.transition = '';
        }, 400);
    }
    
    showTypingIndicator() {
        this.isTyping = true;
        const messagesContainer = document.getElementById('chatbot-messages');
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message typing';
        typingDiv.id = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-indicator flex items-center">
                <div class="flex space-x-1 mr-3">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                <span style="color: #64748b; font-size: 13px; font-weight: 500; font-family: 'Inter', sans-serif;">AI đang suy nghĩ...</span>
            </div>
        `;
        
        // Add entrance animation for typing indicator
        typingDiv.style.opacity = '0';
        typingDiv.style.transform = 'translateY(10px)';
        messagesContainer.appendChild(typingDiv);
        
        requestAnimationFrame(() => {
            typingDiv.style.transition = 'all 0.3s ease';
            typingDiv.style.opacity = '1';
            typingDiv.style.transform = 'translateY(0)';
        });
        
        messagesContainer.scrollTo({
            top: messagesContainer.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Fallback: try to get from meta tag
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        return '';
    }
    
    saveConversationHistory() {
        try {
            // Chỉ lưu 20 cuộc hội thoại gần nhất
            const limitedHistory = this.conversationHistory.slice(-20);
            localStorage.setItem('chatbot_history', JSON.stringify(limitedHistory));
        } catch (error) {
            console.warn('Cannot save conversation history:', error);
        }
    }
    
    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('chatbot_history');
            if (saved) {
                this.conversationHistory = JSON.parse(saved);
                
                // Xóa lịch sử cũ hơn 7 ngày
                const weekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
                this.conversationHistory = this.conversationHistory.filter(
                    item => item.timestamp > weekAgo
                );
            }
        } catch (error) {
            console.warn('Cannot load conversation history:', error);
            this.conversationHistory = [];
        }
    }
    
    formatMessage(message) {
        // Basic formatting for bot messages
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic text
            .replace(/\n/g, '<br>')                            // Line breaks
            .replace(/`(.*?)`/g, '<code style="background: rgba(59, 130, 246, 0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">$1</code>'); // Inline code
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Chờ một chút để đảm bảo trang đã load xong
    setTimeout(() => {
        new ChatbotManager();
    }, 1000);
});

// Export for potential use in other scripts
window.ChatbotManager = ChatbotManager;