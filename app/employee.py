# File Name: employee.py
# Location: kpcb_hrms/app/employee.py

from flask import Blueprint, render_template, session, jsonify, request
from app.utils.auth_decorators import role_required
from app import db
import datetime

# Import the unified Time & Action Domain
from app.repositories.sql_time_action_repo import SqlTimeActionRepository
from app.services.time_action_service import TimeActionService

# Create the Employee Blueprint with a URL prefix
employee_bp = Blueprint('employee', __name__, url_prefix='/employee')

@employee_bp.route('/dashboard')
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def dashboard():
    """Renders the Employee Dashboard."""
    employee_id = session.get('employee_id')
    current_year = datetime.datetime.now().year
    
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    
    try:
        metrics = service.get_leave_summary(employee_id, current_year)
    except Exception:
        metrics = {"LeavesTaken": 0.0, "LeavesLeft": 0.0, "PendingApprovals": 0}
        
    return render_template('dashboards/employee.html', user=session, metrics=metrics)

@employee_bp.route('/my-attendance')
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def my_attendance_page():
    """Renders the personal attendance ledger view."""
    today = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('employee/my_attendance.html', user=session, today=today)

# ---------------------------------------------------------
# ATTENDANCE API ROUTES
# ---------------------------------------------------------
@employee_bp.route('/api/attendance/my-register', methods=['GET'])
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def get_my_attendance():
    """API to fetch monthly personal attendance records."""
    employee_id = session.get('employee_id')
    month_str = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
    year, month = map(int, month_str.split('-'))
    
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    
    try:
        register = service.fetch_my_attendance_register(employee_id, year, month)
        return jsonify(register), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# LEAVE MANAGEMENT API ROUTES
# ---------------------------------------------------------
@employee_bp.route('/api/leave-summary', methods=['GET'])
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def get_leave_summary():
    """API to fetch high-level leave summary metrics for the dashboard."""
    employee_id = session.get('employee_id')
    current_year = datetime.datetime.now().year
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        metrics = service.get_leave_summary(employee_id, current_year)
        return jsonify(metrics), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@employee_bp.route('/api/leave-balances', methods=['GET'])
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def get_leave_balances():
    """API to fetch the active leave balances for the logged-in employee."""
    employee_id = session.get('employee_id')
    current_year = datetime.datetime.now().year
    
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    
    try:
        balances = service.fetch_employee_leave_balances_by_id(employee_id, current_year)
        return jsonify(balances), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@employee_bp.route('/api/leave-types', methods=['GET'])
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def get_leave_types():
    """API to fetch the list of dynamic leave categories for dropdown configuration."""
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        types = service.fetch_leave_types()
        return jsonify(types), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@employee_bp.route('/api/leave/apply', methods=['POST'])
@role_required('Admin', 'Employee', 'Payroll User', 'Attendance User')
def apply_leave():
    """API for an employee to submit a leave request."""
    data = request.json
    employee_id = session.get('employee_id')
    
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    
    try:
        result = service.submit_leave_application(employee_id, data)
        return jsonify({"message": "Leave application submitted successfully", "data": result}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500