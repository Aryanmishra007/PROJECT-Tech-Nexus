/* ============================================================
   NexaAI — Complete Frontend Logic
   ============================================================ */

'use strict';

// ── State ──────────────────────────────────────────────────────
let currentUser = null;
let currentRole = 'ai';
let currentAnalysis = null;
let interviewQuestions = [];
let currentQuestionIndex = 0;
let interviewAnswers = [];
let diagnosticQuestions = [];
let diagnosticAnswers = [];
let speechRecognition = null;
let isRecording = false;
let selectedFile = null;
let selectedDiagnosticOption = null;
let diagnosticScore = 0;

// Role display names
const ROLE_LABELS = {
  ai:           'AI Engineer',
  data_analyst: 'Data Analyst',
  web_developer:'Web Developer',
  ml_engineer:  'ML Engineer',
  devops:       'DevOps Engineer'
};

/* ══════════════════════════════════════════════════════════════
   PAGE / SCREEN ROUTING
   ══════════════════════════════════════════════════════════════ */

function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const target = document.getElementById(pageId);
  if (target) {
    target.classList.add('active');
    window.scrollTo(0, 0);
  }
}

function showScreen(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const target = document.getElementById(screenId);
  if (target) {
    target.classList.add('active');
    // Animate in
    target.style.animation = 'none';
    void target.offsetWidth; // reflow
    target.style.animation = 'fadeIn 0.35s ease';
  }

  // Update sidebar nav active state
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.screen === screenId) {
      item.classList.add('active');
    }
  });

  // Update header title
  const titleMap = {
    'screen-dashboard':  'Dashboard',
    'screen-upload':     'Upload Resume',
    'screen-skills':     'Skill Report',
    'screen-diagnostic': 'Diagnostic Test',
    'screen-learning':   'Learning Path',
    'screen-interview':  'Mock Interview',
    'screen-ats':        'ATS Suggestions',
    'screen-admin':      'Admin Analytics',
    'screen-profile':    'My Profile'
  };
  const titleEl = document.getElementById('header-title');
  if (titleEl) titleEl.textContent = titleMap[screenId] || 'NexaAI';

  // Close sidebar on mobile
  if (window.innerWidth <= 768) closeSidebar();
}

/* ══════════════════════════════════════════════════════════════
   SIDEBAR TOGGLE (MOBILE)
   ══════════════════════════════════════════════════════════════ */

function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!sidebar) return;
  const isOpen = sidebar.classList.contains('open');
  if (isOpen) {
    closeSidebar();
  } else {
    sidebar.classList.add('open');
    if (overlay) {
      overlay.classList.add('visible');
      overlay.style.display = 'block';
    }
  }
}

function closeSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) {
    overlay.classList.remove('visible');
    setTimeout(() => { overlay.style.display = 'none'; }, 300);
  }
}

/* ══════════════════════════════════════════════════════════════
   AUTH — REGISTER
   ══════════════════════════════════════════════════════════════ */

async function handleRegister() {
  const name     = document.getElementById('reg-name')?.value.trim();
  const email    = document.getElementById('reg-email')?.value.trim();
  const password = document.getElementById('reg-password')?.value;
  const confirm  = document.getElementById('reg-confirm')?.value;

  // Validation
  if (!name || !email || !password || !confirm) {
    showToast('Please fill in all fields', 'error');
    return;
  }
  if (!isValidEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }
  if (password.length < 6) {
    showToast('Password must be at least 6 characters', 'error');
    return;
  }
  if (password !== confirm) {
    showToast('Passwords do not match', 'error');
    return;
  }

  const btn = document.getElementById('register-btn');
  setButtonLoading(btn, true, 'Creating Account...');

  try {
    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ name, email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Registration failed');
    }

    currentUser = data.user || { name, email };
    
    // Clear registration form
    document.getElementById('reg-name').value = '';
    document.getElementById('reg-email').value = '';
    document.getElementById('reg-password').value = '';
    document.getElementById('reg-confirm').value = '';
    
    showToast(`Welcome to NexaAI, ${name}!`, 'success');
    
    // Hide auth page and show dashboard
    showPage('app-page');
    loadDashboard();
    showScreen('screen-dashboard');
  } catch (err) {
    showToast(err.message || 'Registration failed. Please try again.', 'error', 5000);
  } finally {
    setButtonLoading(btn, false, 'Create Account');
  }
}

/* ══════════════════════════════════════════════════════════════
   AUTH — TAB SWITCHING
   ══════════════════════════════════════════════════════════════ */

function switchAuthTab(tab) {
  // Hide all panels and deactivate all buttons (old tabs + new pills)
  ['login', 'signup', 'admin', 'forgot'].forEach(t => {
    const panel = document.getElementById('auth-tab-' + t);
    const oldBtn = document.getElementById('tab-' + t);
    const pillBtn = document.getElementById('pill-' + t);
    if (panel)   panel.classList.add('hidden');
    if (oldBtn)  oldBtn.classList.remove('active');
    if (pillBtn) pillBtn.classList.remove('active');
  });

  // Show selected panel and activate matching buttons
  const activePanel = document.getElementById('auth-tab-' + tab);
  const activeOldBtn = document.getElementById('tab-' + tab);
  const activePill  = document.getElementById('pill-' + tab);
  if (activePanel)  activePanel.classList.remove('hidden');
  if (activeOldBtn) activeOldBtn.classList.add('active');
  if (activePill)   activePill.classList.add('active');

  // Reset forgot password form when switching tabs
  if (tab === 'forgot') {
    resetForgotPasswordForm();
  }
}

/* ══════════════════════════════════════════════════════════════
   AUTH — FORGOT PASSWORD
   ══════════════════════════════════════════════════════════════ */

let forgotPasswordEmail = '';

function resetForgotPasswordForm() {
  const step1 = document.getElementById('forgot-step-1');
  const step2 = document.getElementById('forgot-step-2');
  if (step1) step1.classList.remove('hidden');
  if (step2) step2.classList.add('hidden');
  
  // Clear inputs
  const forgotEmail = document.getElementById('forgot-email');
  const resetCode = document.getElementById('reset-code');
  const resetNewPwd = document.getElementById('reset-new-password');
  const resetConfirmPwd = document.getElementById('reset-confirm-password');
  
  if (forgotEmail) forgotEmail.value = '';
  if (resetCode) resetCode.value = '';
  if (resetNewPwd) resetNewPwd.value = '';
  if (resetConfirmPwd) resetConfirmPwd.value = '';
  
  forgotPasswordEmail = '';
}

async function handleForgotPassword() {
  const email = document.getElementById('forgot-email')?.value.trim();

  if (!email) {
    showToast('Please enter your email address', 'error');
    return;
  }
  if (!isValidEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }

  const btn = document.getElementById('forgot-btn');
  setButtonLoading(btn, true, 'Sending...');

  try {
    const res = await fetch('/api/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Failed to process request');
    }

    forgotPasswordEmail = email;
    
    // Show step 2
    const step1 = document.getElementById('forgot-step-1');
    const step2 = document.getElementById('forgot-step-2');
    if (step1) step1.classList.add('hidden');
    if (step2) step2.classList.remove('hidden');

    // Show the reset code to the user (since we don't have email)
    if (data.reset_code) {
      // Display code in the UI
      const codeDisplay = document.getElementById('display-reset-code');
      if (codeDisplay) codeDisplay.textContent = data.reset_code;
      
      showToast(`Reset code generated successfully!`, 'success');
    } else {
      showToast('Reset code sent! Check your email.', 'success');
    }

  } catch (err) {
    showToast(err.message || 'Failed to send reset code', 'error');
  } finally {
    setButtonLoading(btn, false, '<i class="bi bi-send"></i> Send Reset Code');
  }
}

async function handleResetPassword() {
  const code = document.getElementById('reset-code')?.value.trim();
  const newPassword = document.getElementById('reset-new-password')?.value;
  const confirmPassword = document.getElementById('reset-confirm-password')?.value;

  if (!code) {
    showToast('Please enter the reset code', 'error');
    return;
  }
  if (!newPassword || !confirmPassword) {
    showToast('Please enter your new password', 'error');
    return;
  }
  if (newPassword.length < 6) {
    showToast('Password must be at least 6 characters', 'error');
    return;
  }
  if (newPassword !== confirmPassword) {
    showToast('Passwords do not match', 'error');
    return;
  }

  const btn = document.getElementById('reset-btn');
  setButtonLoading(btn, true, 'Resetting...');

  try {
    const res = await fetch('/api/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        email: forgotPasswordEmail,
        reset_code: code,
        new_password: newPassword 
      })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Failed to reset password');
    }

    showToast('Password reset successfully! Please sign in.', 'success');
    resetForgotPasswordForm();
    switchAuthTab('login');

  } catch (err) {
    showToast(err.message || 'Failed to reset password', 'error');
  } finally {
    setButtonLoading(btn, false, '<i class="bi bi-check-circle"></i> Reset Password');
  }
}

/* ══════════════════════════════════════════════════════════════
   AUTH — ADMIN LOGIN
   ══════════════════════════════════════════════════════════════ */

async function handleAdminLogin() {
  const email    = document.getElementById('admin-email')?.value.trim();
  const password = document.getElementById('admin-password')?.value;

  if (!email || !password) {
    showToast('Please enter admin email and password', 'error');
    return;
  }
  if (!isValidEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }

  const btn = document.getElementById('admin-login-btn');
  setButtonLoading(btn, true, 'Admin Sign In...');

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Login failed');
    }

    if (data.user.role !== 'admin') {
      throw new Error('This account is not an admin account');
    }

    currentUser = data.user;
    showToast('Welcome Admin!', 'success');
    showPage('app-page');
    loadDashboard();
    showScreen('screen-admin');
  } catch (err) {
    showToast(err.message || 'Admin login failed.', 'error');
  } finally {
    setButtonLoading(btn, false, 'Admin Sign In');
  }
}

/* ══════════════════════════════════════════════════════════════
   AUTH — LOGIN
   ══════════════════════════════════════════════════════════════ */

async function handleLogin() {
  const email    = document.getElementById('login-email')?.value.trim();
  const password = document.getElementById('login-password')?.value;

  if (!email || !password) {
    showToast('Please enter email and password', 'error');
    return;
  }
  if (!isValidEmail(email)) {
    showToast('Please enter a valid email address', 'error');
    return;
  }

  const btn = document.getElementById('login-btn');
  setButtonLoading(btn, true, 'Signing In...');

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Login failed');
    }

    currentUser = data.user || { email };
    
    // Clear login form
    document.getElementById('login-email').value = '';
    document.getElementById('login-password').value = '';
    
    showToast('Welcome back!', 'success');
    
    // Hide auth page and show dashboard
    showPage('app-page');
    loadDashboard();
    showScreen('screen-dashboard');
  } catch (err) {
    // Show clear error message to user
    const errorMsg = err.message || 'Invalid email or password.';
    console.log('[Login Error]', errorMsg);
    showToast(errorMsg, 'error', 5000);
  } finally {
    setButtonLoading(btn, false, 'Sign In');
  }
}

/* ── Logout ────────────────────────────────────────────────── */

async function logout() {
  try {
    await fetch('/api/logout', { method: 'POST', credentials: 'include' });
  } catch (_) { /* silent */ }
  currentUser = null;
  currentAnalysis = null;
  interviewQuestions = [];
  diagnosticQuestions = [];
  showToast('You have been logged out', 'info');
  showPage('auth-page');
  switchAuthTab('login');
}

/* ── Check Auth on Load ─────────────────────────────────────── */

async function checkAuth() {
  try {
    const res = await fetch('/api/user', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      showPage('app-page');
      loadDashboard();
      showScreen('screen-dashboard');
    } else {
      showPage('auth-page');
      switchAuthTab('login');
    }
  } catch (_) {
    showPage('auth-page');
    switchAuthTab('login');
  }
}

/* ══════════════════════════════════════════════════════════════
   DASHBOARD
   ══════════════════════════════════════════════════════════════ */

async function loadDashboard() {
  // Update display name
  const nameEl = document.getElementById('user-display-name');
  const avatarEl = document.getElementById('user-avatar-initials');
  const sidebarNameEl = document.getElementById('sidebar-user-name');
  const sidebarRoleEl = document.getElementById('sidebar-user-role');

  const name = currentUser?.name || currentUser?.email?.split('@')[0] || 'User';
  const role = currentUser?.role || 'student';
  
  if (nameEl) nameEl.textContent = name;
  if (sidebarNameEl) sidebarNameEl.textContent = name;
  if (avatarEl) avatarEl.textContent = name.charAt(0).toUpperCase();
  if (sidebarRoleEl) sidebarRoleEl.textContent = role === 'admin' ? 'Admin' : 'Student';
  
  // Show/hide admin section based on role
  updateAdminAccess(role);
  
  // Add pulse animation to analyze button to attract attention
  const analyzeBtn = document.getElementById('analyze-btn');
  if (analyzeBtn) {
    analyzeBtn.classList.add('btn-pulse');
    // Remove pulse after first click
    analyzeBtn.addEventListener('click', () => {
      analyzeBtn.classList.remove('btn-pulse');
    }, { once: true });
  }

  try {
    const res = await fetch('/api/user-stats', { credentials: 'include' });
    if (res.ok) {
      const data = await res.json();
      updateStatCards(data);
    } else {
      // Show placeholder values
      updateStatCards({ resumes: 0, match_score: 0, skills: 0, interviews: 0 });
    }
  } catch (_) {
    updateStatCards({ resumes: 0, match_score: 0, skills: 0, interviews: 0 });
  }
}

// Show/hide admin elements based on user role
function updateAdminAccess(role) {
  const adminElements = document.querySelectorAll('.admin-only');
  adminElements.forEach(el => {
    if (role === 'admin') {
      el.classList.remove('hidden');
      el.classList.add('visible');
    } else {
      el.classList.add('hidden');
      el.classList.remove('visible');
    }
  });
}

function updateStatCards(data) {
  animateNumber('stat-resumes',    data.resumes    ?? 0);
  animateNumber('stat-match',      data.match_score?? 0, '%');
  animateNumber('stat-skills',     data.skills     ?? 0);
  animateNumber('stat-interviews', data.interviews ?? 0);
}

/* ══════════════════════════════════════════════════════════════
   QUICK ANALYZE
   ══════════════════════════════════════════════════════════════ */

async function quickAnalyze() {
  const roleSelect = document.getElementById('target-role');
  if (!roleSelect || !roleSelect.value) {
    showToast('Please select a target job role', 'error');
    return;
  }

  currentRole = roleSelect.value;
  const btn = document.getElementById('analyze-btn');
  setButtonLoading(btn, true, 'Analyzing...');

  try {
    const res = await fetch('/api/analyze-skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ role: currentRole })
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Analysis failed');

    currentAnalysis = data;
    showScreen('screen-skills');
    displaySkillAnalysis(data);
    showToast('Skill analysis complete!', 'success');
  } catch (err) {
    showToast(err.message || 'Analysis failed. Upload a resume first.', 'error');
  } finally {
    setButtonLoading(btn, false, 'Analyze Skills');
  }
}

/* ══════════════════════════════════════════════════════════════
   FILE UPLOAD
   ══════════════════════════════════════════════════════════════ */

function handleDragOver(event) {
  event.preventDefault();
  event.stopPropagation();
  const zone = document.getElementById('upload-zone');
  if (zone) zone.classList.add('drag-over');
}

function handleDragLeave(event) {
  event.preventDefault();
  const zone = document.getElementById('upload-zone');
  if (zone) zone.classList.remove('drag-over');
}

function handleDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  const zone = document.getElementById('upload-zone');
  if (zone) zone.classList.remove('drag-over');

  const files = event.dataTransfer?.files;
  if (files && files.length > 0) {
    processSelectedFile(files[0]);
  }
}

function handleFileSelect(event) {
  const file = event.target?.files?.[0];
  if (file) processSelectedFile(file);
}

function processSelectedFile(file) {
  const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const allowedExtensions = ['.pdf', '.docx', '.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();

  if (!allowedExtensions.includes(ext)) {
    showToast('Please upload a PDF, DOCX, or TXT file', 'error');
    return;
  }

  if (file.size > 10 * 1024 * 1024) {
    showToast('File size must be under 10MB', 'error');
    return;
  }

  selectedFile = file;

  // Show file info
  const fileInfoEl = document.getElementById('selected-file-info');
  const fileNameEl = document.getElementById('selected-file-name');
  const fileSizeEl = document.getElementById('selected-file-size');
  const uploadBtn  = document.getElementById('upload-btn');

  if (fileNameEl) fileNameEl.textContent = file.name;
  if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.size);
  if (fileInfoEl) fileInfoEl.classList.remove('hidden');
  if (uploadBtn)  uploadBtn.disabled = false;

  showToast(`File "${file.name}" selected`, 'info');
}

async function startUpload() {
  if (!selectedFile) {
    showToast('Please select a resume file first', 'error');
    return;
  }

  const btn         = document.getElementById('upload-btn');
  const progressWrap= document.getElementById('upload-progress-wrap');
  const progressBar = document.getElementById('upload-progress');
  const progressPct = document.getElementById('upload-progress-pct');
  const resultsEl   = document.getElementById('upload-results');

  setButtonLoading(btn, true, 'Uploading...');
  if (progressWrap) progressWrap.classList.remove('hidden');
  if (resultsEl)    resultsEl.classList.add('hidden');

  // Simulate progress animation (0→85%) while uploading
  let pct = 0;
  const interval = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8 + 3, 85);
    if (progressBar) progressBar.style.width = pct + '%';
    if (progressPct) progressPct.textContent = Math.round(pct) + '%';
  }, 200);

  try {
    const formData = new FormData();
    formData.append('resume', selectedFile);

    const res = await fetch('/api/upload-resume', {
      method: 'POST',
      credentials: 'include',
      body: formData
    });
    const data = await res.json();

    clearInterval(interval);

    // Complete progress
    if (progressBar) progressBar.style.width = '100%';
    if (progressPct) progressPct.textContent = '100%';

    if (!res.ok) throw new Error(data.error || 'Upload failed');

    // Store analysis if returned
    if (data.data) currentAnalysis = data.data;

    // Display results
    displayUploadResults(data.data || data);
    showToast('Resume parsed successfully!', 'success');
  } catch (err) {
    clearInterval(interval);
    if (progressBar) progressBar.style.width = '0%';
    showToast(err.message || 'Upload failed. Please try again.', 'error');
  } finally {
    setButtonLoading(btn, false, 'Upload & Analyze');
  }
}

function displayUploadResults(data) {
  const resultsEl = document.getElementById('upload-results');
  if (!resultsEl) return;

  resultsEl.classList.remove('hidden');

  // Skills parsed
  const skillsContainer = document.getElementById('parsed-skills');
  if (skillsContainer && data.skills) {
    skillsContainer.innerHTML = '';
    data.skills.forEach(skill => {
      const chip = document.createElement('span');
      chip.className = 'chip chip-green';
      chip.innerHTML = `<i class="bi bi-check-circle"></i> ${capitalize(skill)}`;
      skillsContainer.appendChild(chip);
    });
  }

  // Skill count
  const countEl = document.getElementById('parsed-skill-count');
  if (countEl) countEl.textContent = data.skills?.length ?? 0;

  // Name / email if available
  const nameEl = document.getElementById('parsed-name');
  if (nameEl && data.name) nameEl.textContent = data.name;

  const emailEl = document.getElementById('parsed-email');
  if (emailEl && data.email) emailEl.textContent = data.email;
}

/* ══════════════════════════════════════════════════════════════
   SKILL ANALYSIS DISPLAY
   ══════════════════════════════════════════════════════════════ */

function displaySkillAnalysis(analysis) {
  if (!analysis) return;

  // Role label
  const roleLabel = document.getElementById('role-label');
  if (roleLabel) roleLabel.textContent = analysis.role_title || ROLE_LABELS[analysis.role_key] || 'Role';

  // Readiness
  const readinessEl = document.getElementById('readiness-value');
  if (readinessEl) readinessEl.textContent = analysis.readiness_level || 'Intermediate';

  const recEl = document.getElementById('recommendation-text');
  if (recEl) recEl.textContent = analysis.recommendation || '';

  // Circular SVG ring — circumference = 339.29
  const pct = analysis.overall_score ?? 0;
  const circumference = 339.29;
  const offset = circumference - (pct / 100 * circumference);

  const ringFill = document.getElementById('circle-fill');
  const ringValueText = document.getElementById('ring-value');
  if (ringFill) {
    ringFill.style.strokeDashoffset = circumference; // reset
    setTimeout(() => {
      ringFill.style.strokeDashoffset = offset;
    }, 100);
  }
  if (ringValueText) ringValueText.textContent = pct + '%';

  // Match % text
  const matchPctEl = document.getElementById('match-pct');
  if (matchPctEl) matchPctEl.textContent = pct + '%';

  // Category progress bars
  const catScores = analysis.category_scores || {};
  setProgressBar('bar-technical', catScores.technical ?? 0);
  setProgressBar('bar-tools',     catScores.tools     ?? 0);
  setProgressBar('bar-soft',      catScores.soft_skills ?? 0);

  const techPctEl = document.getElementById('pct-technical');
  const toolsPctEl= document.getElementById('pct-tools');
  const softPctEl = document.getElementById('pct-soft');
  if (techPctEl) techPctEl.textContent = (catScores.technical ?? 0) + '%';
  if (toolsPctEl) toolsPctEl.textContent = (catScores.tools ?? 0) + '%';
  if (softPctEl) softPctEl.textContent = (catScores.soft_skills ?? 0) + '%';

  // Skill chips
  renderSkillChips(analysis.skills_matched  || [], 'skills-have',     'have');
  renderSkillChips(analysis.skills_missing  || [], 'skills-missing',  'missing');
  renderSkillChips(analysis.skills_priority || [], 'skills-priority', 'priority');

  // Counts
  setTextContent('count-have',     (analysis.skills_matched  || []).length);
  setTextContent('count-missing',  (analysis.skills_missing  || []).length);
  setTextContent('count-priority', (analysis.skills_priority || []).length);
}

function setProgressBar(id, pct) {
  const bar = document.getElementById(id);
  if (bar) {
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.width = Math.min(pct, 100) + '%';
    }, 150);
  }
}

function renderSkillChips(skills, containerId, type) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  if (!skills || skills.length === 0) {
    container.innerHTML = `<span class="text-muted fs-sm" style="font-style:italic">None identified</span>`;
    return;
  }

  const classMap = { have: 'chip-have', missing: 'chip-missing', priority: 'chip-priority' };
  const iconMap  = { have: 'bi-check-circle', missing: 'bi-x-circle', priority: 'bi-star-fill' };
  const cls  = classMap[type]  || 'chip-info';
  const icon = iconMap[type]   || 'bi-circle';

  skills.forEach(skill => {
    const chip = document.createElement('span');
    chip.className = `chip ${cls}`;
    chip.innerHTML = `<i class="bi ${icon}"></i> ${capitalize(skill)}`;
    
    // Make missing skill chips clickable to start diagnostic test
    if (type === 'missing') {
      chip.style.cursor = 'pointer';
      chip.title = 'Click to start diagnostic test for this skill';
      chip.addEventListener('click', () => startDiagnosticForSkill(skill));
    }
    
    container.appendChild(chip);
  });
}

// Start diagnostic test for a specific skill
async function startDiagnosticForSkill(skill) {
  if (!skill) return;
  
  showToast(`Starting test for: ${skill}`, 'info');
  navToScreen('screen-diagnostic');
  
  const container = document.getElementById('diag-question-card');
  if (container) {
    container.innerHTML = '<div class="loading-overlay"><div class="spinner spinner-lg"></div></div>';
    container.classList.remove('hidden');
  }
  
  try {
    const res = await fetch(`/api/diagnostic-test/${encodeURIComponent(skill)}`, {
      credentials: 'include'
    });
    const data = await res.json();
    
    if (!res.ok) throw new Error(data.error || 'Failed to load questions');
    
    if (!data.questions || data.questions.length === 0) {
      showToast(`No questions available for ${skill}`, 'info');
      return;
    }
    
    diagnosticQuestions = data.questions;
    diagnosticAnswers = [];
    diagnosticScore = 0;
    currentQuestionIndex = 0;
    
    setTextContent('diagnostic-skill-name', skill);
    
    const resultEl = document.getElementById('diag-result');
    if (resultEl) resultEl.classList.add('hidden');
    
    loadDiagnosticQuestion(0);
  } catch (err) {
    showToast(err.message || 'Failed to load test questions', 'error');
    if (container) {
      container.innerHTML = `
        <div class="empty-state">
          <i class="bi bi-exclamation-circle"></i>
          <p>Failed to load questions. Please try again.</p>
        </div>
      `;
    }
  }
}

/* ══════════════════════════════════════════════════════════════
   DIAGNOSTIC TEST
   ══════════════════════════════════════════════════════════════ */

async function startDiagnosticTest() {
  if (!currentAnalysis) {
    showToast('Please analyze your skills first', 'error');
    return;
  }

  const missingSkills = currentAnalysis.skills_missing || [];
  if (missingSkills.length === 0) {
    showToast('No missing skills to test! You have great coverage.', 'info');
    return;
  }

  // Pick the first missing skill with questions available
  const skill = missingSkills[0];
  const btn = document.getElementById('start-diagnostic-btn');
  setButtonLoading(btn, true, 'Loading Test...');

  try {
    const res = await fetch(`/api/diagnostic-test/${encodeURIComponent(skill)}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Failed to load diagnostic');

    diagnosticQuestions = data.questions || [];
    diagnosticAnswers = new Array(diagnosticQuestions.length).fill(null);
    diagnosticScore = 0;

    showScreen('screen-diagnostic');
    setTextContent('diagnostic-skill-name', capitalize(skill));
    loadDiagnosticQuestion(0);
    showToast(`Diagnostic test: ${capitalize(skill)}`, 'info');
  } catch (err) {
    showToast(err.message || 'Could not load test', 'error');
  } finally {
    if (btn) setButtonLoading(btn, false, 'Start Diagnostic Test');
  }
}

function loadDiagnosticQuestion(index) {
  if (index >= diagnosticQuestions.length) {
    const score = diagnosticAnswers.filter((a, i) => a === diagnosticQuestions[i]?.correct).length;
    showDiagnosticResults(score, diagnosticQuestions.length);
    return;
  }

  selectedDiagnosticOption = null;
  const q = diagnosticQuestions[index];

  // Question text
  setTextContent('diag-question-num', `Question ${index + 1} of ${diagnosticQuestions.length}`);
  setTextContent('diag-question-text', q.question);

  // Options
  const optionsContainer = document.getElementById('diag-options');
  if (optionsContainer) {
    optionsContainer.innerHTML = '';
    q.options.forEach((opt, i) => {
      const btn = document.createElement('button');
      btn.className = 'option-btn';
      btn.dataset.index = i;
      btn.innerHTML = `
        <span class="option-letter">${String.fromCharCode(65 + i)}</span>
        <span>${opt}</span>
      `;
      btn.onclick = () => selectDiagnosticOption(i, i === q.correct);
      optionsContainer.appendChild(btn);
    });
  }

  // Progress bar
  const progressPct = ((index) / diagnosticQuestions.length) * 100;
  const progressBar = document.getElementById('diag-progress-bar');
  if (progressBar) progressBar.style.width = progressPct + '%';
  setTextContent('diag-progress-text', `${index + 1}/${diagnosticQuestions.length}`);

  // Next button state
  const nextBtn = document.getElementById('diag-next-btn');
  if (nextBtn) nextBtn.disabled = true;

  // Hide explanation
  const explBox = document.getElementById('diag-explanation');
  if (explBox) explBox.classList.add('hidden');
}

function selectDiagnosticOption(optionIndex, isCorrect) {
  if (selectedDiagnosticOption !== null) return; // Already answered

  selectedDiagnosticOption = optionIndex;
  diagnosticAnswers[currentDiagnosticIndex()] = optionIndex;

  const optionBtns = document.querySelectorAll('#diag-options .option-btn');
  const q = diagnosticQuestions[currentDiagnosticIndex()];

  optionBtns.forEach((btn, i) => {
    btn.disabled = true;
    if (i === q.correct) {
      btn.classList.add('correct');
    } else if (i === optionIndex && !isCorrect) {
      btn.classList.add('wrong');
    }
  });

  // Show explanation
  const explBox = document.getElementById('diag-explanation');
  if (explBox && q.explanation) {
    explBox.textContent = '💡 ' + q.explanation;
    explBox.classList.remove('hidden');
  }

  // Enable next
  const nextBtn = document.getElementById('diag-next-btn');
  if (nextBtn) nextBtn.disabled = false;
}

function currentDiagnosticIndex() {
  const qNum = document.getElementById('diag-question-num')?.textContent || 'Question 1';
  const match = qNum.match(/(\d+)/);
  return match ? parseInt(match[1]) - 1 : 0;
}

function nextDiagnosticQuestion() {
  const idx = currentDiagnosticIndex() + 1;
  if (idx >= diagnosticQuestions.length) {
    const score = diagnosticAnswers.filter((a, i) => a === diagnosticQuestions[i]?.correct).length;
    showDiagnosticResults(score, diagnosticQuestions.length);
  } else {
    loadDiagnosticQuestion(idx);
  }
}

function showDiagnosticResults(score, total) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;

  const resultEl = document.getElementById('diag-result');
  const questionEl = document.getElementById('diag-question-card');

  if (questionEl) questionEl.classList.add('hidden');
  if (resultEl) {
    resultEl.classList.remove('hidden');

    setTextContent('result-score', `${score}/${total}`);
    setTextContent('result-pct', `${pct}%`);

    let msg, cls;
    if (pct >= 75) {
      msg = 'Excellent work! You have strong knowledge of this skill.';
      cls = 'text-success';
      // Launch confetti for high scores!
      if (pct >= 80) {
        launchConfetti();
      }
    } else if (pct >= 50) {
      msg = 'Good effort! Review the topics you missed and try again.';
      cls = 'text-warning';
    } else {
      msg = 'Keep learning! Check the learning path for resources on this skill.';
      cls = 'text-danger';
    }
    const msgEl = document.getElementById('result-message');
    if (msgEl) {
      msgEl.textContent = msg;
      msgEl.className = cls;
    }
  }

  // Update progress to 100%
  const progressBar = document.getElementById('diag-progress-bar');
  if (progressBar) progressBar.style.width = '100%';
}

/* ══════════════════════════════════════════════════════════════
   LEARNING PATH
   ══════════════════════════════════════════════════════════════ */

async function loadLearningPath() {
  const role = currentAnalysis?.role_key || currentRole || 'ai';
  const missingSkills = currentAnalysis?.skills_missing || [];
  const container = document.getElementById('roadmap-container');
  const titleEl   = document.getElementById('learning-path-title');

  if (container) container.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p class="loading-text">Building your personalized path...</p></div>';

  try {
    const res = await fetch('/api/learning-path', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ target_role: role, missing_skills: missingSkills })
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Failed to load learning path');

    if (titleEl) titleEl.textContent = data.title || 'Your Learning Path';
    buildRoadmap(data, container);
  } catch (err) {
    if (container) container.innerHTML = `<div class="empty-state"><i class="bi bi-exclamation-circle"></i><p>${err.message}</p></div>`;
  }
}

function buildRoadmap(learningPath, container) {
  if (!container) return;
  container.innerHTML = '';

  const steps = learningPath.steps || [];
  if (steps.length === 0) {
    container.innerHTML = '<div class="empty-state"><i class="bi bi-check-circle"></i><p>No steps needed — you already have all required skills!</p></div>';
    return;
  }

  steps.forEach((step, idx) => {
    const stepEl = document.createElement('div');
    stepEl.className = 'roadmap-step animate-fade';
    stepEl.style.animationDelay = (idx * 0.08) + 's';

    const topicsHtml = (step.topics || []).map(t => `<span class="topic-chip">${t}</span>`).join('');
    const resourcesHtml = (step.resources || []).map(r =>
      `<a href="${r.url}" target="_blank" rel="noopener noreferrer" class="resource-link">
        <i class="bi bi-box-arrow-up-right"></i> ${r.name}
      </a>`
    ).join('');

    stepEl.innerHTML = `
      <div class="step-dot">${step.step || idx + 1}</div>
      <div class="step-card">
        <div class="step-header">
          <div class="step-title">${step.skill}</div>
          <span class="step-duration"><i class="bi bi-clock"></i> ${step.duration}</span>
        </div>
        <div class="step-topics">${topicsHtml}</div>
        ${resourcesHtml ? `<div class="step-resources">${resourcesHtml}</div>` : ''}
      </div>
    `;
    container.appendChild(stepEl);
  });
}

/* ══════════════════════════════════════════════════════════════
   MOCK INTERVIEW
   ══════════════════════════════════════════════════════════════ */

async function loadInterviewQuestions(role) {
  // Get role from parameter, select dropdown, currentRole, or default to 'ai'
  const roleSelect = document.getElementById('interview-role-select');
  role = role || (roleSelect ? roleSelect.value : null) || currentRole || 'ai';
  currentRole = role;
  
  // Sync the role select dropdown
  if (roleSelect && roleSelect.value !== role) {
    roleSelect.value = role;
  }
  
  currentQuestionIndex = 0;
  interviewAnswers = [];

  console.log('[Interview] Loading questions for role:', role);

  // Show loading state in question text, not by replacing the whole card
  const qText = document.getElementById('q-text');
  const qNum = document.getElementById('q-num');
  if (qText) qText.textContent = 'Loading questions...';
  if (qNum) qNum.innerHTML = '<i class="bi bi-hourglass-split"></i> Preparing...';

  try {
    const res = await fetch('/api/interview-questions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ role })
    });
    
    console.log('[Interview] API response status:', res.status);
    
    // Handle auth errors
    if (res.status === 401) {
      showToast('Please log in to access mock interviews', 'error');
      showScreen('screen-auth');
      return;
    }
    
    const data = await res.json();
    console.log('[Interview] API response data:', data);

    if (!res.ok) throw new Error(data.error || 'Failed to load questions');

    interviewQuestions = data.questions || [];
    console.log('[Interview] Questions loaded:', interviewQuestions.length);
    
    if (interviewQuestions.length === 0) throw new Error('No questions available');

    interviewAnswers = new Array(interviewQuestions.length).fill(null);
    displayQuestion(0);
    updateQProgress();
    showToast(`${interviewQuestions.length} questions loaded. Good luck!`, 'info');
  } catch (err) {
    console.error('[Interview] Error:', err);
    showToast(err.message || 'Could not load interview questions', 'error');
    if (qText) qText.textContent = 'Failed to load questions. Click "New Set" to try again.';
    if (qNum) qNum.innerHTML = '<i class="bi bi-exclamation-circle"></i> Error';
  }
}

function displayQuestion(index) {
  if (!interviewQuestions || interviewQuestions.length === 0) {
    console.error('[Interview] No questions loaded');
    return;
  }
  
  if (index >= interviewQuestions.length) {
    showInterviewComplete();
    return;
  }

  currentQuestionIndex = index;
  const q = interviewQuestions[index];
  
  if (!q) {
    console.error('[Interview] Question at index', index, 'is undefined');
    return;
  }

  const qText = document.getElementById('q-text');
  const qNum  = document.getElementById('q-num');
  const answerBox = document.getElementById('answer-box');

  if (qText) qText.textContent = q.question;
  if (qNum)  qNum.innerHTML = `<i class="bi bi-question-circle"></i> Question ${index + 1} of ${interviewQuestions.length}`;
  if (answerBox) {
    answerBox.value = interviewAnswers[index] || '';
    answerBox.focus();
  }

  // Hide feedback card
  const feedbackCard = document.getElementById('feedback-card');
  if (feedbackCard) feedbackCard.classList.add('hidden');

  // Update next button text
  const nextBtn = document.getElementById('next-question-btn');
  if (nextBtn) {
    nextBtn.innerHTML = index < interviewQuestions.length - 1 
      ? 'Next Question <i class="bi bi-arrow-right"></i>' 
      : 'Finish Interview <i class="bi bi-check-circle"></i>';
  }

  updateQProgress();
}

async function submitAnswer() {
  const answerBox = document.getElementById('answer-box');
  const answer = answerBox?.value?.trim();

  console.log('[Interview] Submitting answer, length:', answer?.length);

  if (!answer) {
    showToast('Please write an answer before submitting', 'error');
    return;
  }

  // Check if questions have been loaded
  if (!interviewQuestions || interviewQuestions.length === 0) {
    showToast('Please load interview questions first', 'error');
    loadInterviewQuestions(currentRole);
    return;
  }

  const question = interviewQuestions[currentQuestionIndex];
  console.log('[Interview] Current question:', question);
  
  if (!question) {
    showToast('No question loaded. Click "New Set" to load questions.', 'error');
    return;
  }

  // Save answer
  interviewAnswers[currentQuestionIndex] = answer;

  const btn = document.getElementById('submit-answer-btn');
  setButtonLoading(btn, true, 'Getting Feedback...');

  try {
    console.log('[Interview] Calling /api/submit-answer');
    const res = await fetch('/api/submit-answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        question: question.question,
        answer,
        role: currentRole,
        question_index: currentQuestionIndex
      })
    });
    
    console.log('[Interview] Submit response status:', res.status);
    
    // Handle auth errors
    if (res.status === 401) {
      showToast('Session expired. Please log in again.', 'error');
      showScreen('screen-auth');
      return;
    }
    
    const data = await res.json();
    console.log('[Interview] Submit response data:', data);

    if (!res.ok) throw new Error(data.error || 'Feedback failed');

    displayFeedback(data.feedback);
    updateQProgress();
  } catch (err) {
    console.error('[Interview] Submit error:', err);
    showToast(err.message || 'Could not get feedback. Check your connection.', 'error');
  } finally {
    setButtonLoading(btn, false, '<i class="bi bi-send-fill"></i> Submit Answer');
  }
}

function displayFeedback(feedback) {
  const feedbackCard = document.getElementById('feedback-card');
  if (!feedbackCard) return;

  feedbackCard.classList.remove('hidden');

  const score = feedback.score || 0;
  const rating = feedback.rating || 'Average';

  // Score circle class
  let scoreClass = 'poor';
  if (score >= 8)      scoreClass = 'excellent';
  else if (score >= 6) scoreClass = 'good';
  else if (score >= 4) scoreClass = 'average';

  const scoreCircle = document.getElementById('fb-score-circle');
  const fbRating    = document.getElementById('fb-rating');
  const fbGeneral   = document.getElementById('fb-general');
  const fbStrengths = document.getElementById('fb-strengths');
  const fbImprovements = document.getElementById('fb-improvements');
  const fbKeywords  = document.getElementById('fb-keywords');

  if (scoreCircle) {
    scoreCircle.textContent = score;
    scoreCircle.className = `score-circle ${scoreClass}`;
  }
  if (fbRating) fbRating.textContent = rating;
  if (fbGeneral) fbGeneral.textContent = feedback.feedback || '';

  if (fbStrengths) {
    fbStrengths.innerHTML = (feedback.strengths || []).map(s =>
      `<li><i class="bi bi-check-circle-fill"></i> ${s}</li>`
    ).join('');
  }

  if (fbImprovements) {
    fbImprovements.innerHTML = (feedback.improvements || []).map(i =>
      `<li><i class="bi bi-arrow-up-circle-fill"></i> ${i}</li>`
    ).join('');
  }

  if (fbKeywords && feedback.keywords_mentioned?.length > 0) {
    fbKeywords.innerHTML = feedback.keywords_mentioned.map(kw =>
      `<span class="chip chip-purple">${capitalize(kw)}</span>`
    ).join('');
  }

  // Scroll feedback into view
  feedbackCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function nextQuestion() {
  const next = currentQuestionIndex + 1;
  if (next >= interviewQuestions.length) {
    showInterviewComplete();
  } else {
    displayQuestion(next);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

function showInterviewComplete() {
  const answered = interviewAnswers.filter(a => a !== null).length;
  showToast(`Interview complete! ${answered}/${interviewQuestions.length} questions answered.`, 'success');
  // Could navigate to a results screen or show summary
}

function updateQProgress() {
  const total    = interviewQuestions.length;
  const answered = interviewAnswers.filter(a => a !== null).length;
  const pct      = total > 0 ? (answered / total) * 100 : 0;

  const progressBar = document.getElementById('q-progress-bar');
  const doneLabel   = document.getElementById('q-done-label');

  if (progressBar) progressBar.style.width = pct + '%';
  if (doneLabel)   doneLabel.textContent = `${answered}/${total} answered`;

  // Render dots
  const dotsContainer = document.getElementById('answer-history');
  if (dotsContainer) {
    dotsContainer.innerHTML = '';
    for (let i = 0; i < total; i++) {
      const dot = document.createElement('div');
      dot.className = 'answer-dot';
      dot.textContent = i + 1;
      if (i === currentQuestionIndex) dot.classList.add('current');
      else if (interviewAnswers[i] !== null) dot.classList.add('answered');
      dotsContainer.appendChild(dot);
    }
  }
}

/* ── Speech Recognition (Mic) ─────────────────────────────── */

function toggleMic() {
  const micBtn = document.getElementById('mic-btn');
  const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechAPI) {
    showToast('Speech recognition is not supported in this browser', 'warning');
    return;
  }

  if (isRecording) {
    // Stop recording
    if (speechRecognition) speechRecognition.stop();
    isRecording = false;
    if (micBtn) {
      micBtn.classList.remove('recording');
      micBtn.innerHTML = '<i class="bi bi-mic"></i>';
    }
    return;
  }

  // Start recording
  speechRecognition = new SpeechAPI();
  speechRecognition.continuous = true;
  speechRecognition.interimResults = true;
  speechRecognition.lang = 'en-US';

  speechRecognition.onresult = (event) => {
    const answerBox = document.getElementById('answer-box');
    if (!answerBox) return;

    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        transcript += event.results[i][0].transcript + ' ';
      }
    }
    if (transcript) answerBox.value += transcript;
  };

  speechRecognition.onerror = () => {
    isRecording = false;
    if (micBtn) {
      micBtn.classList.remove('recording');
      micBtn.innerHTML = '<i class="bi bi-mic"></i>';
    }
    showToast('Speech recognition error', 'error');
  };

  speechRecognition.onend = () => {
    isRecording = false;
    if (micBtn) {
      micBtn.classList.remove('recording');
      micBtn.innerHTML = '<i class="bi bi-mic"></i>';
    }
  };

  speechRecognition.start();
  isRecording = true;
  if (micBtn) {
    micBtn.classList.add('recording');
    micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
  }
  showToast('Listening... Speak your answer', 'info');
}

/* ══════════════════════════════════════════════════════════════
   ATS SUGGESTIONS
   ══════════════════════════════════════════════════════════════ */

async function loadATSSuggestions() {
  if (!currentAnalysis) {
    showToast('Please analyze your skills first to get ATS suggestions', 'info');
    return;
  }

  const container = document.getElementById('ats-suggestions-list');
  const scoreEl   = document.getElementById('ats-score-value');
  const keywordsEl= document.getElementById('ats-keywords');

  if (container) container.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';

  try {
    const res = await fetch('/api/ats-suggestions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        role: currentAnalysis.role_key || currentRole,
        skills: currentAnalysis.skills_matched || []
      })
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Failed to get ATS suggestions');

    displayATSSuggestions(data);
  } catch (err) {
    if (container) container.innerHTML = `<div class="empty-state"><i class="bi bi-exclamation-circle"></i><p>${err.message}</p></div>`;
  }
}

function displayATSSuggestions(data) {
  const container  = document.getElementById('ats-suggestions-list');
  const scoreEl    = document.getElementById('ats-score-value');
  const keywordsEl = document.getElementById('ats-keywords');
  const meterBar   = document.getElementById('ats-score-bar');

  if (scoreEl) {
    scoreEl.textContent = (data.ats_score ?? 0) + '%';
    animateNumber('ats-score-value', data.ats_score ?? 0, '%');
  }

  if (meterBar) {
    meterBar.style.width = '0%';
    setTimeout(() => { meterBar.style.width = (data.ats_score ?? 0) + '%'; }, 200);
    // Color based on score
    const score = data.ats_score ?? 0;
    meterBar.className = 'cat-bar-fill ' + (score >= 70 ? 'bar-green' : score >= 40 ? 'bar-amber' : 'bar-red');
  }

  if (keywordsEl && data.missing_keywords?.length > 0) {
    keywordsEl.innerHTML = data.missing_keywords.map(kw =>
      `<span class="keyword-tag"><i class="bi bi-plus-circle"></i> ${capitalize(kw)}</span>`
    ).join('');
  }

  if (container) {
    container.innerHTML = '';
    (data.suggestions || []).forEach(suggestion => {
      const card = document.createElement('div');
      card.className = 'suggestion-card animate-fade';
      card.innerHTML = `
        <div>
          <span class="priority-badge priority-${suggestion.priority}">
            ${suggestion.priority === 'high' ? '🔴' : suggestion.priority === 'medium' ? '🟡' : '🟢'}
            ${capitalize(suggestion.priority)}
          </span>
        </div>
        <div class="suggestion-body">
          <div class="suggestion-title">${suggestion.suggestion}</div>
          <div class="suggestion-detail">${suggestion.detail || ''}</div>
          <span class="badge badge-cyan" style="margin-top:0.4rem">${suggestion.category}</span>
        </div>
      `;
      container.appendChild(card);
    });
  }
}

/* ══════════════════════════════════════════════════════════════
   ADMIN ANALYTICS
   ══════════════════════════════════════════════════════════════ */

async function loadAdminAnalytics() {
  try {
    const res = await fetch('/api/admin/analytics', { credentials: 'include' });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || 'Failed to load analytics');
    
    const analytics = data.analytics || data;

    // Update stats
    animateNumber('admin-total-users',    analytics.total_users    ?? 0);
    animateNumber('admin-total-resumes',  analytics.total_resumes  ?? 0);
    animateNumber('admin-avg-score',      analytics.avg_match_score ?? 0, '%');

    // Skill gaps chart
    const gapsContainer = document.getElementById('skill-gaps-chart');
    if (gapsContainer && analytics.common_skill_gaps) {
      gapsContainer.innerHTML = '';
      const maxCount = Math.max(...analytics.common_skill_gaps.map(g => g[1]), 1);
      analytics.common_skill_gaps.forEach(item => {
        const skill = item[0];
        const count = item[1];
        const percentage = Math.round((count / maxCount) * 100);
        const row = document.createElement('div');
        row.className = 'bar-row';
        row.innerHTML = `
          <span class="bar-row-label">${capitalize(skill)}</span>
          <div class="bar-row-track">
            <div class="bar-row-fill bar-red" style="width:${percentage}%"></div>
          </div>
          <span class="bar-row-val">${count}</span>
        `;
        gapsContainer.appendChild(row);
      });
    }

    // Role readiness table
    const tableBody = document.getElementById('role-readiness-body');
    if (tableBody && analytics.role_stats) {
      tableBody.innerHTML = '';
      analytics.role_stats.forEach(row => {
        const tr = document.createElement('tr');
        const score = row.avg_score || 0;
        const scoreClass = score >= 70 ? 'text-success' : score >= 40 ? 'text-warning' : 'text-danger';
        tr.innerHTML = `
          <td><strong>${ROLE_LABELS[row.target_role] || row.target_role}</strong></td>
          <td>${row.count}</td>
          <td class="${scoreClass}"><strong>${score}%</strong></td>
          <td><span class="badge ${score >= 70 ? 'badge-green' : score >= 40 ? 'badge-amber' : 'badge-red'}">${score >= 70 ? 'Ready' : score >= 40 ? 'Developing' : 'Beginner'}</span></td>
        `;
        tableBody.appendChild(tr);
      });
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

/* ══════════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
   ══════════════════════════════════════════════════════════════ */

function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  if (!container) {
    console.error('Toast container not found!');
    alert(message); // Fallback to alert if container missing
    return;
  }

  const iconMap = {
    success: 'bi-check-circle-fill',
    error:   'bi-x-circle-fill',
    info:    'bi-info-circle-fill',
    warning: 'bi-exclamation-triangle-fill'
  };

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <div class="toast-icon"><i class="bi ${iconMap[type] || iconMap.info}"></i></div>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.closest('.toast').remove()">
      <i class="bi bi-x"></i>
    </button>
  `;

  container.appendChild(toast);
  
  console.log('[Toast]', type, message);

  // Auto dismiss after specified duration
  const timer = setTimeout(() => {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
  }, duration);

  // Cancel timer on close click
  toast.querySelector('.toast-close').addEventListener('click', () => {
    clearTimeout(timer);
  });
}

/* ══════════════════════════════════════════════════════════════
   ANIMATE NUMBER (Count-Up)
   ══════════════════════════════════════════════════════════════ */

function animateNumber(elementId, targetValue, suffix = '') {
  const el = document.getElementById(elementId);
  if (!el) return;

  const duration = 800;
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (targetValue - start) * eased);
    el.textContent = current + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

/* ══════════════════════════════════════════════════════════════
   HELPER FUNCTIONS
   ══════════════════════════════════════════════════════════════ */

function setButtonLoading(btn, loading, text) {
  if (!btn) return;
  btn.disabled = loading;
  if (loading) {
    btn.dataset.originalText = btn.textContent;
    btn.innerHTML = `<div class="spinner-sm spinner"></div> ${text}`;
  } else {
    btn.innerHTML = text || btn.dataset.originalText || 'Submit';
  }
}

function setTextContent(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/* ══════════════════════════════════════════════════════════════
   INTERVIEW ROLE CHANGE
   ══════════════════════════════════════════════════════════════ */

function changeInterviewRole() {
  const roleSelect = document.getElementById('interview-role-select');
  if (roleSelect && roleSelect.value) {
    loadInterviewQuestions(roleSelect.value);
  }
}

/* ══════════════════════════════════════════════════════════════
   NAVIGATION HANDLERS
   ══════════════════════════════════════════════════════════════ */

function navToScreen(screenId) {
  // Check admin access for admin screen
  if (screenId === 'screen-admin') {
    if (!currentUser || currentUser.role !== 'admin') {
      showToast('Access denied. Admin privileges required.', 'error');
      return;
    }
  }
  
  // Lazy-load data when navigating to certain screens
  switch (screenId) {
    case 'screen-dashboard':
      loadDashboard();
      break;
    case 'screen-learning':
      loadLearningPath();
      break;
    case 'screen-interview':
      // Always reload questions to ensure fresh state
      loadInterviewQuestions(currentRole);
      break;
    case 'screen-ats':
      loadATSSuggestions();
      break;
    case 'screen-pricing':
      checkSubscription();
      break;
    case 'screen-admin':
      loadAdminAnalytics();
      break;
    case 'screen-profile':
      loadProfile();
      break;
  }
  showScreen(screenId);
}

/* ══════════════════════════════════════════════════════════════
   PROFILE
   ══════════════════════════════════════════════════════════════ */

function loadProfile() {
  if (!currentUser) return;

  const name  = currentUser.name  || currentUser.email?.split('@')[0] || 'User';
  const email = currentUser.email || '—';
  const role  = currentUser.role  || 'student';

  // Avatar initial
  const avatarEl = document.getElementById('profile-avatar-lg');
  if (avatarEl) avatarEl.textContent = name.charAt(0).toUpperCase();

  // Info fields
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('profile-name',  name);
  set('profile-email', email);
  set('profile-role',  role === 'admin' ? 'Admin' : 'Student');

  // Member since — derive from currentUser or fallback to today
  const since = currentUser.created_at
    ? new Date(currentUser.created_at).toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })
    : new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' });
  set('profile-since', since);

  // Pull live stats
  fetch('/api/user-stats', { credentials: 'include' })
    .then(res => res.ok ? res.json() : Promise.reject())
    .then(data => {
      set('profile-stat-resumes', data.resumes    ?? 0);
      set('profile-stat-skills',  data.skills     ?? 0);
      set('profile-stat-tests',   data.interviews ?? 0);
    })
    .catch(() => { /* leave at 0 */ });
}

/* ══════════════════════════════════════════════════════════════
   ANIMATED COUNTERS FOR AUTH PAGE
   ══════════════════════════════════════════════════════════════ */

function animateAuthCounters() {
  const counters = document.querySelectorAll('.counter');
  counters.forEach(counter => {
    const target = parseInt(counter.dataset.target) || 0;
    const duration = 2000;
    const start = 0;
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (target - start) * eased);
      counter.textContent = current.toLocaleString() + '+';
      if (progress < 1) requestAnimationFrame(updateCounter);
    }

    requestAnimationFrame(updateCounter);
  });
}

/* ══════════════════════════════════════════════════════════════
   CONFETTI ANIMATION FOR TEST COMPLETION
   ══════════════════════════════════════════════════════════════ */

function launchConfetti() {
  const colors = ['#7c3aed', '#06b6d4', '#f59e0b', '#10b981', '#ef4444'];
  for (let i = 0; i < 80; i++) {
    const el = document.createElement('div');
    el.className = 'confetti-piece';
    el.style.cssText = `
      position: fixed;
      left: ${Math.random() * 100}vw;
      top: -10px;
      width: 10px;
      height: 10px;
      background: ${colors[i % colors.length]};
      border-radius: 2px;
      animation: confetti-fall ${2 + Math.random() * 2}s linear forwards;
      animation-delay: ${Math.random() * 0.5}s;
      pointer-events: none;
      z-index: 9998;
    `;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 5000);
  }
}

/* ══════════════════════════════════════════════════════════════
   DOM CONTENT LOADED — INIT
   ══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  // Check authentication state
  checkAuth();

  // ── Animate counter elements on auth page ──────────────────
  animateAuthCounters();

  // ── Sidebar nav item click handlers ────────────────────────
  document.querySelectorAll('.nav-item[data-screen]').forEach(item => {
    item.addEventListener('click', () => {
      navToScreen(item.dataset.screen);
    });
  });

  // ── Upload zone event listeners ─────────────────────────────
  const uploadZone = document.getElementById('upload-zone');
  if (uploadZone) {
    uploadZone.addEventListener('dragover',   handleDragOver);
    uploadZone.addEventListener('dragleave',  handleDragLeave);
    uploadZone.addEventListener('drop',       handleDrop);
  }

  const fileInput = document.getElementById('file-input');
  if (fileInput) {
    fileInput.addEventListener('change', handleFileSelect);
  }

  // ── Auth form — Enter key support ───────────────────────────
  document.querySelectorAll('input[type="password"]').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        // Determine active auth tab by the panel the input lives in
        const panel = input.closest('.auth-tab-panel');
        if (panel?.id === 'auth-tab-login')  handleLogin();
        else if (panel?.id === 'auth-tab-signup') handleRegister();
        else if (panel?.id === 'auth-tab-admin')  handleAdminLogin();
      }
    });
  });

  // ── Sidebar overlay click to close ─────────────────────────
  const overlay = document.getElementById('sidebar-overlay');
  if (overlay) {
    overlay.addEventListener('click', closeSidebar);
  }

  // ── Interview role select change ────────────────────────────
  const interviewRoleSelect = document.getElementById('interview-role-select');
  if (interviewRoleSelect) {
    interviewRoleSelect.addEventListener('change', changeInterviewRole);
  }

  // ── Keyboard shortcuts ──────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    // Escape closes mobile sidebar
    if (e.key === 'Escape') closeSidebar();
  });

  // Payment method option handlers
  document.querySelectorAll('.payment-option').forEach(option => {
    option.addEventListener('click', () => {
      document.querySelectorAll('.payment-option').forEach(o => o.classList.remove('selected'));
      option.classList.add('selected');
      option.querySelector('input').checked = true;
      
      const method = option.querySelector('input').value;
      document.getElementById('card-details').classList.toggle('hidden', method !== 'card');
      document.getElementById('upi-details').classList.toggle('hidden', method !== 'upi');
      document.getElementById('netbanking-details').classList.toggle('hidden', method !== 'netbanking');
    });
  });
});

/* ══════════════════════════════════════════════════════════════
   PAYMENT HANDLING
   ══════════════════════════════════════════════════════════════ */

let currentPaymentPlan = null;
let currentPaymentAmount = 0;
let stripe = null;
let cardElement = null;
let currentClientSecret = null;

function openPaymentModal(planId, amount) {
  currentPaymentPlan = planId;
  currentPaymentAmount = amount;
  
  const planNames = {
    'basic': 'Basic Plan',
    'pro': 'Professional Plan',
    'premium': 'Premium Plan'
  };
  
  document.getElementById('payment-plan-name').textContent = planNames[planId] || 'Selected Plan';
  document.getElementById('payment-amount').textContent = '₹' + amount;
  document.getElementById('payment-modal').classList.remove('hidden');
  
  // Initialize Stripe Card Element
  initializeStripeCardElement();
}

function initializeStripeCardElement() {
  if (!stripe && typeof Stripe !== 'undefined') {
    try {
      // Initialize Stripe with test publishable key
      stripe = Stripe('pk_test_51QzLxXP8bBGx9e1EYourTestKeyHere'); // Replace with your test publishable key
      
      const elements = stripe.elements();
      cardElement = elements.create('card', {
        style: {
          base: {
            fontSize: '16px',
            color: '#e2e8f0',
            backgroundColor: 'transparent',
            '::placeholder': {
              color: '#64748b'
            }
          },
          invalid: {
            color: '#ef4444'
          }
        }
      });
      
      cardElement.mount('#stripe-card-element');
      
      cardElement.on('change', (event) => {
        const displayError = document.getElementById('card-errors');
        if (event.error) {
          displayError.textContent = event.error.message;
        } else {
          displayError.textContent = '';
        }
      });
    } catch (err) {
      console.log('Stripe initialization error:', err);
    }
  }
}

function closePaymentModal() {
  document.getElementById('payment-modal').classList.add('hidden');
  currentPaymentPlan = null;
  currentPaymentAmount = 0;
  currentClientSecret = null;
}

async function processPayment() {
  const btn = document.getElementById('pay-now-btn');
  setButtonLoading(btn, true, 'Processing...');
  
  const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value || 'card';
  
  try {
    // For non-card payments, use old flow
    if (paymentMethod !== 'card') {
      await processNonCardPayment(paymentMethod);
      return;
    }
    
    // Step 1: Create payment intent
    const orderRes = await fetch('/api/payment/create-order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        plan_id: currentPaymentPlan,
        amount: currentPaymentAmount
      })
    });
    const orderData = await orderRes.json();
    
    if (!orderRes.ok) throw new Error(orderData.error || 'Failed to create payment intent');
    
    currentClientSecret = orderData.client_secret;
    
    // Check if demo mode
    if (orderData.demo_mode || !stripe) {
      // Demo mode - skip Stripe and directly verify
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const verifyRes = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          payment_id: orderData.payment_intent_id,
          plan_id: currentPaymentPlan,
          payment_method: 'card'
        })
      });
      const verifyData = await verifyRes.json();
      
      if (!verifyRes.ok) throw new Error(verifyData.error || 'Payment verification failed');
      
      showToast('Payment successful! Your subscription is now active.', 'success');
      closePaymentModal();
      updatePlanBadge();
      return;
    }
    
    // Step 2: Confirm payment with Stripe
    const { error, paymentIntent } = await stripe.confirmCardPayment(currentClientSecret, {
      payment_method: {
        card: cardElement
      }
    });
    
    if (error) {
      throw new Error(error.message);
    }
    
    if (paymentIntent.status === 'succeeded') {
      // Step 3: Verify payment on backend
      const verifyRes = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          payment_id: paymentIntent.id,
          plan_id: currentPaymentPlan,
          payment_method: 'card'
        })
      });
      const verifyData = await verifyRes.json();
      
      if (!verifyRes.ok) throw new Error(verifyData.error || 'Payment verification failed');
      
      showToast('Payment successful! Your subscription is now active.', 'success');
      closePaymentModal();
      updatePlanBadge();
    } else {
      throw new Error('Payment not completed');
    }
    
  } catch (err) {
    showToast(err.message || 'Payment failed. Please try again.', 'error');
  } finally {
    setButtonLoading(btn, false, '<i class="bi bi-lock-fill"></i> Pay Now');
  }
}

async function processNonCardPayment(paymentMethod) {
  // Old flow for UPI/NetBanking
  const orderRes = await fetch('/api/payment/create-order', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      plan_id: currentPaymentPlan,
      amount: currentPaymentAmount
    })
  });
  const orderData = await orderRes.json();
  
  if (!orderRes.ok) throw new Error(orderData.error || 'Failed to create order');
  
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  const verifyRes = await fetch('/api/payment/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      payment_id: orderData.payment_intent_id || orderData.order_id,
      plan_id: currentPaymentPlan,
      payment_method: paymentMethod
    })
  });
  const verifyData = await verifyRes.json();
  
  if (!verifyRes.ok) throw new Error(verifyData.error || 'Payment verification failed');
  
  showToast('Payment successful! Your subscription is now active.', 'success');
  closePaymentModal();
  updatePlanBadge();
}

function updatePlanBadge() {
  const planBadge = document.getElementById('current-plan-badge');
  if (planBadge) {
    const planNames = { 'basic': 'Basic', 'pro': 'Professional', 'premium': 'Premium' };
    planBadge.textContent = planNames[currentPaymentPlan] + ' Plan';
    planBadge.className = 'badge badge-green';
  }
}

// Check subscription status on pricing page load
async function checkSubscription() {
  try {
    const res = await fetch('/api/subscription/status', { credentials: 'include' });
    const data = await res.json();
    
    if (data.has_subscription) {
      const planBadge = document.getElementById('current-plan-badge');
      if (planBadge) {
        const planNames = { 'basic': 'Basic', 'pro': 'Professional', 'premium': 'Premium' };
        planBadge.textContent = (planNames[data.plan] || data.plan) + ' Plan';
        planBadge.className = 'badge badge-green';
      }
    }
  } catch (err) {
    console.error('Failed to check subscription:', err);
  }
}

// Copy UPI ID to clipboard
function copyUpiId() {
  const upiId = 'arynmishra2007@okhdfcbank';
  navigator.clipboard.writeText(upiId).then(() => {
    showToast('UPI ID copied to clipboard!', 'success');
  }).catch(() => {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = upiId;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast('UPI ID copied to clipboard!', 'success');
  });
}

// Show fallback QR display if image fails to load
function showQrFallback() {
  const container = document.getElementById('qr-container');
  if (container) {
    container.innerHTML = `
      <div style="text-align: center; padding: 20px; background: var(--surface2); border-radius: var(--radius);">
        <i class="bi bi-qr-code-scan" style="font-size: 120px; color: var(--accent); display: block; margin-bottom: 10px;"></i>
        <p style="color: var(--muted); margin: 0; font-size: 0.9rem;">
          QR Code not found.<br>
          <small>Place payment-qr.png in project root</small>
        </p>
      </div>
    `;
  }
}
