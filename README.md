# Vikmo - Sales Order & Inventory (Assignment)

## Overview

This repository contains a simplified Sales Order & Inventory Management backend built with Django and Django REST Framework. It implements products, inventory, dealers, orders with status flow, stock validation, and admin-only inventory adjustments with audit.

Features implemented
- Product catalog with unique SKU and pricing
- Inventory per product (one-to-one)
- Dealers (customers) with contact details
- Orders and OrderItems with preserved unit price and auto-calculated totals
- Order status flow: Draft → Confirmed → Delivered
- Stock validation when confirming orders; atomic stock deduction
- Pre-delete handler to restore stock for confirmed orders
- Admin-only inventory adjustments with audit trail (who changed stock)
- RESTful APIs for products, dealers, orders, and admin inventory adjustments
- Frontend UX improvements: Admin button hidden for non-admins, auto-redirect to Admin on page load when stored token belongs to an admin, and a small toast shown when redirecting after login
- Unit tests covering critical scenarios

Stack
- Python 3.10+
- Django 4.2+ (project created using Django)
- Django REST Framework
- SQLite (default) — can be switched to PostgreSQL in `settings.py`

---

## Setup (local)

1. Clone the repo

```bash
git clone <your-repo-url>
cd inventory_lite
```

2. Create a virtual environment and install dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Apply migrations and create a superuser

```bash
python vikmo/manage.py migrate
python vikmo/manage.py createsuperuser
```

4. Run the development server

```bash
python vikmo/manage.py runserver
```

5. Run tests

```bash
python vikmo/manage.py test sales
```

---

## API Endpoints
Base URL: `http://localhost:8000/api/`

### Products
- GET `/api/products/` — list all products with stock
- POST `/api/products/` — create a new product
- GET `/api/products/{id}/` — get product details
- PUT `/api/products/{id}/` — update product
- DELETE `/api/products/{id}/` — delete product

Product example (create)

curl:

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Brake Pad", "sku": "BP-001", "price": "500.00", "description": "Front brake pad"}'
```

Response (201):
```json
{
  "id": 1,
  "name": "Brake Pad",
  "sku": "BP-001",
  "description": "Front brake pad",
  "price": "500.00",
  "active": true,
  "stock": 0,
  "created_at": "...",
  "updated_at": "..."
}
```

Inventory starts at 0; use admin adjustments to add stock.

### Dealers
- GET `/api/dealers/` — list dealers
- POST `/api/dealers/` — create a dealer
- GET `/api/dealers/{id}/` — retrieve dealer with list of orders
- PUT `/api/dealers/{id}/` — update dealer

Create dealer example

```bash
curl -X POST http://localhost:8000/api/dealers/ -H "Content-Type: application/json" -d '{"name":"ABC Motors", "code":"ABC"}'
```

### Orders
- GET `/api/orders/` — list all orders
- POST `/api/orders/` — create a new DRAFT order
- GET `/api/orders/{id}/` — get order with items
- PUT `/api/orders/{id}/` — update a DRAFT order (cannot edit confirmed/delivered)  - Note: Do not change `status` via the PUT endpoint; use `/confirm/` and `/deliver/` actions instead. The backend will reject attempts to modify `status` and return a helpful message.- POST `/api/orders/{id}/confirm/` — confirm order (validates stock, deducts on success)
- POST `/api/orders/{id}/deliver/` — mark confirmed order as delivered
- POST `/api/orders/{id}/cancel/` — cancel a DRAFT order (sets status to `CANCELLED`; only allowed while order is still DRAFT)

Create draft order example

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{"dealer": 1, "items": [{"product": 1, "quantity": 10}]}'
```

Confirm / Deliver / Cancel examples

Confirm order (attempt to confirm a DRAFT order):

```bash
curl -X POST http://localhost:8000/api/orders/1/confirm/
```

If an order contains items with insufficient stock, the API returns HTTP 400 and includes per-item messages. Example response:

```json
{
  "detail": "Insufficient stock",
  "items": [
    {"product": "BP-001", "product_name": "Brake Pad", "available": 5, "requested": 10, "message": "Insufficient stock for Brake Pad. Available: 5, Requested: 10"}
  ]
}
```

When confirmed successfully, stock is deducted in an atomic transaction and the order status becomes `CONFIRMED`.

Deliver order (mark a confirmed order as delivered):

```bash
curl -X POST http://localhost:8000/api/orders/1/deliver/
```

Cancel order (cancel a DRAFT order):

```bash
curl -X POST http://localhost:8000/api/orders/1/cancel/
```

Cancellation is only allowed while the order is still `DRAFT`. The API returns a helpful error when attempting invalid status transitions (for example, cancelling a confirmed order will return HTTP 400 with `Only Draft orders can be cancelled`).

### Inventory (Admin Only)
- GET `/api/inventory/` — list inventory levels (admin only)
- PUT `/api/inventory/{id}/adjust/` — manual stock adjustment (admin only) — body: `{ "change": -10, "note": "correction" }`

Note: Inventory adjustments are recorded in an audit table (`InventoryAdjustment`) with the `changed_by` user and timestamp.

Example adjust (admin session required):

```bash
# Use Postman or admin session auth - ensure you're authenticated as admin
curl -X PUT http://localhost:8000/api/inventory/1/adjust/ \
  -H "Content-Type: application/json" \
  -d '{"change": -10, "note": "stock correction"}'
```

Response (200):
```json
{"detail": "Inventory adjusted"}
```

---

## Sample Test Scenarios (curl)

1. Create product & inventory
```bash
curl -X POST http://localhost:8000/api/products/ -H "Content-Type: application/json" -d '{"name":"Brake Pad","sku":"BP-001","price":"500.00"}'
# Create dealer
curl -X POST http://localhost:8000/api/dealers/ -H "Content-Type: application/json" -d '{"name":"ABC Motors", "code":"ABC"}'
# Adjust inventory as admin (via Postman or admin session) to add 100 units
# Create draft order
curl -X POST http://localhost:8000/api/orders/ -H "Content-Type: application/json" -d '{"dealer":1, "items":[{"product":1, "quantity":10}]}'
# Confirm
curl -X POST http://localhost:8000/api/orders/1/confirm/
# Deliver
curl -X POST http://localhost:8000/api/orders/1/deliver/
```

This should reduce stock accordingly and reflect order status transitions.

---

## Assumptions & Notes
- Orders preserve `unit_price` and `product` snapshot fields so historical order data remains valid even if product price or record changes.
- Deleting a product sets `OrderItem.product` to NULL to preserve past orders. Deleting a dealer is prevented if it has orders (`PROTECT`).
- Authentication: API uses JSON Web Tokens (SimpleJWT). Endpoints: `POST /api/auth/login/` (returns `access` and `refresh` tokens), `POST /api/auth/refresh/` (exchange `refresh` for a new `access`), `POST /api/auth/logout/` (optional logout helper) and `GET /api/auth/me/` (returns user info for the current token). Inventory adjustments require admin privileges. For API clients like Postman, authenticate using `POST /api/auth/login/` then include `Authorization: Bearer <access>` or use cookies/session if preferred.
- Order numbers follow format `ORD-YYYYMMDD-XXXX` (auto-generated on creation).

---

## Next steps & Improvements (optional for bonus)
- Add concurrency tests and stronger race-condition checks
- Add Postman collection file (included) and export
- Add Docker + docker-compose for reproducible environment
- Build a simple frontend (Django templates or React) for manual testing
- Add more thorough API schema/docs (Swagger/OpenAPI)

---

## Postman Collection
A minimal Postman collection is provided at `postman_collection.json` with example requests for the main flows.

## Frontend (minimal React app)
A small React frontend is available under `frontend/` (Vite). It provides basic product listings, order creation (draft), and order actions (confirm/deliver).

Run the frontend during development:

```bash
cd frontend
npm install
npm run dev
```

Authentication flow (JWT):
1. Create a superuser in Django via `python vikmo/manage.py createsuperuser`.
2. Use `POST /api/auth/login/` to obtain `access` and `refresh` tokens (body: `{ "username": "<user>", "password": "<pass>" }`).
3. The frontend stores `access` and `refresh` tokens in `localStorage` and uses `GET /api/auth/me/` to fetch the current user profile for UI decisions (for example, whether the user is an admin).
4. The frontend automatically refreshes the access token in the background (interval-based and on 401) using `POST /api/auth/refresh/`; if the refresh fails, tokens are cleared and the user must re-login.
5. UX details: the Admin button is hidden for non-admin users, the app auto-redirects to the Admin view on page load if the stored token belongs to an admin, and a small toast modal is shown saying "Redirecting to Admin..." immediately before the redirect.

Quick verification (Admin redirect & toast):

1. Create a Django superuser and start both servers (`python vikmo/manage.py runserver` and `cd frontend && npm run dev`).
2. Login via the frontend as the superuser. You should see a small toast "Redirecting to Admin..." and the app should navigate to the Admin inventory UI automatically.
3. Reload the page while still logged in: the app will detect the stored token via `GET /api/auth/me/` and auto-redirect to Admin again if the user is staff.

The Vite server proxies `/api` to the Django backend (http://localhost:8000) so API calls should work out-of-the-box during local development.

Build for production:

```bash
cd frontend
npm run build
```

---

If you'd like, I can now:
- Add Docker + compose
- Export a full Postman collection with auth examples
- Add CI (GitHub Actions) to run tests on push

Let me know which you'd prefer next. ✅
