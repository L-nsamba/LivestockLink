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
    document.querySelectorAll('.nav-item[id^="nav-"]').forEach(n => n.classList.remove('active'));
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
        const card = btn.closet('.user-card');
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