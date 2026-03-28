<h1 align="center"> 🐄🚚 LIVESTOCK LINK </h1>

## 📋 Project Overview
Livestock Link is a web-based platform that connects farmers with livestock transporters in Rwanda, bringing structure and reliability to a system that has long relied on informal networks. Small-scale farmers often face major logistical challenges, with animals sometimes trekking long distances or being transported in unsafe conditions that increase mortality. Livestock Link solves this by providing a centralized platform where farmers can create transport requests, connect with available transporters, and track deliveries.

---

## 📹 Video Walkthrough & Live Deployment URL
* Link to Video Walkthrough - coming soon......
* Link to Live Deployment - [https://livestocklink.leonnsamba.tech](https://livestocklink.leonnsamba.tech)

---

## ⚙️ Tech Stack

| Layer        | Technology              |
|--------------|-------------------------|
| Frontend     | HTML, CSS, JavaScript   |
| Backend      | Python, Flask           |
| Database     | MySQL (hosted on Aiven) |
| ORM          | SQLAlchemy              |
| Auth         | JWT                     |
| Dev Tools    | APIdog, DataGrip, pytest|

---

## 📂 Project Structure
```
livestock-link/
├── backend/
│   ├── app.py            # Centralizes all endpoint routes under one server
│   ├── config.py
│   ├── models/           # Database table structure with SQLAlchemy
│   ├── routes/           # All API endpoint route files and respective logic
│   ├── utils/            # Authentication logic with JWT 
│   └── database/         # Run once to create tables within database hosted on Aiven
├── frontend/
│   ├── more_html/        # HTML skeleton for respective user dashboards
│   ├── more_css/         # Styling for resepctive user dashboards
│   └── more_js/          # JS logic for respective user dashboards
├── tests/                # Pytests for each routes file (API endpoint tests)
├── docs/                 # API Documentation, Deployment Guide, ERD & System Architecture
├── screenshots/          # APIdog endpoint testing images, Deployment guide images
├── conftest.py           # Sharing configuration across files and directories
├── .env.example         
├── requirements.txt
└── README.md
```

## 🎯 Getting / Prerequisites

- Python 3.10+
- pip
- A running MySQL instance or Aiven account
- An SSH key for server access (for deployment)

---

### 🛠️ Installation
```bash
git clone https://github.com/L-nsamba/LivestockLink.git
cd livestock-link
python3 -m venv virtual_env           # Creation of virtual environment
sourve virtual_env/bin/actviate       # Activating virtual environment
pip install -r requirements.txt       # Installing all requirements in virtual environment
```
### Environment Setup

Copy the example env file and fill in your credentials:
```bash
cp .env.example .env
```
```env
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=your_aiven_host
DB_PORT=3306
DB_NAME=livestock_link
DB_CA=/path/to/ca.pem
ADMIN_REGISTRATION_KEY=your_admin_registration_key
SECRET_KEY=your_jwt_secret
```
### ⚠️ Note
- Never commit your `.env` file or `ca.pem` to version control
- Both are listed in `.gitignore`
- When deploying to a new server transfer `ca.pem` manually via scp and recreate `.env` by hand 

### 📌 Database Setup

Run this once to create all tables:
```bash
python backend/models/db_setup.py
```

### Running Locally
```bash
cd backend
flask run
OR
python -m backend.app      # From the root directory
```
- Then open `frontend/index.html` in your browser using a local deployment extension like Live Server.
- API calls to `http://127.0.0.1:5000` by default

---

## 🌐 Live Deployment

Livestock Link is live and accessible at:

[https://livestocklink.leonnsamba.tech](https://livestocklink.leonnsamba.tech)

### 🛠️ Deployment Stack

| Component | Technology |
|-----------|------------|
| Web Server | Nginx 1.18 |
| WSGI Server | Gunicorn |
| SSL | Let's Encrypt (Certbot) |
| Hosting | Ubuntu 24 (AWS EC2) |
| Database | MySQL via Aiven Cloud |

### Deployment Overview
The application runs on a single Ubuntu server with Nginx acting as
a reverse proxy, serving the static files directly and forwarding all
`/api/` requests to Flask backend running on `127.0.0.1:5000` via Gunicorn

For the full step-by-step deployment guide refer to:
[docs/deployment.md](docs/deployment.md).

---

## 📋 API Documentation

Full API documentation is available in 
[docs/api_documentation.md](docs/api_documentation.md).

This includes the endpoints, requests/response formats, authentication
requirements, and example payloads. APIdog was used for the GUI testing
and all screenshots are avaliable in the [screenshots/](screenshots/) folder.

### 📝 Quick Reference

#### Auth
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login | No |
| POST | `/api/auth/logout` | Logout | Yes |

#### Transport Requests
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/requests/` | Create transport request | Yes (Farmer) |
| GET | `/api/requests/` | Get all pending requests | Yes (Transporter) |
| GET | `/api/requests/farmer/<id>` | Get farmer's requests | Yes (Farmer) |
| PUT | `/api/requests/<id>` | Update a request | Yes (Farmer) |
| DELETE | `/api/requests/<id>` | Cancel a request | Yes (Farmer) |

#### Bookings
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/bookings/` | Accept a request | Yes (Transporter) |
| GET | `/api/bookings/transporter/<id>` | Get transporter jobs | Yes (Transporter) |
| PUT | `/api/bookings/<id>/status` | Update delivery status | Yes (Transporter) |

#### Ratings
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/ratings/` | Submit a rating | Yes (Farmer) |
| GET | `/api/ratings/transporter/<id>` | Get transporter ratings | Yes |

#### Admin
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/users` | View all users | Yes (Admin) |
| GET | `/api/admin/requests` | View all requests | Yes (Admin) |
| GET | `/api/admin/bookings` | View all bookings | Yes (Admin) |
| PUT | `/api/admin/users/<id>/deactivate` | Deactivate user | Yes (Admin) |
| DELETE | `/api/admin/users/<id>` | Delete user | Yes (Admin) |

---

## ✅ Testing
```bash
pytest tests/
```

| Test File | Coverage |
|-----------|----------|
| `test_admin.py` | Admin Registration, login, logout |
| `test_auth_api.py` | Farmer / Transporter Registration, login, logout |
| `test_transport_request.py` | Request CRUD operations |
| `test_booking_api.py` | Booking creation and status updates |
| `test_ratings.py` | Rating submission and retrieval |
| `test_admin.py` | Admin routes and access control |

---

### 🏅 Contributors
-  [**Leon Nsamba**](https://github.com/L-nsamba)
-  [**Mufaro Kunze Victoria**](https://github.com/mufaro-k07)
-  [**Mitchell Barure**](https://github.com/MitchellBarure)
-  [**Michael Okinyi Odhiambo**](https://github.com/Mich-O)
-  [**Queen Ruth Uwera**](https://github.com/Queenu-7)
-  [**Lincoln Keza Batsinduka**](https://github.com/Lincoln-code0)
