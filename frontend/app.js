const chatDisplay = document.getElementById('chat-display');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const emailInput = document.getElementById('customer-email');

let sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
const statusIndicator = document.getElementById('connection-status');
const statusText = statusIndicator.querySelector('.status-text');

let lastMessageCount = 0;
let isPolling = false;

async function checkConnection() {
    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'Backend Online';
        } else {
            throw new Error('Not OK');
        }
    } catch (error) {
        statusIndicator.className = 'status-indicator offline';
        statusText.textContent = 'Backend Offline';
    }
}

// Check every 5 seconds
checkConnection();
setInterval(checkConnection, 5000);

async function pollMessages() {
    if (isPolling) return;
    const email = emailInput.value.trim();
    if (!email) return;

    isPolling = true;
    try {
        // We use the same chat endpoint or a new one to get history
        // For simplicity, let's add a quick history fetch in the background
        const response = await fetch(`http://localhost:8000/chat/history?session_id=${sessionId}&email=${email}`);
        if (response.ok) {
            const messages = await response.json();
            if (messages.length > lastMessageCount) {
                // New messages found!
                const newMsgs = messages.slice(lastMessageCount);
                newMsgs.forEach(m => {
                    if (m.role === 'assistant' || m.role === 'human') {
                        addMessage(m.content, 'assistant');
                    }
                });
                lastMessageCount = messages.length;
            }
        }
    } catch (error) {
        console.error("Polling error:", error);
    } finally {
        isPolling = false;
    }
}

// Start polling every 3 seconds
setInterval(pollMessages, 3000);

async function sendMessage() {
    const message = userInput.value.trim();
    const email = emailInput.value.trim();

    if (!message || !email) return;

    // Add user message to UI
    addMessage(message, 'user');
    lastMessageCount++; // Increment for polling
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
            // Update the count so polling doesn't duplicate this
            lastMessageCount++;
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
