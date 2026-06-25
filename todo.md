

## AUTH/RBAC SYSTEM OVERHAUL

### 12. Security Hardening — Critical Fixes

**Files:** `fastapi_admin/api/auth.py`, `fastapi_admin/auth/views.py`, `fastapi_admin/router.py`, new files

**Problem:** Multiple security gaps: hardcoded JWT secret, no CSRF protection, no rate limiting on login, no password strength validation, `validate-field` endpoint has no auth.

#### Phase 1: Fix Hardcoded JWT Secret

- [ ] 1.1 Update `fastapi_admin/api/auth.py`
  - Remove `_DEFAULT_SECRET = "admin-api-secret-change-me"`
  - Raise `HTTPException(500)` if no `secret_key` configured — never use fallback
  - Validate `secret_key` minimum length (32 chars) at startup

- [ ] 1.2 Update `fastapi_admin/admin/core.py`
  - Add secret_key validation in `setup()` — raise `ConfigError` if empty or too short

#### Phase 2: Add CSRF Protection

- [x] 2.1 Create `fastapi_admin/auth/csrf.py`
  - `generate_csrf_token(session_payload: dict) -> str` — HMAC of session user_id + timestamp
  - `validate_csrf_token(request: Request, token: str) -> bool` — verify token from form body
  - Token embedded in signed cookie, validated on every POST

- [x] 2.2 Update `fastapi_admin/auth/dependencies.py`
  - Add `require_csrf_token` dependency for state-changing POST routes
  - Read CSRF token from form body, compare against cookie-stored token

- [x] 2.3 Update `fastapi_admin/auth/views.py`
  - Set CSRF cookie on GET /login, validate on POST /login and POST /logout

- [x] 2.4 Update `fastapi_admin/views/roles.py`
  - Add CSRF token to role create/edit/delete POST handlers

- [x] 2.5 Update `fastapi_admin/router.py`
  - Add CSRF validation to model create/edit/delete/bulk POST routes

- [x] 2.6 Update templates
  - Add hidden `<input name="csrf_token">` to `login.html`, `role_form.html`, `form.html`

#### Phase 3: Rate Limiting on Login

- [ ] 3.1 Create `fastapi_admin/auth/ratelimit.py`
  - In-memory sliding window rate limiter (no external deps)
  - `RateLimiter(max_attempts=5, window_seconds=900)` class
  - Key by IP for HTML login, by email for API token endpoint
  - Return `429 Too Many Requests` with `Retry-After` header

- [ ] 3.2 Update `fastapi_admin/auth/views.py`
  - Apply rate limiter to `POST /admin/login` — 5 attempts per IP per 15 min

- [ ] 3.3 Update `fastapi_admin/api/auth.py`
  - Apply rate limiter to `POST /api/auth/token` — 10 attempts per email per 15 min

#### Phase 4: Password Strength Validation

- [ ] 4.1 Create `fastapi_admin/auth/password.py`
  - `validate_password_strength(password: str) -> list[str]` — return list of errors (empty = valid)
  - Rules: min 12 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
  - Optional: check against breached password list (configurable)

- [ ] 4.2 Update `fastapi_admin/auth/backend.py`
  - Call `validate_password_strength()` in authenticate flow (for user creation)

- [ ] 4.3 Update `fastapi_admin/config/auth.py`
  - Add `password_min_length: int = 12`, `password_require_uppercase: bool = True`, etc.

#### Phase 5: Fix validate-field Auth Gap

- [ ] 5.1 Update `fastapi_admin/router.py`
  - Add `Depends(require_permission(registered.table_name, "view"))` to `validate-field` endpoint (line 57)

#### Phase 6: Tests

- [ ] 6.1 Create `tests/test_security.py`
  - Test rate limiter: block after 5 attempts, reset after window
  - Test CSRF: reject POST without valid token
  - Test password validation: reject weak passwords
  - Test JWT secret validation: reject empty/short secret
  - Test validate-field: require authentication

### 13. JWT Redesign — Embed Roles + Permissions

**Files:** `fastapi_admin/api/auth.py`, `fastapi_admin/api/schemas.py`, `fastapi_admin/api/crud.py`, `fastapi_admin/auth/models.py`

**Problem:** JWT only contains `user_id`. Every API request requires a DB lookup to resolve permissions. No refresh token mechanism. No token revocation.

#### Phase 1: Redesign JWT Payload

- [ ] 1.1 Update `fastapi_admin/api/auth.py`
  - New JWT payload structure:
    ```json
    {
      "sub": "1",
      "roles": ["Admin", "Editor"],
      "permissions": {"products": ["view", "create", "edit"], "orders": ["view"]},
      "is_superuser": false,
      "exp": "...",
      "iat": "...",
      "jti": "uuid"
    }
    ```
  - `create_access_token(user, secret_key, expires_delta)` — build payload from user object + roles + permissions
  - Short-lived access token: 30 min (configurable)
  - Remove `_DEFAULT_SECRET` fallback (done in Phase 12)

- [ ] 1.2 Update `fastapi_admin/api/schemas.py`
  - Add `TokenResponse` with `access_token`, `refresh_token`, `token_type`, `expires_in`

#### Phase 2: Add Refresh Token Flow

- [ ] 2.1 Create `fastapi_admin/auth/models.py` — `AdminRefreshToken`
  - Columns: `id`, `user_id` (FK), `token_hash` (SHA256 of jti), `expires_at`, `created_at`, `revoked_at`
  - Index on `user_id` + `token_hash`

- [ ] 2.2 Create Alembic migration for `admin_refresh_tokens` table

- [ ] 2.3 Update `fastapi_admin/api/auth.py`
  - `POST /api/auth/token` — also issue refresh token (7-day expiry)
  - `POST /api/auth/refresh` — exchange refresh token for new access token
  - `POST /api/auth/logout` — revoke refresh token (invalidate session)
  - Refresh token rotation: new refresh token on each refresh

- [ ] 2.4 Update `fastapi_admin/api/schemas.py`
  - Add `RefreshRequest`, `RefreshResponse`, `LogoutRequest` schemas

#### Phase 3: Refactor API CRUD to Use JWT-Embedded Permissions

- [ ] 3.1 Update `fastapi_admin/api/crud.py`
  - Decode JWT → extract `roles`, `permissions`, `is_superuser` from payload
  - Permission check: look up `permissions[table_name]` from JWT (no DB hit)
  - Keep DB fallback only for superuser check (in case `is_superuser` changed)
  - Refactor `_get_current_user()` and `_check_permission()` to use `Depends()`

- [ ] 3.2 Create `fastapi_admin/api/deps.py`
  - `get_api_current_user(request)` — decode JWT, return user payload (no DB)
  - `require_api_permission(table_name, action)` — check JWT-embedded permissions
  - `require_api_superuser()` — check `is_superuser` in JWT

#### Phase 4: Add Missing API Endpoints

- [ ] 4.1 Update `fastapi_admin/api/auth.py`
  - `GET /api/auth/me` — return current user info from JWT (no DB)

- [ ] 4.2 Create `fastapi_admin/api/roles.py`
  - `GET /api/roles/` — list roles (superuser only)
  - `POST /api/roles/` — create role (superuser only)
  - `PUT /api/roles/{id}` — update role (superuser only)
  - `DELETE /api/roles/{id}` — delete role (superuser only)

#### Phase 5: Tests

- [ ] 5.1 Create `tests/test_jwt.py`
  - Test JWT payload contains roles + permissions
  - Test access token expiry (30 min)
  - Test refresh token flow: obtain → refresh → old token invalid
  - Test refresh token revocation on logout
  - Test permission check from JWT payload (no DB)
  - Test `/api/auth/me` returns correct user info

### 14. Session Security

**Files:** `fastapi_admin/auth/views.py`, `fastapi_admin/auth/session.py`, `fastapi_admin/auth/models.py`, `fastapi_admin/config/auth.py`

**Problem:** Sessions not invalidated on password change. Cookie security settings too permissive. No session fixation prevention beyond itsdangerous timestamps.

#### Phase 1: Session Invalidation on Password Change

- [ ] 1.1 Update `fastapi_admin/auth/models.py`
  - Add `password_changed_at` column to `AdminUser` (DateTime, nullable)

- [ ] 1.2 Create Alembic migration for `password_changed_at`

- [ ] 1.3 Update `fastapi_admin/auth/session.py`
  - `encode()` now includes `iat` (issued at) timestamp in payload
  - `decode()` returns payload with `iat` for comparison

- [ ] 1.4 Update `fastapi_admin/auth/dependencies.py`
  - In `get_current_admin_user()`: compare session `iat` vs `user.password_changed_at`
  - Reject session if `password_changed_at > iat` → force re-login

- [ ] 1.5 Update `fastapi_admin/auth/views.py`
  - On password change: set `user.password_changed_at = datetime.now(UTC)`
  - On logout: revoke all refresh tokens for user

#### Phase 2: Secure Cookie Settings

- [ ] 2.1 Update `fastapi_admin/config/auth.py`
  - Add `session_samesite: str = "strict"` (upgrade from "lax")
  - Add `session_secure_auto: bool = True` (auto-detect HTTPS from SECRET_KEY presence)

- [ ] 2.2 Update `fastapi_admin/auth/views.py`
  - Use `samesite` from config (was hardcoded "lax")
  - Set `secure=True` when `session_secure_auto` and secret_key is set

#### Phase 3: Tests

- [ ] 3.1 Create `tests/test_session_security.py`
  - Test session rejected after password change
  - Test cookie samesite=strict
  - Test session fixation prevention

### 15. Admin User Management UI

**Files:** New `fastapi_admin/views/users.py`, new templates, `fastapi_admin/admin/core.py`

**Problem:** No UI for managing admin users. Users can only be created via seed code or direct DB access. Role management exists but user management does not.

#### Phase 1: User Management Views

- [ ] 1.1 Create `fastapi_admin/views/users.py`
  - `GET /admin/users` — list admin users with role, status, last login (superuser only)
  - `GET /admin/users/create` — create form (email, password, full_name, role picker, is_superuser)
  - `POST /admin/users/create` — handle creation with password validation
  - `GET /admin/users/{id}` — edit form
  - `POST /admin/users/{id}` — save changes
  - `POST /admin/users/{id}/delete` — soft-delete (set `is_active=False`)
  - Prevent superuser from deactivating themselves

- [ ] 1.2 Create `templates/pages/users/list.html`
  - User table with email, full name, role badge, status, last login, actions

- [ ] 1.3 Create `templates/pages/users/form.html`
  - Create/edit form with email, password, full name, role dropdown, is_superuser toggle

- [ ] 1.4 Update `fastapi_admin/admin/core.py`
  - Include `users_router` in `_build_router()` with admin prefix

#### Phase 2: Tests

- [ ] 2.1 Create `tests/test_user_management.py`
  - Test list users (superuser only)
  - Test create user with valid/invalid data
  - Test edit user
  - Test delete user (soft-delete)
  - Test prevent self-deactivation

### 16. Password Change + Profile

**Files:** New `fastapi_admin/views/profile.py`, new templates, `fastapi_admin/auth/views.py`

**Problem:** No way for admin users to change their own password or view their profile.

#### Phase 1: Password Change

- [ ] 1.1 Create `fastapi_admin/views/profile.py`
  - `GET /admin/profile/password` — show change password form
  - `POST /admin/profile/password` — validate current password, set new one
  - After change: invalidate session, redirect to login

- [ ] 1.2 Create `templates/pages/profile/password.html`
  - Form with current_password, new_password, confirm_password fields

#### Phase 2: User Profile

- [ ] 2.1 Update `fastapi_admin/views/profile.py`
  - `GET /admin/profile` — show current user info (email, full_name, role, last login)
  - `POST /admin/profile` — update full_name, email (with password confirmation)

- [ ] 2.2 Create `templates/pages/profile/profile.html`
  - Profile display + edit form

#### Phase 3: Tests

- [ ] 3.1 Create `tests/test_profile.py`
  - Test password change flow
  - Test session invalidation after password change
  - Test profile update

### 17. Two-Factor Authentication (TOTP)

**Files:** New `fastapi_admin/auth/totp.py`, new `fastapi_admin/views/totp.py`, new `fastapi_admin/auth/models.py`, new templates

**Problem:** No multi-factor authentication. Admin accounts protected only by password.

#### Phase 1: TOTP Model + Logic

- [ ] 1.1 Create `fastapi_admin/auth/models.py` — `AdminUserTOTP`
  - Columns: `id`, `user_id` (FK, unique), `secret_key` (encrypted), `enabled` (Boolean), `created_at`
  - `backup_codes` (JSON — hashed backup codes for recovery)

- [ ] 1.2 Create Alembic migration for `admin_user_totp` table

- [ ] 1.3 Create `fastapi_admin/auth/totp.py`
  - `generate_secret() -> str` — generate TOTP secret
  - `get_totp_uri(secret, email) -> str` — otpauth:// URI for QR code
  - `verify_totp(secret, code) -> bool` — verify TOTP code
  - `generate_backup_codes(count=10) -> list[str]` — one-time-use codes
  - Uses `pyotp` library

- [ ] 1.4 Update `pyproject.toml`
  - Add `pyotp >= 2.9.0` dependency
  - Add `qrcode >= 7.4` dependency

#### Phase 2: 2FA Setup Flow

- [ ] 2.1 Create `fastapi_admin/views/totp.py`
  - `GET /admin/profile/2fa` — show QR code + setup instructions
  - `POST /admin/profile/2fa/enable` — verify TOTP code, enable 2FA, show backup codes
  - `POST /admin/profile/2fa/disable` — verify current TOTP code + password, disable 2FA
  - `POST /admin/profile/2fa/backup-codes` — generate new set (invalidates old)

- [ ] 2.2 Create `templates/pages/2fa/setup.html`
  - QR code display, TOTP code input, backup codes display

- [ ] 2.3 Create `templates/pages/2fa/verify.html`
  - TOTP code input for login verification

#### Phase 3: 2FA Enforcement on Login

- [ ] 3.1 Update `fastapi_admin/auth/views.py`
  - After password verification, check if user has 2FA enabled
  - If yes: redirect to `GET /admin/verify-2fa` with temp token
  - On TOTP verification: complete login, set session cookie

- [ ] 3.2 Update `fastapi_admin/api/auth.py`
  - After password verification, check if user has 2FA enabled
  - If yes: return `428 Precondition Required` with `{"requires_2fa": true, "temp_token": "..."}`
  - `POST /api/auth/verify-2fa` — verify TOTP code, return access + refresh tokens

- [ ] 3.3 Update `fastapi_admin/api/schemas.py`
  - Add `TwoFARequiredResponse`, `TwoFAVerifyRequest` schemas

#### Phase 4: Tests

- [ ] 4.1 Create `tests/test_2fa.py`
  - Test TOTP setup flow: generate secret → verify code → enable
  - Test TOTP verification on login
  - Test backup codes: use once, reject reuse
  - Test 2FA disable flow
  - Test API 2FA flow with 428 response

### 18. Audit Logging for Security Events

**Files:** `fastapi_admin/auth/views.py`, `fastapi_admin/api/auth.py`, `fastapi_admin/views/totp.py`, `fastapi_admin/views/users.py`

**Problem:** Security events (password change, 2FA toggle, failed logins) are not logged.

#### Phase 1: Log Failed Login Attempts

- [ ] 1.1 Create `fastapi_admin/auth/models.py` — `AdminLoginAttempt`
  - Columns: `id`, `email`, `ip_address`, `user_agent`, `success` (Boolean), `timestamp`
  - Index on `email` + `timestamp`

- [ ] 1.2 Create Alembic migration for `admin_login_attempts` table

- [ ] 1.3 Update `fastapi_admin/auth/views.py`
  - On failed login: record email, IP, user-agent, success=False
  - On successful login: record success=True

- [ ] 1.4 Update `fastapi_admin/api/auth.py`
  - Same logging for API token endpoint

#### Phase 2: Log Security Events

- [ ] 2.1 Update `fastapi_admin/auth/views.py`
  - Password changed → audit log entry
  - 2FA enabled/disabled → audit log entry

- [ ] 2.2 Update `fastapi_admin/views/users.py`
  - User created/edited/deleted → audit log entry

- [ ] 2.3 Update `fastapi_admin/views/roles.py`
  - Role permissions changed → audit log entry

#### Phase 3: Tests

- [ ] 3.1 Create `tests/test_security_audit.py`
  - Test failed login recorded
  - Test password change recorded
  - Test 2FA toggle recorded
  - Test user management recorded

---

## IMPLEMENTATION ORDER

1. **Phase 12** (security hardening) — do first, critical fixes
2. **Phase 13** (JWT redesign) — core to robustness goal
3. **Phase 14** (session security) — builds on Phase 12
4. **Phase 15** (user management UI) — new feature
5. **Phase 16** (password change + profile) — new feature
6. **Phase 17** (2FA) — most complex, builds on everything else
7. **Phase 18** (audit logging) — polish layer