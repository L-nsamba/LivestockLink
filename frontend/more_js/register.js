import { showToast, togglePassword } from "./login.js";

const BASE_URL = 'http://127.0.0.1:5000'

// Validation to ensure user enters required valid information in all fields of the form
function validateForm(data) {
    if (!data.full_name.trim()) return 'Full name is required.';
    if (!data.email.includes('@')) return 'Please enter a valid email.';
    if (!data.contact.trim()) return 'Phone number is required';
    if (data.password.length < 8) return 'Password must be at least 8 characters';
    if (!data.role) return 'Please select a user type';
    if (data.role === 'FARMER') {
        if (!data.farm_location) return 'Farm location is required';
    }
    if (data.role === 'TRANSPORTER') {
        if (!data.vehicle_type) return 'Vehicle type is required';
        if (!data.vehicle_capacity) return 'Vehicle capacity is required';
        if (!data.license_number) return 'License number is required';
    }
    if (data.role === 'ADMIN') {
        if (!data.admin_key) return 'Invalid Admin Key';
    }
    return null;
}

// Function extracts the relevant valid user data entered in the fields
async function handleRegister() {
    const btn = document.getElementById('signup-btn');

    const phoneCode = document.getElementById('phone_code').value;
    const phoneNum = document.getElementById('phone').value.replace(/\s/g, '');

    const data = {
        full_name : document.getElementById('full_name').value.trim(),
        email : document.getElementById('email').value.trim(),
        contact : phoneCode + phoneNum,
        password : document.getElementById('password').value,
        role : document.getElementById('role').value,
        // This field will only show when a user selects admin and only accepts the single secret key
        admin_key: document.getElementById('admin_key')?.value || null,
        // These additional fields will only pop up when the Transporter option is selected
        farm_location : document.getElementById('farm_location')?.value || null,
        vehicle_type : document.getElementById('vehicle_type')?.value || null,
        vehicle_capacity : document.getElementById('vehicle_capacity')?.value || null,
        license_number : document.getElementById('license_number')?.value || null,
        organization_name : document.getElementById('organization_name')?.value || null,
    };

    const error = validateForm(data)
    if (error) {
        showToast(error, 'error');
        return;
    }

    
    btn.disabled = true;
    btn.textContent = 'Creating account....';

    // User creation and referencing the url path to the api logic for registration
    try {
        // Url route to the path which allows admin creation (/api/admin/register)
        const url = data.role === 'ADMIN'
            ? `${BASE_URL}/api/admin/register`
            : `${BASE_URL}/api/auth/register`;

        const response = await fetch(url, {
            method : 'POST',
            headers : {'Content-Type' : 'application/json'},
            body : JSON.stringify(data),
        });

        const result = await  response.json();

            if (response.ok) {
                showToast('Account created! Redirecting....', 'success');
                setTimeout(() => {window.location.href = './more_html/login.html';}, 1800);
            } else {
                showToast(result.error || 'Registration failed. Try again', 'error');
                btn.disabled = false;
                btn.textContent = 'Sign Up'
            } 
    } catch (err) {
            showToast('Cannot reach server. Ensure Flask is running');
            btn.disabled = false;
            btn.textContent = 'Sign Up';
        }
    }

window.handleRegister = handleRegister;
window.togglePassword = togglePassword;


// Only when transporter role is selected will the additional transporter specific fields appear
// Only when farmer role is selected will the farm location field appear
// Only when admin role is selected will the admin key appear
document.getElementById('role').addEventListener('change', function () {
    document.getElementById('transporter-fields').style.display =
        this.value === 'TRANSPORTER' ? 'block' : 'none';
    document.getElementById('farmer-fields').style.display =
        this.value === 'FARMER' ? 'block' : 'none';
    document.getElementById('admin-fields').style.display =
        this.value === 'ADMIN' ? 'block' : 'none';
});

// Allowing Enter Key to submit form
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleRegister();
});