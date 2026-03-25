const token = sessionStorage.getItem('token');
const BASE  = 'http://127.0.0.1:5000/api';

const authHeaders = {
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
};

// ── Generic fetch ────────────────────────────────────────────────
async function apiFetch(path) {
  const res = await fetch(`${BASE}${path}`, { headers: authHeaders });
  if (res.status === 401 || res.status === 403) {
    alert('Session expired. Please log in again.');
    window.location.href = '../more_html/login.html';
    return;
  }
  if (!res.ok) throw new Error(`Request failed: ${path} (${res.status})`);
  return res.json();
}

// ── Stat Cards ───────────────────────────────────────────────────
// Targets: stat-total-users, stat-pending, stat-completed (your HTML IDs)
async function loadStats() {
  const d = await apiFetch('/admin/charts/stats');
  document.getElementById('stat-total-users').textContent = d.total_users;
  document.getElementById('stat-pending').textContent     = d.pending_requests;
  document.getElementById('stat-completed').textContent   = d.completed_trips;
}

// ── Bar Chart: Requests over time ────────────────────────────────
// Canvas ID in HTML: barChart
async function loadRequestsChart() {
  const d = await apiFetch('/admin/charts/requests-per-day');
  new Chart(document.getElementById('barChart'), {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{
        label: 'Requests',
        data: d.data,
        backgroundColor: 'rgba(74, 111, 165, 0.75)',
        borderRadius: 6,
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: '#f0f4f8' } },
        x: { grid: { display: false } }
      }
    }
  });
}

// ── Donut Chart: Status breakdown ────────────────────────────────
// Canvas ID in HTML: donutChart
// Status values from Bookings model: ACCEPTED, PICKED_UP, IN_TRANSIT, DELIVERED, CANCELLED
async function loadStatusChart() {
  const d = await apiFetch('/admin/charts/status-breakdown');
  const colors = {
    ACCEPTED:   '#8bbcaa',
    PICKED_UP:  '#76e4f7',
    IN_TRANSIT: '#f6ad55',
    DELIVERED:  '#4a6fa5',
    CANCELLED:  '#FF5C5C'
  };
  new Chart(document.getElementById('donutChart'), {
    type: 'doughnut',
    data: {
      labels: d.labels,
      datasets: [{
        data: d.data,
        backgroundColor: d.labels.map(l => colors[l] || '#dce8e4'),
        borderWidth: 2,
        borderColor: '#fff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { padding: 16, font: { size: 11, family: 'DM Sans' } }
        }
      }
    }
  });
}

// ── Horizontal Bar: Top pickup locations ─────────────────────────
// Canvas ID in HTML: hbarChart
async function loadLocationsChart() {
  const d = await apiFetch('/admin/charts/top-pickup-locations');
  new Chart(document.getElementById('hbarChart'), {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{
        label: 'Requests',
        data: d.data,
        backgroundColor: 'rgba(139, 188, 170, 0.8)',
        borderRadius: 6,
        borderWidth: 0
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f0f4f8' } },
        y: { grid: { display: false } }
      }
    }
  });
}

// ── Users Grid ───────────────────────────────────────────────────
// Renders into cards-grid using user-card structure matching your CSS
let allUsers = [];

async function loadUsersGrid() {
  allUsers = await apiFetch('/admin/users');
  renderUsers(allUsers);
}

function renderUsers(users) {
  const grid  = document.getElementById('users-grid');
  const empty = document.getElementById('users-empty');

  if (!users || !users.length) {
    grid.innerHTML = '';
    empty.style.display = 'flex';
    return;
  }

  empty.style.display = 'none';

  // role class must be lowercase to match your CSS: .role-farmer, .role-transporter, .role-admin
  grid.innerHTML = users.map(u => `
    <div class="user-card" id="card-${u.user_id}">
      <div class="user-card-header">
        <div>
          <div class="user-name">${u.full_name}</div>
          <span class="role-badge role-${u.role.toLowerCase()}">${u.role}</span>
        </div>
      </div>

      <div class="card-field">
        <span class="card-field-label">Email</span>
        <span class="card-field-value">${u.email}</span>
      </div>
      <div class="card-field">
        <span class="card-field-label">Contact</span>
        <span class="card-field-value">${u.contact || '—'}</span>
      </div>

      <div class="card-actions">
        <button class="btn-update" onclick="openEditModal('${u.user_id}', '${u.full_name}', '${u.email}', '${u.contact || ''}')">
          Edit
        </button>
        <button class="btn-delete" onclick="deleteUser('${u.user_id}')">
          Delete
        </button>
      </div>
    </div>
  `).join('');
}

// ── Search + Role Filter ─────────────────────────────────────────
document.getElementById('user-search').addEventListener('input', filterUsers);
document.getElementById('role-filter').addEventListener('change', filterUsers);

function filterUsers() {
  const search = document.getElementById('user-search').value.toLowerCase();
  const role   = document.getElementById('role-filter').value.toLowerCase();

  const filtered = allUsers.filter(u => {
    const matchSearch = u.full_name.toLowerCase().includes(search) ||
                        u.email.toLowerCase().includes(search);
    const matchRole   = role === 'all' || u.role.toLowerCase() === role;
    return matchSearch && matchRole;
  });

  renderUsers(filtered);
}

// ── Delete User ──────────────────────────────────────────────────
async function deleteUser(userId) {
  if (!confirm('Are you sure you want to delete this user?')) return;
  const res = await fetch(`${BASE}/admin/users/${userId}`, {
    method: 'DELETE',
    headers: authHeaders
  });
  if (res.ok) {
    allUsers = allUsers.filter(u => u.user_id !== userId);
    document.getElementById(`card-${userId}`)?.remove();
    if (!allUsers.length) {
      document.getElementById('users-empty').style.display = 'flex';
    }
  } else {
    alert('Failed to delete user.');
  }
}

// ── Edit Modal ───────────────────────────────────────────────────
let editingUserId = null;

function openEditModal(userId, name, email, contact) {
  editingUserId = userId;
  document.getElementById('edit-name').value  = name;
  document.getElementById('edit-email').value = email;
  document.getElementById('edit-phone').value = contact;
  document.getElementById('edit-location').value = '';
  document.getElementById('update-modal').classList.add('open');
}

function closeEditModal() {
  editingUserId = null;
  document.getElementById('update-modal').classList.remove('open');
}

document.getElementById('modal-close-btn').addEventListener('click', closeEditModal);
document.getElementById('modal-cancel-btn').addEventListener('click', closeEditModal);

document.getElementById('modal-save-btn').addEventListener('click', async () => {
  if (!editingUserId) return;

  const res = await fetch(`${BASE}/admin/users/${editingUserId}`, {
    method: 'PUT',
    headers: authHeaders,
    body: JSON.stringify({
      full_name: document.getElementById('edit-name').value,
      email:     document.getElementById('edit-email').value,
      contact:   document.getElementById('edit-phone').value
    })
  });

  if (res.ok) {
    closeEditModal();
    await loadUsersGrid(); // refresh so card shows updated info
  } else {
    alert('Failed to update user.');
  }
});

// ── Notifications: Tab switching ─────────────────────────────────
// Your HTML uses .notif-panel with display:none / .active for show
document.querySelectorAll('.notif-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.notif-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.notif-panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`panel-${tab.dataset.panel}`).classList.add('active');
  });
});

async function loadNotifications() {
  await Promise.all([loadCompletedTrips(), loadRatings()]);
}

// ── Notifications: Completed Trips ───────────────────────────────
async function loadCompletedTrips() {
  const list = document.getElementById('trips-list');
  try {
    const data = await apiFetch('/admin/completed-trips');

    if (!data.length) {
      list.innerHTML = '<p class="notif-sub" style="padding:1rem;">No completed trips yet.</p>';
      return;
    }

    list.innerHTML = data.map(t => `
      <div class="notif-item">
        <div class="notif-body">
          <div class="notif-text">
            ${t.pickup_location} → ${t.destination_location}
          </div>
          <div class="notif-sub">
            ${t.animal_quantity}x ${t.animal_type} &nbsp;·&nbsp; Pickup: ${t.pickup_date}
          </div>
        </div>
        <div class="notif-meta">
          <div class="notif-time">${new Date(t.accepted_at).toLocaleDateString()}</div>
        </div>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<p class="notif-sub" style="padding:1rem;">Could not load trips.</p>';
  }
}

// ── Notifications: Ratings ────────────────────────────────────────
// Rating fields: rating_id, booking_id, rating_by, rating_for, score, comment, created_at
async function loadRatings() {
  const list = document.getElementById('ratings-list');
  try {
    const data = await apiFetch('/admin/ratings');

    if (!data.length) {
      list.innerHTML = '<p class="notif-sub" style="padding:1rem;">No ratings yet.</p>';
      return;
    }

    list.innerHTML = data.map(r => `
      <div class="notif-item">
        <div class="notif-body">
          <div class="star-row">
            ${[1,2,3,4,5].map(i =>
              `<span class="star ${i <= r.score ? '' : 'empty'}">★</span>`
            ).join('')}
          </div>
          <div class="notif-text" style="margin-top:0.35rem;">
            ${r.comment || '<em style="color:#6b8a88">No comment left</em>'}
          </div>
          <div class="notif-sub">Booking #${r.booking_id.slice(0, 8)}…</div>
        </div>
        <div class="notif-meta">
          <div class="notif-time">${new Date(r.created_at).toLocaleDateString()}</div>
        </div>
      </div>
    `).join('');
  } catch {
    list.innerHTML = '<p class="notif-sub" style="padding:1rem;">Could not load ratings.</p>';
  }
}

// ── Section Switching ─────────────────────────────────────────────
function switchSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById(`section-${name}`).classList.add('active');
  document.getElementById(`nav-${name}`).classList.add('active');
}

// ── Sidebar (mobile) ──────────────────────────────────────────────
function toggleSidebar() {
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebar-overlay');
  const hamburger = document.getElementById('hamburger');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('open');
  hamburger.classList.toggle('open');
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-overlay').classList.remove('open');
  document.getElementById('hamburger').classList.remove('open');
}

// ── Logout ────────────────────────────────────────────────────────
function handleLogout() {
  sessionStorage.clear();
  window.location.href = '../more_html/login.html';
}

// ── Boot ──────────────────────────────────────────────────────────
// Show first notif panel on load
document.addEventListener('DOMContentLoaded', () => {
  const firstPanel = document.getElementById('panel-trips');
  if (firstPanel) firstPanel.classList.add('active');
});

Promise.all([
  loadStats(),
  loadRequestsChart(),
  loadStatusChart(),
  loadLocationsChart(),
  loadUsersGrid(),
  loadNotifications()
]).catch(err => console.error('Dashboard load error:', err));