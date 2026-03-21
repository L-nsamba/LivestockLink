const BASE_URL = 'http://127.0.0.1:5000'

// Extracting tokens from local storage after login
function getToken() {return localStorage.getItem('token')};

function authHeaders () {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}

// Simulation of accepting and declining requests locally
let dismissedRequestIds = new Set();
let currentModalRequest = null;
let notifications = []; // Local notification storage

const requestCache = {}; // Stores full request objects, populated when loading the request endpoint calls

// Navigation bar, navigation/switching between elements in sidebar
function switchSection (name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('section-' + name).classList.add('active');
    const navEl = document.getElementById('nav-' + name);
    if (navEl) navEl.classList.add('active');
    closeSidebar();

    if (name === 'dashboard') loadDashboard();
    if (name === 'find') loadFindFarmer();
    if (name === 'history') loadHistory();
    if (name === 'notifications') loadNotifications();
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('hamburger').classList.toggle('open');
    document.getElementById('sidebar-overlay').classList.toggle('open');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('hamburger').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('open');
}

// Card builder indicating farmer info (find farmer section) on transporter dashboard
function buildCard(r) {
    const dateStr = r.pickup_date
        ? new Date(r.pickup_date).toLocaleString('en-GB', {day: '2-digit', month:'short', year: 'numeric' })
        : '-';
    return `
        <div class="request-card" id="card-${r.request_id}">
            <div class="card-field">
                <span class="card-field-label">Farmer ID</span>
                <span class="card-field-label">${r.farmer_id}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">Animal Type</span>
                <span class="card-field-label">${r.animal_type}</span>
            </div>
        
            <div class="card-field">
                <span class="card-field-label">Animal Quantity</span>
                <span class="card-field-label">${r.animal_quantity}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">From</span>
                <span class="card-field-label">${r.pickup_location}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">To</span>
                <span class="card-field-label">${r.destination_location}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">Date</span>
                <span class="card-field-label">${dateStr}</span>
            </div>

            <div class="card-actions">
                <button class="btn-accept" onclick="acceptRequest('${r.request_id}')">Accept</button>
                // <button class="btn-decline" onclick="declineRequest('${r.request_id}')">Decline</button>
                <button class="btn-more-info" onclick="openModal('${r.request_id}')">More Info</button>

            </div>
        </div>`

}

// Dashboard section