# Application Layer Guidelines

This directory contains the core logic and UI for the KPCB HRMS application.

## 1. Blueprints & Routes
- Routes are organized into Flask Blueprints: `auth_bp`, `admin_bp`, and `employee_bp`.
- UI routes (rendering templates) and API routes (returning JSON) should be clearly separated within the blueprint files where possible.
- **Route Decoration:** Ensure all non-public routes are decorated with `@login_required` and, where applicable, `@role_required`.

## 2. Service Layer (`app/services/`)
- Services must handle all business validation.
- Do not perform database transactions directly in the service; delegate to the repository.
- Handle exceptions gracefully and raise informative `ValueError` or `RuntimeError` that can be caught by the route handlers to return appropriate HTTP status codes.

## 3. Repository Layer (`app/repositories/`)
- **Interfaces:** Define all repository methods in `interfaces.py` using abstract base classes (`ABC`).
- **SQL Sanitization:** Use `_sanitize_row` or similar helper methods to ensure that database types (like `datetime`) are converted to JSON-serializable strings before being returned to the service.
- **Commits:** The repository is responsible for committing (`db.session.commit()`) and rolling back (`db.session.rollback()`) transactions.

## 4. Templates & UI (`app/templates/`)
- **Layouts:** Use `layouts/admin_base.html` and `layouts/employee_base.html` for consistent UI across roles.
- **Styling:** Prefer Vanilla CSS. External frameworks should be avoided unless explicitly requested.
- **Dynamic Content:** Frontend logic (JavaScript) should be kept clean and modular, preferably integrated into the relevant HTML files or separate `.js` files if they grow too large.

## 5. Error Handling
- Use `try...except` blocks in route handlers to catch service-level exceptions.
- Return consistent JSON error responses: `{"error": "Message"}` with appropriate HTTP codes (400 for validation, 401 for auth, 403 for forbidden, 500 for internal errors).
