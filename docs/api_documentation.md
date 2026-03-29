# LivestockLink Backend API Documentation

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Environment Variables](#environment-variables)
4. [Database Models & Schemas](#database-models--schemas)
5. [Authentication & Authorization](#authentication--authorization)
6. [API Endpoints](#api-endpoints)
    - [Authentication](#authentication-endpoints)
    - [Transport Requests](#transport-request-endpoints)
    - [Bookings](#booking-endpoints)
    - [Ratings](#rating-endpoints)
    - [Admin](#admin-endpoints)
7. [State Flows & Business Logic](#state-flows--business-logic)
8. [Error Handling](#error-handling)
9. [Utility Functions & Charts](#utility-functions--charts)
10. [Database Setup](#database-setup)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Flask 3.1.3 |
| ORM | SQLAlchemy 2.0.48 |
| Database | MySQL (hosted on Aiven) |
| Authentication | JWT via PyJWT 2.12.1 |
| Password Hashing | bcrypt 5.0.0 |
| CORS | flask-cors 6.0.2 |
| Python | 3.10+ |
| API Format | REST / JSON |

---

## Project Structure

```
backend/
├── app.py                              # Flask app factory, blueprint registration
├── config.py                           # Configuration (currently empty)
├── database/
│   ├── __init__.py
│   ├── db.py                           # SQLAlchemy engine, Base, Session setup
│   └── database_setup.py               # Script to create all tables
├── models/
│   ├── __init__.py
│   ├── user.py                         # Base user table
│   ├── farmer.py                       # Farmer-specific profile fields
│   ├── transporter.py                  # Transporter-specific profile fields
│   ├── transport_request.py            # Transport request model
│   ├── booking.py                      # Booking model
│   └── rating.py                       # Rating model
├── routes/
│   ├── __init__.py
│   ├── auth_api.py                     # Register, login, logout
│   ├── transport_requests_api.py       # Transport request CRUD
│   ├── bookings_api.py                 # Booking management
│   ├── ratings_api.py                  # Rating CRUD
│   └── admin.py                        # Admin dashboard & user management
├── utils/
│   ├── auth_decorator.py               # require_role() decorator, get_current_user_id()
│   └── jwt_utils.py                    # JWT generation & verification
└── charts/
    ├── __init__.py
    ├── requests_vs_dates.py            # Requests per day/month charts
    ├── status_breakdown.py             # Status distribution charts
    └── top_pickup_locations.py         # Location frequency charts
```

---

## Environment Variables

All environment variables are required unless noted as optional.

| Variable | Description |
|----------|-------------|
| `DB_USER` | MySQL username |
| `DB_PASS` | MySQL password |
| `DB_HOST` | Aiven MySQL host URL |
| `DB_PORT` | MySQL port (typically `3306`) |
| `DB_NAME` | Database name |
| `DB_CA` | Path to SSL CA certificate |
| `ADMIN_REGISTRATION_KEY` | Secret key required to register an admin account |
| `JWT_SECRET_KEY` | Secret used to sign/verify JWT tokens |

---

## Database Models & Schemas

### User (`users`)

The base identity table for all roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | CHAR(36) | PK | UUID, auto-generated |
| `full_name` | VARCHAR(100) | NOT NULL | |
| `contact` | VARCHAR(25) | NOT NULL | Phone or contact number |
| `password_hash` | VARCHAR(225) | NOT NULL | bcrypt hash |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | |
| `role` | ENUM | NOT NULL | `FARMER`, `TRANSPORTER`, or `ADMIN` |
| `created_at` | DATETIME | DEFAULT UTC now | |

---

### Farmer (`farmer`)

Extends `users` for farmer-specific data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | CHAR(36) | PK, FK → `users.user_id` | |
| `farm_location` | VARCHAR(200) | NOT NULL | |
| `created_at` | DATETIME | DEFAULT UTC now | |

---

### Transporter (`transporter`)

Extends `users` for transporter-specific data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | CHAR(36) | PK, FK → `users.user_id` | |
| `vehicle_type` | VARCHAR(100) | NOT NULL | |
| `vehicle_capacity` | INTEGER | NOT NULL | |
| `license_number` | VARCHAR(50) | UNIQUE, NOT NULL | |
| `organization_name` | VARCHAR(150) | Nullable | |
| `created_at` | DATETIME | DEFAULT UTC now | |

---

### Transport Request (`transport_requests`)

A farmer's request to transport livestock.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `request_id` | CHAR(36) | PK | UUID, auto-generated |
| `farmer_id` | CHAR(36) | FK → `users.user_id`, NOT NULL | |
| `pickup_location` | VARCHAR(150) | NOT NULL | |
| `destination_location` | VARCHAR(150) | NOT NULL | |
| `pickup_date` | DATETIME | NOT NULL | |
| `animal_type` | VARCHAR(50) | NOT NULL | |
| `animal_quantity` | INTEGER | NOT NULL | |
| `status` | ENUM | DEFAULT `PENDING` | `PENDING`, `BOOKED`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED` |
| `notes` | TEXT | Nullable | |
| `created_at` | DATETIME | DEFAULT UTC now | |

---

### Booking (`bookings`)

Created when a transporter accepts a transport request.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `booking_id` | CHAR(36) | PK | UUID, auto-generated |
| `request_id` | CHAR(36) | UNIQUE, FK → `transport_requests.request_id`, NOT NULL | One booking per request |
| `transporter_id` | CHAR(36) | FK → `users.user_id`, NOT NULL | |
| `accepted_at` | DATETIME | DEFAULT UTC now, NOT NULL | |
| `status` | ENUM | DEFAULT `ACCEPTED` | `ACCEPTED`, `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `CANCELLED` |

Relationships:
- `transport_request` — 1:1 with TransportRequest
- `ratings` — 1:many with Rating

---

### Rating (`ratings`)

A farmer's rating of a transporter after delivery.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `rating_id` | CHAR(36) | PK | UUID, auto-generated |
| `booking_id` | CHAR(36) | FK → `bookings.booking_id`, NOT NULL | |
| `rating_by` | CHAR(36) | FK → `users.user_id`, NOT NULL | The farmer who gave the rating |
| `rating_for` | CHAR(36) | FK → `users.user_id`, NOT NULL | The transporter being rated |
| `score` | INTEGER | NOT NULL | 1–5 scale |
| `comment` | TEXT | Nullable | |
| `created_at` | DATETIME | DEFAULT UTC now | |

Relationships:
- `booking` — links back to the associated Booking
- `rater` — User who submitted the rating
- `rated_user` — User who received the rating

---

## Authentication & Authorization

### JWT Tokens

Generated on successful register or login. Must be included in the `Authorization` header for all protected endpoints.

```
Authorization: Bearer <token>
```

**Token Payload:**
```json
{
  "user_id": "uuid",
  "role": "FARMER | TRANSPORTER | ADMIN",
  "exp": "unix timestamp (8 hours from issue)"
}
```

- **Algorithm:** HS256
- **Expiry:** 8 hours
- **Secret:** `JWT_SECRET_KEY` environment variable

### `@require_role(*roles)` Decorator

Applied to protected routes. Validates the `Authorization` header, decodes the JWT, and checks that the token's role is in the allowed set.

| Condition | Status | Response |
|-----------|--------|----------|
| Missing or malformed `Authorization` header | 401 | `{"error": "Missing or invalid authorization header"}` |
| Token expired | 401 | `{"error": "Token expired"}` |
| Invalid token signature | 401 | `{"error": "Invalid token"}` |
| Role not in allowed roles | 403 | `{"error": "Insufficient permissions"}` |

### `get_current_user_id()`

Helper function that reads the `Authorization` header from the current request context and returns the `user_id` from the decoded JWT payload. Used for ownership checks (e.g., ensuring a farmer can only access their own requests).

### Password Security

- Passwords are hashed with `bcrypt.hashpw(password, bcrypt.gensalt())` before storage.
- Verified with `bcrypt.checkpw(provided_password, stored_hash)` on login.
- Raw passwords are never stored or returned.

---

## API Endpoints

> **Base URL:** All endpoints are prefixed with `/api` unless otherwise noted.

---

### Authentication Endpoints

**Blueprint prefix:** none (routes define full path starting with `/api/auth`)

---

#### `POST /api/auth/register`

Register a new farmer or transporter. Automatically creates a role-specific profile record.

**Auth Required:** No

**Request Body:**

```json
{
  "full_name": "string",
  "contact": "string",
  "email": "string",
  "password": "string",
  "role": "FARMER | TRANSPORTER",

  // Required if role == "FARMER"
  "farm_location": "string",

  // Required if role == "TRANSPORTER"
  "vehicle_type": "string",
  "vehicle_capacity": "integer",
  "license_number": "string",
  "organization_name": "string (optional)"
}
```

**Success Response `201`:**

```json
{
  "message": "User created",
  "token": "jwt_token_string",
  "user": {
    "user_id": "uuid",
    "full_name": "string",
    "email": "string",
    "role": "FARMER | TRANSPORTER",
    "farmer_id": "uuid (only if FARMER)",
    "transporter_id": "uuid (only if TRANSPORTER)"
  }
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing required fields |
| 403 | Attempting to register as `ADMIN` |
| 409 | Email already registered |
| 500 | Server error |

---

#### `POST /api/auth/login`

Authenticate an existing user and receive a JWT token.

**Auth Required:** No

**Request Body:**

```json
{
  "email": "string",
  "password": "string",
  "role": "FARMER | TRANSPORTER | ADMIN"
}
```

**Success Response `200`:**

```json
{
  "message": "Login successful",
  "token": "jwt_token_string",
  "user": {
    "user_id": "uuid",
    "full_name": "string",
    "email": "string",
    "role": "string",
    "farmer_id": "uuid (only if FARMER)",
    "transporter_id": "uuid (only if TRANSPORTER)"
  }
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing email, password, or role |
| 401 | Invalid credentials (wrong password, wrong role, or user not found) |
| 500 | Server error |

---

#### `POST /api/auth/logout`

Stateless logout. The backend does not invalidate the token — the client is expected to discard it.

**Auth Required:** No

**Success Response `200`:**

```json
{
  "message": "User logged out successfully"
}
```

---

### Transport Request Endpoints

**Blueprint prefix:** none (routes define full path starting with `/api/requests`)

---

#### `POST /api/requests`

Create a new transport request.

**Auth Required:** Yes — `FARMER` only

**Request Body:**

```json
{
  "pickup_location": "string",
  "destination_location": "string",
  "pickup_date": "ISO 8601 datetime string",
  "animal_type": "string",
  "animal_quantity": "integer",
  "notes": "string (optional)"
}
```

**Success Response `201`:**

```json
{
  "message": "Request created",
  "request_id": "uuid"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing required fields |
| 401 | Missing or invalid token |
| 500 | Server error |

---

#### `GET /api/requests`

Retrieve all transport requests with status `PENDING`. Intended for transporters to browse available jobs.

**Auth Required:** Yes — `TRANSPORTER` only

**Success Response `200`:**

```json
[
  {
    "request_id": "uuid",
    "farmer_id": "uuid",
    "farmer_name": "string",
    "pickup_location": "string",
    "destination_location": "string",
    "pickup_date": "ISO datetime string",
    "animal_type": "string",
    "animal_quantity": "integer",
    "status": "PENDING",
    "notes": "string | null",
    "created_at": "ISO datetime string"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Insufficient permissions |
| 500 | Server error |

---

#### `GET /api/requests/farmer/<farmer_id>`

Retrieve all transport requests belonging to a specific farmer, including booking and transporter details if applicable.

**Auth Required:** Yes — `FARMER` only

**Authorization:** The authenticated farmer's `user_id` must match `farmer_id` in the path.

**Success Response `200`:**

```json
[
  {
    "request_id": "uuid",
    "farmer_id": "uuid",
    "pickup_location": "string",
    "destination_location": "string",
    "pickup_date": "ISO datetime string",
    "animal_type": "string",
    "animal_quantity": "integer",
    "status": "PENDING | BOOKED | IN_TRANSIT | DELIVERED | CANCELLED",
    "notes": "string | null",
    "created_at": "ISO datetime string",
    "booking_id": "uuid | null",
    "transporter_id": "uuid | null",
    "transporter_name": "string | null",
    "license_number": "string | null"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Authenticated user is not the owner (`farmer_id` mismatch) |
| 500 | Server error |

---

#### `PUT /api/requests/<request_id>`

Update fields of a transport request. Only `PENDING` requests can be modified.

**Auth Required:** Yes — `FARMER` only

**Authorization:** The authenticated farmer must own the request.

**Request Body:** All fields are optional; only provided fields are updated.

```json
{
  "pickup_location": "string",
  "destination_location": "string",
  "pickup_date": "ISO 8601 datetime string",
  "animal_type": "string",
  "animal_quantity": "integer",
  "notes": "string"
}
```

**Success Response `200`:**

```json
{
  "message": "Request updated"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Request is not in `PENDING` status |
| 400 | No valid fields provided to update |
| 401 | Missing or invalid token |
| 403 | Authenticated user does not own the request |
| 404 | Request not found |
| 500 | Server error |

---

#### `DELETE /api/requests/<request_id>`

Cancel a transport request. Sets status to `CANCELLED`. Only `PENDING` requests can be cancelled this way.

**Auth Required:** Yes — `FARMER` only

**Authorization:** The authenticated farmer must own the request.

**Success Response `200`:**

```json
{
  "message": "Request cancelled"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Request is not in `PENDING` status |
| 401 | Missing or invalid token |
| 403 | Authenticated user does not own the request |
| 404 | Request not found |
| 500 | Server error |

---

### Booking Endpoints

**Blueprint prefix:** `/api` (routes then add `/bookings/...`)

---

#### `POST /api/bookings`

Accept a transport request by creating a booking. Sets the associated transport request status to `BOOKED`.

**Auth Required:** Yes — `TRANSPORTER` only

**Request Body:**

```json
{
  "request_id": "uuid"
}
```

**Success Response `201`:**

```json
{
  "message": "Booking created successfully",
  "booking_id": "uuid"
}
```

**Side Effects:**
- `transport_requests.status` → `BOOKED`

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing `request_id` |
| 400 | Transport request is not in `PENDING` status |
| 400 | Transport request is already booked |
| 401 | Missing or invalid token |
| 403 | Insufficient permissions |
| 404 | Transport request not found |
| 500 | Server error |

---

#### `GET /api/bookings/transporter/<transporter_id>`

Retrieve all bookings for a specific transporter, enriched with the associated transport request details.

**Auth Required:** Yes — `TRANSPORTER` only

**Authorization:** The authenticated transporter's `user_id` must match `transporter_id` in the path.

**Success Response `200`:**

```json
[
  {
    "booking_id": "uuid",
    "request_id": "uuid",
    "transporter_id": "uuid",
    "accepted_at": "ISO datetime string",
    "status": "ACCEPTED | PICKED_UP | IN_TRANSIT | DELIVERED | CANCELLED",
    "farmer_id": "uuid",
    "farmer_name": "string",
    "pickup_location": "string",
    "destination_location": "string",
    "pickup_date": "ISO datetime string",
    "animal_type": "string",
    "animal_quantity": "integer",
    "notes": "string | null"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Authenticated user is not the owner (`transporter_id` mismatch) |
| 500 | Server error |

---

#### `GET /api/bookings/<booking_id>`

Retrieve a single booking by ID.

**Auth Required:** Yes — `TRANSPORTER` only

**Authorization:** The authenticated transporter must own the booking.

**Success Response `200`:**

```json
{
  "booking_id": "uuid",
  "request_id": "uuid",
  "transporter_id": "uuid",
  "accepted_at": "ISO datetime string",
  "status": "ACCEPTED | PICKED_UP | IN_TRANSIT | DELIVERED | CANCELLED"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Authenticated user does not own the booking |
| 404 | Booking not found |
| 500 | Server error |

---

#### `PUT /api/bookings/<booking_id>`

Update the status of a booking. Advancing the booking status also syncs the associated transport request status.

**Auth Required:** Yes — `TRANSPORTER` only

**Authorization:** The authenticated transporter must own the booking.

**Request Body:**

```json
{
  "status": "ACCEPTED | PICKED_UP | IN_TRANSIT | DELIVERED | CANCELLED"
}
```

**Success Response `200`:**

```json
{
  "message": "Booking status updated successfully"
}
```

**Side Effects by status value:**

| Booking Status Set | Transport Request Status Synced To |
|--------------------|------------------------------------|
| `IN_TRANSIT` | `IN_TRANSIT` |
| `DELIVERED` | `DELIVERED` |
| `CANCELLED` | `PENDING` (re-opens the request for other transporters) |

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing `status` field |
| 400 | Invalid status value |
| 401 | Missing or invalid token |
| 403 | Authenticated user does not own the booking |
| 404 | Booking not found |
| 500 | Server error |

---

#### `DELETE /api/bookings/<booking_id>`

Cancel a booking. The associated transport request reverts to `PENDING`. Cannot cancel a delivered booking.

**Auth Required:** Yes — `TRANSPORTER` only

**Authorization:** The authenticated transporter must own the booking.

**Success Response `200`:**

```json
{
  "message": "Booking cancelled successfully"
}
```

**Side Effects:**
- `transport_requests.status` → `PENDING`

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Booking is already `DELIVERED` (cannot be cancelled) |
| 401 | Missing or invalid token |
| 403 | Authenticated user does not own the booking |
| 404 | Booking not found |
| 500 | Server error |

---

### Rating Endpoints

**Blueprint prefix:** none (routes define full path starting with `/api/ratings`)

---

#### `POST /api/ratings`

Submit a rating for a transporter after a delivered booking.

**Auth Required:** Yes — `FARMER` only

**Request Body:**

```json
{
  "booking_id": "uuid",
  "score": "integer (1–5)",
  "comment": "string (optional)"
}
```

**Success Response `201`:**

```json
{
  "message": "Rating created",
  "rating_id": "uuid"
}
```

**Validation Rules:**
- The booking must have status `DELIVERED`.
- The authenticated farmer must be the farmer in the associated transport request.
- A farmer cannot rate the same booking more than once.
- Score must be an integer between 1 and 5 inclusive.

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing `score` field |
| 400 | Score is not between 1 and 5 |
| 400 | Farmer has already rated this booking |
| 403 | No delivered booking found for the given ID, or the farmer does not own the booking |
| 401 | Missing or invalid token |
| 500 | Server error |

---

#### `GET /api/ratings/transporter/<transporter_id>`

Retrieve all ratings received by a specific transporter.

**Auth Required:** No

**Success Response `200`:**

```json
[
  {
    "rating_id": "uuid",
    "booking_id": "uuid",
    "rating_by": "uuid",
    "score": "integer",
    "comment": "string | null"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 500 | Server error |

---

#### `GET /api/ratings/farmer/<farmer_id>`

Retrieve all ratings submitted by a specific farmer.

**Auth Required:** Yes — `FARMER` only

**Authorization:** The authenticated farmer's `user_id` must match `farmer_id` in the path.

**Success Response `200`:**

```json
[
  {
    "rating_id": "uuid",
    "booking_id": "uuid",
    "rating_for": "uuid",
    "score": "integer",
    "comment": "string | null"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Authenticated user is not the owner (`farmer_id` mismatch) |
| 500 | Server error |

---

#### `GET /api/ratings/<rating_id>`

Retrieve a single rating by ID.

**Auth Required:** No

**Success Response `200`:**

```json
{
  "rating_id": "uuid",
  "booking_id": "uuid",
  "rating_by": "uuid",
  "rating_for": "uuid",
  "score": "integer",
  "comment": "string | null"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 404 | Rating not found |
| 500 | Server error |

---

#### `PUT /api/ratings/<rating_id>`

Update an existing rating's score and/or comment.

**Auth Required:** Yes — `FARMER` only

**Authorization:** Only the farmer who submitted the rating can edit it.

**Request Body:** All fields optional; only provided fields are updated.

```json
{
  "score": "integer (1–5)",
  "comment": "string"
}
```

**Success Response `200`:**

```json
{
  "message": "Rating updated"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Provided `score` is not between 1 and 5 |
| 401 | Missing or invalid token |
| 403 | Authenticated user is not the rating author |
| 404 | Rating not found |
| 500 | Server error |

---

#### `DELETE /api/ratings/<rating_id>`

Delete a rating.

**Auth Required:** Yes — `FARMER` only

**Authorization:** Only the farmer who submitted the rating can delete it.

**Success Response `200`:**

```json
{
  "message": "Rating deleted"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 401 | Missing or invalid token |
| 403 | Authenticated user is not the rating author |
| 404 | Rating not found |
| 500 | Server error |

---

### Admin Endpoints

**Blueprint prefix:** none (routes define full path starting with `/api/admin`)

All admin endpoints except `POST /api/admin/register` require a valid `ADMIN` JWT token.

---

#### `POST /api/admin/register`

Register a new admin account. Requires a secret key set in the environment.

**Auth Required:** No

**Request Body:**

```json
{
  "full_name": "string",
  "contact": "string",
  "email": "string",
  "password": "string",
  "admin_key": "string"
}
```

The `admin_key` must match the `ADMIN_REGISTRATION_KEY` environment variable exactly.

**Success Response `201`:**

```json
{
  "message": "Admin created",
  "token": "jwt_token_string",
  "user": {
    "user_id": "uuid",
    "full_name": "string",
    "email": "string",
    "role": "ADMIN"
  }
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Missing required fields |
| 403 | Invalid `admin_key` |
| 409 | Email already registered |
| 500 | Server error |

---

#### `GET /api/admin/users`

Retrieve all registered users across all roles, including role-specific profile fields.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
[
  {
    "user_id": "uuid",
    "full_name": "string",
    "email": "string",
    "contact": "string",
    "role": "FARMER | TRANSPORTER | ADMIN",
    "created_at": "DD MMM YYYY",

    // FARMER-specific
    "farm_location": "string",

    // TRANSPORTER-specific
    "vehicle_type": "string",
    "vehicle_capacity": "integer",
    "license_number": "string",
    "organization_name": "string | null"
  }
]
```

> `created_at` is returned as a human-readable string (e.g., `"28 Mar 2025"`), not an ISO timestamp.

---

#### `GET /api/admin/users/<user_id>`

Retrieve a single user by ID.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "user_id": "uuid",
  "full_name": "string",
  "email": "string",
  "role": "FARMER | TRANSPORTER | ADMIN"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 404 | User not found |

---

#### `PUT /api/admin/users/<user_id>`

Update a user's base or profile fields. Supports updating both `users` table fields and role-specific profile fields in a single request.

**Auth Required:** Yes — `ADMIN` only

**Request Body:** All fields optional.

```json
{
  "full_name": "string",
  "email": "string",
  "contact": "string",

  // FARMER profile fields
  "farm_location": "string",

  // TRANSPORTER profile fields
  "vehicle_type": "string",
  "vehicle_capacity": "integer",
  "license_number": "string",
  "organization_name": "string"
}
```

**Success Response `200`:**

```json
{
  "message": "User updated"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 404 | User not found |

---

#### `DELETE /api/admin/users/<user_id>`

Delete a user and all associated data.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "message": "User deleted"
}
```

**Side Effects (cascade):**
- Ratings where `rating_by == user_id` or `rating_for == user_id`
- Bookings where `transporter_id == user_id`
- Transport requests where `farmer_id == user_id`
- The farmer or transporter profile record

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 404 | User not found |
| 500 | Server error |

---

#### `GET /api/admin/bookings`

Retrieve all bookings across the platform, enriched with transporter and farmer names.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
[
  {
    "booking_id": "uuid",
    "transporter_id": "uuid",
    "transporter_name": "string",
    "farmer_id": "uuid",
    "farmer_name": "string",
    "pickup_location": "string",
    "destination_location": "string",
    "animal_type": "string",
    "animal_quantity": "integer",
    "status": "ACCEPTED | PICKED_UP | IN_TRANSIT | DELIVERED | CANCELLED",
    "accepted_at": "ISO datetime string"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 500 | Server error |

---

#### `GET /api/admin/ratings`

Retrieve all ratings across the platform, enriched with rater and rated user names.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
[
  {
    "rating_id": "uuid",
    "booking_id": "uuid",
    "rating_by": "uuid",
    "rating_by_name": "string",
    "rating_for": "uuid",
    "rating_for_name": "string",
    "score": "integer",
    "comment": "string | null",
    "created_at": "ISO datetime string"
  }
]
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 500 | Server error |

---

#### `GET /api/admin/stats`

High-level platform statistics for the admin dashboard.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "total_users": "integer",
  "active_requests": "integer (count of transport_requests with status PENDING)",
  "completed_trips": "integer (count of transport_requests with status DELIVERED)"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 500 | Server error |

---

#### `GET /api/admin/charts/requests-per-day`

Returns the number of transport requests created per calendar day for chart rendering.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "labels": ["YYYY-MM-DD", "YYYY-MM-DD", "..."],
  "data": [3, 7, 2, "..."]
}
```

---

#### `GET /api/admin/charts/status-breakdown`

Returns the count of transport requests grouped by status.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "labels": ["PENDING", "BOOKED", "IN_TRANSIT", "DELIVERED", "CANCELLED"],
  "data": [12, 5, 3, 20, 2]
}
```

---

#### `GET /api/admin/charts/booking-status-breakdown`

Returns the count of bookings grouped by status.

**Auth Required:** Yes — `ADMIN` only

**Success Response `200`:**

```json
{
  "labels": ["ACCEPTED", "PICKED_UP", "IN_TRANSIT", "DELIVERED", "CANCELLED"],
  "data": [4, 2, 1, 18, 3]
}
```

---

#### `GET /api/admin/charts/top-pickup-locations`

Returns the most frequently used pickup locations.

**Auth Required:** Yes — `ADMIN` only

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `4` | Number of top locations to return |

**Success Response `200`:**

```json
{
  "labels": ["Nairobi", "Eldoret", "Nakuru", "Kisumu"],
  "data": [23, 18, 12, 9]
}
```

---

#### `GET /api/admin/charts/top-destination-locations`

Returns the most frequently used destination locations.

**Auth Required:** Yes — `ADMIN` only

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `4` | Number of top destinations to return |

**Success Response `200`:**

```json
{
  "labels": ["Mombasa", "Nairobi", "Thika", "Kisii"],
  "data": [19, 15, 11, 7]
}
```

---

## State Flows & Business Logic

### Transport Request Lifecycle

```
PENDING ──(transporter books)──► BOOKED
                                    │
                        ┌───────────┴────────────┐
                        ▼                        ▼
                   IN_TRANSIT             CANCELLED
                        │               (transport request reverts to PENDING)
                        ▼
                    DELIVERED
```

Transport request status is managed by two actors:
- **Farmer** — can cancel (`DELETE /api/requests/<id>`) only while `PENDING`.
- **Transporter** — drives status forward by updating booking status via `PUT /api/bookings/<id>`.

### Booking Status Sync

Booking status changes cascade to the parent transport request:

| Booking Status Updated To | Transport Request Status Becomes |
|---------------------------|----------------------------------|
| `IN_TRANSIT` | `IN_TRANSIT` |
| `DELIVERED` | `DELIVERED` |
| `CANCELLED` | `PENDING` |

### Rating Constraints

| Rule | Detail |
|------|--------|
| Only `DELIVERED` bookings can be rated | Status check on booking before creating rating |
| Farmers can only rate their own deliveries | Cross-checks `farmer_id` on the transport request |
| One rating per booking per farmer | Duplicate check before insert |
| Only the rating author can edit or delete their rating | `rating_by == current_user_id` check |

### Authorization Summary

| Endpoint Pattern | Allowed Roles | Ownership Enforced |
|------------------|---------------|-------------------|
| Create transport request | FARMER | — |
| View all PENDING requests | TRANSPORTER | — |
| View/edit/delete own requests | FARMER | `farmer_id == current_user_id` |
| Create booking | TRANSPORTER | — |
| View/update/delete own bookings | TRANSPORTER | `transporter_id == current_user_id` |
| Submit rating | FARMER | Must own the booking's transport request |
| Edit/delete rating | FARMER | `rating_by == current_user_id` |
| View transporter ratings | Public | — |
| All admin endpoints | ADMIN | — |

---

## Error Handling

### Standard Error Response Shape

All error responses return JSON with a single `error` key:

```json
{
  "error": "descriptive message"
}
```

### HTTP Status Code Reference

| Code | Meaning | Typical Trigger |
|------|---------|-----------------|
| `200` | OK | Successful read/update/delete |
| `201` | Created | Successful resource creation |
| `400` | Bad Request | Missing fields, invalid values, invalid state transition |
| `401` | Unauthorized | Missing, expired, or invalid JWT token |
| `403` | Forbidden | Valid token but wrong role or ownership mismatch |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Duplicate email on registration |
| `500` | Internal Server Error | Unhandled exception |

---

## Utility Functions & Charts

### JWT Utilities (`backend/utils/jwt_utils.py`)

```python
generate_token(user_id: str, role: str) -> str
# Creates a signed JWT with user_id, role, and exp (8h from now)
# Algorithm: HS256, Secret: JWT_SECRET_KEY

decode_token(token: str) -> dict
# Decodes and verifies a JWT
# Returns: {"user_id": str, "role": str, "exp": int}
# Raises: jwt.ExpiredSignatureError, jwt.InvalidTokenError
```

### Chart Utilities (`backend/charts/`)

All chart functions query the database directly and return a consistent shape:

```python
{"labels": [str, ...], "data": [int, ...]}
```

| Function | Module | Description |
|----------|--------|-------------|
| `get_requests_per_day()` | `requests_vs_dates.py` | Transport request count grouped by day |
| `get_requests_per_month()` | `requests_vs_dates.py` | Transport request count grouped by month |
| `get_request_status_breakdown()` | `status_breakdown.py` | Transport request count per status value |
| `get_booking_status_breakdown()` | `status_breakdown.py` | Booking count per status value |
| `get_top_pickup_locations(limit=4)` | `top_pickup_locations.py` | Most common pickup locations |
| `get_top_destination_locations(limit=4)` | `top_pickup_locations.py` | Most common destination locations |

---

## Database Setup

Run once to create all tables in the correct dependency order:

```bash
python backend/database/database_setup.py
```

**Table creation order:**
1. `users`
2. `farmer`
3. `transporter`
4. `transport_requests`
5. `bookings`
6. `ratings`

The database connection uses SSL (Aiven-hosted MySQL). The CA certificate path is provided via the `DB_CA` environment variable. The SQLAlchemy engine is configured with `ssl_ca` in the connection arguments.

### Session Management

The project uses a scoped session factory (`sessionmaker`) bound to the SQLAlchemy engine. Each route imports and uses `Session` from `backend/database/db.py`. Sessions are committed or rolled back and closed within each route handler.
