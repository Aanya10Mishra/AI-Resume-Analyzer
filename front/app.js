console.log('✅ app.js is loading...');

// ==================== CONFIGURATION ====================
const API_URL = 'http://localhost:5000';

// ==================== STATE ====================
let currentUser = null;
let resumes = [];
let jobDescriptions = [];
let selectedFile = null;
let analysisProgressInterval = null;
let activeOperationId = null;
let activeOperationName = null;
let analysisRenderNonce = 0;
let latestAnalysisSnapshot = null;
let latestAISnapshot = null;
let aiWorkspaceRawText = '';
let aiWorkspaceTitle = 'AI Results Workspace';

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ App loaded!');
    
    // Initialize AOS
    if (typeof AOS !== 'undefined') {
        AOS.init({ duration: 800, once: true });
    }
    
    // Hide status banner after 2 seconds
    setTimeout(function() {
        var statusEl = document.getElementById('api-status');
        if (statusEl) statusEl.style.display = 'none';
    }, 2000);
    
    // Load user
    loadUserFromStorage();
    
    // Setup forms
    setupForms();
    
    // Setup navigation
    setupNavigation();
    
    // If user is logged in, show dashboard; otherwise show landing
    if (currentUser) {
        showSection('dashboard');
        var lastTab = localStorage.getItem('activeDashboardTab') || 'resumes';
        showDashboardTab(lastTab);
    }
    
    // Initial file upload setup
    setupFileUpload();
});

// ==================== NAVIGATION SETUP ====================
function setupNavigation() {
    var featuresLink = document.querySelector('a[href="#features"]');
    var howItWorksLink = document.querySelector('a[href="#how-it-works"]');
    
    if (featuresLink) {
        featuresLink.addEventListener('click', function(e) {
            e.preventDefault();
            showSection('landing');
            setTimeout(function() {
                var featuresSection = document.getElementById('features');
                if (featuresSection) {
                    featuresSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        });
    }
    
    if (howItWorksLink) {
        howItWorksLink.addEventListener('click', function(e) {
            e.preventDefault();
            showSection('landing');
            setTimeout(function() {
                var howItWorksSection = document.getElementById('how-it-works');
                if (howItWorksSection) {
                    howItWorksSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        });
    }
    
    console.log('✅ Navigation setup complete');
}

// ==================== API STATUS ====================
async function checkAPIStatus() {
    var statusEl = document.getElementById('api-status');
    var statusText = document.getElementById('status-text');
    
    if (!statusEl || !statusText) return;
    
    try {
        // Create abort controller for timeout
        var controller = new AbortController();
        var timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
        
        var response = await fetch(API_URL + '/api/health', { signal: controller.signal });
        clearTimeout(timeoutId);
        
        var data = await response.json();
        
        statusEl.className = 'fixed top-16 left-0 right-0 z-30 text-center py-2 text-sm font-medium bg-green-100 text-green-800';
        statusText.innerHTML = '✅ Backend connected - ' + (data.embedding_model || 'Ready');
        
        setTimeout(function() {
            statusEl.style.display = 'none';
        }, 3000);
    } catch (error) {
        console.error('❌ Backend not connected:', error.message);
        statusEl.className = 'fixed top-16 left-0 right-0 z-30 text-center py-2 text-sm font-medium bg-yellow-100 text-yellow-800';
        statusText.innerHTML = '⚠️ Connecting to backend... Try refreshing in a moment';
        
        // Retry after 3 seconds
        setTimeout(checkAPIStatus, 3000);
    }
}

// ==================== USER STORAGE ====================
function loadUserFromStorage() {
    var saved = localStorage.getItem('user');
    if (saved) {
        currentUser = JSON.parse(saved);
        console.log('✅ User loaded:', currentUser.email);
        updateUIForLoggedInUser();
    }
}

function updateUIForLoggedInUser() {
    var authButtons = document.getElementById('auth-buttons');
    var userMenu = document.getElementById('user-menu');
    var userName = document.getElementById('user-name');
    var userRole = document.getElementById('user-role');
    var dashboardUserName = document.getElementById('dashboard-user-name');
    var dashboardRoleBadge = document.getElementById('dashboard-role-badge');
    
    if (authButtons) authButtons.classList.add('hidden');
    if (userMenu) userMenu.classList.remove('hidden');
    if (userName) userName.textContent = currentUser.full_name;
    if (userRole) userRole.textContent = currentUser.role;
    if (dashboardUserName) dashboardUserName.textContent = currentUser.full_name;
    if (dashboardRoleBadge) dashboardRoleBadge.textContent = currentUser.role;
}

function updateUIForLoggedOutUser() {
    var authButtons = document.getElementById('auth-buttons');
    var userMenu = document.getElementById('user-menu');
    
    if (authButtons) authButtons.classList.remove('hidden');
    if (userMenu) userMenu.classList.add('hidden');
}

function getAnalysisStorageKey() {
    if (!currentUser || !currentUser.id) return null;
    return 'latestAnalysis:' + currentUser.id;
}

function getResumeNameById(resumeId) {
    for (var i = 0; i < resumes.length; i++) {
        if (parseInt(resumes[i].id) === parseInt(resumeId)) {
            return resumes[i].filename || ('Resume #' + resumeId);
        }
    }
    return 'Resume #' + resumeId;
}

function getJDTitleById(jdId) {
    for (var i = 0; i < jobDescriptions.length; i++) {
        if (parseInt(jobDescriptions[i].id) === parseInt(jdId)) {
            return jobDescriptions[i].title || ('JD #' + jdId);
        }
    }
    return 'JD #' + jdId;
}

function saveLatestAnalysisSnapshot(snapshot) {
    latestAnalysisSnapshot = snapshot;
    var key = getAnalysisStorageKey();
    if (!key) return;
    try {
        localStorage.setItem(key, JSON.stringify(snapshot));
    } catch (e) {
        console.warn('Could not persist analysis snapshot:', e);
    }
}

function loadLatestAnalysisSnapshot() {
    var key = getAnalysisStorageKey();
    if (!key) return null;
    try {
        var raw = localStorage.getItem(key);
        if (!raw) return null;
        var parsed = JSON.parse(raw);
        latestAnalysisSnapshot = parsed;
        return parsed;
    } catch (e) {
        console.warn('Could not load saved analysis snapshot:', e);
        return null;
    }
}

function clearLatestAnalysisSnapshot() {
    latestAnalysisSnapshot = null;
    var key = getAnalysisStorageKey();
    if (!key) return;
    localStorage.removeItem(key);
}

function getAIStorageKey() {
    if (!currentUser || !currentUser.id) return null;
    return 'latestAIResult:' + currentUser.id;
}

function saveLatestAISnapshot(snapshot) {
    latestAISnapshot = snapshot;
    var key = getAIStorageKey();
    if (!key) return;
    try {
        localStorage.setItem(key, JSON.stringify(snapshot));
    } catch (e) {
        console.warn('Could not persist AI snapshot:', e);
    }
}

function loadLatestAISnapshot() {
    var key = getAIStorageKey();
    if (!key) return null;
    try {
        var raw = localStorage.getItem(key);
        if (!raw) return null;
        var parsed = JSON.parse(raw);
        latestAISnapshot = parsed;
        return parsed;
    } catch (e) {
        console.warn('Could not load saved AI snapshot:', e);
        return null;
    }
}

function clearLatestAISnapshot() {
    latestAISnapshot = null;
    var key = getAIStorageKey();
    if (!key) return;
    localStorage.removeItem(key);
}

function restoreSavedAnalysisToUI() {
    var container = document.getElementById('analysis-results');
    if (!container) return;
    
    var snapshot = latestAnalysisSnapshot || loadLatestAnalysisSnapshot();
    if (!snapshot || !snapshot.data) return;
    
    container.innerHTML = renderAnalysisResults(snapshot.data, snapshot.meta || {});
    container.style.display = 'block';
    container.style.visibility = 'visible';
    container.style.opacity = '1';
    container.style.minHeight = 'auto';
    container.style.maxHeight = 'none';
    container.style.height = 'auto';
    container.style.overflow = 'visible';
}

function getMatchingAnalysisSnapshot(resumeId, jdId) {
    var snapshot = latestAnalysisSnapshot || loadLatestAnalysisSnapshot();
    if (!snapshot || !snapshot.meta || !snapshot.data) return null;
    if (parseInt(snapshot.meta.resume_id) !== parseInt(resumeId)) return null;
    if (parseInt(snapshot.meta.jd_id) !== parseInt(jdId)) return null;
    return snapshot;
}

function restoreSavedAIResultsToUI() {
    var snapshot = latestAISnapshot || loadLatestAISnapshot();
    if (!snapshot || !snapshot.type || !snapshot.data) return;

    var payload = buildAIWorkspacePayload(snapshot.type, snapshot.data);
    if (!payload) return;
    setAIWorkspaceResult(payload);
}

function isAIWorkspaceVisible() {
    var aiContent = document.getElementById('content-ai');
    return !!(aiContent && !aiContent.classList.contains('hidden'));
}

function setAIWorkspaceStatus(message) {
    var statusEl = document.getElementById('ai-inline-status');
    var statusTextEl = document.getElementById('ai-inline-status-text');
    var statusPercentEl = document.getElementById('ai-inline-status-percent');
    var statusBarEl = document.getElementById('ai-inline-status-bar');
    if (!statusEl || !isAIWorkspaceVisible()) return;
    if (!message) {
        statusEl.classList.add('hidden');
        if (statusTextEl) statusTextEl.textContent = '';
        if (statusPercentEl) statusPercentEl.textContent = '0%';
        if (statusBarEl) statusBarEl.style.width = '10%';
        return;
    }
    var text = String(message);
    var match = text.match(/\((\d{1,3})%\)/);
    var percent = match ? Math.max(0, Math.min(100, parseInt(match[1], 10))) : null;
    var cleanText = text.replace(/\s*\(\d{1,3}%\)\s*/, ' ').trim();

    if (statusTextEl) statusTextEl.textContent = cleanText || 'Working...';
    if (statusPercentEl) statusPercentEl.textContent = (percent !== null ? percent : 0) + '%';
    if (statusBarEl) statusBarEl.style.width = (percent !== null ? percent : 12) + '%';
    statusEl.classList.remove('hidden');
}

function normalizeRawText(value) {
    if (typeof value === 'string') return value;
    if (value === undefined || value === null) return '';
    try {
        return JSON.stringify(value, null, 2);
    } catch (e) {
        return String(value);
    }
}

function setAIWorkspaceHeaderTitle(title) {
    aiWorkspaceTitle = title || 'AI Results Workspace';
    var titleEl = document.getElementById('ai-results-title');
    if (titleEl) titleEl.textContent = aiWorkspaceTitle;
}

function setAIWorkspaceResult(payload) {
    var previewEl = document.getElementById('ai-results');
    var rawTextEl = document.getElementById('ai-results-raw-text');
    if (!previewEl) return;

    setAIWorkspaceHeaderTitle(payload.title || 'AI Results Workspace');
    previewEl.innerHTML = payload.html || '';
    aiWorkspaceRawText = normalizeRawText(payload.raw || '');
    if (rawTextEl) rawTextEl.textContent = aiWorkspaceRawText;
    switchAIResultView('preview');
}

function switchAIResultView(view) {
    var previewWrap = document.getElementById('ai-results-preview');
    var rawWrap = document.getElementById('ai-results-raw');
    var previewBtn = document.getElementById('ai-view-preview-btn');
    var rawBtn = document.getElementById('ai-view-raw-btn');

    var showRaw = view === 'raw';
    if (previewWrap) previewWrap.classList.toggle('hidden', showRaw);
    if (rawWrap) rawWrap.classList.toggle('hidden', !showRaw);

    if (previewBtn) {
        previewBtn.classList.toggle('bg-primary-500', !showRaw);
        previewBtn.classList.toggle('text-white', !showRaw);
        previewBtn.classList.toggle('bg-gray-100', showRaw);
        previewBtn.classList.toggle('text-gray-700', showRaw);
    }
    if (rawBtn) {
        rawBtn.classList.toggle('bg-primary-500', showRaw);
        rawBtn.classList.toggle('text-white', showRaw);
        rawBtn.classList.toggle('bg-gray-100', !showRaw);
        rawBtn.classList.toggle('text-gray-700', !showRaw);
    }
}

function copyAIResultText() {
    if (!aiWorkspaceRawText) {
        showToast('No result text available to copy', 'warning');
        return;
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(aiWorkspaceRawText)
            .then(function() { showToast('Copied to clipboard', 'success'); })
            .catch(function() { showToast('Copy failed', 'error'); });
        return;
    }
    showToast('Clipboard not supported in this browser', 'warning');
}

function downloadAIResultText() {
    if (!aiWorkspaceRawText) {
        showToast('No result text available to download', 'warning');
        return;
    }
    var stamp = new Date().toISOString().slice(0, 10);
    var safeTitle = (aiWorkspaceTitle || 'ai-result')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
    triggerTextDownload((safeTitle || 'ai-result') + '-' + stamp + '.txt', aiWorkspaceRawText, 'text/plain;charset=utf-8');
    showToast('Result downloaded', 'success');
}

function buildAIWorkspacePayload(type, data) {
    if (type === 'suggestions') {
        return {
            title: 'AI Resume Improvement',
            html: renderAISuggestions(data),
            raw: normalizeRawText(data)
        };
    }
    if (type === 'career_path') {
        return {
            title: 'Career Path Analysis',
            html: renderCareerPath(data),
            raw: normalizeRawText(data)
        };
    }
    if (type === 'interview_prep') {
        var guide = data && data.interview_guide ? data.interview_guide : {};
        var prepText = guide.preparation_guide || normalizeRawText(data);
        return {
            title: 'Interview Preparation Guide',
            html: renderInterviewPrep(data),
            raw: prepText
        };
    }
    if (type === 'cover_letter') {
        return {
            title: 'Cover Letter',
            html: renderCoverLetter(data),
            raw: data.cover_letter || normalizeRawText(data)
        };
    }
    if (type === 'tailored_resume') {
        return {
            title: 'Tailored Resume Draft',
            html: renderTailoredResume(data),
            raw: data.tailored_resume || normalizeRawText(data)
        };
    }
    return null;
}

// ==================== SETUP FORMS ====================
function setupForms() {
    var loginForm = document.getElementById('login-form');
    var registerForm = document.getElementById('register-form');
    var jdForm = document.getElementById('jd-form');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleLogin();
        });
    }
    
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleRegister();
        });
    }
    
    if (jdForm) {
        jdForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleCreateJD();
        });
    }
}

// ==================== FILE UPLOAD ====================
function setupFileUpload() {
    var dropZone = document.getElementById('drop-zone');
    var fileInput = document.getElementById('resume-file');
    
    if (!dropZone || !fileInput) return;
    
    // Clone to remove old listeners
    var newDropZone = dropZone.cloneNode(true);
    dropZone.parentNode.replaceChild(newDropZone, dropZone);
    dropZone = newDropZone;
    
    var newFileInput = fileInput.cloneNode(true);
    fileInput.parentNode.replaceChild(newFileInput, fileInput);
    fileInput = newFileInput;
    
    dropZone.style.cursor = 'pointer';
    
    dropZone.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '#667eea';
        dropZone.style.backgroundColor = 'rgba(102, 126, 234, 0.1)';
    });
    
    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '#d1d5db';
        dropZone.style.backgroundColor = '';
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '#d1d5db';
        dropZone.style.backgroundColor = '';
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleSelectedFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', function() {
        if (fileInput.files && fileInput.files.length > 0) {
            handleSelectedFile(fileInput.files[0]);
        }
    });
}

function handleSelectedFile(file) {
    var fileName = file.name.toLowerCase();
    var isValid = fileName.endsWith('.pdf') || fileName.endsWith('.docx') || fileName.endsWith('.doc');
    
    if (!isValid) {
        showToast('Please upload a PDF or DOCX file', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showToast('File size must be less than 10MB', 'error');
        return;
    }
    
    selectedFile = file;
    
    var dropZone = document.getElementById('drop-zone');
    var uploadBtn = document.getElementById('upload-btn');
    
    if (dropZone) {
        dropZone.innerHTML = 
            '<div class="text-5xl text-green-500 mb-4"><i class="fas fa-file-check"></i></div>' +
            '<p class="text-gray-800 font-semibold">' + file.name + '</p>' +
            '<p class="text-gray-500 text-sm mt-1">' + (file.size / 1024).toFixed(2) + ' KB</p>' +
            '<p class="text-green-500 text-sm mt-2"><i class="fas fa-check-circle mr-1"></i>Ready to upload</p>';
    }
    
    if (uploadBtn) {
        uploadBtn.disabled = false;
        uploadBtn.classList.remove('opacity-50');
    }
    
    showToast('File selected: ' + file.name, 'success');
}

function resetDropZone() {
    selectedFile = null;
    
    var dropZone = document.getElementById('drop-zone');
    var uploadBtn = document.getElementById('upload-btn');
    var fileInput = document.getElementById('resume-file');
    
    if (dropZone) {
        dropZone.innerHTML = 
            '<div class="text-6xl text-primary-300 mb-4"><i class="fas fa-cloud-upload-alt"></i></div>' +
            '<p class="text-gray-600 font-medium">Drag & drop your resume here</p>' +
            '<p class="text-gray-400 text-sm mt-2">or click to browse (PDF, DOCX)</p>';
    }
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.classList.add('opacity-50');
    }
    if (fileInput) {
        fileInput.value = '';
    }
    
    setTimeout(setupFileUpload, 100);
}

// ==================== NAVIGATION ====================
function showSection(sectionId) {
    var sections = document.querySelectorAll('.page-section');
    for (var i = 0; i < sections.length; i++) {
        sections[i].classList.remove('active');
    }
    
    var targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    window.scrollTo(0, 0);
    
    if (sectionId === 'dashboard' && currentUser) {
        loadUserData();
        setTimeout(setupFileUpload, 300);
    }
    
    if (typeof AOS !== 'undefined') {
        AOS.refresh();
    }
}

function showDashboardTab(tabId) {

    localStorage.setItem('activeDashboardTab', tabId);

    var tabs = document.querySelectorAll('.dashboard-tab');
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove('bg-gradient-to-r', 'from-primary-500', 'to-secondary-500', 'text-white');
        tabs[i].classList.add('text-gray-600');
    }
    
    var activeTab = document.getElementById('tab-' + tabId);
    if (activeTab) {
        activeTab.classList.add('bg-gradient-to-r', 'from-primary-500', 'to-secondary-500', 'text-white');
        activeTab.classList.remove('text-gray-600');
    }
    
    var contents = document.querySelectorAll('.dashboard-content');
    for (var j = 0; j < contents.length; j++) {
        contents[j].classList.add('hidden');
    }
    
    var activeContent = document.getElementById('content-' + tabId);
    if (activeContent) {
        activeContent.classList.remove('hidden');
    }
    
    if (tabId === 'resumes') {
        setTimeout(setupFileUpload, 300);
    }
    
    if (tabId === 'analysis') {
        restoreSavedAnalysisToUI();
    }
    
    if (tabId === 'ai') {
        restoreSavedAIResultsToUI();
    }
}

// ==================== TOAST ====================
function showToast(message, type) {
    type = type || 'success';
    var container = document.getElementById('toast-container');
    if (!container) {
        console.log('Toast:', type, message);
        return;
    }
    
    var colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    var icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    var toast = document.createElement('div');
    toast.className = 'toast ' + colors[type] + ' text-white px-6 py-4 rounded-xl shadow-lg flex items-center gap-3 mb-2';
    toast.innerHTML = '<i class="fas ' + icons[type] + ' text-xl"></i><span class="font-medium">' + message + '</span>';
    
    container.appendChild(toast);
    
    setTimeout(function() {
        toast.remove();
    }, 4000);
}

// ==================== LOADING ====================
function showLoading(message) {
    if (isAIWorkspaceVisible()) {
        setAIWorkspaceStatus(message || 'Working...');
        return;
    }
    var loadingText = document.getElementById('loading-text');
    var loadingOverlay = document.getElementById('loading-overlay');
    
    if (loadingText) loadingText.textContent = message || 'Loading...';
    if (loadingOverlay) loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    var loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.classList.add('hidden');
    if (isAIWorkspaceVisible()) {
        setAIWorkspaceStatus('');
    }
}

// ==================== AUTH ====================
async function handleLogin() {
    var email = document.getElementById('login-email').value;
    var password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        showToast('Please fill in all fields', 'warning');
        return;
    }
    
    showLoading('Logging in...');
    
    try {
        var response = await fetch(API_URL + '/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email, password: password })
        });
        
        var data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateUIForLoggedInUser();
            document.getElementById('login-email').value = '';
            document.getElementById('login-password').value = '';
            showSection('dashboard');
            showToast('Welcome back, ' + currentUser.full_name + '!', 'success');
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Connection error', 'error');
    } finally {
        hideLoading();
    }
}

async function handleRegister() {
    var full_name = document.getElementById('reg-name').value;
    var email = document.getElementById('reg-email').value;
    var password = document.getElementById('reg-password').value;
    var role = document.getElementById('reg-role').value;
    
    if (!full_name || !email || !password) {
        showToast('Please fill in all fields', 'warning');
        return;
    }
    
    showLoading('Creating account...');
    
    try {
        var response = await fetch(API_URL + '/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: full_name, email: email, password: password, role: role })
        });
        
        var data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateUIForLoggedInUser();
            document.getElementById('reg-name').value = '';
            document.getElementById('reg-email').value = '';
            document.getElementById('reg-password').value = '';
            showSection('dashboard');
            showToast('Welcome, ' + currentUser.full_name + '!', 'success');
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showToast('Connection error', 'error');
    } finally {
        hideLoading();
    }
}

function logout() {
    clearLatestAnalysisSnapshot();
    clearLatestAISnapshot();
    currentUser = null;
    selectedFile = null;
    localStorage.removeItem('user');
    resumes = [];
    jobDescriptions = [];
    updateUIForLoggedOutUser();
    showSection('landing');
    showToast('Logged out successfully', 'info');
}

// ==================== DATA LOADING ====================
async function loadUserData() {
    if (!currentUser) return;
    await loadResumes();
    await loadJDs();
    populateDropdowns();
    restoreSavedAnalysisToUI();
    restoreSavedAIResultsToUI();
}

async function loadResumes() {
    if (!currentUser) return;
    
    try {
        var response = await fetch(API_URL + '/api/resume/user/' + currentUser.id);
        var data = await response.json();
        resumes = data.resumes || [];
        renderResumesList();
    } catch (error) {
        console.error('Error loading resumes:', error);
        resumes = [];
        renderResumesList();
    }
}

function renderResumesList() {
    var container = document.getElementById('resumes-list');
    if (!container) return;
    
    if (resumes.length === 0) {
        container.innerHTML = '<div class="text-center py-10 text-gray-400"><i class="fas fa-inbox text-4xl mb-3"></i><p>No resumes yet. Upload one!</p></div>';
        return;
    }
    
    var html = '';
    for (var i = 0; i < resumes.length; i++) {
        var r = resumes[i];
        html += '<div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-primary-50 transition-colors mb-3">';
        html += '<div class="flex items-center gap-4">';
        html += '<div class="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center"><i class="fas fa-file-alt text-white"></i></div>';
        html += '<div><h4 class="font-semibold text-gray-800">' + r.filename + '</h4>';
        html += '<p class="text-sm text-gray-500">ID: ' + r.id + '</p></div></div>';
        html += '<div class="flex items-center gap-2">';
        html += '<button onclick="getAISuggestionsForResume(' + r.id + ')" class="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600"><i class="fas fa-robot"></i></button>';
        html += '<button onclick="deleteResume(' + r.id + ')" class="p-2 bg-red-500 text-white rounded-lg hover:bg-red-600"><i class="fas fa-trash"></i></button>';
        html += '</div></div>';
    }
    
    container.innerHTML = html;
}

async function uploadResume() {
    if (!currentUser) {
        showToast('Please login first', 'warning');
        return;
    }
    
    if (!selectedFile) {
        showToast('Please select a file first', 'warning');
        return;
    }
    
    showLoading('Uploading resume...');
    
    var formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('user_id', currentUser.id.toString());
    
    try {
        var response = await fetch(API_URL + '/api/resume/upload', {
            method: 'POST',
            body: formData
        });
        
        var data = await response.json();
        
        if (response.ok) {
            showToast('Resume uploaded successfully!', 'success');
            selectedFile = null;
            resetDropZone();
            await loadResumes();
            populateDropdowns();
        } else {
            showToast(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Connection error', 'error');
    } finally {
        hideLoading();
    }
}

async function deleteResume(resumeId) {
    if (!confirm('Delete this resume?')) return;
    
    showLoading('Deleting...');
    
    try {
        var response = await fetch(API_URL + '/api/resume/' + resumeId, { method: 'DELETE' });
        
        if (response.ok) {
            showToast('Deleted', 'success');
            await loadResumes();
            populateDropdowns();
        } else {
            showToast('Delete failed', 'error');
        }
    } catch (error) {
        showToast('Error', 'error');
    } finally {
        hideLoading();
    }
}

// ==================== JOB DESCRIPTIONS ====================
async function loadJDs() {
    if (!currentUser) return;
    
    try {
        var response = await fetch(API_URL + '/api/jd/user/' + currentUser.id);
        var data = await response.json();
        jobDescriptions = data.job_descriptions || [];
        renderJDsList();
    } catch (error) {
        console.error('Error loading JDs:', error);
        jobDescriptions = [];
        renderJDsList();
    }
}

function renderJDsList() {
    var container = document.getElementById('jds-list');
    if (!container) return;
    
    if (jobDescriptions.length === 0) {
        container.innerHTML = '<div class="text-center py-10 text-gray-400"><i class="fas fa-inbox text-4xl mb-3"></i><p>No job descriptions yet.</p></div>';
        return;
    }
    
    var html = '';
    for (var i = 0; i < jobDescriptions.length; i++) {
        var jd = jobDescriptions[i];
        html += '<div class="p-4 bg-gray-50 rounded-xl hover:bg-purple-50 transition-colors mb-3">';
        html += '<div class="flex items-center gap-4">';
        html += '<div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center"><i class="fas fa-briefcase text-white"></i></div>';
        html += '<div><h4 class="font-semibold text-gray-800">' + jd.title + '</h4>';
        html += '<p class="text-sm text-gray-500">' + (jd.company || 'N/A') + ' • ID: ' + jd.id + '</p></div></div></div>';
    }
    
    container.innerHTML = html;
}

async function handleCreateJD() {
    if (!currentUser) {
        showToast('Please login first', 'warning');
        return;
    }
    
    var title = document.getElementById('jd-title').value;
    var company = document.getElementById('jd-company').value;
    var description = document.getElementById('jd-description').value;
    
    if (!title || !description) {
        showToast('Fill in title and description', 'warning');
        return;
    }
    
    showLoading('Creating...');
    
    try {
        var response = await fetch(API_URL + '/api/jd/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUser.id,
                title: title,
                company: company,
                description: description
            })
        });
        
        var data = await response.json();
        
        if (response.ok) {
            showToast('Created!', 'success');
            document.getElementById('jd-title').value = '';
            document.getElementById('jd-company').value = '';
            document.getElementById('jd-description').value = '';
            await loadJDs();
            populateDropdowns();
        } else {
            showToast(data.error || 'Failed', 'error');
        }
    } catch (error) {
        showToast('Error', 'error');
    } finally {
        hideLoading();
    }
}

// ==================== DROPDOWNS ====================
function populateDropdowns() {
    var resumeSelects = ['analysis-resume', 'ai-resume', 'interview-resume', 'coverletter-resume', 'tailor-resume'];
    var jdSelects = ['analysis-jd', 'interview-jd', 'coverletter-jd', 'tailor-jd'];
    
    for (var i = 0; i < resumeSelects.length; i++) {
        var el = document.getElementById(resumeSelects[i]);
        if (el) {
            var html = '<option value="">-- Select Resume --</option>';
            for (var j = 0; j < resumes.length; j++) {
                html += '<option value="' + resumes[j].id + '">' + resumes[j].filename + '</option>';
            }
            el.innerHTML = html;
        }
    }
    
    for (var k = 0; k < jdSelects.length; k++) {
        var el2 = document.getElementById(jdSelects[k]);
        if (el2) {
            var html2 = '<option value="">-- Select Job --</option>';
            for (var l = 0; l < jobDescriptions.length; l++) {
                html2 += '<option value="' + jobDescriptions[l].id + '">' + jobDescriptions[l].title + '</option>';
            }
            el2.innerHTML = html2;
        }
    }
}

// ==================== ANALYSIS ====================
function beginOperation(operationName) {
    if (activeOperationId) {
        showToast('Please wait for "' + activeOperationName + '" to finish.', 'info');
        return null;
    }
    activeOperationName = operationName;
    activeOperationId = operationName + '-' + Date.now() + '-' + Math.floor(Math.random() * 10000);
    return activeOperationId;
}

function showOperationLoading(operationId, message) {
    if (!operationId || operationId !== activeOperationId) return;
    setAIWorkspaceStatus(message);
    if (!isAIWorkspaceVisible()) {
        showLoading(message);
    }
}

function finishOperation(operationId) {
    if (!operationId || operationId !== activeOperationId) return;
    stopLoadingMessageRotation(operationId);
    hideLoading();
    setAIWorkspaceStatus('');
    activeOperationId = null;
    activeOperationName = null;
}

function startLoadingMessageRotation(messages, intervalMs, operationId) {
    stopLoadingMessageRotation(operationId);
    var i = 0;
    analysisProgressInterval = setInterval(function() {
        if (!messages || messages.length === 0) return;
        showOperationLoading(operationId, messages[i % messages.length]);
        i++;
    }, intervalMs || 2200);
}

function stopLoadingMessageRotation(operationId) {
    if (operationId && activeOperationId && operationId !== activeOperationId) {
        return;
    }
    if (analysisProgressInterval) {
        clearInterval(analysisProgressInterval);
        analysisProgressInterval = null;
    }
}

function sleep(ms) {
    return new Promise(function(resolve) {
        setTimeout(resolve, ms);
    });
}

async function startAsyncMatchJob(resumeId, jdId) {
    var response = await fetch(API_URL + '/api/analyze/match/async', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: parseInt(resumeId), jd_id: parseInt(jdId) })
    });
    
    var data = await response.json().catch(function() { return {}; });
    if (!response.ok) {
        throw new Error(data.error || ('Failed to start analysis (HTTP ' + response.status + ')'));
    }
    return data;
}

async function getAsyncMatchStatus(jobId) {
    var response = await fetch(API_URL + '/api/analyze/match/status/' + jobId);
    var data = await response.json().catch(function() { return {}; });
    
    if (!response.ok) {
        throw new Error(data.error || ('Failed to check analysis status (HTTP ' + response.status + ')'));
    }
    return data;
}

async function waitForAsyncMatch(jobId, timeoutMs, pollMs, control, operationId) {
    var startedAt = Date.now();
    var timeout = timeoutMs || 180000;
    var interval = pollMs || 1200;
    
    while (Date.now() - startedAt < timeout) {
        if (control && control.cancelled) {
            throw new Error('Polling cancelled');
        }

        var statusData = await getAsyncMatchStatus(jobId);
        var progress = typeof statusData.progress === 'number' ? statusData.progress : null;
        var statusText = statusData.message || 'Analyzing...';
        
        if (control && control.cancelled) {
            throw new Error('Polling cancelled');
        }

        if (progress !== null) {
            showOperationLoading(operationId, '🔍 ' + statusText + ' (' + progress + '%)');
        } else {
            showOperationLoading(operationId, '🔍 ' + statusText);
        }
        
        if (statusData.status === 'completed') {
            return statusData.result || {};
        }
        
        if (statusData.status === 'failed') {
            throw new Error(statusData.error || 'Analysis failed on server');
        }
        
        await sleep(interval);
    }
    
    throw new Error('Analysis is taking too long. Please try again.');
}

async function analyzeMatch(event) {
    // Prevent any default behavior or form submission
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('analyzeMatch called - starting analysis');
    
    var resumeId = document.getElementById('analysis-resume').value;
    var jdId = document.getElementById('analysis-jd').value;
    
    if (!resumeId || !jdId) {
        showToast('Select both resume and job', 'warning');
        return false;
    }
    
    var operationId = beginOperation('analysis');
    if (!operationId) {
        return false;
    }
    var localRenderNonce = ++analysisRenderNonce;

    var analyzeBtn = event && event.currentTarget ? event.currentTarget : null;
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        analyzeBtn.classList.add('opacity-60', 'cursor-not-allowed');
    }
    
    showOperationLoading(operationId, '🚀 Starting analysis...');
    startLoadingMessageRotation([
        '📥 Sending analysis request...',
        '🧠 Running semantic and skill matching...',
        '📊 Calculating ATS and section scores...',
        '📝 Preparing detailed recommendations...'
    ], 2200, operationId);
    
    var analysisPollControl = { cancelled: false };
    try {
        var startedJob = await startAsyncMatchJob(resumeId, jdId);
        var result = await waitForAsyncMatch(
            startedJob.job_id,
            180000,
            startedJob.poll_interval_ms || 1200,
            analysisPollControl,
            operationId
        );

        // Ignore stale completions from older requests.
        if (localRenderNonce !== analysisRenderNonce || operationId !== activeOperationId) {
            return false;
        }
        
        console.log('✅ Analysis complete:', result);
        
        var snapshot = {
            data: result,
            meta: {
                resume_id: parseInt(resumeId),
                jd_id: parseInt(jdId),
                resume_name: getResumeNameById(resumeId),
                jd_title: getJDTitleById(jdId),
                analyzed_at: new Date().toISOString()
            }
        };
        saveLatestAnalysisSnapshot(snapshot);
        
        var container = document.getElementById('analysis-results');
        console.log('Container found:', container);
        
        if (container) {
            var html = renderAnalysisResults(snapshot.data, snapshot.meta);
            console.log('HTML generated, length:', html.length);
            container.innerHTML = html;
            
            // FORCE VISIBILITY - Remove all height restrictions
            container.style.display = 'block';
            container.style.visibility = 'visible';
            container.style.opacity = '1';
            container.style.minHeight = 'auto';
            container.style.maxHeight = 'none';
            container.style.height = 'auto';
            container.style.overflow = 'visible';
            
            // Scroll into view
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            console.log('✅ Results rendered and visible');
        } else {
            console.error('❌ Container #analysis-results not found!');
        }
        
        showToast('✅ Analysis complete!', 'success');
    } catch (error) {
        if (error && error.message === 'Polling cancelled') {
            return false;
        }
        console.error('Analysis error:', error);
        showToast('❌ Error: ' + (error.message || 'Analysis failed'), 'error');
    } finally {
        analysisPollControl.cancelled = true;
        finishOperation(operationId);
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.classList.remove('opacity-60', 'cursor-not-allowed');
        }
    }
    
    return false;
}

function renderAnalysisResults(data, meta) {
    meta = meta || {};
    var matchScore = data.match_score || 0;
    var atsScore = 0;
    
    if (data.ats_score) {
        atsScore = typeof data.ats_score === 'object' 
            ? (data.ats_score.percentage || 0) 
            : data.ats_score;
    }
    
    var analyzedAtText = '';
    if (meta.analyzed_at) {
        var analyzedDate = new Date(meta.analyzed_at);
        if (!isNaN(analyzedDate.getTime())) {
            analyzedAtText = analyzedDate.toLocaleString();
        }
    }
    
    var html = '<div class="space-y-6">';
    
    // Persisted report actions
    html += '<div class="bg-gray-50 rounded-2xl border border-gray-200 p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">';
    html += '<div>';
    html += '<p class="text-sm font-semibold text-gray-700">Saved Analysis Report</p>';
    html += '<p class="text-xs text-gray-500 mt-1">' + (meta.resume_name || 'Selected Resume') + ' vs ' + (meta.jd_title || 'Selected Job Description') + '</p>';
    if (analyzedAtText) {
        html += '<p class="text-xs text-gray-500 mt-1">Analyzed: ' + analyzedAtText + '</p>';
    }
    html += '</div>';
    html += '<div class="flex items-center gap-2">';
    html += '<button type="button" onclick="downloadAnalysisReport(\'txt\')" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-semibold hover:opacity-90">';
    html += '<i class="fas fa-download mr-2"></i>Download Report</button>';
    html += '<button type="button" onclick="downloadAnalysisReport(\'json\')" class="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg text-sm font-semibold hover:bg-gray-50">';
    html += '<i class="fas fa-file-code mr-2"></i>JSON</button>';
    html += '</div></div>';
    
    // Main Score Cards
    html += '<div class="grid md:grid-cols-2 gap-6">';
    
    // Match Score Card
    var matchColor = matchScore >= 70 ? 'from-green-500 to-teal-500' : 
                     matchScore >= 50 ? 'from-yellow-500 to-orange-500' : 
                     'from-red-500 to-pink-500';
    
    html += '<div class="bg-gradient-to-br ' + matchColor + ' rounded-2xl p-6 text-white text-center">';
    html += '<div class="w-28 h-28 mx-auto rounded-full bg-white/20 flex flex-col items-center justify-center mb-4">';
    html += '<span class="text-4xl font-bold">' + Math.round(matchScore) + '%</span></div>';
    html += '<h4 class="text-xl font-bold">Match Score</h4>';
    html += '<p class="text-white/80 text-sm mt-1">Overall job compatibility</p></div>';
    
    // ATS Score Card
    var atsColor = atsScore >= 70 ? 'from-green-500 to-emerald-500' : 
                   atsScore >= 50 ? 'from-yellow-500 to-amber-500' : 
                   'from-red-500 to-rose-500';
    
    html += '<div class="bg-gradient-to-br ' + atsColor + ' rounded-2xl p-6 text-white text-center">';
    html += '<div class="w-28 h-28 mx-auto rounded-full bg-white/20 flex flex-col items-center justify-center mb-4">';
    html += '<span class="text-4xl font-bold">' + Math.round(atsScore) + '%</span></div>';
    html += '<h4 class="text-xl font-bold">ATS Score</h4>';
    html += '<p class="text-white/80 text-sm mt-1">Resume format & keywords</p></div>';
    
    html += '</div>';
    
    // Score Breakdown
    if (data.score_breakdown) {
        html += '<div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-chart-pie text-primary-500 mr-2"></i>Score Breakdown</h3>';
        html += '<div class="space-y-4">';
        
        var breakdown = data.score_breakdown;
        var weights = data.scoring_weights || {};
        
        var items = [
            { name: 'Semantic Match', key: 'semantic_similarity', weight: weights.semantic || '40%', color: 'bg-purple-500' },
            { name: 'Skill Match', key: 'skill_match', weight: weights.skills || '35%', color: 'bg-blue-500' },
            { name: 'Experience Match', key: 'experience_match', weight: weights.experience || '15%', color: 'bg-green-500' },
            { name: 'Keyword Match', key: 'keyword_match', weight: weights.keywords || '10%', color: 'bg-orange-500' }
        ];
        
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            var value = breakdown[item.key] || 0;
            
            html += '<div>';
            html += '<div class="flex justify-between items-center mb-1">';
            html += '<span class="text-gray-700 font-medium">' + item.name + '</span>';
            html += '<div class="flex items-center gap-2">';
            html += '<span class="text-xs text-gray-400">Weight: ' + item.weight + '</span>';
            html += '<span class="font-bold text-gray-800">' + Math.round(value) + '%</span>';
            html += '</div></div>';
            html += '<div class="w-full bg-gray-200 rounded-full h-2.5">';
            html += '<div class="' + item.color + ' h-2.5 rounded-full transition-all duration-500" style="width: ' + Math.min(value, 100) + '%"></div>';
            html += '</div></div>';
        }
        
        html += '</div></div>';
    }
    
    // Matched Skills
    var matchedSkills = data.matched_skills || [];
    if (matchedSkills.length > 0) {
        html += '<div class="bg-green-50 rounded-2xl p-6 border border-green-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-check-circle text-green-500 mr-2"></i>';
        html += 'Matched Skills <span class="text-green-600">(' + matchedSkills.length + ')</span></h3>';
        html += '<div class="flex flex-wrap gap-2">';
        for (var j = 0; j < matchedSkills.length; j++) {
            html += '<span class="px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">';
            html += '<i class="fas fa-check mr-1"></i>' + matchedSkills[j] + '</span>';
        }
        html += '</div></div>';
    }
    
    // Missing Skills (Skill Gap)
    var missingSkills = data.missing_skills || [];
    if (missingSkills.length > 0) {
        html += '<div class="bg-red-50 rounded-2xl p-6 border border-red-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>';
        html += 'Skill Gap <span class="text-red-600">(' + missingSkills.length + ' missing)</span></h3>';
        html += '<p class="text-gray-600 mb-3">Consider learning these skills to improve your match:</p>';
        html += '<div class="flex flex-wrap gap-2">';
        for (var k = 0; k < missingSkills.length; k++) {
            html += '<span class="px-3 py-1.5 bg-red-100 text-red-700 rounded-full text-sm font-medium">';
            html += '<i class="fas fa-plus mr-1"></i>' + missingSkills[k] + '</span>';
        }
        html += '</div></div>';
    }
    
    // Extra Skills (Your Advantage)
    var extraSkills = data.extra_skills || [];
    if (extraSkills.length > 0) {
        html += '<div class="bg-blue-50 rounded-2xl p-6 border border-blue-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-star text-blue-500 mr-2"></i>';
        html += 'Your Additional Skills <span class="text-blue-600">(' + extraSkills.length + ')</span></h3>';
        html += '<p class="text-gray-600 mb-3">Skills you have that could add value:</p>';
        html += '<div class="flex flex-wrap gap-2">';
        for (var l = 0; l < Math.min(extraSkills.length, 15); l++) {
            html += '<span class="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">' + extraSkills[l] + '</span>';
        }
        if (extraSkills.length > 15) {
            html += '<span class="px-3 py-1.5 bg-blue-200 text-blue-800 rounded-full text-sm font-medium">+' + (extraSkills.length - 15) + ' more</span>';
        }
        html += '</div></div>';
    }
    
    // Experience Analysis
    var expAnalysis = data.experience_analysis;
    if (expAnalysis && (expAnalysis.resume_years > 0 || expAnalysis.required_years > 0)) {
        html += '<div class="bg-purple-50 rounded-2xl p-6 border border-purple-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-briefcase text-purple-500 mr-2"></i>Experience Analysis</h3>';
        
        html += '<div class="grid grid-cols-3 gap-4 text-center mb-4">';
        
        html += '<div class="bg-white rounded-xl p-4 shadow-sm">';
        html += '<p class="text-3xl font-bold text-purple-600">' + (expAnalysis.resume_years || 0) + '</p>';
        html += '<p class="text-gray-500 text-sm">Your Experience</p></div>';
        
        html += '<div class="bg-white rounded-xl p-4 shadow-sm">';
        html += '<p class="text-3xl font-bold text-purple-600">' + (expAnalysis.required_years || 0) + '</p>';
        html += '<p class="text-gray-500 text-sm">Required Years</p></div>';
        
        var expMatchColor = expAnalysis.meets_requirement ? 'text-green-600' : 'text-orange-600';
        html += '<div class="bg-white rounded-xl p-4 shadow-sm">';
        html += '<p class="text-3xl font-bold ' + expMatchColor + '">' + Math.round(expAnalysis.match_percentage || 0) + '%</p>';
        html += '<p class="text-gray-500 text-sm">Match</p></div>';
        
        html += '</div>';
        
        var statusIcon = expAnalysis.meets_requirement ? 'fa-check-circle text-green-500' : 'fa-info-circle text-orange-500';
        html += '<p class="text-center text-gray-600"><i class="fas ' + statusIcon + ' mr-2"></i>' + (expAnalysis.status || '') + '</p>';
        
        html += '</div>';
    }
    
    // Section Scores
    var sectionScores = data.section_scores;
    if (sectionScores && Object.keys(sectionScores).length > 0) {
        html += '<div class="bg-indigo-50 rounded-2xl p-6 border border-indigo-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-file-alt text-indigo-500 mr-2"></i>Resume Section Scores</h3>';
        html += '<div class="grid grid-cols-2 md:grid-cols-3 gap-3">';
        
        var sectionNames = {
            'skills': 'Skills',
            'experience': 'Experience', 
            'education': 'Education',
            'projects': 'Projects',
            'summary': 'Summary',
            'certifications': 'Certifications'
        };
        
        for (var section in sectionScores) {
            var score = sectionScores[section] || 0;
            var sectionColor = score >= 60 ? 'bg-green-100 text-green-700' : 
                              score >= 40 ? 'bg-yellow-100 text-yellow-700' : 
                              'bg-gray-100 text-gray-500';
            
            html += '<div class="' + sectionColor + ' rounded-xl p-3 text-center">';
            html += '<p class="text-2xl font-bold">' + Math.round(score) + '%</p>';
            html += '<p class="text-sm">' + (sectionNames[section] || section) + '</p></div>';
        }
        
        html += '</div></div>';
    }
    
    // Suggestions
    var suggestions = data.suggestions || [];
    if (suggestions.length > 0) {
        html += '<div class="bg-amber-50 rounded-2xl p-6 border border-amber-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-lightbulb text-amber-500 mr-2"></i>Improvement Suggestions</h3>';
        html += '<div class="space-y-3">';
        
        for (var m = 0; m < suggestions.length; m++) {
            var sug = suggestions[m];
            var priorityColor = sug.priority === 'high' ? 'border-red-400 bg-red-50' : 
                               sug.priority === 'medium' ? 'border-yellow-400 bg-yellow-50' : 
                               'border-green-400 bg-green-50';
            var priorityBadge = sug.priority === 'high' ? 'bg-red-100 text-red-700' : 
                               sug.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' : 
                               'bg-green-100 text-green-700';
            
            html += '<div class="border-l-4 ' + priorityColor + ' p-4 rounded-r-xl">';
            html += '<div class="flex items-start justify-between gap-2">';
            html += '<div>';
            html += '<p class="font-semibold text-gray-800">' + (sug.category || 'Suggestion') + '</p>';
            html += '<p class="text-gray-600 text-sm mt-1">' + sug.suggestion + '</p>';
            if (sug.impact) {
                html += '<p class="text-xs text-gray-500 mt-2"><i class="fas fa-chart-line mr-1"></i>Impact: ' + sug.impact + '</p>';
            }
            html += '</div>';
            html += '<span class="px-2 py-1 ' + priorityBadge + ' rounded-full text-xs font-medium capitalize">' + sug.priority + '</span>';
            html += '</div></div>';
        }
        
        html += '</div></div>';
    }
    
    // Recommendations
    var recommendations = data.recommendations || [];
    if (recommendations.length > 0) {
        html += '<div class="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-2xl p-6 border border-primary-100">';
        html += '<h3 class="text-lg font-bold text-gray-800 mb-4">';
        html += '<i class="fas fa-clipboard-check text-primary-500 mr-2"></i>Recommendations</h3>';
        html += '<ul class="space-y-2">';
        
        for (var n = 0; n < recommendations.length; n++) {
            html += '<li class="flex items-start gap-3 text-gray-700">';
            html += '<i class="fas fa-arrow-right text-primary-500 mt-1 flex-shrink-0"></i>';
            html += '<span>' + recommendations[n] + '</span></li>';
        }
        
        html += '</ul></div>';
    }
    
    html += '</div>';
    return html;
}

function triggerTextDownload(filename, content, mimeType) {
    var blob = new Blob([content], { type: mimeType || 'text/plain;charset=utf-8' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
}

function buildAnalysisReportText(snapshot) {
    var data = snapshot.data || {};
    var meta = snapshot.meta || {};
    var lines = [];
    
    lines.push('AI Resume Analyzer - Analysis Report');
    lines.push('===================================');
    lines.push('Resume: ' + (meta.resume_name || ('Resume #' + (meta.resume_id || 'N/A'))));
    lines.push('Job Description: ' + (meta.jd_title || ('JD #' + (meta.jd_id || 'N/A'))));
    lines.push('Analyzed At: ' + (meta.analyzed_at ? new Date(meta.analyzed_at).toLocaleString() : 'N/A'));
    lines.push('');
    lines.push('Main Scores');
    lines.push('-----------');
    lines.push('Match Score: ' + Math.round(data.match_score || 0) + '%');
    lines.push('ATS Score: ' + Math.round((data.ats_score && data.ats_score.percentage) || data.ats_score || 0) + '%');
    lines.push('');
    
    var matchedSkills = data.matched_skills || [];
    var missingSkills = data.missing_skills || [];
    lines.push('Matched Skills (' + matchedSkills.length + '): ' + (matchedSkills.length ? matchedSkills.join(', ') : 'None'));
    lines.push('Missing Skills (' + missingSkills.length + '): ' + (missingSkills.length ? missingSkills.join(', ') : 'None'));
    lines.push('');
    
    var recommendations = data.recommendations || [];
    lines.push('Recommendations');
    lines.push('---------------');
    if (recommendations.length) {
        for (var i = 0; i < recommendations.length; i++) {
            lines.push((i + 1) + '. ' + recommendations[i]);
        }
    } else {
        lines.push('No recommendations available.');
    }
    
    return lines.join('\n');
}

function downloadAnalysisReport(format) {
    var snapshot = latestAnalysisSnapshot || loadLatestAnalysisSnapshot();
    if (!snapshot || !snapshot.data) {
        showToast('No analysis report found to download', 'warning');
        return;
    }
    
    var meta = snapshot.meta || {};
    var ts = meta.analyzed_at ? new Date(meta.analyzed_at) : new Date();
    var stamp = ts.getFullYear() + '-' + String(ts.getMonth() + 1).padStart(2, '0') + '-' + String(ts.getDate()).padStart(2, '0');
    
    if (format === 'json') {
        triggerTextDownload('analysis-report-' + stamp + '.json', JSON.stringify(snapshot, null, 2), 'application/json;charset=utf-8');
        showToast('JSON report downloaded', 'success');
        return;
    }
    
    var textReport = buildAnalysisReportText(snapshot);
    triggerTextDownload('analysis-report-' + stamp + '.txt', textReport, 'text/plain;charset=utf-8');
    showToast('Analysis report downloaded', 'success');
}

// ==================== AI SUGGESTIONS ====================
function getAISuggestions() {
    var resumeId = document.getElementById('ai-resume').value;
    if (!resumeId) {
        showToast('Select a resume', 'warning');
        return;
    }
    getAISuggestionsForResume(resumeId);
}

function getAISuggestionsForResume(resumeId) {
    showLoading('Getting AI suggestions...');
    
    fetch(API_URL + '/api/ai/improve-resume/' + resumeId)
    .then(function(response) { return response.json(); })
    .then(function(data) {
        hideLoading();
        console.log('AI suggestions:', data);

        var payload = buildAIWorkspacePayload('suggestions', data);
        if (payload) setAIWorkspaceResult(payload);
        saveLatestAISnapshot({
            type: 'suggestions',
            data: data,
            saved_at: new Date().toISOString()
        });
        showDashboardTab('ai');
        showToast('Suggestions loaded!', 'success');
    })
    .catch(function(error) {
        hideLoading();
        console.error('AI error:', error);
        showToast('Error getting suggestions', 'error');
    });
}

function renderAISuggestions(data) {
    var html = '<div class="space-y-4 w-full text-sm">';
    
    var current = data.current_ats_score || 0;
    var potential = data.potential_ats_score || 0;
    
    // Score Header
    html += '<div class="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-xl p-4 text-white text-sm">';
    html += '<h3 class="font-bold mb-3"><i class="fas fa-magic mr-2"></i>AI Analysis</h3>';
    html += '<div class="grid grid-cols-3 gap-2 text-center">';
    html += '<div class="bg-white/20 rounded-lg p-2"><p class="text-xs opacity-80">Current</p><p class="text-xl font-bold">' + current + '%</p></div>';
    html += '<div class="flex items-center justify-center"><i class="fas fa-arrow-right opacity-80 text-lg"></i></div>';
    html += '<div class="bg-white/20 rounded-lg p-2"><p class="text-xs opacity-80">Potential</p><p class="text-xl font-bold text-yellow-300">' + potential + '%</p></div>';
    html += '</div></div>';
    
    // Suggestions (detailed, no truncation)
    var suggestions = data.ai_suggestions || data.suggestions || [];
    if (suggestions.length > 0) {
        html += '<div class="space-y-3">';
        html += '<h3 class="text-sm font-bold text-gray-800"><i class="fas fa-list-check text-primary-500 mr-2"></i>Detailed Resume Improvement Plan</h3>';
        for (var i = 0; i < suggestions.length; i++) {
            var s = suggestions[i];
            var text = typeof s === 'string' ? s : (s.suggestion || s.text || JSON.stringify(s));
            var category = typeof s === 'object' ? (s.category || 'General') : 'General';
            var priority = typeof s === 'object' ? (s.priority || 'medium') : 'medium';
            var why = typeof s === 'object' ? (s.why_it_matters || '') : '';
            var actionSteps = (typeof s === 'object' && Array.isArray(s.action_steps)) ? s.action_steps : [];
            var exampleRewrite = typeof s === 'object' ? (s.example_rewrite || '') : '';
            var impact = typeof s === 'object' ? (s.estimated_impact || s.impact || '') : '';

            var badgeClass = priority === 'high'
                ? 'bg-red-100 text-red-700'
                : (priority === 'low' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700');

            html += '<div class="p-3 rounded-xl border border-primary-100 bg-white">';
            html += '<div class="flex items-center justify-between gap-2 mb-2">';
            html += '<p class="font-semibold text-gray-800">' + (i + 1) + '. ' + category + '</p>';
            html += '<span class="px-2 py-0.5 rounded-full text-xs font-medium capitalize ' + badgeClass + '">' + priority + '</span>';
            html += '</div>';
            html += '<p class="text-gray-700">' + text + '</p>';
            
            if (why) {
                html += '<p class="text-xs text-gray-600 mt-2"><i class="fas fa-circle-info mr-1"></i><strong>Why:</strong> ' + why + '</p>';
            }

            if (actionSteps.length > 0) {
                html += '<div class="mt-2">';
                html += '<p class="text-xs font-semibold text-gray-700 mb-1">Action Steps</p>';
                html += '<div class="space-y-1">';
                for (var a = 0; a < actionSteps.length; a++) {
                    html += '<p class="text-xs text-gray-700">• ' + actionSteps[a] + '</p>';
                }
                html += '</div></div>';
            }

            if (exampleRewrite) {
                html += '<div class="mt-2 p-2 bg-gray-50 rounded-lg border border-gray-200">';
                html += '<p class="text-xs font-semibold text-gray-700 mb-1">Example Rewrite</p>';
                html += '<p class="text-xs text-gray-700">' + exampleRewrite + '</p>';
                html += '</div>';
            }

            if (impact) {
                html += '<p class="text-xs text-emerald-700 mt-2"><i class="fas fa-chart-line mr-1"></i><strong>Impact:</strong> ' + impact + '</p>';
            }

            html += '</div>';
        }
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// ==================== CAREER PATH ====================
function getCareerPath() {
    if (!currentUser) {
        showToast('Login first', 'warning');
        return;
    }
    
    // Get selected career field from dropdown
    var careerFieldSelect = document.getElementById('career-field-select');
    var selectedField = careerFieldSelect ? careerFieldSelect.value : '';
    
    var loadingMsg = selectedField ? 
        `🗺️  Analyzing career path for ${selectedField} (may take up to 35 seconds)...` :
        '🗺️  Generating detailed career recommendations (may take up to 35 seconds)...';
    
    showLoading(loadingMsg);
    
    // Helper function to add timeout to fetch
    function fetchWithTimeout(url, options, timeoutMs) {
        return Promise.race([
            fetch(url, options),
            new Promise(function(_, reject) {
                setTimeout(function() {
                    reject(new Error('Request timeout after ' + timeoutMs + 'ms'));
                }, timeoutMs);
            })
        ]);
    }
    
    // Build URL with optional career_field parameter
    var apiUrl = API_URL + '/api/ai/career-path/' + currentUser.id;
    if (selectedField) {
        apiUrl += '?career_field=' + encodeURIComponent(selectedField);
    }
    
    fetchWithTimeout(apiUrl, {}, 35000)
    .then(function(response) { 
        if (!response.ok) throw new Error('API returned ' + response.status);
        return response.json(); 
    })
    .then(function(data) {
        hideLoading();
        console.log('Career path:', data);

        var payload = buildAIWorkspacePayload('career_path', data);
        if (payload) setAIWorkspaceResult(payload);
        saveLatestAISnapshot({
            type: 'career_path',
            data: data,
            saved_at: new Date().toISOString()
        });
        var msg = selectedField ? 
            `✅ Career path for ${selectedField} generated! Check the results in the AI Workspace.` :
            '✅ Career path generated! Check the results in the AI Workspace.';
        showToast(msg, 'success');
    })
    .catch(function(error) {
        hideLoading();
        console.error('Career path error:', error);
        showToast('❌ Error: ' + (error.message || 'Career path generation failed'), 'error');
    });
}

function renderCareerPath(data) {
    var html = '<div class="space-y-4 w-full text-sm">';
    
    // Show if this is a real-time analysis for a specific field
    if (data.selected_field) {
        html += '<div class="bg-blue-50 rounded-lg p-3 border-l-4 border-blue-500">';
        html += '<p class="text-xs text-blue-700"><strong>✨ Real-time Analysis:</strong> Personalized career path for <strong>' + data.selected_field + '</strong></p>';
        html += '</div>';
    }
    
    // Analysis Type
    if (data.analysis_type) {
        html += '<div class="bg-indigo-50 rounded-lg p-3 border border-indigo-200">';
        html += '<p class="text-xs text-indigo-700"><i class="fas fa-info-circle mr-1"></i>' + data.analysis_type + '</p>';
        html += '</div>';
    }
    
    // Current Skills
    if (data.current_skills && data.current_skills.length > 0) {
        html += '<div class="bg-blue-50 rounded-lg p-3 border border-blue-100">';
        html += '<h3 class="font-bold text-blue-700 text-xs mb-2"><i class="fas fa-tools mr-1"></i>Current Skill Inventory (' + data.current_skills.length + ')</h3>';
        html += '<div class="flex flex-wrap gap-1">';
        for (var i = 0; i < Math.min(data.current_skills.length, 12); i++) {
            html += '<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">' + data.current_skills[i] + '</span>';
        }
        if (data.current_skills.length > 12) {
            html += '<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">+' + (data.current_skills.length - 12) + ' more</span>';
        }
        html += '</div></div>';
    }
    
    // Recommended roadmap breakdown - NOW WITH REAL-TIME ANALYSIS
    if (data.recommended_roadmap) {
        var roadmap = data.recommended_roadmap;
        html += '<div class="bg-green-50 rounded-lg p-3 border border-green-100">';
        html += '<h3 class="font-bold text-green-700 text-xs mb-3"><i class="fas fa-road mr-1"></i>Your Personalized Career Roadmap</h3>';
        
        // Current Level
        if (roadmap.current_level) {
            html += '<div class="mb-3 p-2 bg-white rounded-lg border border-green-200">';
            html += '<p class="text-xs font-semibold text-gray-800"><i class="fas fa-level-up-alt mr-1"></i>Current Level: ' + roadmap.current_level + '</p>';
            if (roadmap.level_analysis) {
                html += '<p class="text-xs text-gray-700 mt-1">' + roadmap.level_analysis + '</p>';
            }
            html += '</div>';
        }
        
        // Skill Gaps
        if (roadmap.skill_gaps && roadmap.skill_gaps.length > 0) {
            html += '<div class="mb-3 p-2 bg-white rounded-lg border border-amber-200">';
            html += '<p class="text-xs font-semibold text-amber-800"><i class="fas fa-exclamation-circle mr-1"></i>Skill Gaps to Close:</p>';
            html += '<div class="flex flex-wrap gap-1 mt-2">';
            for (var sg = 0; sg < roadmap.skill_gaps.length; sg++) {
                html += '<span class="px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs">' + roadmap.skill_gaps[sg] + '</span>';
            }
            html += '</div></div>';
        }
        
        // Timeline
        if (roadmap.estimated_timeline) {
            html += '<div class="mb-3 p-2 bg-white rounded-lg border border-purple-200">';
            html += '<p class="text-xs text-purple-700"><i class="fas fa-clock mr-1"></i><strong>Estimated Timeline:</strong> ' + roadmap.estimated_timeline + '</p>';
            html += '</div>';
        }
        
        // Short, Medium, Long term
        var roadmapSections = [
            { key: 'short_term', title: 'Short Term (0-6 months)', icon: 'fa-hourglass-start' },
            { key: 'medium_term', title: 'Medium Term (6-18 months)', icon: 'fa-hourglass-half' },
            { key: 'long_term', title: 'Long Term (18+ months)', icon: 'fa-hourglass-end' }
        ];
        
        for (var r = 0; r < roadmapSections.length; r++) {
            var section = roadmapSections[r];
            var values = roadmap[section.key] || [];
            if (!values.length) continue;
            
            var sectionColors = [
                { bg: 'bg-blue-50', border: 'border-blue-200', title: 'text-blue-800' },
                { bg: 'bg-purple-50', border: 'border-purple-200', title: 'text-purple-800' },
                { bg: 'bg-green-50', border: 'border-green-200', title: 'text-green-800' }
            ];
            var colors = sectionColors[r];
            
            html += '<div class="mb-3 p-3 ' + colors.bg + ' rounded-lg border ' + colors.border + '">';
            html += '<p class="text-xs font-semibold ' + colors.title + ' mb-2"><i class="fas ' + section.icon + ' mr-1"></i>' + section.title + '</p>';
            for (var v = 0; v < values.length; v++) {
                html += '<p class="text-xs text-gray-700 mb-1">• ' + values[v] + '</p>';
            }
            html += '</div>';
        }
        
        html += '</div>';
    }
    
    // Immediate Actions (NEW)
    if (data.recommended_roadmap && data.recommended_roadmap.immediate_actions && data.recommended_roadmap.immediate_actions.length > 0) {
        html += '<div class="bg-red-50 rounded-lg p-3 border border-red-200">';
        html += '<h3 class="font-bold text-red-700 text-xs mb-2"><i class="fas fa-rocket mr-1"></i>Immediate Action Items</h3>';
        for (var ia = 0; ia < data.recommended_roadmap.immediate_actions.length; ia++) {
            html += '<p class="text-xs text-gray-700 mb-1"><strong>' + (ia + 1) + '.</strong> ' + data.recommended_roadmap.immediate_actions[ia] + '</p>';
        }
        html += '</div>';
    }
    
    // Career Insights (NEW - from AI)
    if (data.career_insights) {
        html += '<div class="bg-gradient-to-br from-cyan-50 to-blue-50 rounded-lg p-3 border border-cyan-200">';
        html += '<h3 class="font-bold text-cyan-700 text-xs mb-2"><i class="fas fa-lightbulb mr-1"></i>AI Career Insights</h3>';
        if (data.career_insights.overall_summary) {
            html += '<p class="text-xs text-gray-700 mb-2">' + data.career_insights.overall_summary + '</p>';
        }
        if (data.career_insights.suggestions && Array.isArray(data.career_insights.suggestions)) {
            html += '<p class="text-xs font-semibold text-gray-800 mb-2">Key Recommendations:</p>';
            for (var ins = 0; ins < Math.min(data.career_insights.suggestions.length, 3); ins++) {
                var insight = data.career_insights.suggestions[ins];
                html += '<div class="mb-2 p-2 bg-white rounded-lg border-l-2 border-cyan-400">';
                if (insight.suggestion) {
                    html += '<p class="text-xs text-gray-800"><strong>→</strong> ' + insight.suggestion + '</p>';
                }
                if (insight.why_it_matters) {
                    html += '<p class="text-xs text-gray-600 mt-1"><em>Why: ' + insight.why_it_matters + '</em></p>';
                }
                html += '</div>';
            }
        }
        html += '</div>';
    }
    
    // Career Options (detailed)
    if (data.career_options && data.career_options.length > 0) {
        html += '<div class="bg-purple-50 rounded-lg p-3 border border-purple-100">';
        html += '<h3 class="font-bold text-purple-700 text-xs mb-2"><i class="fas fa-briefcase mr-1"></i>Related Career Paths</h3>';
        for (var j = 0; j < Math.min(data.career_options.length, 6); j++) {
            var career = data.career_options[j];
            html += '<div class="mb-2 p-2 bg-white rounded-lg border border-purple-100">';
            html += '<p class="text-xs font-semibold text-gray-800">' + (j + 1) + '. ' + (career.title || 'Career Path') + '</p>';
            if (career.description) {
                html += '<p class="text-xs text-gray-600 mt-1">' + career.description.substring(0, 100) + '...</p>';
            }
            html += '</div>';
        }
        html += '</div>';
    }
    
    // Data Source
    if (data.data_source || data.powered_by) {
        html += '<div class="bg-gray-100 rounded-lg p-2 border border-gray-300">';
        html += '<p class="text-xs text-gray-600 text-center"><i class="fas fa-database mr-1"></i>' + (data.powered_by || data.data_source) + '</p>';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// ==================== COVER LETTER ====================
async function getCoverLetter(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    var resumeId = document.getElementById('coverletter-resume').value;
    var jdId = document.getElementById('coverletter-jd').value;
    var toneEl = document.getElementById('coverletter-tone');
    var tone = toneEl ? toneEl.value : 'professional';

    if (!resumeId || !jdId) {
        showToast('Select both resume and job', 'warning');
        return false;
    }

    var operationId = beginOperation('cover letter generation');
    if (!operationId) return false;

    var actionBtn = event && event.currentTarget ? event.currentTarget : null;
    if (actionBtn) {
        actionBtn.disabled = true;
        actionBtn.classList.add('opacity-60', 'cursor-not-allowed');
    }

    showOperationLoading(operationId, '✉️ Generating tailored cover letter...');
    startLoadingMessageRotation([
        '✍️ Drafting personalized opening and value pitch...',
        '🎯 Aligning your profile with job requirements...',
        '📄 Finalizing cover letter structure and closing...'
    ], 2200, operationId);

    function fetchWithTimeout(url, options, timeoutMs) {
        return Promise.race([
            fetch(url, options),
            new Promise(function(_, reject) {
                setTimeout(function() {
                    reject(new Error('Request timeout after ' + timeoutMs + 'ms'));
                }, timeoutMs);
            })
        ]);
    }

    try {
        var response = await fetchWithTimeout(
            API_URL + '/api/ai/cover-letter/' + resumeId + '/' + jdId + '?tone=' + encodeURIComponent(tone),
            {},
            45000
        );
        var data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || ('Cover letter API error: ' + response.status));
        }

        var payload = buildAIWorkspacePayload('cover_letter', data);
        if (payload) setAIWorkspaceResult(payload);

        saveLatestAISnapshot({
            type: 'cover_letter',
            data: data,
            saved_at: new Date().toISOString()
        });

        showDashboardTab('ai');
        showToast('✅ Cover letter ready!', 'success');
    } catch (error) {
        console.error('Cover letter error:', error);
        showToast('❌ Error: ' + (error.message || 'Cover letter generation failed'), 'error');
    } finally {
        finishOperation(operationId);
        if (actionBtn) {
            actionBtn.disabled = false;
            actionBtn.classList.remove('opacity-60', 'cursor-not-allowed');
        }
    }

    return false;
}

function renderCoverLetter(data) {
    var html = '<div class="space-y-4 w-full text-sm text-left">';
    html += '<div class="bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg p-4 text-white">';
    html += '<h3 class="font-bold text-base"><i class="fas fa-envelope-open-text mr-2"></i>Tailored Cover Letter</h3>';
    html += '<p class="text-xs opacity-90 mt-1">' + (data.job_title || 'Role') + ' at ' + (data.company || 'Company') + '</p>';
    html += '<p class="text-xs opacity-90 mt-1">Tone: ' + (data.tone || 'professional') + '</p>';
    html += '</div>';

    if (data.key_alignment_points && data.key_alignment_points.length > 0) {
        html += '<div class="bg-blue-50 rounded-lg p-4 border border-blue-100">';
        html += '<h4 class="font-semibold text-blue-700 mb-2"><i class="fas fa-bullseye mr-1"></i>Alignment Points</h4>';
        for (var i = 0; i < data.key_alignment_points.length; i++) {
            html += '<p class="text-xs text-gray-700 mb-1">• ' + data.key_alignment_points[i] + '</p>';
        }
        html += '</div>';
    }

    html += '<div class="bg-white rounded-lg p-4 border border-gray-200">';
    html += '<h4 class="font-semibold text-gray-800 mb-2"><i class="fas fa-file-lines mr-1"></i>Generated Letter</h4>';
    html += '<pre class="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed text-left">' + (data.cover_letter || 'No cover letter generated.') + '</pre>';
    html += '</div>';
    html += '</div>';
    return html;
}

function escapeHtml(text) {
    return String(text || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatTailoredResumeSections(text) {
    var clean = String(text || '').replace(/\r\n/g, '\n').trim();
    if (!clean) return '<p class="text-gray-500">No tailored resume generated.</p>';

    var blocks = clean.split(/\n{2,}/);
    var html = '';

    for (var i = 0; i < blocks.length; i++) {
        var lines = blocks[i].split('\n').map(function(line) {
            return line.trim();
        }).filter(Boolean);
        if (!lines.length) continue;

        var title = lines[0];
        var body = lines.slice(1);
        var looksLikeTitle = /^[A-Z0-9\s\-\(\)]+$/.test(title) || title.endsWith(':');
        var isAtsKeywordSection = title.toUpperCase().indexOf('ATS KEYWORDS TO INCLUDE') !== -1;

        if (!looksLikeTitle) {
            body = lines;
            title = 'Section';
        }

        html += '<section class="mb-6">';
        html += '<h5 class="text-sm font-bold tracking-wide text-gray-800 border-b border-gray-200 pb-2 mb-3">' + escapeHtml(title) + '</h5>';

        var bulletLines = [];
        var textLines = [];
        for (var j = 0; j < body.length; j++) {
            var line = body[j];
            if (line.startsWith('- ') || line.startsWith('• ')) {
                bulletLines.push(line.replace(/^[-•]\s*/, ''));
            } else {
                textLines.push(line);
            }
        }

        if (textLines.length) {
            for (var k = 0; k < textLines.length; k++) {
                html += '<p class="text-sm text-gray-700 leading-relaxed mb-2">' + escapeHtml(textLines[k]) + '</p>';
            }
        }

        if (bulletLines.length) {
            if (isAtsKeywordSection) {
                html += '<div class="flex flex-wrap gap-2">';
                for (var m = 0; m < bulletLines.length; m++) {
                    html += '<span class="px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium">' + escapeHtml(bulletLines[m]) + '</span>';
                }
                html += '</div>';
            } else {
                html += '<ul class="list-disc ml-5 space-y-1">';
                for (var n = 0; n < bulletLines.length; n++) {
                    html += '<li class="text-sm text-gray-700 leading-relaxed">' + escapeHtml(bulletLines[n]) + '</li>';
                }
                html += '</ul>';
            }
        }

        html += '</section>';
    }

    return html;
}

// ==================== TAILORED RESUME ====================
async function getTailoredResume(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    var resumeId = document.getElementById('tailor-resume').value;
    var jdId = document.getElementById('tailor-jd').value;

    if (!resumeId || !jdId) {
        showToast('Select both resume and job', 'warning');
        return false;
    }

    var operationId = beginOperation('tailored resume generation');
    if (!operationId) return false;

    var actionBtn = event && event.currentTarget ? event.currentTarget : null;
    if (actionBtn) {
        actionBtn.disabled = true;
        actionBtn.classList.add('opacity-60', 'cursor-not-allowed');
    }

    showOperationLoading(operationId, '🧩 Generating one-click tailored resume...');
    startLoadingMessageRotation([
        '🔎 Mapping JD requirements to your profile...',
        '✍️ Rewriting summary and experience bullets...',
        '✅ Building ATS keyword and edit checklist...'
    ], 2200, operationId);

    function fetchWithTimeout(url, options, timeoutMs) {
        return Promise.race([
            fetch(url, options),
            new Promise(function(_, reject) {
                setTimeout(function() {
                    reject(new Error('Request timeout after ' + timeoutMs + 'ms'));
                }, timeoutMs);
            })
        ]);
    }

    try {
        var response = await fetchWithTimeout(
            API_URL + '/api/ai/tailor-resume/' + resumeId + '/' + jdId,
            {},
            50000
        );
        var data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || ('Tailored resume API error: ' + response.status));
        }

        var payload = buildAIWorkspacePayload('tailored_resume', data);
        if (payload) setAIWorkspaceResult(payload);

        saveLatestAISnapshot({
            type: 'tailored_resume',
            data: data,
            saved_at: new Date().toISOString()
        });

        showDashboardTab('ai');
        showToast('✅ Tailored resume ready!', 'success');
    } catch (error) {
        console.error('Tailored resume error:', error);
        showToast('❌ Error: ' + (error.message || 'Tailored resume generation failed'), 'error');
    } finally {
        finishOperation(operationId);
        if (actionBtn) {
            actionBtn.disabled = false;
            actionBtn.classList.remove('opacity-60', 'cursor-not-allowed');
        }
    }

    return false;
}

function renderTailoredResume(data) {
    var html = '<div class="space-y-4 w-full text-sm text-left">';
    html += '<div class="bg-gradient-to-r from-indigo-500 to-violet-500 rounded-lg p-4 text-white">';
    html += '<h3 class="font-bold text-base"><i class="fas fa-wand-magic-sparkles mr-2"></i>One-Click Tailored Resume</h3>';
    html += '<p class="text-xs opacity-90 mt-1">' + (data.job_title || 'Role') + ' at ' + (data.company || 'Company') + '</p>';
    if (data.generation_mode) {
        html += '<p class="text-xs opacity-90 mt-1">Mode: ' + data.generation_mode + '</p>';
    }
    html += '</div>';

    if (data.keyword_alignment && data.keyword_alignment.length > 0) {
        html += '<div class="bg-indigo-50 rounded-lg p-4 border border-indigo-100">';
        html += '<h4 class="font-semibold text-indigo-700 mb-2"><i class="fas fa-key mr-1"></i>Keyword Alignment</h4>';
        for (var i = 0; i < data.keyword_alignment.length; i++) {
            html += '<p class="text-xs text-gray-700 mb-1">• ' + data.keyword_alignment[i] + '</p>';
        }
        html += '</div>';
    }

    html += '<div class="bg-gray-100 rounded-xl p-4">';
    html += '<div class="max-w-4xl mx-auto bg-white rounded-lg shadow-sm border border-gray-200 p-8">';
    html += '<div class="mb-6">';
    html += '<h4 class="text-lg font-bold text-gray-900"><i class="fas fa-file-pen mr-2 text-indigo-500"></i>Tailored Resume Draft</h4>';
    html += '<p class="text-xs text-gray-500 mt-1">Styled as resume-ready content</p>';
    html += '</div>';
    html += '<div class="resume-preview">';
    html += formatTailoredResumeSections(data.tailored_resume || '');
    html += '</div>';
    html += '</div>';
    html += '</div>';
    html += '</div>';
    return html;
}

// ==================== INTERVIEW PREP ====================
async function getInterviewPrep(event) {
    // Prevent any default behavior or form submission
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('getInterviewPrep called - preparing interview guide');
    
    var resumeId = document.getElementById('interview-resume').value;
    var jdId = document.getElementById('interview-jd').value;
    
    if (!resumeId || !jdId) {
        showToast('Select both resume and job', 'warning');
        return false;
    }
    
    var operationId = beginOperation('interview preparation');
    if (!operationId) {
        return false;
    }
    // Invalidate any pending analysis-only render from older requests.
    analysisRenderNonce++;

    var interviewBtn = event && event.currentTarget ? event.currentTarget : null;
    if (interviewBtn) {
        interviewBtn.disabled = true;
        interviewBtn.classList.add('opacity-60', 'cursor-not-allowed');
    }
    
    showOperationLoading(operationId, '🔄 Preparing interview guide...');
    startLoadingMessageRotation([
        '🧠 Building interview profile from resume and JD...',
        '🤖 Generating likely interview questions...',
        '📝 Preparing focused checklist and strategies...',
        '✅ Finalizing your interview plan...'
    ], 2300, operationId);
    
    // Helper function to add timeout to fetch
    function fetchWithTimeout(url, options, timeoutMs) {
        return Promise.race([
            fetch(url, options),
            new Promise(function(_, reject) {
                setTimeout(function() {
                    reject(new Error('Request timeout after ' + timeoutMs + 'ms'));
                }, timeoutMs);
            })
        ]);
    }

    try {
        // Speed optimization: do not block on analysis job for interview prep.
        // Reuse cached analysis if available for same resume/jd pair.
        var cachedAnalysis = getMatchingAnalysisSnapshot(resumeId, jdId);

        var interviewData = await fetchWithTimeout(
            API_URL + '/api/ai/interview-prep/' + resumeId + '/' + jdId,
            {},
            45000
        ).then(function(response) {
            if (!response.ok) {
                if (response.status === 504) {
                    throw new Error('AI service took too long. Please try again.');
                }
                throw new Error('Interview prep API error: ' + response.status);
            }
            return response.json();
        });

        var data = interviewData;
        console.log('Interview prep:', data);

        // If a matching analysis is already saved, reuse it instantly.
        if (cachedAnalysis && cachedAnalysis.data) {
            var analysisData = cachedAnalysis.data;
            data.match_score = analysisData.match_score;
            data.ats_score = analysisData.ats_score;
            data.score_breakdown = analysisData.score_breakdown;
            data.matched_skills = analysisData.matched_skills;
            data.missing_skills = analysisData.missing_skills;
        }
        
        var payload = buildAIWorkspacePayload('interview_prep', data);
        if (payload) setAIWorkspaceResult(payload);
        saveLatestAISnapshot({
            type: 'interview_prep',
            data: data,
            saved_at: new Date().toISOString()
        });
        showToast('✅ Interview prep ready!', 'success');
    } catch (error) {
        console.error('Interview prep error:', error);
        
        var errorMsg = error.message || String(error);
        
        // Handle specific error types
        if (errorMsg.includes('timeout') || errorMsg.includes('504')) {
            showToast('⏱️  Taking longer than expected, but results are on the way. Please try again in a moment.', 'warning');
        } else if (errorMsg.includes('404')) {
            showToast('❌ Resume or job description not found', 'error');
        } else if (errorMsg.includes('500')) {
            showToast('❌ Server error. Please try again.', 'error');
        } else {
            showToast('❌ Error: ' + errorMsg, 'error');
        }
    } finally {
        finishOperation(operationId);
        if (interviewBtn) {
            interviewBtn.disabled = false;
            interviewBtn.classList.remove('opacity-60', 'cursor-not-allowed');
        }
    }
    
    return false;
}

function renderInterviewPrep(data) {
    var html = '<div class="space-y-4 w-full text-sm">';
    
    var matchScore = data.match_score || 0;
    
    // Header with Job Info and Score
    html += '<div class="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg p-4 text-white">';
    html += '<h3 class="font-bold text-sm mb-2"><i class="fas fa-comments mr-1"></i>' + (data.job_title || 'Position') + ' at ' + (data.company || 'Company') + '</h3>';
    html += '<div class="text-lg font-bold">' + Math.round(matchScore) + '% Match Score</div>';
    html += '<p class="text-xs opacity-90 mt-1">Your resume alignment with this role</p>';
    html += '</div>';
    
    // Strengths to Highlight
    if (data.strengths_to_highlight && data.strengths_to_highlight.length > 0) {
        html += '<div class="bg-green-50 rounded-lg p-4 border-l-4 border-green-500">';
        html += '<h3 class="font-bold text-green-700 mb-2"><i class="fas fa-check-circle mr-1"></i>Strengths to Highlight</h3>';
        for (var s = 0; s < Math.min(data.strengths_to_highlight.length, 5); s++) {
            html += '<div class="mb-2 text-gray-700"><span class="text-green-600 font-semibold">✓</span> ' + data.strengths_to_highlight[s] + '</div>';
        }
        html += '</div>';
    }
    
    // Potential Weaknesses
    if (data.potential_weaknesses && data.potential_weaknesses.length > 0) {
        html += '<div class="bg-yellow-50 rounded-lg p-4 border-l-4 border-yellow-500">';
        html += '<h3 class="font-bold text-yellow-700 mb-2"><i class="fas fa-exclamation-circle mr-1"></i>Areas to Address</h3>';
        for (var w = 0; w < Math.min(data.potential_weaknesses.length, 5); w++) {
            html += '<div class="mb-2 text-gray-700"><span class="text-yellow-600 font-semibold">⚠</span> ' + data.potential_weaknesses[w] + '</div>';
        }
        html += '</div>';
    }
    
    // Interview Guide - Key Areas
    if (data.interview_guide && data.interview_guide.key_areas && data.interview_guide.key_areas.length > 0) {
        html += '<div class="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">';
        html += '<h3 class="font-bold text-blue-700 mb-3"><i class="fas fa-lightbulb mr-1"></i>Key Topics to Prepare</h3>';
        for (var k = 0; k < Math.min(data.interview_guide.key_areas.length, 8); k++) {
            html += '<div class="mb-2 flex gap-2"><span class="text-blue-600 flex-shrink-0">→</span><span class="text-gray-700">' + data.interview_guide.key_areas[k] + '</span></div>';
        }
        html += '</div>';
    }
    
    // Expected Questions
    if (data.interview_guide && data.interview_guide.likely_questions && data.interview_guide.likely_questions.length > 0) {
        html += '<div class="bg-purple-50 rounded-lg p-4 border-l-4 border-purple-500">';
        html += '<h3 class="font-bold text-purple-700 mb-3"><i class="fas fa-question-circle mr-1"></i>Likely Interview Questions</h3>';
        for (var q = 0; q < Math.min(data.interview_guide.likely_questions.length, 5); q++) {
            html += '<div class="mb-3 bg-white rounded p-2">';
            html += '<p class="text-gray-800 font-semibold text-xs mb-1">Q' + (q+1) + ': ' + data.interview_guide.likely_questions[q] + '</p>';
            html += '</div>';
        }
        html += '</div>';
    }
    
    // Preparation Checklist
    if (data.preparation_checklist && data.preparation_checklist.length > 0) {
        html += '<div class="bg-indigo-50 rounded-lg p-4 border-l-4 border-indigo-500">';
        html += '<h3 class="font-bold text-indigo-700 mb-3"><i class="fas fa-tasks mr-1"></i>Preparation Checklist</h3>';
        for (var c = 0; c < Math.min(data.preparation_checklist.length, 6); c++) {
            var checklist_item = data.preparation_checklist[c];
            // Handle both string items and object items
            var item_text = typeof checklist_item === 'string' ? checklist_item : (checklist_item.item || checklist_item.title || JSON.stringify(checklist_item));
            var item_details = typeof checklist_item === 'object' ? (checklist_item.details || '') : '';
            
            html += '<div class="mb-2">';
            html += '<div class="flex gap-2"><input type="checkbox" class="rounded" /> <span class="text-gray-700 font-semibold text-sm">' + item_text + '</span></div>';
            if (item_details) {
                html += '<p class="text-xs text-gray-600 ml-6 mt-1">' + item_details + '</p>';
            }
            html += '</div>';
        }
        html += '</div>';
    }
    
    // Answer Strategies
    if (data.interview_guide && data.interview_guide.answer_strategies && data.interview_guide.answer_strategies.length > 0) {
        html += '<div class="bg-orange-50 rounded-lg p-4 border-l-4 border-orange-500">';
        html += '<h3 class="font-bold text-orange-700 mb-3"><i class="fas fa-brain mr-1"></i>Answer Strategies</h3>';
        for (var a = 0; a < Math.min(data.interview_guide.answer_strategies.length, 4); a++) {
            html += '<div class="mb-2 text-gray-700">💡 ' + data.interview_guide.answer_strategies[a] + '</div>';
        }
        html += '</div>';
    }
    
    // Tips & Advice
    if (data.interview_guide && data.interview_guide.tips && data.interview_guide.tips.length > 0) {
        html += '<div class="bg-red-50 rounded-lg p-4 border-l-4 border-red-500">';
        html += '<h3 class="font-bold text-red-700 mb-3"><i class="fas fa-star mr-1"></i>Pro Tips</h3>';
        for (var t = 0; t < Math.min(data.interview_guide.tips.length, 4); t++) {
            html += '<div class="mb-2 text-gray-700">🎯 ' + data.interview_guide.tips[t] + '</div>';
        }
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// ==================== GLOBAL FUNCTIONS ====================
window.showSection = showSection;
window.showDashboardTab = showDashboardTab;
window.logout = logout;
window.uploadResume = uploadResume;
window.deleteResume = deleteResume;
window.resetDropZone = resetDropZone;
window.analyzeMatch = analyzeMatch;
window.getAISuggestions = getAISuggestions;
window.getAISuggestionsForResume = getAISuggestionsForResume;
window.getCareerPath = getCareerPath;
window.getCoverLetter = getCoverLetter;
window.getTailoredResume = getTailoredResume;
window.getInterviewPrep = getInterviewPrep;
window.downloadAnalysisReport = downloadAnalysisReport;
window.switchAIResultView = switchAIResultView;
window.copyAIResultText = copyAIResultText;
window.downloadAIResultText = downloadAIResultText;

console.log('✅ All functions loaded!');

// ==================== EXPORTS FOR HTML WRAPPERS ====================
window._showSection = showSection;
window._showDashboardTab = showDashboardTab;
window._logout = logout;
window._handleLogin = handleLogin;
window._handleRegister = handleRegister;
window._uploadResume = uploadResume;
window._loadResumes = loadResumes;
console.log('✅ Functions exported to window object');
