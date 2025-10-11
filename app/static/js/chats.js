// chats.js - fetches user sessions and messages and renders them
(async function(){
    const sessionsList = document.getElementById('sessionsList');
    const conversationArea = document.getElementById('conversationArea');
    const noSessions = document.getElementById('noSessions');
    const noConversation = document.getElementById('noConversation');

    async function fetchSessions(){
        try{
            const res = await fetch('/api/chat/sessions', { credentials: 'include' });
            if(res.status === 401){ window.location.href = '/login'; return; }
            const sessions = await res.json();
            renderSessions(sessions);
        }catch(err){
            sessionsList.innerHTML = '<p style="color:var(--danger-color)">Failed to load sessions</p>';
            console.error(err);
        }
    }

    function renderSessions(sessions){
        if(!sessions || sessions.length === 0){
            noSessions.textContent = 'No conversations yet.';
            return;
        }
        noSessions.remove();
        sessionsList.innerHTML = '';
        sessions.forEach(sess => {
            const el = document.createElement('div');
            el.className = 'session-item';
            el.style.padding = '0.5rem';
            el.style.borderBottom = '1px solid #f1f1f1';
            el.style.cursor = 'pointer';
            el.innerHTML = `<strong>${sess.title || 'Untitled'}</strong><div style="font-size:0.9rem;color:var(--gray-color)">${sess.message_count || 0} messages · ${new Date(sess.updated_at).toLocaleString()}</div>`;
            el.addEventListener('click', () => loadConversation(sess.session_id || sess._id));
            sessionsList.appendChild(el);
        });
    }

    async function loadConversation(sessionId){
        try{
            const res = await fetch(`/api/chat/sessions/${sessionId}/messages`, { credentials: 'include' });
            if(res.status === 401){ window.location.href = '/login'; return; }
            const messages = await res.json();
            renderConversation(messages);
        }catch(err){
            conversationArea.innerHTML = '<p style="color:var(--danger-color)">Failed to load messages</p>';
            console.error(err);
        }
    }

    function renderConversation(messages){
        conversationArea.innerHTML = '';
        if(!messages || messages.length === 0){
            conversationArea.innerHTML = '<p style="color:var(--gray-color)">No messages in this conversation yet.</p>';
            return;
        }
        messages.forEach(m => {
            const wrapper = document.createElement('div');
            wrapper.style.display = 'flex';
            wrapper.style.flexDirection = 'column';
            wrapper.style.gap = '0.25rem';

            const meta = document.createElement('div');
            meta.style.fontSize = '0.8rem';
            meta.style.color = 'var(--gray-color)';
            meta.textContent = `${m.message_type.toUpperCase()} · ${m.timestamp ? new Date(m.timestamp).toLocaleString() : ''}`;

            const msg = document.createElement('div');
            msg.className = 'chat-message ' + (m.message_type === 'ai' ? 'ai' : (m.message_type === 'system' ? 'system' : 'user'));
            msg.style.marginBottom = '0.5rem';
            msg.style.padding = '0.75rem 1rem';
            msg.style.borderRadius = '12px';
            msg.style.maxWidth = '80%';
            msg.textContent = m.content;
            if(m.message_type === 'user') msg.style.alignSelf = 'flex-end';

            wrapper.appendChild(meta);
            wrapper.appendChild(msg);
            conversationArea.appendChild(wrapper);
        });
    }

    // Initial load
    // If there is a session_id in the path, auto-open it
    const pathParts = window.location.pathname.split('/').filter(Boolean);
    const maybeSessionId = pathParts.length >= 2 ? pathParts[1] : null; // /chats/{session_id}
    fetchSessions().then(() => {
        if (maybeSessionId) {
            loadConversation(maybeSessionId);
        }
    });

    // Optional: poll for new sessions every 10s
    setInterval(fetchSessions, 10000);
})();
