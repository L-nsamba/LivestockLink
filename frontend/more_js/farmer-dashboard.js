const BASE_URL = 'http://127.0.0.1:5000';

// Grabbing user information from localStorage, this information is set when a user logins in
const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
const USER = {
    user_id : storedUser.user_id || 0,
    farmer_id : storedUser.farmer_id || 0,
    name : storedUser.full_name || 'Not Available',
    email  : storedUser.email || 'Not Available'
};

// Section switching logic
function switchSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById(`section-${name}`).classList.add('active');
    document.getElementById(`nav-${name}`).classList.add('active');

    if (name === 'history') loadHistory();
    if (name === 'notifications') loadNotifications();
}

// Toast notification message
function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`
    setTimeout(() => {t.className = 'toast'; }, 3500);
}

// Transport request submission
async function submitRequest() {
    const btn = document.getElementById('submit-btn');

    const payload = {
        farmer_id : USER.farmer_id,
        pickup_location : document.getElementById('pickup_location').value.trim(),
        pickup_date : document.getElementById('pickup_date').value,
        destination : document.getElementById('destination').value.trim(),
        animal_type :  document.getElementById('animal_type').value,
        animal_quantity : parseInt(document.getElementById('animal_quantity').value),
        notes : document.getElementById('notes').value.trim() || null,
    };


    // Basic field validation
    const required = ['pickup_location', 'pickup_date', 'destination', 'animal_type', 'animal_quantity'];

    for (const f of required) {
        if (!payload[f]) {  showToast('Please fill in all required fields', 'error'); return
        }
        if (isNaN(payload.animal_quantity) || payload.animal_quantity < 1) {
            showToast('Animal quantity must be at least 1 ', 'error'); return;
        }
    }

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Submitting...';

        try {
            const res = await fetch(`${BASE_URL}/api/requests`, {
                method : 'POST',
                headers : {'Content-Type' : 'application/json'},
                body : JSON.stringify(payload),
            });
            const data = await res.json();

            if (res.ok) {
                showToast('Transport request submitted! ✅', 'success');
                // Clearing form after successful request submission
                ['pickup_location', 'pickup_date', 'destination', 'animal_quantity', 'notes'].forEach(id => {
                    document.getElementById(id).value = '';
                });
                document.getElementById('animal_type').selectedIndex = 0;
                // Addition of notification to notification tab after request submitted
                addLocalNotification('✅ Your transport request has been submitted and is awaiting a transporter.');
            } else {
                showToast(data.error || 'Submission failed. Try again.', 'error')
            }
        } catch (err) {
            showToast('Cannot reach server. Is Flask running?', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Submit Request';
        }
}

// Loading trip history
async function loadHistory()  {
    const tbody = document.getElementById('history-tbody');
    tbody.innerHTML = `<tr>
                            <td colspan="6">
                                <div class="empty-state">
                                    <div class="emoji">⏳</div>
                                    <div>Loading....</div>
                                </div>
                            </td>
                        </tr>`;
    
    try {
        // Accessing that specific farmers transaction history stored in the requests table in the db and retrieving it with an api call
        const res = await fetch(`${BASE_URL}/api/requests/farmer/${USER.farmer_id}`);
        const requests = await res.json()

        if (!requests.length) {
            tbody.innerHTML = 
            `<tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="emoji">🚛</div>
                        <div>No trips yet. Create your first transport request!</div>
                    </div>
                </td>
            </tr>`;
            return;
        }

        // Trip history overview
        tbody.innerHTML = requests.map(r => `
            <tr>
                <td class="cb-col"><input type="checkbox" class="row-cb"/></td>
                <td data-label="Transporter">${r.transporter_id || '<span style="color: #6b8a88">Unassigned</span'}</td>
                <td data-label="Pickup">${r.pickup_location}</td>
                <td data-label="Dropoff">${r.destination}</td>
                <td data-label="Date">${formatDate(r.pickup_date)}</td>
                <td data-label="Status"><span class="status-badge ${r.status.toLowerCase()}">${formatStatus(r.status)}</span></td>
                <td data-label="">
                    <button class="link-btn" onclick='openTripModal(${JSON.stringify(r)})'>More Info</button>
                </td> 
            
            </tr>
            `).join('');
    } catch (err) {
        tbody.innerHTML = 
        `<tr>
            <td colspan="6">
                <div class="empty-state">
                    <div class="emoji">⚠️</div>
                    <div>Could not load trips. Is Flask running?</div>
                </div>
            </td>
        </tr>`;
    }
}

// Notification creation, storage and updating functions
const localNotifs = [];

function addLocalNotification(msg) {
    localNotifs.unshift({id: Date.now(), message: msg, time: new Date().toLocaleString(), unread: true, hasMore: false})
    updateNotifCount();
}

function updateNotifCount() {
    const unread = localNotifs.filter(n => n.unread).length;
    document.getElementById('notif-count').textContent = unread;
    document.getElementById('sidebar-notif-count').textContent = unread;
}

function loadNotifications() {
    const list = document.getElementById('notif-list');
    if (!localNotifs.length) {
        list.innerHTML = `<div class="empty-state"><div class="emoji">📭</div><div>No notifications yet.</div></div>`;
        return;
    }
    list.innerHTML = localNotifs.map(n => `
        <div class="notif-item ${n.unread ? 'unread' : ''}" onclick="markRead(${n.id}, this)">
          <span class="notif-text">${n.message}</span>
          <div class="notif-meta">
            ${n.hasMore ? `<button class="link-btn" style="display:block;margin-bottom:4px">More Info</button>` : ''}
            <span class="notif-time">${n.time}</span>
          </div>
        </div>
        `).join('');
}

function markRead(id, el) {
    const n = localNotifs.find(x => x.id === id);
    if (n) {n.unread = false; el.classList.remove('unread'); updateNotifCount();}

}

// Trip Receipt in more info in notifications table
// This function displays the receipt and if trip complete allows the farmer to rate the transporter
function openTripModal(r) {
    const isComplete = r.status === 'DELIVERED' || r.status === 'COMPLETE';
    document.getElementById('modal-body').innerHTML = `
        <div class="receipt-row"><span class="receipt-label">Pickup</span><span class="receipt-value">${r.pickup_location}</span></div>
        <div class="receipt-row"><span class="receipt-label">Destination</span><span class="receipt-value">${r.destination}</span></div>
        <div class="receipt-row"><span class="receipt-label">Date</span><span class="receipt-value">${formatDate(r.pickup_date)}</span></div>
        <div class="receipt-row"><span class="receipt-label">Animal Type</span><span class="receipt-value">${r.animal_type}</span></div>
        <div class="receipt-row"><span class="receipt-label">Quantity</span><span class="receipt-value">${r.animal_quantity}</span></div>
        <div class="receipt-row"><span class="receipt-label">Transporter</span><span class="receipt-value">${r.transporter_name || 'Awaiting match'}</span></div>
        <div class="receipt-row"><span class="receipt-label">Status</span><span class="receipt-value"><span class="status-badge ${r.status.toLowerCase()}">${formatStatus(r.status)}</span></span></div>
        ${r.notes ? `<div class="receipt-row"><span class="receipt-label">Notes</span><span class="receipt-value">${r.notes}</span></div>` : ''}
        ${isComplete ? `
          <div class="rating-section">
            <div class="rating-label">Rate your transporter</div>
            <div class="stars" id="stars">
              ${[1,2,3,4,5].map(i => `<span class="star" data-val="${i}" onclick="setRating(${i}, ${r.request_id})">★</span>`).join('')}
            </div>
            <button class="btn-rate" onclick="submitRating(${r.request_id})">Submit Rating</button>
          </div>
        ` : ''}
      `;
      document.getElementById('trip-modal').classList.add('open');

}

let selectedRating = 0;
function setRating(val) {
    selectedRating = val;
    document.querySelectorAll('.star').forEach((s, i) => {
    s.classList.toggle('active', i < val);
    });
}

// Ratings and submission logic when rating file is done (submitRating() + closeModal())
async function submitRating(requestId) {
    if (!selectedRating) { showToast('Please select a star rating.', 'error'); return; }
    showToast(`Rating of ${selectedRating}★ submitted. Thank you!`, 'success');
    closeModal();
    // TODO: wire to POST /api/ratings/ when bookings are in place
}

function closeModal() {
    document.getElementById('trip-modal').classList.remove('open');
    selectedRating = 0;
}

// Close modal on overlay click
document.getElementById('trip-modal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

// ── Checkbox select all ──
function toggleAll(master) {
    document.querySelectorAll('.row-cb').forEach(cb => cb.checked = master.checked);
}

// ── Helpers ──
function formatDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-GB', { day:'2-digit', month:'2-digit', year:'2-digit' }).replace(/\//g, '-');
}

function formatStatus(s) {
    const map = { PENDING:'Pending', BOOKED:'Booked', IN_TRANSIT:'In Transit', DELIVERED:'Complete', CANCELLED:'Cancelled' };
    return map[s] || s;
}


function handleLogout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

// Mobile side bar
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const hamburger = document.getElementById('hamburger');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
    hamburger.classList.toggle('open')
}

function closeSidebar() {
    document.querySelector('.sidebar').classList.remove('open');
    document.getElementById('sidebar-overlay').classList.remove('open');
    document.getElementById('hamburger').classList.remove('open');
}

// Closing sidebar upon clicking on mobile
document.querySelectorAll('.nav-item, .logout-btn').forEach(el => {
    el.addEventListener('click', () => {
        if (window.innerWidth < 768) closeSidebar();
    });
});

updateNotifCount();