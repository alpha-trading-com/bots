// Tab functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });

    const fetchDmBtn = document.getElementById('fetch-dm-btn');
    const clearDmBtn = document.getElementById('clear-dm-btn');
    const userId = "1285396632921309267";
    const dmResults = document.getElementById('dm-results');

    fetchDmBtn.addEventListener('click', async function() {
        // Disable button during fetch
        fetchDmBtn.disabled = true;
        fetchDmBtn.textContent = 'Loading...';
        dmResults.innerHTML = '<div class="loading">Fetching history...</div>';

        try {
            const response = await fetch(`/api/dm/messages/${userId}?limit=100`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            displayDmResults(data);
        } catch (error) {
            dmResults.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        } finally {
            fetchDmBtn.disabled = false;
            fetchDmBtn.textContent = 'Fetch History';
        }
    });


    function displayDmResults(data) {
        const messages = data.messages || [];
        const channelId = data.channel_id || 'N/A';

        if (messages.length === 0) {
            dmResults.innerHTML = '<div class="info">No messages found in history.</div>';
            return;
        }

        let html = "";

        html += '<div class="messages-container">';
        messages.forEach(msg => {
            const timestamp = msg.timestamp ? new Date(msg.timestamp).toLocaleString() : 'Unknown';
            const authorClass = msg.is_bot ? 'bot-message' : 'user-message';
            html += `
                <div class="message ${authorClass}">
                    <div class="message-content">${escapeHtml(msg.content || '(No content)')}</div>
                </div>
            `;
        });
        html += '</div>';

        dmResults.innerHTML = html;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    const channelMessageInput = document.getElementById('channel-message-input');
    const sendChannelBtn = document.getElementById('send-channel-btn');
    console.log(sendChannelBtn);
    console.log(channelMessageInput);

    sendChannelBtn.addEventListener('click', async function() {
        const content = channelMessageInput.value.trim();
        if (!content) {
            return;
        }
        sendChannelMessage(content);
    });

    function sendChannelMessage(content) {
        fetch(`/api/dm/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: content, user_id: userId }),
        }).then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        }).then(data => {
            channelMessageInput.value = '';
            channelMessageInput.focus();
        }).catch(error => {
            console.error('Error:', error);
            alert('Failed to send message: ' + (error.detail || error.message || 'Unknown error'));
        });
    }

    const clearChannelBtn = document.getElementById('clear-channel-btn');
    clearChannelBtn.addEventListener('click', function() {
        clearChannelMessages(); 
    });

    function clearChannelMessages() {
        fetch(`/api/channel/clear?user_id=${encodeURIComponent(userId)}`, {
            method: 'POST',
        }).then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        }).then(data => {
            console.log(data);
        }).catch(error => {
            console.error('Error:', error);
            alert('Failed to clear messages: ' + (error.detail || error.message || 'Unknown error'));
        });
    }
});

