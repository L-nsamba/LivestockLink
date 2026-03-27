const BASE_URL = 'https://livestocklink.leonnsamba.tech';

// Grabbing user information from localStorage, this information is set when a user logins in
const storedUser = JSON.parse(sessionStorage.getItem('user') || '{}')
const USER = {
    user_id : storedUser.user_id || 0,
    name : storedUser.full_name || 'Not Available',
    email  : storedUser.email || 'Not Available'
};

// Helper to build auth headers for every API call
function authHeaders() {
    const token = sessionStorage.getItem('token') || '';
    return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` };
}

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
    t.innerHTML = msg;
    t.className = `toast ${type} show`
    setTimeout(() => {t.className = 'toast'; }, 3500);
}

// Transport request submission
async function submitRequest() {
    const btn = document.getElementById('submit-btn');

    const payload = {
        pickup_location : document.getElementById('pickup_location').value.trim(),
        pickup_date : document.getElementById('pickup_date').value,
        destination_location : document.getElementById('destination').value.trim(),
        animal_type :  document.getElementById('animal_type').value,
        animal_quantity : parseInt(document.getElementById('animal_quantity').value),
        notes : document.getElementById('notes').value.trim() || null,
    };


    // Basic field validation
    const required = ['pickup_location', 'pickup_date', 'destination_location', 'animal_type', 'animal_quantity'];

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
                headers : authHeaders(),
                body : JSON.stringify(payload),
            });
            const data = await res.json();

            if (res.ok) {
                showToast('<i class="fa-solid fa-circle-check"></i> Transport request submitted!', 'success');
                // Clearing form after successful request submission
                ['pickup_location', 'pickup_date', 'destination', 'animal_quantity', 'notes'].forEach(id => {
                    document.getElementById(id).value = '';
                });
                document.getElementById('animal_type').selectedIndex = 0;
                // Mark this request as seen so syncRequestNotifications doesn't double-notify
                if (data.request_id) {
                    const seen = JSON.parse(localStorage.getItem(SEEN_KEY) || '[]');
                    seen.push(data.request_id);
                    localStorage.setItem(SEEN_KEY, JSON.stringify(seen));
                }
                // Addition of notification to notification tab after request submitted
                addLocalNotification(`<i class="fa-solid fa-bell"></i> Your transport request (${payload.animal_type} to ${payload.destination_location}) has been submitted and is awaiting a transporter.`);
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
                                    <div class="emoji">
                                        <i class="fa-solid fa-hourglass"></i>
                                    </div>
                                    <div>Loading....</div>
                                </div>
                            </td>
                        </tr>`;
    
    try {
        // Accessing that specific farmers transaction history stored in the requests table in the db and retrieving it with an api call
        const res = await fetch(`${BASE_URL}/api/requests/farmer/${USER.user_id}`, { headers: authHeaders() });
        const requests = await res.json()

        if (!requests.length) {
            tbody.innerHTML = 
            `<tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="emoji">
                            <i class="fa-solid fa-truck"></i>
                        </div>
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
                <td data-label="Transporter">${r.transporter_name || r.transporter_id || '<span style="color: #6b8a88">Unassigned</span'}</td>
                <td data-label="Pickup">${r.pickup_location}</td>
                <td data-label="Dropoff">${r.destination_location}</td>
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
                    <div class="emoji">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                    </div>
                    <div>Could not load trips. Is Flask running?</div>
                </div>
            </td>
        </tr>`;
    }
}

// Notification creation, storage and updating functions
// Notifications are stored in localStorage so they persist across page loads/logins
const NOTIF_KEY = `notifs_${USER.user_id}`;
const SEEN_KEY = `seen_requests_${USER.user_id}`;
const SEEN_STATUS_KEY = `seen_statuses_${USER.user_id}`;

function getNotifs() {
    return JSON.parse(localStorage.getItem(NOTIF_KEY) || '[]');
}

function saveNotifs(notifs) {
    localStorage.setItem(NOTIF_KEY, JSON.stringify(notifs));
}

function addLocalNotification(msg) {
    const notifs = getNotifs();
    notifs.unshift({ id: Date.now(), message: msg, time: new Date().toLocaleString(), unread: true });
    saveNotifs(notifs);
    updateNotifCount();
}

function updateNotifCount() {
    const unread = getNotifs().filter(n => n.unread).length;
    const notifCount = document.getElementById('notif-count');
    const sidebarCount = document.getElementById('sidebar-notif-count');
    if (notifCount) notifCount.textContent = unread;
    if (sidebarCount) sidebarCount.textContent = unread;
}

function loadNotifications() {
    const notifs = getNotifs();
    const list = document.getElementById('notif-list');
    if (!notifs.length) {
        list.innerHTML = `
        <div class="empty-state">
            <div class="emoji">
                <i class="fa-solid fa-envelope"></i>
            </div>
        <div>No notifications yet.</div></div>`;
        return;
    }
    list.innerHTML = notifs.map(n => `
        <div class="notif-item ${n.unread ? 'unread' : ''}" onclick="markRead(${n.id}, this)">
          <span class="notif-text">${n.message}</span>
          <div class="notif-meta">
            <span class="notif-time">${n.time}</span>
          </div>
        </div>
        `).join('');
}

function markRead(id, el) {
    const notifs = getNotifs();
    const n = notifs.find(x => x.id === id);
    if (n) { n.unread = false; saveNotifs(notifs); el.classList.remove('unread'); updateNotifCount(); }
}

// On page load, fetch the farmer's requests from the server and generate notifications
// for any requests we haven't notified about yet (catches requests made via APIdog etc.)
// Also detects status changes made by the transporter and notifies the farmer.
async function syncRequestNotifications() {
    try {
        const res = await fetch(`${BASE_URL}/api/requests/farmer/${USER.user_id}`, { headers: authHeaders() });
        if (!res.ok) return;
        const requests = await res.json();

        const seen = JSON.parse(localStorage.getItem(SEEN_KEY) || '[]');
        const seenStatuses = JSON.parse(localStorage.getItem(SEEN_STATUS_KEY) || '{}');
        let seenChanged = false;
        let statusChanged = false;

        for (const r of requests) {
            // Notify for newly seen requests (submitted externally)
            if (!seen.includes(r.request_id)) {
                seen.push(r.request_id);
                seenStatuses[r.request_id] = r.status;
                addLocalNotification(`Your transport request (${r.animal_type} to ${r.destination_location}) was submitted and is awaiting a transporter.`);
                seenChanged = true;
                statusChanged = true;
                continue;
            }

            // Notify when transporter changes the status
            const prevStatus = seenStatuses[r.request_id];
            if (prevStatus !== r.status) {
                seenStatuses[r.request_id] = r.status;
                statusChanged = true;

                if (r.status === 'BOOKED') {
                    addLocalNotification(`<i class="fa-solid fa-circle-check"></i> A transporter has accepted your request (${r.animal_type} to ${r.destination_location}). Your livestock is being prepared for pickup!`);
                } else if (r.status === 'IN_TRANSIT') {
                    addLocalNotification(`<i class="fa-solid fa-truck-moving"></i> Your livestock (${r.animal_type} to ${r.destination_location}) is now in transit!`);
                } else if (r.status === 'DELIVERED') {
                    addLocalNotification(`<i class="fa-solid fa-flag-checkered"></i> Your transport request (${r.animal_type} to ${r.destination_location}) has been completed. Please rate your transporter.`);
                } else if (r.status === 'PENDING' && prevStatus === 'BOOKED') {
                    addLocalNotification(`<i class="fa-solid fa-circle-exclamation"></i> Your transporter has cancelled the booking for (${r.animal_type} to ${r.destination_location}). Your request is now available for other transporters.`);
                }
            }
        }

        if (seenChanged) localStorage.setItem(SEEN_KEY, JSON.stringify(seen));
        if (statusChanged) localStorage.setItem(SEEN_STATUS_KEY, JSON.stringify(seenStatuses));
    } catch (_) {
        // silently fail — notifications will still show stored ones
    }
}

// Trip Receipt in more info in notifications table
// This function displays the receipt and if trip complete allows the farmer to rate the transporter
function openTripModal(r) {
    const isComplete = r.status === 'DELIVERED' || r.status === 'COMPLETE';
    const isPending = r.status === 'PENDING';
    document.getElementById('modal-body').innerHTML = `
        <div class="receipt-row"><span class="receipt-label">Pickup</span><span class="receipt-value">${r.pickup_location}</span></div>
        <div class="receipt-row"><span class="receipt-label">Destination</span><span class="receipt-value">${r.destination_location}</span></div>
        <div class="receipt-row"><span class="receipt-label">Date</span><span class="receipt-value">${formatDate(r.pickup_date)}</span></div>
        <div class="receipt-row"><span class="receipt-label">Animal Type</span><span class="receipt-value">${r.animal_type}</span></div>
        <div class="receipt-row"><span class="receipt-label">Quantity</span><span class="receipt-value">${r.animal_quantity}</span></div>
        <div class="receipt-row"><span class="receipt-label">Transporter ID</span><span class="receipt-value">${r.transporter_id || 'Awaiting match'}</span></div>
        <div class="receipt-row"><span class="receipt-label">Status</span><span class="receipt-value"><span class="status-badge ${r.status.toLowerCase()}">${formatStatus(r.status)}</span></span></div>
        ${r.notes ? `<div class="receipt-row"><span class="receipt-label">Notes</span><span class="receipt-value">${r.notes}</span></div>` : ''}
        ${isComplete ? `
          <div class="rating-section">
            <div class="rating-label">Rate your transporter</div>
            <div class="stars" id="stars">
              ${[1,2,3,4,5].map(i => `<span class="star" data-val="${i}" onclick="setRating(${i})">★</span>`).join('')}
            </div>
            <button class="btn-rate" onclick="submitRating('${r.booking_id}')">Submit Rating</button>
          </div>
        ` : ''}
        ${isPending ? `
          <div class="cancel-section">
            <button class="btn-cancel-request" onclick="deleteRequest('${r.request_id}', '${r.animal_type}', '${r.destination_location}')">Cancel Request</button>
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

// Ratings and submission logic
async function submitRating(bookingId) {
    if (!selectedRating) { showToast('Please select a star rating.', 'error'); return; }
    try {
        const res = await fetch(`${BASE_URL}/api/ratings`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ booking_id: bookingId, score: selectedRating }),
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Rating of ${selectedRating}★ submitted. Thank you!`, 'success');
            closeModal();
        } else {
            showToast(data.error || 'Could not submit rating.', 'error');
        }
    } catch (err) {
        showToast('Cannot reach server. Is Flask running?', 'error');
    }
}

function closeModal() {
    document.getElementById('trip-modal').classList.remove('open');
    selectedRating = 0;
}

async function deleteRequest(requestId, animalType, destination) {
    if (!confirm('Are you sure you want to cancel this request?')) return;
    try {
        const res = await fetch(`${BASE_URL}/api/requests/${requestId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Request cancelled.', 'success');
            addLocalNotification(`<i class="fa-solid fa-circle-xmark"></i> Your transport request (${animalType} to ${destination}) has been cancelled.`);
            closeModal();
            loadHistory();
        } else {
            showToast(data.error || 'Could not cancel request.', 'error');
        }
    } catch (err) {
        showToast('Cannot reach server. Is Flask running?', 'error');
    }
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
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
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

// On load: restore persisted notification count, then sync with server
updateNotifCount();
syncRequestNotifications();
