const chatDisplay = document.getElementById('chat-display');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const emailInput = document.getElementById('customer-email');

let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);

async function sendMessage() {
    const message = userInput.value.trim();
    const email = emailInput.value.trim();

    if (!message || !email) return;

    // Add user message to UI
    addMessage(message, 'user');
    userInput.value = '';

    // Add typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                customer_email: email,
                session_id: sessionId
            }),
        });

        const data = await response.json();
        removeTypingIndicator(typingId);

        if (data.response) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage("Sorry, I encountered an error. Please try again.", 'assistant');
        }
    } catch (error) {
        console.error('Error:', error);
        removeTypingIndicator(typingId);
        addMessage("Connection error. Is the backend running?", 'assistant');
    }
}

function addMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}`;
    
    // Convert markdown-like syntax (very basic) to HTML
    const formattedText = text.replace(/\n/g, '<br>');
    
    msgDiv.innerHTML = `<div class="bubble">${formattedText}</div>`;
    chatDisplay.appendChild(msgDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.id = id;
    typingDiv.className = 'message assistant';
    typingDiv.innerHTML = '<div class="bubble">...</div>';
    chatDisplay.appendChild(typingDiv);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
