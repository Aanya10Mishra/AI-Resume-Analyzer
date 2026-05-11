// ==================== PASSWORD RESET FUNCTIONALITY ====================

/**
 * Show Forgot Password Modal
 */
function showForgotPasswordModal() {
    const modal = document.createElement('div');
    modal.id = 'forgot-password-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div class="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 text-white rounded-t-lg">
                <h2 class="text-2xl font-bold">Reset Password</h2>
            </div>
            
            <div class="p-6">
                <div id="forgot-step-1" class="forgot-step">
                    <p class="text-gray-600 mb-4">Enter your email address and we'll send you a reset link</p>
                    <input type="email" id="forgot-email" placeholder="Enter your email" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <div id="forgot-error-1" class="text-red-500 text-sm mb-4 hidden"></div>
                    <button onclick="sendResetEmail()" class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition">Send Reset Link</button>
                </div>
                
                <div id="forgot-step-2" class="forgot-step hidden">
                    <p class="text-gray-600 mb-4">We've sent a reset code to your email. Enter it below along with your new password</p>
                    <input type="text" id="forgot-token" placeholder="Enter reset token" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <input type="password" id="forgot-new-password" placeholder="New password" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <small class="text-gray-500 text-xs mb-3 block">
                        • At least 8 characters<br>
                        • One uppercase letter<br>
                        • One number
                    </small>
                    <div id="forgot-error-2" class="text-red-500 text-sm mb-4 hidden"></div>
                    <button onclick="resetPasswordWithToken()" class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition">Reset Password</button>
                </div>
                
                <button onclick="closeForgotPasswordModal()" class="w-full mt-4 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeForgotPasswordModal();
        }
    });
}

/**
 * Send reset email
 */
async function sendResetEmail() {
    const email = document.getElementById('forgot-email').value.trim();
    const errorEl = document.getElementById('forgot-error-1');
    errorEl.classList.add('hidden');
    
    if (!email) {
        errorEl.textContent = 'Please enter your email address';
        errorEl.classList.remove('hidden');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('Reset token:', data.reset_token);
            
            // Move to step 2
            document.getElementById('forgot-step-1').classList.add('hidden');
            document.getElementById('forgot-step-2').classList.remove('hidden');
            document.getElementById('forgot-token').value = data.reset_token;
            
            console.log('✅ Reset email sent!');
        } else {
            errorEl.textContent = data.error || 'Error sending reset email';
            errorEl.classList.remove('hidden');
        }
    } catch (e) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('hidden');
        console.error('Error:', e);
    }
}

/**
 * Reset password with token
 */
async function resetPasswordWithToken() {
    const token = document.getElementById('forgot-token').value.trim();
    const newPassword = document.getElementById('forgot-new-password').value;
    const errorEl = document.getElementById('forgot-error-2');
    errorEl.classList.add('hidden');
    
    if (!token || !newPassword) {
        errorEl.textContent = 'Please fill in all fields';
        errorEl.classList.remove('hidden');
        return;
    }
    
    if (newPassword.length < 8) {
        errorEl.textContent = 'Password must be at least 8 characters';
        errorEl.classList.remove('hidden');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                reset_token: token,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Password reset successful! Please login with your new password.');
            closeForgotPasswordModal();
            showSection('landing');
        } else {
            errorEl.textContent = data.error || 'Error resetting password';
            errorEl.classList.remove('hidden');
        }
    } catch (e) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('hidden');
        console.error('Error:', e);
    }
}

/**
 * Close forgot password modal
 */
function closeForgotPasswordModal() {
    const modal = document.getElementById('forgot-password-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Show Change Password Modal (for logged-in users)
 */
function showChangePasswordModal() {
    if (!currentUser) {
        alert('Please login first');
        return;
    }
    
    const modal = document.createElement('div');
    modal.id = 'change-password-modal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div class="bg-gradient-to-r from-green-600 to-blue-600 px-6 py-4 text-white rounded-t-lg">
                <h2 class="text-2xl font-bold">Change Password</h2>
            </div>
            
            <div class="p-6">
                <input type="password" id="current-password" placeholder="Current password" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-green-500">
                <input type="password" id="new-password" placeholder="New password" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-green-500">
                <input type="password" id="confirm-password" placeholder="Confirm new password" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-2 focus:outline-none focus:ring-2 focus:ring-green-500">
                <small class="text-gray-500 text-xs mb-3 block">
                    • At least 8 characters<br>
                    • One uppercase letter<br>
                    • One number
                </small>
                <div id="change-password-error" class="text-red-500 text-sm mb-4 hidden"></div>
                <button onclick="performChangePassword()" class="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition">Change Password</button>
                <button onclick="closeChangePasswordModal()" class="w-full mt-3 bg-gray-300 text-gray-700 py-2 rounded-lg hover:bg-gray-400 transition">Cancel</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeChangePasswordModal();
        }
    });
}

/**
 * Perform password change
 */
async function performChangePassword() {
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const errorEl = document.getElementById('change-password-error');
    errorEl.classList.add('hidden');
    
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        errorEl.textContent = 'Please fill in all fields';
        errorEl.classList.remove('hidden');
        return;
    }
    
    if (newPassword.length < 8) {
        errorEl.textContent = 'New password must be at least 8 characters';
        errorEl.classList.remove('hidden');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        errorEl.textContent = 'Passwords do not match';
        errorEl.classList.remove('hidden');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/auth/change-password/${currentUser.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ Password changed successfully!');
            closeChangePasswordModal();
        } else {
            errorEl.textContent = data.error || 'Error changing password';
            errorEl.classList.remove('hidden');
        }
    } catch (e) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('hidden');
        console.error('Error:', e);
    }
}

/**
 * Close change password modal
 */
function closeChangePasswordModal() {
    const modal = document.getElementById('change-password-modal');
    if (modal) {
        modal.remove();
    }
}
