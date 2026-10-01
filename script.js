document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const eventSummaryInput = document.getElementById('eventSummary');
    const documentTextInput = document.getElementById('documentText');
    const goalInput = document.getElementById('goal');
    const chatMessages = document.getElementById('chatMessages');

    // Sanitize text to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function appendMessage(sender, htmlContent) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = htmlContent;
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    analyzeBtn.addEventListener('click', async () => {
        const eventSummary = eventSummaryInput.value.trim();
        const documentText = documentTextInput.value.trim();
        const goal = goalInput.value.trim();

        if (!eventSummary && !documentText && !goal) {
            alert('Lütfen en az bir alanı doldurunuz.');
            return;
        }

        // Add user request summary message (escaped)
        appendMessage('user', `
            <strong>Olay:</strong> ${escapeHtml(eventSummary) || '-'}<br>
            <strong>Amaç:</strong> ${escapeHtml(goal) || '-'}
        `);

        // Add loading bot message
        analyzeBtn.disabled = true;
        analyzeBtn.innerText = 'Analiz Ediliyor... ⏳';
        const loadingMsg = appendMessage('bot', '<em>Hukuk ajanları mevzuat ve içtihatları inceliyor, lütfen bekleyin...</em>');

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    eventSummary: eventSummary,
                    documentText: documentText,
                    goal: goal
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || `Sunucu hatası: ${response.status}`);
            }

            const data = await response.json();
            
            // Replace loading message with report
            loadingMsg.querySelector('.message-content').innerHTML = `
                <div class="report-box">
                    <div class="section-title">🔬 HUKUKİ ANALİZ RAPORU</div>
                    <div style="white-space: pre-wrap; line-height: 1.6;">${data.analysis}</div>
                </div>
            `;
        } catch (error) {
            loadingMsg.querySelector('.message-content').innerHTML = `
                <div style="color: #e74c3c;">
                    <strong>❌ Hata Oluştu:</strong> ${escapeHtml(error.message)}
                </div>
            `;
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerText = 'Analizi Başlat 🚀';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    });
});
