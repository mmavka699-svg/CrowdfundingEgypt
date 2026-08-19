document.addEventListener('DOMContentLoaded', () => {
    const isAuthenticated = window.userIsAuthenticated === true;
    const welcomeMessage = isAuthenticated 
        ? "Hi there! How can I help you with Crowd-Funding Egypt today?" 
        : "Please <a href='/login/'>log in</a> to use the chatbot.";

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
                    <p>${welcomeMessage}</p>
                </div>
            </div>
            <div class="chatbot-input-area">
                <input type="text" class="chatbot-input" id="chatbot-input" placeholder="Type your message..." autocomplete="off" ${!isAuthenticated ? 'disabled' : ''}>
                <button class="chatbot-send-btn" id="chatbot-send-btn" ${!isAuthenticated ? 'disabled' : ''}>
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

    // Store conversation history
    let chatHistory = [];
    const MAX_HISTORY = 10; // Cap history to control token usage
    const API_TIMEOUT_MS = 35000; // 35 second timeout

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
            chatHistory = []; // Reset history
            messagesContainer.innerHTML = `
                <div class="chatbot-message chatbot-message-bot">
                    <p style="margin-bottom:0;">${welcomeMessage}</p>
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
        // Premium Headings
        html = html.replace(/^###\s+(.*)$/gm, '<h4 style="margin: 14px 0 6px 0; color: #1a4331; font-weight: 600; letter-spacing: 0.5px;">$1</h4>');
        html = html.replace(/^##\s+(.*)$/gm, '<h3 style="margin: 18px 0 8px 0; color: #1a4331; font-weight: 700; border-bottom: 1px solid rgba(26,67,49,0.15); padding-bottom: 6px; letter-spacing: 0.5px;">$1</h3>');
        html = html.replace(/^#\s+(.*)$/gm, '<h2 style="margin: 22px 0 10px 0; color: #1a4331; font-weight: 800; border-bottom: 2px solid rgba(26,67,49,0.2); padding-bottom: 6px; letter-spacing: 1px;">$1</h2>');
        
        // Blockquotes (Premium touch)
        html = html.replace(/^>\s+(.*)$/gm, '<blockquote style="border-left: 4px solid #b8860b; background-color: rgba(184,134,11,0.05); padding: 8px 12px; margin: 10px 0; color: #555; font-style: italic; border-radius: 4px;">$1</blockquote>');

        // Bold (Slightly colored to pop)
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #1a4331; font-weight: 700;">$1</strong>');
        // Italic
        html = html.replace(/\*([^\*\n]+)\*/g, '<em>$1</em>');
        // Links (Elegant gold/brown tone)
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #b8860b; text-decoration: none; border-bottom: 1px solid #b8860b; padding-bottom: 1px; font-weight: 500; transition: opacity 0.2s;">$1</a>');
        // Bullet Points (Custom elegant bullets)
        html = html.replace(/^[\*\-]\s+(.*)$/gm, '<div style="margin-left: 8px; padding-left: 12px; position: relative; margin-bottom: 6px;"><span style="position: absolute; left: 0; color: #b8860b;">&bull;</span>$1</div>');
        
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        
        // Clean up excessive line breaks
        html = html.replace(/(<br>\s*){2,}/g, '<br><br>');
        
        // Remove <br> immediately after or before heading/blockquote tags so it doesn't look too spaced out
        html = html.replace(/(<\/h[234]>|<\/blockquote>)\s*(<br>\s*)+/g, '$1');
        html = html.replace(/(<br>\s*)+(<h[234]|<blockquote)/g, '$2');
        
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
            // Push user message to history
            chatHistory.push({ role: 'user', parts: [{ text: message }] });

            // Trim history to last MAX_HISTORY entries
            const trimmedHistory = chatHistory.slice(-MAX_HISTORY);

            const csrftoken = getCookie('csrftoken');

            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ message: message, history: trimmedHistory }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const data = await response.json();
            hideTyping();

            if (response.ok) {
                appendMessage(data.reply || "I'm sorry, I couldn't generate a reply.");
                // Push bot reply to history
                if (data.reply) {
                    chatHistory.push({ role: 'model', parts: [{ text: data.reply }] });
                }
            } else {
                if (response.status === 401 || (data && data.needs_login)) {
                    appendMessage("Please <a href='/login/'>log in</a> to use the chatbot.");
                    inputField.disabled = true;
                    if (sendBtn) sendBtn.disabled = true;
                } else {
                    appendMessage("Error: " + (data.error || "Something went wrong."));
                }
                // Remove the user message from history if the request failed
                chatHistory.pop();
            }

        } catch (error) {
            hideTyping();
            // Remove the user message from history on network/timeout errors
            chatHistory.pop();
            if (error.name === 'AbortError') {
                appendMessage("The request timed out. Please try again.");
            } else {
                appendMessage("Network error. Please try again later.");
            }
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
