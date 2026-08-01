/**
 * Chat Polling and AJAX CSRF Handler
 */

document.addEventListener('DOMContentLoaded', () => {
  const chatBox = document.getElementById('chatBox');
  const chatForm = document.getElementById('chatForm');
  const messageInput = document.getElementById('messageInput');
  const getCsrfToken = () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

  if (chatBox && chatForm) {
    const chatId = chatBox.dataset.chatId;
    let lastMessageId = parseInt(chatBox.dataset.lastId || 0);

    const scrollToBottom = () => {
      chatBox.scrollTop = chatBox.scrollHeight;
    };

    scrollToBottom();

    // AJAX Form submission
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const content = messageInput.value.trim();
      if (!content) return;

      messageInput.value = '';

      try {
        const response = await fetch(`/chat/${chatId}/send`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ content })
        });

        if (response.ok) {
          const data = await response.json();
          appendMessage(data.message, true);
          lastMessageId = Math.max(lastMessageId, data.message.id);
          scrollToBottom();
        }
      } catch (err) {
        console.error('Failed to send message:', err);
      }
    });

    // Short-interval polling every 3 seconds
    setInterval(async () => {
      try {
        const response = await fetch(`/chat/${chatId}/messages?after=${lastMessageId}`, {
          headers: {
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
              if (msg.id > lastMessageId) {
                const currentUserId = parseInt(document.body.dataset.userId || 0);
                const isSentByMe = (msg.sender_id === currentUserId);
                appendMessage(msg, isSentByMe);
                lastMessageId = Math.max(lastMessageId, msg.id);
              }
            });
            scrollToBottom();
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    function appendMessage(msg, isSentByMe) {
      const bubbleClass = isSentByMe ? 'message-sent' : 'message-received';
      const div = document.createElement('div');
      div.className = `message-bubble ${bubbleClass}`;
      div.innerHTML = `
        <div class="small text-muted mb-1" style="${isSentByMe ? 'color: #e0e7ff !important;' : ''}">${escapeHtml(msg.sender_name)}</div>
        <div>${escapeHtml(msg.content)}</div>
        <div class="small text-end mt-1 opacity-75" style="font-size: 0.7rem;">${msg.sent_at}</div>
      `;
      chatBox.appendChild(div);
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
  }
});
