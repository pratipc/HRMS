# KPCB HRMS

KPCB HRMS (Kolkata Police Cooperative Bank Human Resource Management System)
is an enterprise HRMS application developed using Python Flask, SQL Server,
Stored Procedures, Jinja2, and Tailwind CSS.

## Overview

The system was developed to manage employee records, attendance, leave,
payroll, approval workflows, role-based access, and administrative operations.

The application follows a **Thin API / Thick Database** architecture, with
business-critical operations implemented through SQL Server Stored Procedures
and a layered Flask architecture using Blueprints, Services, and Repositories.

## Key Work Implemented

- Employee Master and bulk employee onboarding
- Authentication and Role-Based Access Control (RBAC)
- Biometric attendance and web punch-in/out
- Employee attendance ledger and reporting
- Dynamic leave policy and leave balance management
- Multi-level, branch-specific leave approval workflows
- Year-end leave carry-forward, capping, and expiration processing
- Dynamic payroll and salary calculation
- Employee-specific deductions, allowances, and tax configurations
- Provisional payroll and automated arrears/LWP reconciliation
- Payroll locking and transactional controls
- System audit trail with before/after data snapshots
- User activity and administrative monitoring
- Branch-aware HR workflows and Head Office controls

## Technology Stack

**Backend:** Python, Flask  
**Database:** Microsoft SQL Server, T-SQL, Stored Procedures  
**ORM / DB Access:** SQLAlchemy, pyodbc  
**Frontend:** Jinja2, HTML, Tailwind CSS, JavaScript  
**Architecture:** Application Factory, Blueprints, Services, Repositories,
Thin API / Thick Database

## Engineering Highlights

- Transaction-safe bulk processing with rollback mechanisms
- Database-level validation and business rules
- Configurable workflows instead of hardcoded business logic
- RBAC and Maker-Checker controls
- Audit logging and historical data protection
- Cross-month payroll reconciliation
- Performance-conscious asynchronous activity logging

## AI-Assisted Development

AI-assisted development tools, including **Antigravity CLI**, were used to
accelerate implementation, debugging, refactoring, and development workflows.
Generated suggestions and code were reviewed, modified, tested, and validated
during development.
