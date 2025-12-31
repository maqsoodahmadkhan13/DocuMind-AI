const API_URL = "http://127.0.0.1:8000";
let state = {
    token: localStorage.getItem('token') || null,
    user: localStorage.getItem('user') || null,
    docId: localStorage.getItem('docId') || null,
    filename: localStorage.getItem('filename') || null
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    if (state.docId) {
        updateActiveDocForUI();
    }

    // Global drag prevention to stop browser from opening dropped files
    window.addEventListener('dragover', e => e.preventDefault());
    window.addEventListener('drop', e => e.preventDefault());
});

function checkAuth() {
    const authSection = document.getElementById('auth-section');
    const dashboardSection = document.getElementById('dashboard-section');

    if (state.token) {
        authSection.classList.add('hidden');
        authSection.classList.remove('active');
        dashboardSection.classList.remove('hidden');
        dashboardSection.classList.add('active');
        document.getElementById('username-display').innerText = state.user || 'User';
    } else {
        dashboardSection.classList.add('hidden');
        dashboardSection.classList.remove('active');
        authSection.classList.remove('hidden');
        authSection.classList.add('active');
    }
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

// --- Auth Functions ---
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            body: formData
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Login failed' }));
            throw new Error(errorData.detail || 'Login failed');
        }
        const data = await res.json();

        if (!data.access_token) {
            throw new Error('Invalid response from server');
        }

        loginSuccess(data.access_token, username);
    } catch (err) {
        alert(err.message || 'Login failed. Please try again.');
    }
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;

    try {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Registration failed' }));
            throw new Error(errorData.detail || 'Registration failed');
        }
        alert("Registration success! Please sign in.");
        switchAuth('login');
    } catch (err) {
        alert(err.message || 'Registration failed. Please try again.');
    }
});

function loginSuccess(token, username) {
    state.token = token;
    state.user = username;
    localStorage.setItem('token', token);
    localStorage.setItem('user', username);
    checkAuth();
    showToast(`Welcome, ${username}!`);
}

function logout() {
    state = { token: null, user: null, docId: null, filename: null };
    localStorage.clear();
    checkAuth();
}

function switchAuth(type) {
    const loginForm = document.getElementById('login-form');
    const regForm = document.getElementById('register-form');
    if (type === 'register') {
        loginForm.classList.add('hidden');
        regForm.classList.remove('hidden');
    } else {
        regForm.classList.add('hidden');
        loginForm.classList.remove('hidden');
    }
}

// --- Navigation ---
function switchTab(tabId) {
    // Update Sidebar
    document.querySelectorAll('.nav-links li').forEach(li => li.classList.remove('active'));
    const activeNavItem = document.querySelector(`.nav-links li[onclick="switchTab('${tabId}')"]`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    // Update Content
    document.querySelectorAll('.tab-content').forEach(div => {
        div.classList.remove('active');
        div.classList.add('hidden');
    });

    const target = document.getElementById(`${tabId}-tab`);
    if (target) {
        target.classList.remove('hidden');
        setTimeout(() => target.classList.add('active'), 50); // fade in
    }
}

// --- File Upload ---
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => handleUpload(e.target.files[0]));

async function handleUpload(file) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const statusDiv = document.getElementById('upload-status');
    statusDiv.innerText = "Uploading & Processing...";

    try {
        const res = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${state.token}` },
            body: formData
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
            throw new Error(errorData.detail || 'Upload failed');
        }
        const data = await res.json();

        if (!data.id || !data.filename) {
            throw new Error('Invalid response from server');
        }

        state.docId = data.id;
        state.filename = data.filename;
        localStorage.setItem('docId', data.id);
        localStorage.setItem('filename', data.filename);

        statusDiv.innerText = "";
        updateActiveDocForUI();
        showToast("Document Processed Successfully");
    } catch (err) {
        statusDiv.innerText = "Error: " + err.message;
    }
}

function updateActiveDocForUI() {
    if (state.filename) {
        console.log("Updating UI for doc:", state.filename);
        const card = document.getElementById('active-doc-card');
        card.classList.remove('hidden');
        card.style.display = 'flex'; // Force display just in case
        document.getElementById('active-filename').innerText = state.filename;
        document.getElementById('chat-doc-name').innerText = state.filename;
    }
}

// --- Chat ---
async function sendChat() {
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg || !state.docId) {
        if (!state.docId) alert("Please upload a document first.");
        return;
    }

    addMessageToUI('user', msg);
    input.value = '';

    try {
        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ doc_id: state.docId, question: msg })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to get answer');
        }

        const data = await res.json();
        addMessageToUI('ai', data.answer);
    } catch (err) {
        addMessageToUI('system', `Error: ${err.message || 'Failed to fetch answer.'}`);
    }
}

function addMessageToUI(role, text) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    // Use textContent instead of innerText for better security and consistency
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// --- Quiz ---
async function generateQuiz() {
    if (!state.docId) { showToast("Upload a document first"); return; }

    const count = parseInt(document.getElementById('quiz-count').value);
    const type = document.getElementById('quiz-type').value;
    const resultContainer = document.getElementById('quiz-results');

    resultContainer.innerHTML = '<p>Generating Quiz...</p>';
    resultContainer.classList.remove('hidden');

    try {
        const res = await fetch(`${API_URL}/quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ doc_id: state.docId, num_questions: count, quiz_type: type })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to generate quiz');
        }

        const data = await res.json();
        if (!data.questions || !Array.isArray(data.questions)) {
            throw new Error('Invalid quiz data received');
        }
        renderQuiz(data.questions);
    } catch (err) {
        resultContainer.innerHTML = `<p>Error: ${err.message || 'Failed to generate quiz.'}</p>`;
    }
}

function renderQuiz(questions) {
    const container = document.getElementById('quiz-results');
    container.innerHTML = '';

    questions.forEach((q, idx) => {
        const card = document.createElement('div');
        card.className = 'quiz-card-item';

        let optionsHtml = '';
        if (q.options && q.options.length > 0) {
            // Escape HTML and quotes properly
            const escapedCorrect = String(q.correct_answer).replace(/'/g, "\\'").replace(/"/g, '&quot;');
            optionsHtml = `<div class="quiz-options">
                ${q.options.map(opt => {
                const escapedOpt = String(opt).replace(/"/g, '&quot;').replace(/'/g, "&#39;");
                return `<div class="option-btn" onclick="checkAnswer(this, '${escapedCorrect}')">${escapedOpt}</div>`;
            }).join('')}
            </div>`;
        } else {
            const escapedAnswer = String(q.correct_answer).replace(/"/g, '&quot;').replace(/'/g, "&#39;");
            optionsHtml = `<p class="mt-2 text-muted">Thinking point: <span class="blur-reveal" onclick="this.classList.remove('blur-reveal')">${escapedAnswer}</span></p>`;
        }

        card.innerHTML = `
            <h4>Q${idx + 1}: ${q.question_text}</h4>
            ${optionsHtml}
        `;
        container.appendChild(card);
    });
}

function checkAnswer(el, correct) {
    if (el.innerText === correct) {
        el.style.borderColor = 'var(--success)';
        el.style.color = 'var(--success)';
    } else {
        el.style.borderColor = '#ef4444';
        el.style.textDecoration = 'line-through';
    }
}

// --- Summary ---
async function generateSummary(length, buttonElement) {
    if (!state.docId) { showToast("Upload a document first"); return; }

    // Update UI buttons
    document.querySelectorAll('.summary-controls button').forEach(btn => btn.classList.remove('active'));
    if (buttonElement) {
        buttonElement.classList.add('active');
    } else {
        // Fallback: find button by checking onclick attribute
        const buttons = document.querySelectorAll('.summary-controls button');
        buttons.forEach(btn => {
            const onclickAttr = btn.getAttribute('onclick');
            if (onclickAttr && onclickAttr.includes(`'${length}'`)) {
                btn.classList.add('active');
            }
        });
    }

    const contentBox = document.getElementById('summary-content');
    contentBox.innerHTML = '<p>Generating summary...</p>';

    try {
        const res = await fetch(`${API_URL}/summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ doc_id: state.docId, length: length })
        });

        if (!res.ok) {
            const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || 'Failed to generate summary');
        }

        const data = await res.json();
        if (!data.summary) {
            throw new Error('No summary received');
        }
        // Escape HTML to prevent XSS
        const escapedSummary = String(data.summary).replace(/</g, '&lt;').replace(/>/g, '&gt;');
        contentBox.innerHTML = `<p>${escapedSummary}</p>`;
    } catch (err) {
        contentBox.innerHTML = `<p>Error: ${err.message || 'Failed to generate summary.'}</p>`;
    }
}
