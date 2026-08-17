document.addEventListener('DOMContentLoaded', () => {
    // 1. Inject HTML for the chatbot
    const chatbotHTML = `
        <div id="chatbot-container" class="d-none">
            <div class="chatbot-header">
                <div class="chatbot-header-title">
                    <i class="fa-solid fa-robot"></i> CrowdFundingEgypt Chatbot
                </div>
                <div class="chatbot-header-actions">
                    <button class="chatbot-btn" id="chatbot-clear-btn" title="Clear Chat"><i class="fa-solid fa-trash-can"></i></button>
                    <button class="chatbot-btn d-none d-md-flex" id="chatbot-expand-btn" title="Expand"><i class="fa-solid fa-expand"></i></button>
                    <button class="chatbot-btn chatbot-close" id="chatbot-close-btn" title="Close">&times;</button>
                </div>
            </div>
            <div class="chatbot-messages" id="chatbot-messages">
                <div class="chatbot-message chatbot-message-bot">
                    <p>Hi there! How can I help you with Crowd-Funding Egypt today?</p>
                </div>
            </div>
            <div class="chatbot-input-area">
                <input type="text" class="chatbot-input" id="chatbot-input" placeholder="Type your message..." autocomplete="off">
                <button class="chatbot-send-btn" id="chatbot-send-btn">
                    <i class="fa-solid fa-paper-plane"></i>
                </button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', chatbotHTML);

    const toggleBtn = document.getElementById('chatbot-toggle');
    const container = document.getElementById('chatbot-container');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const sendBtn = document.getElementById('chatbot-send-btn');
    const inputField = document.getElementById('chatbot-input');
    const messagesContainer = document.getElementById('chatbot-messages');

    // Toggle Chatbot
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            container.classList.toggle('d-none');
            if (!container.classList.contains('d-none')) {
                inputField.focus();
            }
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            container.classList.add('d-none');
        });
    }

    const clearBtn = document.getElementById('chatbot-clear-btn');
    const expandBtn = document.getElementById('chatbot-expand-btn');

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            messagesContainer.innerHTML = `
                <div class="chatbot-message chatbot-message-bot">
                    <p style="margin-bottom:0;">Hi there! How can I help you with Crowd-Funding Egypt today?</p>
                </div>
            `;
        });
    }

    if (expandBtn) {
        expandBtn.addEventListener('click', () => {
            container.classList.toggle('chatbot-expanded');
            const icon = expandBtn.querySelector('i');
            if (container.classList.contains('chatbot-expanded')) {
                icon.classList.remove('fa-expand');
                icon.classList.add('fa-compress');
                expandBtn.title = "Collapse";
            } else {
                icon.classList.remove('fa-compress');
                icon.classList.add('fa-expand');
                expandBtn.title = "Expand";
            }
        });
    }

    // Helper: Get CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Simple formatter for chatbot responses
    function formatBotReply(text) {
        let html = text;
        // Headers -> Bold
        html = html.replace(/^#{1,6}\s+(.*)$/gm, '<strong>$1</strong>');
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: inherit; text-decoration: underline;">$1</a>');
        // Bullet Points
        html = html.replace(/^[\*\-]\s+(.*)$/gm, '&bull; $1');
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        // Clean up excessive line breaks
        html = html.replace(/(<br>\s*){3,}/g, '<br><br>');
        return html;
    }

    // Add Message to UI
    function appendMessage(text, isUser = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chatbot-message ${isUser ? 'chatbot-message-user' : 'chatbot-message-bot'}`;

        const formattedText = isUser ? text.replace(/\n/g, '<br>') : formatBotReply(text);
        msgDiv.innerHTML = `<p style="margin-bottom:0;">${formattedText}</p>`;

        messagesContainer.appendChild(msgDiv);

        // Fix scrolling: if message is taller than the container, align top, otherwise align bottom.
        setTimeout(() => {
            if (msgDiv.offsetHeight > messagesContainer.clientHeight) {
                msgDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                messagesContainer.scrollTo({ top: messagesContainer.scrollHeight, behavior: 'smooth' });
            }
        }, 10);
    }

    // Show Typing Indicator
    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-typing';
        typingDiv.id = 'chatbot-typing-indicator';
        typingDiv.innerHTML = `
            <div class="chatbot-typing-dot"></div>
            <div class="chatbot-typing-dot"></div>
            <div class="chatbot-typing-dot"></div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Hide Typing Indicator
    function hideTyping() {
        const typingDiv = document.getElementById('chatbot-typing-indicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    // Send Message Logic
    async function sendMessage() {
        const message = inputField.value.trim();
        if (!message) return;

        // 1. Add user message
        appendMessage(message, true);
        inputField.value = '';
        inputField.disabled = true;

        // 2. Show typing
        showTyping();

        // 3. API Call
        try {
            const csrftoken = getCookie('csrftoken');
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            hideTyping();

            if (response.ok) {
                appendMessage(data.reply || "I'm sorry, I couldn't generate a reply.");
            } else {
                appendMessage("Error: " + (data.error || "Something went wrong."));
            }

        } catch (error) {
            hideTyping();
            appendMessage("Network error. Please try again later.");
            console.error('Chatbot API Error:', error);
        } finally {
            inputField.disabled = false;
            inputField.focus();
        }
    }

    // Events for Sending
    if (sendBtn && inputField) {
        sendBtn.addEventListener('click', sendMessage);
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
