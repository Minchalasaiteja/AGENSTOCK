// AI Chat page logic for AGENSTOCK

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    let ws;
    let sessionId = null;
    let currentAiMessageElement = null;
    const chatMessages = document.getElementById('chatMessages');

    function appendMessage(content, sender) {
      const msgDiv = document.createElement('div');
      msgDiv.className = `chat-message ${sender}`;
      if (sender === 'ai') {
          // For AI, we create the element but wait for stream
          msgDiv.innerHTML = '<span></span>';
          chatMessages.appendChild(msgDiv);
          currentAiMessageElement = msgDiv.querySelector('span'); // This will be the target for streaming
      } else if (sender === 'system') {
          msgDiv.innerHTML = `<span>${content}</span>`;
          chatMessages.appendChild(msgDiv);
      } else {
          // User messages are instant
          msgDiv.innerHTML = `<span>${content}</span>`;
          chatMessages.appendChild(msgDiv);
      }
      chatMessages.appendChild(msgDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function connectWebSocket(userId) {
        ws = new WebSocket(`ws://localhost:8000/api/chat/ws/${userId}`);

        ws.onopen = () => {
            // The server will send a welcome message upon connection.
            // No action needed here, we just wait for the onmessage event.
        };

        ws.onmessage = (event) => {
            let content = '';
            let data;
            try {
                data = JSON.parse(event.data);
                content = data.content || '';
            } catch (e) {
                appendMessage('Received an invalid response from the server.', 'system');
                return;
            }

            if (data.type === 'stream' && currentAiMessageElement) {
                currentAiMessageElement.innerHTML += content; // Append content as it arrives
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else if (data.type === 'stream_end') {
                currentAiMessageElement = null; // Reset for the next message
            } else if (data.type === 'system') {
                appendMessage(content, 'system');
            } else if (data.content) {
                // Fallback for non-streaming AI messages
                appendMessage(data.content, 'ai');
                currentAiMessageElement.innerHTML = data.content;
                currentAiMessageElement = null;
            }
        };

        ws.onclose = () => {
            appendMessage('Connection closed. Please refresh the page to reconnect.', 'system');
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            appendMessage('Unable to connect to the chat service. Please check your connection.', 'system');
        };
    }

    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const content = chatInput.value.trim();
        if (!content) return;

        appendMessage(content, 'user');

        // Prepare the AI message container for the streaming response
        appendMessage('', 'ai');

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                session_id: sessionId,
                content,
                type: 'chat' // This can be dynamic for different query types
            }));
        } else {
            appendMessage('Not connected to chat service. Please wait or refresh.', 'system');
        }
        chatInput.value = '';
    });

    // Fetch user ID and connect WebSocket
    fetch('/api/auth/me', { credentials: 'include' })
        .then(res => res.json())
        .then(async user => {
            if (!user || !user.username) {
                window.location.href = '/login';
                return;
            }
            // Create a new chat session and get its ID
            const sessionResponse = await fetch('/api/chat/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ title: 'New Chat' })
            });

            if (!sessionResponse.ok) {
                throw new Error('Could not create a chat session.');
            }

            const session = await sessionResponse.json();
            sessionId = session.session_id;
            connectWebSocket(user.username);
        })
        .catch(error => {
            console.error("Chat initialization failed:", error);
            appendMessage('Failed to initialize chat. Please refresh the page.', 'system');
        });
});
