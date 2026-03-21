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
async function loadDashboard() {
    const container = document.getElementById('dashboard-cards');
    const tbody = document.getElementById('dashboard-trips-tbdody');

    // Retrieving top 3 latest requests for the cards latest farmer requests section
    try {
        const res = await fetch (`${BASE_URL}/api/requests`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed to fetch requests');

        // Retrieving farm location data for the cached requests
        requests.forEach(r => { requestCache[r.request_id]= r});

        // Filtering such that records which have been booked don't show up on latest requests
        const visible = requests.filter(r => !dismissedRequestIds.has(r.request_id)).slice(0, 3);

        container.innerHTML = visible.length
        ? visible.map( r => buildCard(r)).join('')
        : `
        <div class="empty-state">
            <i class="fa-solid fa-envelope-open"></i>
            <div>No pending requests right now.</div>
        </div>`
    } catch (e) {
        container.innerHTML = 
        `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>Could not load requests. Check your connection (Is Flask running ?)</div>`
    }

    // Retrieving recent trips for individual transporter from bookings to display on that section of the dashboard
    try {
        const transporterId = getTransporterId();
        const res = await fetch (`${BASE_URL}/api/bookings/transporter/${transporterId}`, { headers: authHeaders()});
        if (!res.ok) throw new Error ('Failed to fetch bookings');
        const bookings = await res.json();
        const recents = bookings.slice(0, 4);

        if (!recents.length) {
            tbody.innerHTML = `<tr><td colspan="4">No trips yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = recents.map(b => {
            const dateStr = b.accepted_at ? b.accepted_at.split('T')[0].split(' ')[0] : '-';
            const farmerLabel = b.farmer_id || '-';
            const route = b.pickup_location
                ? `${b.pickup_location} to ${b.destination_location}`
                : `Request ${b.request_id}`;
            return `
            <tr>
                <td data-label="Farmer">${farmerLabel}</td>
                <td data-label="Trip Details" class="trip-route">${route}</td>
                <td data-label="Date">${dateStr}</td>
                <td data-label="Status"><span class="status-badge ${b.status.toLowerCase()}">${b.status.replace('_',' ')}</span></td>
            </tr>;
            `
        }).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4">Could not load trips.</td></tr>`;
    }
}

// Find Farmer Section
async function loadFindFarmer() {
    const container = document.getElementById('find-cards');
    try {
        // Retrieving farmers from the transport requests route logic
        const res = await fetch(`${BASE_URL}/api/requests`, {headers: authHeaders()});
        if (!res.ok) throw new Error('Failed to fetch requests');
        const requests = await res.json();

        requests.forEach(r => {requestCache[r.request_id] = r; });

        const visible = requests.filter(r => !dismissedRequestIds.has(r.request_id));
        container.innerHTML = visible.length
            ? visible.map(r => buildCard(r)).join('')
            : `
            <div class="empty-state">
                <i class="fa-solid fa-envelope-open"></i>
                <div>No pending requests available at the moment</div>
            </div>`
    } catch (e) {
        container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i>Could not load requests. Check your connection (Is Flask running?)</div>`
    }
}

// Accept request logic
async function acceptRequest(requestId) {
    try {
        const res = await fetch(`${BASE_URL}/api/bookings`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({request_id: requestId})
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.error || 'Could not accept request', '');
            return;
        }

        dismissedRequestIds.add(requestId);

        // Updating notification count when request is accepted
        const r = requestCache[requestId] || {};
        notifications.unshift({
            id: Date.now(),
            message: `<i class="fa-solid fa-check-circle" style="color:#27ae60;margin-right:6px"></i>You accepted a trip: ${r.pickup_location || requestId} → ${r.destination_location || ''}.`,
            time:    new Date().toLocaleString('en-GB', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }),
            unread: true
        });
        updateNotifCount();

        // Card animation styling
        const card = document.getElementById('card-', + requestId);
        if (card) {
            card.style.transition = 'opacity 0.3s, transform 0.3s';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.9)';
            setTimeout(() => card.remove(), 300);
        }
        closeModal();
        showToast('Request accepted! Trip added to your history.', 'success');
    } catch(e) {
        showToast('Network error. Please try again.', '');
    }
}

// The trip receipt which is accessible by transporter when they click more info
function openModal(requestId) {
    const r = requestCache[requestId]
    if (!r) { showToast('Request details not available.', ''); return; }
    currentModalRequest = r;

    const dateStr = r.pickup_date
        ? new Date(r.pickup_date).toLocaleString('en-GB', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'})
        : '-';

    // Defining the trip receipt structure that will display when more info is clicked
    document.getElementById('modal-body').innerHTML = `
        <div class="receipt-row">
            <span class="receipt-label">Farmer ID</span>
            <span class="receipt-value">${r.farmer_id}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Animal Type</span>
            <span class="receipt-value">${r.animal_type}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Quantity</span>
            <span class="receipt-value">${r.animal_quantity}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Pickup Location</span>
            <span class="receipt-value">${r.pickup_location}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Destination</span>
            <span class="receipt-value">${r.destination_location}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Pickup Date</span>
            <span class="receipt-value">${dateStr}</span>
        </div>

        <div class="receipt-row">
            <span class="receipt-label">Status</span>
            <span class="receipt-value"><span class="status-badge pending">PENDING</span></span>
        </div>

        <div class="modal-actions">
            <button class="btn-modal-accept" onclick="acceptRequest('${r.request_id}')"
                <i class="fa-solid fa-check"></i>; Accept Request
            </button>
            <button class="btn-modal-close" onclick=""closeModal()">Close</button>      
        </div>`;

    document.getElementById('request-modal').classList.add('open');
    document.getElementById('request-modal').onclick = function(e) {
        if (e.target === this) closeModal();
    };
}

function closeModal() {
    document.getElementById('request-modal').classList.remove('open');
    currentModalRequest = null;
}