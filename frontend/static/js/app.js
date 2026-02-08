/**
 * Assistive Classroom - Frontend JavaScript
 * Accessible, keyboard-friendly implementation
 */

// ===========================================
// Configuration
// ===========================================
const API_BASE = '/api';

// ===========================================
// State
// ===========================================
let currentProvider = 'ollama';
let lastResult = null;
let cameraActive = false;

// ===========================================
// DOM Elements
// ===========================================
const elements = {
    // Announcements
    announcements: document.getElementById('announcements'),

    // Camera
    cameraFrame: document.getElementById('camera-frame'),
    cameraStatus: document.getElementById('status-text'),
    rtspUrl: document.getElementById('rtsp-url'),
    btnStartCamera: document.getElementById('btn-start-camera'),
    btnStopCamera: document.getElementById('btn-stop-camera'),
    btnRefreshFrame: document.getElementById('btn-refresh-frame'),

    // Provider
    providerSelect: document.getElementById('provider-select'),
    apiKeySection: document.getElementById('api-key-section'),
    openaiKeyGroup: document.getElementById('openai-key-group'),
    claudeKeyGroup: document.getElementById('claude-key-group'),
    openaiApiKey: document.getElementById('openai-api-key'),
    claudeApiKey: document.getElementById('claude-api-key'),
    btnSaveOpenaiKey: document.getElementById('btn-save-openai-key'),
    btnSaveClaudeKey: document.getElementById('btn-save-claude-key'),

    // Actions
    btnReadText: document.getElementById('btn-read-text'),
    btnDescribe: document.getElementById('btn-describe'),
    btnSummarize: document.getElementById('btn-summarize'),
    btnDetailed: document.getElementById('btn-detailed'),
    customPrompt: document.getElementById('custom-prompt'),
    btnSendCustom: document.getElementById('btn-send-custom'),

    // Results
    loadingIndicator: document.getElementById('loading-indicator'),
    resultsDisplay: document.getElementById('results-display'),
    resultsPlaceholder: document.getElementById('results-placeholder'),
    resultsContent: document.getElementById('results-content'),
    resultsProvider: document.getElementById('results-provider'),
    resultsText: document.getElementById('results-text'),
    saveNoteSection: document.getElementById('save-note-section'),
    btnSaveNote: document.getElementById('btn-save-note'),

    // Notes
    notesCountText: document.getElementById('notes-count-text'),
    notesList: document.getElementById('notes-list'),
    notesEmpty: document.getElementById('notes-empty'),

    // Help
    helpDialog: document.getElementById('help-dialog'),
    btnHelp: document.getElementById('btn-help'),
    btnCloseHelp: document.getElementById('btn-close-help')
};

// ===========================================
// Utility Functions
// ===========================================

/**
 * Announce message to screen readers
 */
function announce(message) {
    if (elements.announcements) {
        elements.announcements.textContent = message;
        // Clear after a moment to allow re-announcement of same message
        setTimeout(() => {
            elements.announcements.textContent = '';
        }, 1000);
    }
}

/**
 * Show loading state
 */
function showLoading(message = 'Processing...') {
    if (elements.loadingIndicator) {
        elements.loadingIndicator.querySelector('span').textContent = message;
        elements.loadingIndicator.hidden = false;
    }
    announce(message);
}

/**
 * Hide loading state
 */
function hideLoading() {
    if (elements.loadingIndicator) {
        elements.loadingIndicator.hidden = true;
    }
}

/**
 * Update camera status display
 */
function updateCameraStatus(message, isActive = false) {
    if (elements.cameraStatus) {
        elements.cameraStatus.textContent = message;
    }
    cameraActive = isActive;
    announce(message);
}

/**
 * Display results
 */
function displayResults(text, provider = '', model = '') {
    if (elements.resultsPlaceholder) {
        elements.resultsPlaceholder.hidden = true;
    }
    if (elements.resultsContent) {
        elements.resultsContent.hidden = false;
    }
    if (elements.resultsProvider) {
        elements.resultsProvider.textContent = `Provider: ${provider} ${model}`;
    }
    if (elements.resultsText) {
        elements.resultsText.textContent = text;
        elements.resultsText.classList.remove('status-error');
    }
    if (elements.saveNoteSection) {
        elements.saveNoteSection.hidden = false;
    }

    // Store for saving as note
    lastResult = { text, provider, model };

    announce('Results ready. Use Save to Notes button to save.');
}

/**
 * Display error
 */
function displayError(message) {
    if (elements.resultsPlaceholder) {
        elements.resultsPlaceholder.hidden = true;
    }
    if (elements.resultsContent) {
        elements.resultsContent.hidden = false;
    }
    if (elements.resultsProvider) {
        elements.resultsProvider.textContent = 'Error';
    }
    if (elements.resultsText) {
        elements.resultsText.textContent = message;
        elements.resultsText.classList.add('status-error');
    }

    announce('Error: ' + message);
}

/**
 * Make API request
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || 'Request failed');
    }

    return data;
}

// ===========================================
// Camera Functions
// ===========================================

async function startCamera() {
    const rtspUrl = elements.rtspUrl?.value?.trim();

    if (!rtspUrl) {
        announce('Please enter RTSP URL');
        elements.rtspUrl?.focus();
        return;
    }

    try {
        showLoading('Connecting to camera...');
        const data = await apiRequest('/camera/start', 'POST', { rtsp_url: rtspUrl });

        if (data.success) {
            updateCameraStatus('Camera connected', true);
            // Auto-capture first frame
            await refreshFrame();
        } else {
            updateCameraStatus('Failed to connect');
            displayError(data.error || 'Failed to start camera');
        }
    } catch (error) {
        updateCameraStatus('Connection error');
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

async function stopCamera() {
    try {
        showLoading('Stopping camera...');
        const data = await apiRequest('/camera/stop', 'POST');

        if (data.success) {
            updateCameraStatus('Camera stopped', false);
            if (elements.cameraFrame) {
                elements.cameraFrame.src = '';
                elements.cameraFrame.alt = 'No image captured';
            }
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

async function refreshFrame() {
    try {
        showLoading('Capturing frame...');
        const data = await apiRequest('/capture', 'POST');

        if (data.success && data.image) {
            if (elements.cameraFrame) {
                elements.cameraFrame.src = `data:image/jpeg;base64,${data.image}`;
                elements.cameraFrame.alt = 'Captured camera frame';
            }
            announce('Frame captured');
        } else {
            displayError(data.error || 'Failed to capture frame');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

// ===========================================
// LLM Processing Functions
// ===========================================

async function processWithTask(task) {
    try {
        showLoading(`Processing: ${task}...`);

        const endpoint = task === 'read' ? '/read-text' :
                        task === 'describe' ? '/describe' :
                        task === 'summarize' ? '/summarize' : '/read-text';

        const data = await apiRequest(endpoint, 'POST', { provider: currentProvider });

        if (data.success) {
            const text = data.text || data.description || data.summary;
            displayResults(text, data.provider, data.model);
        } else {
            displayError(data.error || 'Processing failed');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

async function processCustomPrompt() {
    const prompt = elements.customPrompt?.value?.trim();

    if (!prompt) {
        announce('Please enter a custom prompt');
        elements.customPrompt?.focus();
        return;
    }

    try {
        showLoading('Processing custom prompt...');

        const data = await apiRequest('/llm/process', 'POST', {
            task: 'custom',
            provider: currentProvider,
            custom_prompt: prompt
        });

        if (data.success) {
            displayResults(data.text, data.provider, data.model);
        } else {
            displayError(data.error || 'Processing failed');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

async function processDetailed() {
    try {
        showLoading('Processing detailed analysis...');

        const detailedPrompt = 'Describe this image in great detail with approximately 2000 words. Include all visible text, objects, people, colors, composition, context, and any other relevant information you can observe.';

        const data = await apiRequest('/llm/process', 'POST', {
            task: 'custom',
            provider: currentProvider,
            custom_prompt: detailedPrompt
        });

        if (data.success) {
            displayResults(data.text, data.provider, data.model);
        } else {
            displayError(data.error || 'Processing failed');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

// ===========================================
// Notes Functions
// ===========================================

async function loadNotes() {
    try {
        const data = await apiRequest('/notes', 'GET');

        if (data.success) {
            renderNotes(data.notes);
            if (elements.notesCountText) {
                elements.notesCountText.textContent = `${data.count} note${data.count !== 1 ? 's' : ''} saved`;
            }
        }
    } catch (error) {
        console.error('Failed to load notes:', error);
    }
}

function renderNotes(notes) {
    if (!elements.notesList) return;

    if (notes.length === 0) {
        if (elements.notesEmpty) {
            elements.notesEmpty.hidden = false;
        }
        // Remove all note items but keep the empty message
        const noteItems = elements.notesList.querySelectorAll('.note-item');
        noteItems.forEach(item => item.remove());
        return;
    }

    if (elements.notesEmpty) {
        elements.notesEmpty.hidden = true;
    }

    // Clear existing notes
    const noteItems = elements.notesList.querySelectorAll('.note-item');
    noteItems.forEach(item => item.remove());

    // Add notes
    notes.forEach(note => {
        const noteElement = createNoteElement(note);
        elements.notesList.appendChild(noteElement);
    });
}

function createNoteElement(note) {
    const div = document.createElement('div');
    div.className = 'note-item';
    div.setAttribute('role', 'listitem');
    div.dataset.noteId = note.id;

    const title = document.createElement('div');
    title.className = 'note-title';
    title.textContent = note.title;

    const content = document.createElement('div');
    content.className = 'note-content';
    content.textContent = note.content.substring(0, 200) + (note.content.length > 200 ? '...' : '');

    const meta = document.createElement('div');
    meta.className = 'note-meta';
    const date = new Date(note.created_at);
    meta.textContent = `${note.type} • ${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;

    const deleteBtn = document.createElement('button');
    deleteBtn.textContent = 'Delete';
    deleteBtn.setAttribute('aria-label', `Delete note: ${note.title}`);
    deleteBtn.addEventListener('click', () => deleteNote(note.id, note.title));

    div.appendChild(title);
    div.appendChild(content);
    div.appendChild(meta);
    div.appendChild(deleteBtn);

    return div;
}

async function saveNote() {
    if (!lastResult) {
        announce('No result to save');
        return;
    }

    try {
        showLoading('Saving note...');

        const data = await apiRequest('/notes', 'POST', {
            title: `${lastResult.provider} - ${new Date().toLocaleString()}`,
            content: lastResult.text,
            type: lastResult.provider
        });

        if (data.success) {
            announce('Note saved successfully');
            await loadNotes();
        } else {
            displayError(data.error || 'Failed to save note');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

async function deleteNote(noteId, noteTitle) {
    if (!confirm(`Delete note "${noteTitle}"?`)) {
        return;
    }

    try {
        showLoading('Deleting note...');

        const data = await apiRequest(`/notes/${noteId}`, 'DELETE');

        if (data.success) {
            announce('Note deleted');
            await loadNotes();
        } else {
            displayError(data.error || 'Failed to delete note');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

// ===========================================
// Provider & API Key Functions
// ===========================================

function updateProviderVisibility() {
    const provider = elements.providerSelect?.value || 'ollama';
    currentProvider = provider;

    // Show/hide API key sections
    const showApiSection = provider === 'openai' || provider === 'claude';

    if (elements.apiKeySection) {
        elements.apiKeySection.hidden = !showApiSection;
    }
    if (elements.openaiKeyGroup) {
        elements.openaiKeyGroup.hidden = provider !== 'openai';
    }
    if (elements.claudeKeyGroup) {
        elements.claudeKeyGroup.hidden = provider !== 'claude';
    }

    announce(`Provider changed to ${provider}`);
}

async function saveApiKey(provider) {
    const keyInput = provider === 'openai' ? elements.openaiApiKey : elements.claudeApiKey;
    const apiKey = keyInput?.value?.trim();

    if (!apiKey) {
        announce('Please enter an API key');
        keyInput?.focus();
        return;
    }

    try {
        showLoading('Saving API key...');

        const body = provider === 'openai'
            ? { openai_api_key: apiKey }
            : { claude_api_key: apiKey };

        const data = await apiRequest('/settings/api-keys', 'POST', body);

        if (data.success) {
            announce(`${provider} API key saved`);
        } else {
            displayError(data.error || 'Failed to save API key');
        }
    } catch (error) {
        displayError(error.message);
    } finally {
        hideLoading();
    }
}

// ===========================================
// Help Dialog
// ===========================================

function openHelpDialog() {
    if (elements.helpDialog) {
        elements.helpDialog.showModal();
        announce('Help dialog opened');
    }
}

function closeHelpDialog() {
    if (elements.helpDialog) {
        elements.helpDialog.close();
        announce('Help dialog closed');
    }
}

// ===========================================
// Keyboard Shortcuts
// ===========================================

function handleKeyboardShortcuts(event) {
    const isInput = event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA';

    // Help dialog: ?
    if (event.key === '?' && !event.shiftKey && !event.ctrlKey) {
        if (!isInput) {
            event.preventDefault();
            openHelpDialog();
        }
    }

    // Close dialog: Escape
    if (event.key === 'Escape') {
        closeHelpDialog();
    }

    // Shift + shortcuts (skip if in input fields)
    if (event.shiftKey && !isInput) {
        switch (event.key.toLowerCase()) {
            // LLM Actions
            case 'r':
                event.preventDefault();
                processWithTask('read');
                break;
            case 'd':
                event.preventDefault();
                processWithTask('describe');
                break;
            case 's':
                event.preventDefault();
                processWithTask('summarize');
                break;
            case 'a':
                event.preventDefault();
                processDetailed();
                break;
            // Camera
            case 'c':
                event.preventDefault();
                refreshFrame();
                break;
            case 'x':
                event.preventDefault();
                startCamera();
                break;
            case 'z':
                event.preventDefault();
                stopCamera();
                break;
            // Notes
            case 'n':
                event.preventDefault();
                saveNote();
                break;
            case 'l':
                event.preventDefault();
                loadNotes();
                announce('Notes refreshed');
                break;
        }
    }
}

// ===========================================
// Event Listeners
// ===========================================

function initEventListeners() {
    // Camera controls
    elements.btnStartCamera?.addEventListener('click', startCamera);
    elements.btnStopCamera?.addEventListener('click', stopCamera);
    elements.btnRefreshFrame?.addEventListener('click', refreshFrame);

    // Provider selection
    elements.providerSelect?.addEventListener('change', updateProviderVisibility);

    // API key saving
    elements.btnSaveOpenaiKey?.addEventListener('click', () => saveApiKey('openai'));
    elements.btnSaveClaudeKey?.addEventListener('click', () => saveApiKey('claude'));

    // LLM actions
    elements.btnReadText?.addEventListener('click', () => processWithTask('read'));
    elements.btnDescribe?.addEventListener('click', () => processWithTask('describe'));
    elements.btnSummarize?.addEventListener('click', () => processWithTask('summarize'));
    elements.btnDetailed?.addEventListener('click', processDetailed);
    elements.btnSendCustom?.addEventListener('click', processCustomPrompt);

    // Notes
    elements.btnSaveNote?.addEventListener('click', saveNote);

    // Help dialog
    elements.btnHelp?.addEventListener('click', openHelpDialog);
    elements.btnCloseHelp?.addEventListener('click', closeHelpDialog);

    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);

    // Enter key for custom prompt
    elements.customPrompt?.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && event.ctrlKey) {
            event.preventDefault();
            processCustomPrompt();
        }
    });
}

// ===========================================
// Initialization
// ===========================================

function init() {
    console.log('Assistive Classroom initializing...');

    // Initialize event listeners
    initEventListeners();

    // Load initial data
    loadNotes();

    // Set initial provider visibility
    updateProviderVisibility();

    // Announce ready
    announce('Assistive Classroom ready');

    console.log('Assistive Classroom initialized');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
