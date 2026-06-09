# KPCB HRMS Project Guidelines

Welcome to the KPCB HRMS (Human Resource Management System) codebase. This document outlines the foundational mandates, architecture, and development workflows for this repository.

## 1. Tech Stack
- **Backend:** Flask 3.0.3 (Application Factory Pattern)
- **Database:** SQL Server (via SQLAlchemy 2.0.29 & pyodbc)
- **Frontend:** Jinja2 Templates (with Vanilla CSS)
- **Patterns:** Service-Repository Pattern with Dependency Inversion.

## 2. Architecture & Directory Structure
The project follows a modular architecture organized by functional domains:
- `app/`: Main application package.
- `app/services/`: Business logic layer.
- `app/repositories/`: Data access layer (Interfaces + SQL implementations).
- `app/templates/`: UI layouts and components.
- `app/utils/`: Shared decorators and helper functions.

## 3. Core Mandates
### 3.1 Data Access
- **Stored Procedures:** All significant database operations (CRUD, complex logic) **MUST** be performed via SQL Server Stored Procedures. Direct SQLAlchemy ORM mapping for complex queries is discouraged in favor of the established SP pattern.
- **Interfaces:** Repositories must adhere to the interfaces defined in `app/repositories/interfaces.py`.

### 3.2 Business Logic
- Business rules, validation, and orchestration must reside in the **Service Layer** (`app/services/`).
- Services should depend on repository **interfaces**, not concrete implementations (DIP).

### 3.3 Security
- **Authentication:** All protected routes must use the `@login_required` decorator.
- **Authorization:** Role-based access control must be enforced using the `@role_required` decorator (e.g., `@role_required('Admin')`).

## 4. Sub-directory Guidelines
For more specific instructions regarding the application components, refer to:
- [Application Guidelines](./app/GEMINI.md)
