"""
Enhanced JavaScript for ResumeAI Platform with Payments and Admin
"""

// ═══════════════════════════════════════════════════════
// Global State
// ═══════════════════════════════════════════════════════

let currentUser = null;
let currentPlan = null;
let analysisData = null;

// ═══════════════════════════════════════════════════════
// Page Navigation
// ═══════════════════════════════════════════════════════

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById('screen-' + screenId).classList.add('active');
    
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');
    
    // Close sidebar on mobile
    closeSidebar();
    
    // Load data for specific screens
    if (screenId === 'pricing') {
        loadSubscriptionStatus();
    } else if (screenId === 'admin') {
        loadAdminAnalytics();
    }
}

// ═══════════════════════════════════════════════════════
// Authentication
// ═══════════════════════════════════════════════════════

async function handleRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-pass').value;
    const confirm = document.getElementById('reg-confirm').value;
    
    // Validation
    if (!name || !email || !password || !confirm) {
        showError('reg-err', 'All fields are required');
        return;
    }
    
    if (password !== confirm) {
        showError('reg-err', 'Passwords do not match');
        return;
    }
    
    if (password.length < 6) {
        showError('reg-err', 'Password must be at least 6 characters');
        return;
    }
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            showPage('app-page');
            loadUserData();
            showNotification('Welcome to ResumeAI! 🎉', 'success');
        } else {
            showError('reg-err', data.error);
        }
    } catch (error) {
        showError('reg-err', 'Registration failed. Please try again.');
    }
}

async function handleLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-pass').value;
    
    if (!email || !password) {
        document.getElementById('login-err').style.display = 'flex';
        return;
    }
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            showPage('app-page');
            loadUserData();
            
            // Show/hide admin menu
            if (currentUser.role === 'admin') {
                document.getElementById('nav-admin').style.display = 'flex';
            }
            
            showNotification('Welcome back! 👋', 'success');
        } else {
            document.getElementById('login-err').style.display = 'flex';
        }
    } catch (error) {
        document.getElementById('login-err').style.display = 'flex';
    }
}

function showAdminLogin() {
    showPage('login-page');
    document.getElementById('login-email').value = 'admin@resumeai.com';
    document.getElementById('login-pass').focus();
    showNotification('Admin login mode activated 🔐', 'info');
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUser = null;
        showPage('landing-page');
        showNotification('Logged out successfully', 'info');
    } catch (error) {
        console.error('Logout failed:', error);
    }
}

// ═══════════════════════════════════════════════════════
// User Dashboard
// ═══════════════════════════════════════════════════════

async function loadUserData() {
    if (!currentUser) return;
    
    // Set user name
    document.getElementById('user-display-name').textContent = currentUser.name;
    
    // Load stats
    try {
        const response = await fetch('/api/user-stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('stat-resumes').textContent = data.stats.resumes;
            document.getElementById('stat-match').textContent = 
                data.stats.match_score ? data.stats.match_score + '%' : '—';
            document.getElementById('stat-skills').textContent = data.stats.skills;
            document.getElementById('stat-interviews').textContent = data.stats.interviews;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// ═══════════════════════════════════════════════════════
// Payment & Subscription
// ═══════════════════════════════════════════════════════

async function loadSubscriptionStatus() {
    try {
        const response = await fetch('/api/subscription/status');
        const data = await response.json();
        
        const statusDiv = document.getElementById('subscription-status');
        
        if (data.has_subscription) {
            const endDate = new Date(data.end_date);
            statusDiv.innerHTML = `
                <div style="background: linear-gradient(135deg, rgba(0, 230, 118, 0.1) 0%, rgba(0, 217, 255, 0.1) 100%); 
                            border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 15px; padding: 1.5rem; margin-bottom: 2rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <i class="bi bi-check-circle" style="font-size: 2rem; color: var(--success);"></i>
                        <div>
                            <div style="font-weight: 600; font-size: 1.1rem; margin-bottom: 0.3rem;">
                                Active Subscription: ${data.plan.toUpperCase()}
                            </div>
                            <div style="color: var(--muted); font-size: 0.9rem;">
                                Valid until ${endDate.toLocaleDateString('en-IN')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            statusDiv.innerHTML = '';
        }
    } catch (error) {
        console.error('Failed to load subscription:', error);
    }
}

function selectPlan(planId, amount) {
    currentPlan = { id: planId, amount: amount };
    
    // Update modal content
    const planNames = { basic: 'Basic', pro: 'Professional', premium: 'Premium' };
    document.getElementById('payment-plan-name').textContent = planNames[planId];
    document.getElementById('payment-amount').textContent = '₹' + amount;
    
    // Show payment modal
    const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
    modal.show();
}

async function processPayment() {
    if (!currentPlan) return;
    
    try {
        // Create order
        const orderResponse = await fetch('/api/payment/create-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plan_id: currentPlan.id,
                amount: currentPlan.amount
            })
        });
        
        const orderData = await orderResponse.json();
        
        if (orderData.success) {
            // Simulate payment processing
            showNotification('Processing payment...', 'info');
            
            setTimeout(async () => {
                // Verify payment
                const verifyResponse = await fetch('/api/payment/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        payment_id: orderData.order_id,
                        plan_id: currentPlan.id,
                        payment_method: document.getElementById('payment-method-select').value
                    })
                });
                
                const verifyData = await verifyResponse.json();
                
                if (verifyData.success) {
                    // Close modal
                    bootstrap.Modal.getInstance(document.getElementById('paymentModal')).hide();
                    
                    // Show success
                    showNotification('Payment successful! Your subscription is now active. 🎉', 'success');
                    
                    // Reload subscription status
                    loadSubscriptionStatus();
                    loadUserData();
                }
            }, 2000);
        }
    } catch (error) {
        showNotification('Payment failed. Please try again.', 'error');
    }
}

// ═══════════════════════════════════════════════════════
// Admin Dashboard
// ═══════════════════════════════════════════════════════

async function loadAdminAnalytics() {
    try {
        const response = await fetch('/api/admin/analytics');
        const data = await response.json();
        
        if (data.success) {
            const analytics = data.analytics;
            
            // Update stats
            document.getElementById('admin-total-users').textContent = analytics.total_users;
            document.getElementById('admin-total-resumes').textContent = analytics.total_resumes;
            document.getElementById('admin-total-revenue').textContent = '₹' + analytics.total_revenue.toFixed(2);
            document.getElementById('admin-active-subs').textContent = analytics.active_subscriptions;
            
            // Recent users
            const usersHTML = analytics.recent_users.map(user => `
                <div style="padding: 0.8rem; background: rgba(255,255,255,0.03); border-radius: 10px; margin-bottom: 0.5rem;">
                    <div style="font-weight: 600;">${user.name}</div>
                    <div style="font-size: 0.85rem; color: var(--muted);">${user.email}</div>
                </div>
            `).join('');
            document.getElementById('admin-recent-users').innerHTML = usersHTML;
            
            // Revenue by plan
            const revenueHTML = analytics.revenue_by_plan.map(plan => `
                <div style="padding: 0.8rem; background: rgba(255,255,255,0.03); border-radius: 10px; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="text-transform: capitalize;">${plan.plan_type}</span>
                        <strong>₹${plan.revenue}</strong>
                    </div>
                    <div style="font-size: 0.85rem; color: var(--muted);">${plan.count} subscriptions</div>
                </div>
            `).join('');
            document.getElementById('admin-revenue-chart').innerHTML = revenueHTML;
            
            // Common skill gaps
            const skillsHTML = analytics.common_skill_gaps.map(([skill, count]) => `
                <div style="padding: 0.8rem; background: rgba(255,68,68,0.1); border: 1px solid rgba(255,68,68,0.3);
                            border-radius: 10px; text-align: center;">
                    <div style="font-weight: 600;">${skill}</div>
                    <div style="font-size: 0.85rem; color: var(--danger);">${count} students</div>
                </div>
            `).join('');
            document.getElementById('admin-skill-gaps').innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    ${skillsHTML}
                </div>
            `;
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

// ═══════════════════════════════════════════════════════
// Utility Functions
// ═══════════════════════════════════════════════════════

function showError(elementId, message) {
    const errorEl = document.getElementById(elementId);
    document.getElementById(elementId + '-text').textContent = message;
    errorEl.classList.add('show');
    setTimeout(() => errorEl.classList.remove('show'), 5000);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? 'rgba(0, 230, 118, 0.2)' : 
                     type === 'error' ? 'rgba(255, 68, 68, 0.2)' : 
                     'rgba(88, 101, 242, 0.2)'};
        border: 1px solid ${type === 'success' ? 'var(--success)' : 
                           type === 'error' ? 'var(--danger)' : 
                           'var(--accent)'};
        border-radius: 10px;
        color: white;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        backdrop-filter: blur(10px);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebar-overlay').classList.toggle('active');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('active');
}

// ═══════════════════════════════════════════════════════
// Initialize
// ═══════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
    // Check if user is logged in
    try {
        const response = await fetch('/api/user');
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            showPage('app-page');
            loadUserData();
            
            if (currentUser.role === 'admin') {
                document.getElementById('nav-admin').style.display = 'flex';
            }
        }
    } catch (error) {
        // Not logged in, show landing page
        showPage('landing-page');
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(100px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes slideOut {
        from { opacity: 1; transform: translateX(0); }
        to { opacity: 0; transform: translateX(100px); }
    }
`;
document.head.appendChild(style);
