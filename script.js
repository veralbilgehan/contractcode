document.addEventListener('DOMContentLoaded', () => {
    const landing = document.getElementById('landing');
    const views = { contract: document.getElementById('mode-contract'), search: document.getElementById('mode-search'), chat: document.getElementById('mode-chat') };

    function esc(text) { const d = document.createElement('div'); d.textContent = text; return d.innerHTML; }

    function showView(id) {
        landing.classList.add('hidden');
        Object.values(views).forEach(v => v.classList.add('hidden'));
        if (views[id]) views[id].classList.remove('hidden');
    }

    // Mode cards
    document.querySelectorAll('[data-mode]').forEach(btn => {
        btn.addEventListener('click', () => showView(btn.dataset.mode));
    });

    // Back buttons
    document.querySelectorAll('[data-back]').forEach(btn => {
        btn.addEventListener('click', () => {
            Object.values(views).forEach(v => v.classList.add('hidden'));
            landing.classList.remove('hidden');
        });
    });

    // === MODE 1: Contract ===
    const contractBtn = document.getElementById('contractBtn');
    const contractOutput = document.getElementById('contractOutput');
    contractBtn.addEventListener('click', async () => {
        const text = document.getElementById('contractText').value.trim();
        const goal = document.getElementById('contractGoal').value.trim();
        if (!text) return alert('Lütfen sözleşme metnini girin.');
        contractBtn.disabled = true;
        contractBtn.textContent = 'Analiz ediliyor...';
        contractOutput.innerHTML = '<div class="loading">Analiz yapılıyor, lütfen bekleyin...</div>';
        try {
            const res = await fetch('/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ documentText: text, goal: goal || 'risk tespiti' }) });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Sunucu hatası');
            const data = await res.json();
            contractOutput.innerHTML = `<div class="result-box">${data.analysis}</div>`;
        } catch (e) {
            contractOutput.innerHTML = `<div class="error-text">Hata: ${esc(e.message)}</div>`;
        } finally {
            contractBtn.disabled = false;
            contractBtn.textContent = 'Analiz Et';
        }
    });

    // === MODE 2: Search ===
    const searchBtn = document.getElementById('searchBtn');
    const searchOutput = document.getElementById('searchOutput');
    searchBtn.addEventListener('click', async () => {
        const query = document.getElementById('searchQuery').value.trim();
        if (!query) return alert('Lütfen arama konusunu girin.');
        searchBtn.disabled = true;
        searchBtn.textContent = 'Araştırılıyor...';
        searchOutput.innerHTML = '<div class="loading">Mevzuat ve içtihatlar taranıyor...</div>';
        try {
            const res = await fetch('/search', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Sunucu hatası');
            const data = await res.json();
            searchOutput.innerHTML = `<div class="result-box">${data.result}</div>`;
        } catch (e) {
            searchOutput.innerHTML = `<div class="error-text">Hata: ${esc(e.message)}</div>`;
        } finally {
            searchBtn.disabled = false;
            searchBtn.textContent = 'Araştır';
        }
    });

    // === MODE 3: Chat ===
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatBtn = document.getElementById('chatBtn');

    function addMsg(role, text) {
        const div = document.createElement('div');
        div.className = `msg ${role}`;
        div.innerHTML = role === 'user' ? esc(text) : text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return div;
    }

    async function sendChat() {
        const msg = chatInput.value.trim();
        if (!msg) return;
        chatInput.value = '';
        addMsg('user', msg);
        chatBtn.disabled = true;
        const loading = addMsg('bot', 'Düşünüyorum...');
        try {
            const res = await fetch('/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) });
            if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || 'Sunucu hatası');
            const data = await res.json();
            loading.innerHTML = data.reply;
        } catch (e) {
            loading.innerHTML = `<span class="error-text">Hata: ${esc(e.message)}</span>`;
        } finally {
            chatBtn.disabled = false;
        }
    }

    chatBtn.addEventListener('click', sendChat);
    chatInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } });
});
