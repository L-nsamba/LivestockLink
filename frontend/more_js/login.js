const BASE_URL = 'http://127.0.0.1:5000';

// This function ensures the provision of interactive feedback messages to user like error, success
export function showToast(message, type= '') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`
    setTimeout(() => {toast.className = 'toast'; }, 3500);
}

// This function ensures the password is not visible when user is entering 
export function togglePassword(inputId, icon) {
const input = document.getElementById(inputId);
if (input.type === 'password') {
    input.type = 'text';
    icon.textContent = 'Hide';
} else {
    input.type = 'password';
    icon.textContent = 'Show'
}
}

// This function deals with verification of accuracy of the user input for the respective fields 
async function handleLogin() {
    const btn = document.getElementById('login-btn');
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    // Incase one of the fields is not filled in it would display and error message
    if (!email || !password) {
        showToast('Please fill in all fields', 'error'); return
    }
    if (!role) {
        showToast('Please select a user type', 'error'); return
    }

    btn.disabled = true;
    btn.textContent = 'Logging in...'

    try {
        const response = await fetch(`${BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body : JSON.stringify({email, password, role}),
        })

        const result = await response.json();

        if (response.ok) {
            // Storage of the token and user info for later usage across the app
            localStorage.setItem('token', result.token || '');
            localStorage.setItem('user', JSON.stringify(result.user  || {}));

            showToast('Welcome back!', 'success');

            // Redirecting to the respective role dashboard
            setTimeout(() => {
                userRole = (result.user?.role || role).toUpperCase();
                if (userRole === 'FARMER') window.location.href = 'farmer-dashboard.html';
                else if (userRole === 'TRANSPORTER') window.location.href = 'transporter-dashboard.html';
                else if (userRole === 'ADMIN') window.location.href = 'admin-dashboard.html';

            }, 1200);
        } else {
            showToast(result.error || 'Invalid credentials. Try again', 'error');
            btn.disabled = false;
            btn.textContent = 'Log In';
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
        btn.disabled = false;
        btn.textContent = 'Log In';
    }
}

window.handleLogin = handleLogin;
window.togglePassword = togglePassword;

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleLogin();
});