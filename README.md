<h1 align="center"> 🐄🚚 LIVESTOCK LINK </h1>

## 📋 PROJECT OVERVIEW
Livestock Link is a web-based platform that connects farmers with livestock transporters in Rwanda, bringing structure and reliability to a system that has long relied on informal networks. Small-scale farmers often face major logistical challenges, with animals sometimes trekking long distances or being transported in unsafe conditions that increase mortality. Livestock Link solves this by providing a centralized platform where farmers can create transport requests, connect with available transporters, and track deliveries.

## 📹 VIDEO WALKTHROUGH
* Link to Video Walkthrough - coming soon......

## ⚙️ TECH STACK

| Layer        | Technology              |
|--------------|-------------------------|
| Frontend     | HTML, CSS, JavaScript   |
| Backend      | Python, Flask           |
| Database     | MySQL (hosted on Aiven) |
| ORM          | SQLAlchemy              |
| Auth         | JWT                     |
| Dev Tools    | APIdog, DataGrip, pytest|

<br>

## 📂 PROJECT STRUCTURE
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
├── docs/                 # API Documentation, ERD & System Architecture
├── screenshots/          
├── conftest.py           # Sharing configuration across files and directories
├── .env.example         
├── requirements.txt
└── README.md
```

## GETTING STARTED / PREREQUISITES

- Python 3.10+
- pip
- A running MySQL instance or Aiven account

### Installation
```bash
git clone https://github.com/L-nsamba/LivestockLink.git
cd livestock-link
pip install -r requirements.txt
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
### Database Setup

Run this once to create all tables:
```bash
python backend/models/db_setup.py
```

### Running the App
```bash
cd backend
flask run
```
Then open `frontend/index.html` in your browser.

---

### TO  BE CONTINUED (README IN PROGRESS...) 🚧


### 👥 TEAM MEMBERS
1. Leon Nsamba
2. Mitchell Barure
3. Mufaro Victoria Kunze
4. Queen Uwera Ruth
5. Michael Okinyi Odhiambo
6. Batsinduka Keza Lincoln
