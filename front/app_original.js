console.log('✅ app.js is loading...');

// ==================== CONFIGURATION ====================
const API_URL = 'http://localhost:5000';

// ==================== STATE ====================
let currentUser = null;
let resumes = [];
let jobDescriptions = [];
let selectedFile = null;

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
    var loadingText = document.getElementById('loading-text');
    var loadingOverlay = document.getElementById('loading-overlay');
    
    if (loadingText) loadingText.textContent = message || 'Loading...';
    if (loadingOverlay) loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    var loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.classList.add('hidden');
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
    var resumeSelects = ['analysis-resume', 'ai-resume', 'interview-resume'];
    var jdSelects = ['analysis-jd', 'interview-jd'];
    
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
function analyzeMatch(event) {
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
    
    showLoading('Analyzing...');
    
    fetch(API_URL + '/api/analyze/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: parseInt(resumeId), jd_id: parseInt(jdId) })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        hideLoading();
        console.log('✅ Analysis complete:', data);
        
        var container = document.getElementById('analysis-results');
        console.log('Container found:', container);
        
        if (container) {
            var html = renderAnalysisResults(data);
            console.log('HTML generated, length:', html.length);
            container.innerHTML = html;
            
            // FORCE VISIBILITY - fixes fullscreen issue
            container.style.display = 'block';
            container.style.visibility = 'visible';
            container.style.opacity = '1';
            
            // Scroll into view
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            console.log('✅ Results rendered and visible');
        } else {
            console.error('❌ Container #analysis-results not found!');
        }
        showToast('Analysis complete!', 'success');
    })
    .catch(function(error) {
        hideLoading();
        console.error('Analysis error:', error);
        showToast('Error during analysis', 'error');
    });
}

function renderAnalysisResults(data) {
    var matchScore = data.match_score || 0;
    var atsScore = 0;
    
    if (data.ats_score) {
        atsScore = typeof data.ats_score === 'object' 
            ? (data.ats_score.percentage || 0) 
            : data.ats_score;
    }
    
    var html = '<div class="space-y-6">';
    
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
        
        var container = document.getElementById('ai-results');
        if (container) {
            container.innerHTML = renderAISuggestions(data);
        }
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
    var html = '<div class="space-y-4 w-full">';
    
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
    
    // Suggestions
    var suggestions = data.ai_suggestions || data.suggestions || [];
    if (suggestions.length > 0) {
        html += '<div class="space-y-2">';
        html += '<h3 class="text-sm font-bold text-gray-800"><i class="fas fa-list-check text-primary-500 mr-2"></i>Suggestions</h3>';
        for (var i = 0; i < Math.min(suggestions.length, 5); i++) {
            var s = suggestions[i];
            var text = typeof s === 'string' ? s : (s.suggestion || s.text || JSON.stringify(s));
            // Truncate long text
            if (text.length > 80) text = text.substring(0, 80) + '...';
            html += '<div class="p-2 rounded-lg border-l-4 border-primary-500 bg-primary-50 text-xs text-gray-700">' + text + '</div>';
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
    
    showLoading('Generating career path...');
    
    fetch(API_URL + '/api/ai/career-path/' + currentUser.id)
    .then(function(response) { return response.json(); })
    .then(function(data) {
        hideLoading();
        console.log('Career path:', data);
        
        var container = document.getElementById('ai-results');
        if (container) {
            container.innerHTML = renderCareerPath(data);
        }
        showToast('Career path generated!', 'success');
    })
    .catch(function(error) {
        hideLoading();
        console.error('Career path error:', error);
        showToast('Error generating career path', 'error');
    });
}

function renderCareerPath(data) {
    var html = '<div class="space-y-3 w-full text-sm">';
    
    // Current Skills
    if (data.current_skills && data.current_skills.length > 0) {
        html += '<div class="bg-blue-50 rounded-lg p-3 border border-blue-100">';
        html += '<h3 class="font-bold text-blue-700 text-xs mb-2"><i class="fas fa-tools mr-1"></i>Skills (' + Math.min(data.current_skills.length, 5) + ')</h3>';
        html += '<div class="flex flex-wrap gap-1">';
        for (var i = 0; i < Math.min(data.current_skills.length, 5); i++) {
            html += '<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">' + data.current_skills[i] + '</span>';
        }
        if (data.current_skills.length > 5) html += '<span class="text-blue-600 text-xs">+' + (data.current_skills.length - 5) + ' more</span>';
        html += '</div></div>';
    }
    
    // Career Options
    if (data.career_options && data.career_options.length > 0) {
        html += '<div class="bg-purple-50 rounded-lg p-3 border border-purple-100">';
        html += '<h3 class="font-bold text-purple-700 text-xs mb-2"><i class="fas fa-briefcase mr-1"></i>Paths</h3>';
        for (var j = 0; j < Math.min(data.career_options.length, 3); j++) {
            var career = data.career_options[j];
            html += '<p class="text-xs text-gray-700 mb-1">• ' + career.title + '</p>';
        }
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}
            html += '</ul></div>';
        }
        
        if (roadmap.long_term && roadmap.long_term.length > 0) {
            html += '<div class="bg-white rounded-xl p-4 border-l-4 border-purple-500">';
            html += '<h4 class="font-bold text-purple-600 mb-2">Long Term (18+ months)</h4>';
            html += '<ul class="space-y-1">';
            for (var o = 0; o < roadmap.long_term.length; o++) {
                html += '<li class="flex items-start gap-2"><i class="fas fa-star text-purple-500 mt-1"></i>' + roadmap.long_term[o] + '</li>';
            }
            html += '</ul></div>';
        }
        
        html += '</div></div>';
    }
    
    if (data.data_source) {
        html += '<div class="text-center text-sm text-gray-500"><i class="fas fa-database mr-1"></i>' + data.data_source + '</div>';
    }
    
    html += '</div>';
    return html;
}

// ==================== INTERVIEW PREP ====================
function getInterviewPrep(event) {
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
    
    showLoading('Preparing interview guide...');
    
    // First get analysis for accurate scores
    fetch(API_URL + '/api/analyze/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_id: parseInt(resumeId), jd_id: parseInt(jdId) })
    })
    .then(function(response) { return response.json(); })
    .then(function(analysisData) {
        console.log('Analysis for interview:', analysisData);
        
        // Now get interview prep
        return fetch(API_URL + '/api/ai/interview-prep/' + resumeId + '/' + jdId)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            // Merge analysis data
            data.match_score = analysisData.match_score;
            data.ats_score = analysisData.ats_score;
            data.score_breakdown = analysisData.score_breakdown;
            data.matched_skills = analysisData.matched_skills;
            data.missing_skills = analysisData.missing_skills;
            return data;
        });
    })
    .then(function(data) {
        hideLoading();
        console.log('✅ Interview prep complete:', data);
        
        var container = document.getElementById('ai-results');
        console.log('Container found:', container);
        
        if (container) {
            var html = renderInterviewPrep(data);
            console.log('HTML generated, length:', html.length);
            container.innerHTML = html;
            
            // FORCE VISIBILITY - fixes fullscreen issue
            container.style.display = 'block';
            container.style.visibility = 'visible';
            container.style.opacity = '1';
            
            // Scroll into view
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            console.log('✅ Interview prep rendered and visible');
        } else {
            console.error('❌ Container #ai-results not found!');
        }
        showToast('Interview prep ready!', 'success');
    })
    .catch(function(error) {
        hideLoading();
        console.error('Interview prep error:', error);
        showToast('Error generating interview prep', 'error');
    });
}

function renderInterviewPrep(data) {
    var html = '<div class="space-y-3 w-full text-sm">';
    
    var matchScore = data.match_score || 0;
    var atsScore = 0;
    if (data.ats_score) {
        atsScore = typeof data.ats_score === 'object' ? (data.ats_score.percentage || 0) : data.ats_score;
    }
    
    // Header with scores
    html += '<div class="bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg p-3 text-white">';
    html += '<h3 class="font-bold text-xs mb-2"><i class="fas fa-comments mr-1"></i>Interview Prep</h3>';
    html += '<div class="grid grid-cols-2 gap-2">';
    html += '<div class="bg-white/20 rounded-lg p-2 text-center"><p class="font-bold">' + Math.round(matchScore) + '%</p><p class="text-xs opacity-90">Match</p></div>';
    html += '<div class="bg-white/20 rounded-lg p-2 text-center"><p class="font-bold">' + Math.round(atsScore) + '%</p><p class="text-xs opacity-90">ATS</p></div>';
    html += '</div></div>';
    
    // Skills to Highlight
    if (data.matched_skills && data.matched_skills.length > 0) {
        html += '<div class="bg-green-50 rounded-lg p-3 border border-green-100">';
        html += '<h3 class="font-bold text-green-700 text-xs mb-2"><i class="fas fa-star mr-1"></i>Top Skills</h3>';
        html += '<div class="flex flex-wrap gap-1">';
        for (var s = 0; s < Math.min(data.matched_skills.length, 4); s++) {
            html += '<span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">' + data.matched_skills[s] + '</span>';
        }
        html += '</div></div>';
    }
    
    // Key Topics
    if (data.interview_guide && data.interview_guide.key_areas) {
        html += '<div class="bg-blue-50 rounded-lg p-3 border border-blue-100">';
        html += '<h3 class="font-bold text-blue-700 text-xs mb-2"><i class="fas fa-bullseye mr-1"></i>Topics</h3>';
        for (var i = 0; i < Math.min(data.interview_guide.key_areas.length, 4); i++) {
            html += '<p class="text-xs text-gray-700">• ' + data.interview_guide.key_areas[i] + '</p>';
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
window.getInterviewPrep = getInterviewPrep;

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