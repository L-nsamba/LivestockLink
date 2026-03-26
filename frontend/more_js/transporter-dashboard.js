const BASE_URL = 'http://127.0.0.1:5000'

// Extracting tokens from local storage after login
function getToken() {return sessionStorage.getItem('token')};
function getTransporterId(){ return sessionStorage.getItem('user_id'); }


function authHeaders () {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
    };
}

// Simulation of accepting and declining requests locally
let dismissedRequestIds = new Set();
let currentModalRequest = null;
let notifications = JSON.parse(localStorage.getItem('transporter_notifications') || '[]'); // Local notification storage

function saveNotifications() {
    localStorage.setItem('transporter_notifications', JSON.stringify(notifications) || '[]');
}

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
                <span class="card-field-label">Farmer</span>
                <span class="card-field-value">${r.farmer_name || r.farmer_id}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">Animal Type</span>
                <span class="card-field-value">${r.animal_type}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">Quantity</span>
                <span class="card-field-value">${r.animal_quantity}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">From</span>
                <span class="card-field-value">${r.pickup_location}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">To</span>
                <span class="card-field-value">${r.destination_location}</span>
            </div>

            <div class="card-field">
                <span class="card-field-label">Date</span>
                <span class="card-field-value">${dateStr}</span>
            </div>

            <div class="card-actions">
                <button class="btn-accept" onclick="acceptRequest('${r.request_id}')">Accept</button>
                <!--<button class="btn-decline" onclick="declineRequest('${r.request_id}')">Decline</button>-->
                <button class="btn-more-info" onclick="openModal('${r.request_id}')">More Info</button>

            </div>
        </div>`

}

// Dashboard section
async function loadDashboard() {
    const container = document.getElementById('dashboard-cards');
    const tbody = document.getElementById('dashboard-trips-tbody');

    // Retrieving top 3 latest requests for the cards latest farmer requests section
    try {
        const res = await fetch (`${BASE_URL}/api/requests`, { headers: authHeaders() });
        if (!res.ok) throw new Error('Failed to fetch requests');

        const requests = await res.json();

        // Retrieving farm location data for the cached requests
        requests.forEach(r => { requestCache[r.request_id]= r});

        // Filtering such that records which have been booked don't show up on latest requests
        const visible = requests.filter(r => !dismissedRequestIds.has(r.request_id)).slice(0, 4);

        container.innerHTML = visible.length
        ? visible.map( r => buildCard(r)).join('')
        : `
        <div class="empty-state">
            <i class="fa-solid fa-envelope-open"></i>
            <div>No pending requests right now.</div>
        </div>`
    } catch (e) {
        container.innerHTML = 
        `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i> Could not load requests</div>`
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
            const farmerLabel = b.farmer_name || b.farmer_id || '-';
            const route = b.pickup_location
                ? `${b.pickup_location} to ${b.destination_location}`
                : `Request ${b.request_id}`;
            return `
            <tr>
                <td data-label="Farmer">${farmerLabel}</td>
                <td data-label="Trip Details" class="trip-route">${route}</td>
                <td data-label="Date">${dateStr}</td>
                <td data-label="Status"><span class="status-badge ${b.status.toLowerCase()}">${b.status.replace('_',' ')}</span></td>
            </tr>
            `
        }).join('');
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="4"><i class="fa-solid fa-circle-exclamation"></i> Could not load trips.</td></tr>`;
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
        container.innerHTML = `<div class="empty-state"><i class="fa-solid fa-triangle-exclamation"></i> Could not load requests. Check your connection (Is Flask running?)</div>`
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
        const card = document.getElementById('card-' + requestId);
        if (card) {
            card.style.transition = 'opacity 0.3s, transform 0.3s';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.9)';
            setTimeout(() => card.remove(), 300);
        }
        closeModal();
        showToast('Request accepted! Trip added to your history.', 'success');
        saveNotifications();
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

        ${r.notes ? `
        <div class="receipt-row">
            <span class="receipt-label">Notes</span>
            <span class="receipt-value">${r.notes}</span>
        </div>` : ''}

        <div class="modal-actions">
            <button class="btn-modal-accept" onclick="acceptRequest('${r.request_id}')">
                <i class="fa-solid fa-check"></i> Accept Request
            </button>
            <button class="btn-modal-close" onclick="closeModal()">Close</button>      
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

// History section

const STATUS_OPTIONS = {
    ACCEPTED: ['PICKED_UP', 'CANCELLED'],
    PICKED_UP: ['IN_TRANSIT', 'CANCELLED'],
    IN_TRANSIT: ['DELIVERED', 'CANCELLED'],
    DELIVERED: [],
    CANCELLED: []
}

async function loadHistory() {
    const tbody = document.getElementById('history-tbody');

    try {
        const transporterId = getTransporterId();
        const res = await fetch(`${BASE_URL}/api/bookings/transporter/${transporterId}`, {headers: authHeaders()});
        if (!res.ok) throw new Error('Failed to fetch bookings');
        const bookings = await res.json();

        if (!bookings.length) {
            tbody.innerHTML = `
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <i class="fa-solid fa-envelope-open"></i>
                        <div>No trips yet.</div>
                    </div>
                </td>
            </tr>`;
            return;
        }

        tbody.innerHTML = bookings.map(b => {
            const opts = STATUS_OPTIONS[b.status] || [];
            const isDone = opts.length === 0;
            const dateStr = b.accepted_at ? b.accepted_at.split('T')[0].split(' ')[0] : '-';
            const route = b.pickup_location
                ? `${b.pickup_location} to ${b.destination_location}`
                : `Request ${b.request_id}`;

            const selectHtml = isDone
                ? `<span style="color:#6b8a88;font-size:0.82rem;">—</span>`
                : `<select class="status-select" onchange="updateStatus('${b.booking_id}', this.value, '${b.request_id}')">
                       <option value="" disabled selected>Move to…</option>
                       ${opts.map(s => `<option value="${s}">${s.replace('_',' ')}</option>`).join('')}
                   </select>`;

            return `
                <tr id="history-row-${b.booking_id}">
                    <td data-label="Farmer">${b.farmer_name || b.farmer_id || '-'}</td>
                    <td data-label="Trip Details" class="trip-route">${route}</td>
                    <td data-label="Date Accepted">${dateStr}</td>
                    <td data-label="Status"><span class="status-badge ${b.status.toLowerCase()}">${b.status.replace('_',' ')}</span></td>
                    <td data-label="Update Status">${selectHtml}</td>
                </tr>`
        }).join('');
    } catch (e) {
        tbody.innerHTML = `
        <tr>
            <td colspan="5"><i class="fa-solid fa-circle-exclamation"></i> Could not load history. Check your connection</td>
        </tr>`
    }
}


// This function enables a transport to update the request status according to delivery progression
async function updateStatus(bookingId, newStatus, requestId) {
    try {
        const res = await fetch(`${BASE_URL}/api/bookings/${bookingId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify({status: newStatus})
        });

        if (!res.ok) {
            const err = await res.json();
            showToast(err.error || 'Failed to update status.', '');
            return;
        }

        const req = requestCache[requestId] || {};
        notifications.unshift({
            id:      Date.now(),
            message: `<i class="fa-solid fa-truck" style="color:#4a6fa5;margin-right:6px"></i>Status updated to <strong>${newStatus.replace('_',' ')}</strong> for trip: ${req.pickup_location || requestId} → ${req.destination_location || ''}.`,
            time:    new Date().toLocaleString('en-GB', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' }),
            unread:  true
        });
        updateNotifCount();
        loadHistory();
        showToast(`Status updated to ${newStatus.replace('_',' ')}.`, 'success');
        saveNotifications();
    } catch (e) {
        showToast('Network error. Please try again', '');
    }
}

// Notification loading and updating read status


function loadNotifications() {
    const list = document.getElementById('notif-list');
    if (!notifications.length) {
        list.innerHTML = `
        <div class="empty-state">
            <i class="fa-solid fa-bell-slash"></i>
            <div>No notifications yet.</div>
        </div>
        `;
        return;
    }
    list.innerHTML = notifications.map(n => `
        <div class="notif-item ${n.unread ? 'unread' : ''}" onclick="markRead(${n.id})">
            <span class="notif-text">${n.message}</span>
            <div class="notif-meta">
                <span class="notif-time">${n.time}</span>
            </div>
        </div>`).join('');
}


// Updating the notif count icon
function markRead(id) {
    const n = notifications.find(x => x.id === id);
    if (n) n.unread = false;
    loadNotifications();
    updateNotifCount();
    saveNotifications();
}

function updateNotifCount() {
    const count      = notifications.filter(n => n.unread).length;
    const badge      = document.getElementById('notif-count');
    const sideBadge  = document.getElementById('sidebar-notif-count');
    if (count > 0) {
        badge.textContent     = count;
        badge.style.display   = 'flex';
        sideBadge.textContent = count;
        sideBadge.style.display = 'inline';
    } else {
        badge.style.display     = 'none';
        sideBadge.style.display = 'none';
    }
}

// Toast notification message (success or failure notifications)
let toastTimer;
function showToast(msg, type) {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.className = 'toast show ' + (type || '');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.className = 'toast'; }, 3000);
}

// Logout Button
function logout() {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user_id');
    localStorage.removeItem('transporter_notifications');
    window.location.href = '../more_html/login.html';
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    const token = getToken();
    if (token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.role !== 'TRANSPORTER') {
                sessionStorage.removeItem('token');
                sessionStorage.removeItem('user_id');
                window.location.href = '../more_html/login.html';
                return;
            }
        } catch {
            window.location.href = '../more_html/login.html';
            return;
        }
    }
    loadDashboard();
    updateNotifCount();
});