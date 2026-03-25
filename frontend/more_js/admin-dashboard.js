const BASE_URL = 'http://127.0.0.1:5000';

// Extracting the token used for session management from headers
function authHeaders() {
    const token = sessionStorage.getItem('token') || '';
    return {'Content-Type' : 'application/json', 'Authorization' : `Bearer ${token}`}
}

// Sidebar navigation 
// Addition of functionality to switch between different sections on sidebar
function switchSection(name) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-item[id^="nav-"]').forEach(n => n.classList.remove('active')); // id^ is essentially like regex i.e we are extracting all nav-items (class) with the id starting with nav-
    document.getElementById('section-' + name).classList.add('active');
    const navEl = document.getElementById('nav-' + name);
    if (navEl) navEl.classList.add('active');
    closeSidebar();

    // Calling the functions which contain the respective contents of the different sections so that they execute when switched to the section
    if (name === 'users') loadUsers();
    if (name === 'notifications') { loadTripNotifs(); loadRatingNotifs(); }
}

// Essentially what causes the sidebar to opening and closing on the responsive design
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

function handleLogout() {
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('user');
    window.location.href = '../more_html/login.html'
}

// Where users retrieved from the db are stored to provide real time info on the dashboards
let allUsers = []

async function loadUsers () {
    const grid = document.getElementById('users-grid');
    grid.innerHTML = `<p style="color:#6b8a88;padding:1rem;text-align:center;">Loading...</p>`
    document.getElementById('users-empty').style.display = 'none';

    try {
        const res = await fetch(`${BASE_URL}/api/admin/users`, {headers: authHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load users');
        allUsers = data;
        renderUsers(allUsers)
    } catch(err) {
        grid.innerHTML = `<p style="color:#e74c3c;padding:1rem;text-align:center;">${err.message}</p>`
    }
}

// This function is responsible for displaying all users
function renderUsers(list) {
    const grid = document.getElementById('users-grid');
    const empty = document.getElementById('users-empty');
    grid.innerHTML = '';
    if (!list.length) { empty.style.display = 'block'; return; }
    empty.style.display = 'none'
    // Creation of the user cards displayed on the all users section
    list.forEach( u => {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.dataset.id = u.user_id;
        card.innerHTML = `
            <div class="user-card-header">
                <div>
                    <div class="user-name">${u.full_name}</div>
                    <span class="role-badge role-${u.role.toLowerCase()}">${u.role}</span>
                </div>
            </div>

            <div class="card-field">
                <span class="card-field-label">Email</span>
                <span class="card-field-value" data-field="email">${u.email}</span>
            </div>
            <div class="card-field">
                <span class="card-field-label">Contact</span>
                <span class="card-field-value" data-field="contact">${u.contact || '-'}</span>
            </div>
            <div class="card-field">
                <span class="card-field-label">Joined</span>
                <span class="card-field-value">${u.created_at || '-'}</span>
            </div>

            <div class="card-actions">
                <button class="btn-update" onclick="openUpdateModal('${u.user_id}')"><i class="fa-solid fa-pen-to-square"></i>Update</button>
                <button class="btn-delete" onclick="deleteUser('${u.user_id}', this)"><i class="fa-solid fa-trash"></i> Delete</button>
            </div>`;
            grid.appendChild(card);
    });
}

// search & filter
function applyFilters () {
    // Essentially matching names search to those existing within the results
    const q = document.getElementById('user-search').value.toLowerCase();
    const role = document.getElementById('role-filter').value;
    const filtered = allUsers.filter(u => {
        const matchQ = u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q);
        const matchRole = role === 'all' || u.role.toLowerCase() === role;
        return matchQ && matchRole;
    });
    renderUsers(filtered)
}

// Applying event listeners on the search by user name / general role
document.getElementById('user-search').addEventListener('input', applyFilters)
document.getElementById('role-filter').addEventListener('change', applyFilters);

// Deleting a user by admin
async function deleteUser(id, btn) {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/users/${id}`, {
            method: 'DELETE',
            headers: authHeaders()
        });
        if (!res.ok) {
            const data = await res.json();
            showToast(data.error || 'Could not delete user.', 'error')
            return;
        }
        const card = btn.closest('.user-card');
        card.style.transition = 'opacity 0.3s, transform 0.3s';
        card.style.opacity = '0';
        card.style.transform = 'scale(0.95)';
        setTimeout(() => card.remove(), 300);
        allUsers = allUsers.filter(u => String(u.user_id) !== String(id));
        showToast('User deleted', 'error');
    } catch (err) {
        showToast('Cannot reach server. Is Flask running?', 'error');
    }
}

// Updating modal/card containing user information
let editingId = null;

function openUpdateModal(id) {
    const u = allUsers.find(u => String(u.user_id) === String(id)); // Searching through the array of existing users to find the one which matches user_id of searched user
    if (!u) return;
    editingId = id;
    document.getElementById('edit-name').value = u.full_name;
    document.getElementById('edit-email').value = u.email;
    document.getElementById('edit-phone').value = u.contact || '';

    // Hide all role-specific fields first, then show the relevant ones
    document.getElementById('farmer-fields').style.display = 'none';
    document.getElementById('transporter-fields').style.display = 'none';

    if (u.role === 'FARMER') {
        document.getElementById('farmer-fields').style.display = 'block';
        document.getElementById('edit-farm-location').value = u.farm_location || '';
    } else if (u.role === 'TRANSPORTER') {
        document.getElementById('transporter-fields').style.display = 'block';
        document.getElementById('edit-vehicle-type').value = u.vehicle_type || '';
        document.getElementById('edit-vehicle-capacity').value = u.vehicle_capacity || '';
        document.getElementById('edit-license-number').value = u.license_number || '';
        document.getElementById('edit-organization').value = u.organization_name || '';
    }

    document.getElementById('update-modal').classList.add('open');
}

function closeModal() {
    document.getElementById('update-modal').classList.remove('open');
    editingId = null;
}

// Addition of event listiner on close modal button the x icon
document.getElementById('modal-close-btn').addEventListener('click', closeModal);
document.getElementById('modal-cancel-btn').addEventListener('click', closeModal);
document.getElementById('update-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('update-modal')) closeModal();
});


// Addition of an event listnener to the save changes button on the modal/ receipt like pop up containing user info
document.getElementById('modal-save-btn').addEventListener('click', async () => {
    if (!editingId) return;
    const u = allUsers.find(u => String(u.user_id) === String(editingId));
    const payload = {
        full_name: document.getElementById('edit-name').value.trim(),
        email:  document.getElementById('edit-email').value.trim(),
        contact: document.getElementById('edit-phone').value.trim()
    };

    if (u && u.role === 'FARMER') {
        payload.farm_location = document.getElementById('edit-farm-location').value.trim();
    } else if (u && u.role === 'TRANSPORTER') {
        payload.vehicle_type = document.getElementById('edit-vehicle-type').value.trim();
        payload.vehicle_capacity = document.getElementById('edit-vehicle-capacity').value.trim();
        payload.license_number = document.getElementById('edit-license-number').value.trim();
        payload.organization_name = document.getElementById('edit-organization').value.trim();
    }
    try {
        const res = await fetch (`${BASE_URL}/api/admin/users/${editingId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) { showToast(data.error || 'Update failed.', 'error'); return; }
        const u = allUsers.find(u => String(u.user_id) === String(editingId)) // Searching through the array of existing users to find the matching user with the same user_id to the user info that has just been editted
        if (u) {
            if (payload.full_name) u.full_name  = payload.full_name;
            if (payload.email) u.email = payload.email
        }
        const card = document.querySelector(`.user-card[data-id="${editingId}"]`); // Referencing the specific uuid of the user when edits happen so they reflect when admin is done
        if (card) {
            if (payload.full_name) {
                card.querySelector('.user-name').textContent = payload.full_name;
            }
            if (payload.email) card.querySelector('[data-field="email"]').textContent = payload.email
        }
        closeModal();
        showToast('User updated successfully', 'success');
    } catch (err) {
        showToast('Cannot reach server. Is Flask running?', 'error')
    }
});

// notification tab
document.querySelectorAll('.notif-tab').forEach(tab => {
    // This event listener allows the switching between the sections on the notification display i.e from the completed trips to the ratings and vice versa
    tab.addEventListener('click', () => {
        document.querySelectorAll('.notif-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.notif-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById('panel-' + tab.dataset.panel).classList.add('active');
    });
});

// Stars for the ratings
function starsHtml(n) {
    let s = '<div class="star-row">';
    for (let i = 1; i <= 5; i++) s += `<i class="fa-solid fa-star star${i > n ? ' empty' : ''}"></i>`;
    return s + '</div>';
}

// trip notifications
// fetches from the admin bookings endpoint (GET /api/admin/bookings) in the backend hence provides the admin with real time info about trips extracted directly from the db where the info is stored
async function loadTripNotifs() {
    const tripsList = document.getElementById('trips-list');
    tripsList.innerHTML = '<p style="color:#6b8a88;padding:1rem;text-align:center;">Loading...</p>';
    try {
        const res = await fetch(`${BASE_URL}/api/admin/bookings`, { headers: authHeaders() });
        if (!res.ok) throw new Error;
        const bookings = await res.json();
        if (!bookings.length) {
            tripsList.innerHTML = '<div class="empty-state"><i class="fa-solid fa-truck"></i><p>No completed trips yet.</p></div>';
            return;
        }
        // This will effectively display the detailed breakdown of the trip for the admin to see i.e the farmer and the matched transporter, accepted time etc
        tripsList.innerHTML = bookings.map(b => `
            <div>
                <div class="notif-body">
                    <div class="notif-text"><i class="fa-solid fa-truck" style="color:#4a6fa5;margin-right:0.4rem;"></i>Farmer ID ${b.farmer_id} → Transporter ID ${b.transporter_id}</div>
                    <div class="notif-sub">Route: ${b.pickup_location} → ${b.destination_location} &bull; ${b.animal_quantity} ${b.animal_type}</div> 
                </div>
                <div class="notif-meta"><span class="notif-time">${b.accepted_at ? b.accepted_at.split('T')[0] : ''}</span></div>
            </div>`).join('');
    } catch {
        tripsList.innerHTML = '<div class="empty-state"><i class="fa-solid fa-circle-exclamation"></i><p>Could not load trip data.</p></div>';
    }
}

// Rating notifications
// Fetched from the GET /api/admin/ratings endpoint in the backend retrieving real time ratings
async function loadRatingNotifs() {
    const ratingsList = document.getElementById('ratings-list');
    ratingsList.innerHTML = '<p style="color:#6b8a88;padding:1rem;text-align:center;">Loading...</p>';
    try {
        const res = await fetch(`${BASE_URL}/api/admin/ratings`, { headers: authHeaders() });
        if (!res.ok) throw new Error();
        const ratingsData = await res.json();
        if (!ratingsData.length) {
            ratingsList.innerHTML = '<div class="empty-state"><i class="fa-solid fa-star"></i><p>No ratings yet.</p></div>';
            return;
        }
        // The rating display for respective rated transporters for the admin to view
        ratingsList.innerHTML = ratingsData.map(r => `
            <div class="notif-item">
                <div class="notif-body">
                    <div class="notif-text">Farmer ID <strong>${r.rating_by}</strong> rated Transporter ID <strong>${r.rating_for}</strong></div>
                    ${starsHtml(r.score)}
                    ${r.comment ? `<div class="notif-sub" style="margin-top:0.35rem;">"${r.comment}"</div>` : ''}
                </div>
            </div>`).join('');
    } catch {
        ratingsList.innerHTML = '<div class="empty-state"><i class="fa-solid fa-circle-exclamation"></i><p>Could not load rating data.</p></div>';
    }
}

// Toat message styling for success and errors
function showToast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast' + (type? ' ' + type : '');
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 3000);
}

// Dashboard stat cards showing total users, active requests and completed trips
async function loadDashboardStats() {
    const statValues = document.querySelectorAll('.stat-value');
    try {
        const res = await fetch(`${BASE_URL}/api/admin/users`, {headers: authHeaders() });
        if (res.ok) {
            const users = await res.json();
            allUsers = users;
            // Returning the number of users
            if (statValues[0]) statValues[0].textContent = users.length;
        }
    } catch {}
}

// Charts for frontend display
let statusChart = null;

async function loadStatusBreakdownChart() {
    try {
        const res = await fetch(`${BASE_URL}/api/admin/charts/status-breakdown`, {headers: authHeaders()});
        if (!res.ok) throw new Error();
        const chartData = await res.json();

        if (statusChart) statusChart.destroy(); // Error handling to prevent chart duplication

        statusChart = new Chart(document.getElementById('donutChart'), {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.data,
                    backgroundColor: ['#f5c518', '#4a6fa5', '#8bbcaa', '#27ae60', '#FF5C5C'],
                    borderWidth: 2,
                    borderColor: 'white'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { family: 'DM Sans', size: 12 }, padding: 16 }
                    }
                }
            }
        })
    } catch {} // chart fails silently and nothing loads incase of error in backend
}

// Add the chart logic for requests(y) over dates (x) --> this would be like a line or bar graph
// Add the chart logic for top pickup locations and top pickup destinations --> these can be bar graphs, or one vertical one horiztonal bar graph, your choice
// then add the calls down below the loadstatusbreakdownchart
// reference the endpoints that are existing in the admin file, chart endpints were added
// will follow a similar structure to the chart I have above 

document.getElementById('panel-trips').classList.add('active');
loadDashboardStats();
loadStatusBreakdownChart();