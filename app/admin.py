# File Name: admin.py
# Location: kpcb_hrms/app/admin.py

from flask import Blueprint, render_template, session, request, jsonify, Response
from app.utils.auth_decorators import role_required
from app import db
from sqlalchemy import text
import datetime
import csv
from io import StringIO

# 1. Import Core HR Domain (for employees)
from app.repositories.sql_core_hr_repository import SqlCoreHrRepository
from app.services.core_hr_service import CoreHrService

# 2. Import Time & Action Domain (for holidays, leaves, attendance)
from app.repositories.sql_time_action_repo import SqlTimeActionRepository
from app.services.time_action_service import TimeActionService

#3. Payroll Services (for pay scale management and salary details)
from app.repositories.sql_payroll_repository import SqlPayrollRepository
from app.services.payroll_service import PayrollService

# Create the Admin Blueprint with a URL prefix
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@role_required('Admin')
def dashboard():
    """Renders the Admin Dashboard."""
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    metrics = service.get_dashboard_metrics()
    return render_template('dashboards/admin.html', user=session, metrics=metrics)

# ---------------------------------------------------------
# TIME, ATTENDANCE & SHIFT MANAGEMENT
# ---------------------------------------------------------
@admin_bp.route('/attendance-master', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def attendance_master_page():
    """Renders the unified Attendance Register and Ingestion Portal."""
    return render_template('admin/attendance_master.html', user=session, today=datetime.date.today().strftime('%Y-%m-%d'))

@admin_bp.route('/api/attendance/monthly-register', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def get_monthly_attendance_register():
    month_str = request.args.get('month', datetime.date.today().strftime('%Y-%m'))
    service = TimeActionService(SqlTimeActionRepository(db.session))
    
    try:
        year, month = map(int, month_str.split('-'))
        is_uploaded = service.is_attendance_uploaded(year, month)
    except Exception:
        is_uploaded = False
    
    try:
        register = service.fetch_monthly_register(month_str)
        return jsonify({
            "register": register,
            "attendance_uploaded": is_uploaded
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/attendance/register', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def get_attendance_register():
    date_str = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    service = TimeActionService(SqlTimeActionRepository(db.session))
    try:
        register = service.fetch_daily_register(date_str)
        return jsonify(register), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/attendance/manual-template', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def download_manual_attendance_template():
    """Provides a downloadable CSV template for manual attendance upload."""
    csv_content = "EmployeeCode,PunchDate,Status\nKPCB-001,2026-05-01,Present\nKPCB-002,2026-05-01,Absent\nKPCB-003,2026-05-01,Leave\nKPCB-004,2026-05-01,Weekly Off\n"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=manual_attendance_template.csv"}
    )

@admin_bp.route('/api/attendance/manual-upload', methods=['POST'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def upload_manual_attendance():
    """Processes a simple manual attendance CSV format."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    branch_id = request.form.get('branch_id')
    
    if not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "Please upload the manual attendance template as a .CSV file."}), 400
        
    try:
        service = TimeActionService(SqlTimeActionRepository(db.session))
        bid = int(branch_id) if branch_id else None
        success_count, errors = service.process_manual_upload(file, branch_id=bid)
        
        if errors and success_count == 0:
            return jsonify({"error": "Processing failed.", "details": errors}), 400
        elif errors:
            return jsonify({"message": f"Processed {success_count} records with some anomalies.", "details": errors}), 207
        return jsonify({"message": f"Successfully imported {success_count} manual attendance logs!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/attendance/biometric-upload', methods=['POST'])
@role_required('Admin', 'Payroll User', 'Attendance User')
def upload_biometric_punches():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    branch_id = request.form.get('branch_id')
    
    # Validation against improper formats
    if not file.filename.lower().endswith(('.csv', '.xls', '.xlsx')):
        return jsonify({"error": "Please upload your Monthly Basic Report as an .XLS or .CSV file."}), 400
        
    try:
        service = TimeActionService(SqlTimeActionRepository(db.session))
        bid = int(branch_id) if branch_id else None
        # Send the raw file to our bespoke ETL parser
        success_count, errors = service.process_biometric_upload(file, branch_id=bid)
        
        if errors:
            return jsonify({"message": f"Processed {success_count} daily attendance points with anomalies.", "details": errors}), 207
        return jsonify({"message": f"Successfully parsed and mapped {success_count} daily attendance logs. Rosters updated!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ---------------------------------------------------------
# EMPLOYEE DIRECTORY MASTER UI & API ROUTES
# ---------------------------------------------------------
@admin_bp.route('/employees', methods=['GET'])
@role_required('Admin')
def employee_master_page():
    """Renders the Employee Master UI."""
    return render_template('admin/employee_master.html', user=session)

@admin_bp.route('/api/employees/<int:employee_id>', methods=['GET'])
@role_required('Admin')
def get_employee_details(employee_id):
    """API to lazy-load detailed profile (KYC, Banking, Contact) for an employee."""
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        details = service.get_employee_details(employee_id)
        if not details:
            return jsonify({"error": "Employee not found."}), 404
        return jsonify(details), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/employees/<int:employee_id>/profile', methods=['GET'])
@role_required('Admin')
def get_employee_profile(employee_id):
    """Lazy-loads complete decrypted KYC, banking, and payroll details of a specific employee."""
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        profile = service.get_employee_full_profile(employee_id)
        if not profile:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify(profile), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/employees', methods=['GET'])
@role_required('Admin')
def get_employees():
    """API to fetch all active employees, optionally filtered by branch."""
    branch_id = request.args.get('branch_id')
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        employees = service.get_active_employees(branch_id)
        return jsonify(employees), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# BRANCH MANAGEMENT UI & API ROUTES
# ---------------------------------------------------------
@admin_bp.route('/branches', methods=['GET'])
@role_required('Admin')
def branch_master_page():
    """Renders the Branch Master UI."""
    return render_template('admin/branch_master.html', user=session)

@admin_bp.route('/api/branches', methods=['GET'])
@role_required('Admin')
def get_branches():
    """API to fetch all branches."""
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        branches = service.get_branches()
        return jsonify(branches), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/branches', methods=['POST'])
@role_required('Admin')
def add_branch():
    """API to create a new branch."""
    data = request.json
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        result = service.create_branch(data)
        return jsonify({"message": "Branch created successfully!", "data": result}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/branches/<int:branch_id>', methods=['PUT'])
@role_required('Admin')
def edit_branch(branch_id):
    """API to update an existing branch."""
    data = request.json
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        service.update_branch(branch_id, data)
        return jsonify({"message": "Branch updated successfully!"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/branches/<int:branch_id>/head-office', methods=['POST'])
@role_required('Admin')
def set_head_office(branch_id):
    """API to designate a branch as the Head Office."""
    sql = text("EXEC sp_SetHeadOffice @BranchID = :branch_id")
    try:
        db.session.execute(sql, {"branch_id": branch_id})
        db.session.commit()
        return jsonify({"message": "Head Office updated successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/employees', methods=['POST'])
@role_required('Admin')
def add_employee():
    """API to create a new employee."""
    data = request.json
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    
    try:
        result = service.create_new_employee(data)
        return jsonify({"message": "Employee created successfully!", "data": result}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except RuntimeError as re:
        return jsonify({"error": str(re)}), 500
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

@admin_bp.route('/api/employees/<int:employee_id>', methods=['PUT'])
@role_required('Admin')
def edit_employee(employee_id):
    """API to update an existing employee's profile."""
    data = request.json
    repo = SqlCoreHrRepository(db.session)
    service = CoreHrService(repo)
    try:
        result = service.update_employee_profile(employee_id, data)
        return jsonify({"message": "Employee updated successfully!", "data": result}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

@admin_bp.route('/api/employees/template', methods=['GET'])
@role_required('Admin')
def download_employee_template():
    """Provides a downloadable CSV template with expanded KYC, branch, and banking headers."""
    headers = [
        "FirstName", "LastName", "Email", "Phone", "Department", "Designation",
        "DateOfJoining", "PANNumber", "AadharNumber", "BankAccountNumber",
        "BankIFSCCode", "BranchName", "BasicPay"
    ]
    sample_row_1 = [
        "Sourav", "Ganguly", "sourav.g@kpcb.com", "+919876543210", "Administration", "Manager",
        "2026-01-15", "ABCDE1234F", "123456789012", "111222333444", "UTIB0000123", "Kolkata Police HQ", "55000.00"
    ]
    
    csv_content = ",".join(headers) + "\n" + ",".join(sample_row_1) + "\n"
    
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=employee_onboarding_template.csv"}
    )

@admin_bp.route('/api/employees/bulk-upload', methods=['POST'])
@role_required('Admin')
def bulk_upload_employees():
    """API to process bulk employee onboarding from CSV with branch name resolution."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are supported"}), 400

    try:
        # 1. Resolve Branches for mapping
        repo = SqlCoreHrRepository(db.session)
        service = CoreHrService(repo)
        branches = service.get_branches()
        branch_map = {b['BranchName'].strip().lower(): b['BranchID'] for b in branches}

        # 2. Process CSV
        stream = StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_input = csv.DictReader(stream)
        employees_data = list(csv_input)
        
        # 3. Enrich data with resolved BranchIDs
        for row in employees_data:
            branch_name = row.get('BranchName', '').strip().lower()
            if branch_name in branch_map:
                row['BranchID'] = branch_map[branch_name]
            else:
                # Fallback to first branch if name not matched
                if branches:
                    row['BranchID'] = branches[0]['BranchID']
                else:
                    raise ValueError(f"No active branches found to tag employee: {row.get('FirstName')}")

        results = repo.bulk_create_employees(employees_data)
        return jsonify({"message": f"Successfully imported {len(results)} employees."}), 200
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

# ---------------------------------------------------------
# HOLIDAY CALENDAR MASTER UI & API ROUTES
# ---------------------------------------------------------
@admin_bp.route('/holidays', methods=['GET'])
@role_required('Admin')
def holiday_master_page():
    """Renders the Holiday Master UI."""
    return render_template('admin/holiday_master.html', user=session, current_year=datetime.datetime.now().year)

@admin_bp.route('/api/holidays/<int:year>', methods=['GET'])
@role_required('Admin')
def get_holidays(year):
    """API to fetch holidays for a specific calendar year."""
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        holidays = service.fetch_holidays(year)
        return jsonify(holidays), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/holidays', methods=['POST'])
@role_required('Admin')
def add_holiday():
    """API to create a new holiday."""
    data = request.json
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        result = service.create_holiday(data)
        return jsonify({"message": "Holiday added successfully", "data": result}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

@admin_bp.route('/api/holidays/template', methods=['GET'])
@role_required('Admin')
def download_holiday_template():
    """Provides a downloadable CSV template for bulk holiday upload."""
    csv_content = "HolidayDate,HolidayName,HolidayType\n2026-01-26,Republic Day,National\n2026-04-01,Yearly Closing,Bank Closure\n2026-10-19,Durga Puja,State\n"
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=holiday_upload_template.csv"}
    )

@admin_bp.route('/api/holidays/bulk-upload', methods=['POST'])
@role_required('Admin')
def bulk_upload_holidays():
    """API to process bulk holiday upload from CSV."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "Only CSV files are supported"}), 400

    try:
        stream = StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        csv_input = csv.DictReader(stream)
        
        repo = SqlTimeActionRepository(db.session)
        service = TimeActionService(repo)
        
        success_count, errors = service.process_bulk_upload(csv_input)
        
        if errors and success_count == 0:
            return jsonify({"error": "Bulk upload failed.", "details": errors}), 400
        elif errors:
            return jsonify({"message": f"Partial success: Added {success_count} holidays.", "details": errors}), 207
        else:
            return jsonify({"message": f"Successfully imported {success_count} holidays."}), 200
    except Exception as e:
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500

@admin_bp.route('/api/holidays/<int:holiday_id>', methods=['PUT'])
@role_required('Admin')
def edit_holiday(holiday_id):
    """API to edit an existing holiday."""
    data = request.json
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        result = service.modify_holiday(holiday_id, data)
        return jsonify({"message": "Holiday updated successfully", "data": result}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

# ---------------------------------------------------------
# LEAVE MASTER UI & API CONFIGURATION ROUTES
# ---------------------------------------------------------
@admin_bp.route('/leave-master', methods=['GET'])
@role_required('Admin')
def leave_master_page():
    """Renders the Leave Policy Master UI."""
    return render_template(
        'admin/leave_master.html', 
        user=session, 
        current_year=datetime.datetime.now().year
    )

@admin_bp.route('/api/leave-types', methods=['GET'])
@role_required('Admin')
def get_leave_types():
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        return jsonify(service.fetch_leave_types()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leave-types', methods=['POST'])
@role_required('Admin')
def add_leave_type():
    data = request.json
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        result = service.create_leave_policy(data)
        return jsonify({"message": "Leave policy created successfully", "data": result}), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leave-types/<int:type_id>', methods=['PUT'])
@role_required('Admin')
def edit_leave_type(type_id):
    data = request.json
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        result = service.modify_leave_policy(type_id, data)
        return jsonify({"message": "Leave policy updated successfully", "data": result}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# LEAVE APPROVAL WORKFLOW API ENDPOINTS
# ---------------------------------------------------------
@admin_bp.route('/leave-workflow', methods=['GET'])
@role_required('Admin')
def leave_workflow_page():
    """Renders the Leave Workflow Configuration UI."""
    return render_template('admin/leave_workflow.html', user=session)

@admin_bp.route('/api/leaves/workflow/<int:branch_id>', methods=['GET'])
@role_required('Admin')
def get_leave_workflow(branch_id):
    service = TimeActionService(SqlTimeActionRepository(db.session))
    try:
        workflow = service.get_leave_approval_workflow(branch_id)
        return jsonify(workflow), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leaves/workflow/<int:branch_id>/approvers', methods=['GET'])
@role_required('Admin')
def get_eligible_approvers(branch_id):
    service = TimeActionService(SqlTimeActionRepository(db.session))
    try:
        approvers = service.get_eligible_approvers(branch_id)
        return jsonify(approvers), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leaves/workflow/<int:branch_id>', methods=['POST'])
@role_required('Admin')
def save_leave_workflow(branch_id):
    data = request.json
    workflow_data = data.get('workflow', [])
    apply_to_all = data.get('applyToAll', False)
    
    service = TimeActionService(SqlTimeActionRepository(db.session))
    try:
        service.save_leave_approval_workflow(branch_id, workflow_data, apply_to_all)
        return jsonify({"message": "Workflow saved successfully"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# LEAVE APPROVALS UI & REST API ENDPOINTS
# ---------------------------------------------------------
@admin_bp.route('/leave-approvals', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User', 'Employee')
def leave_approvals_page():
    """Renders the Leave Approvals Management Dashboard."""
    return render_template('admin/leave_approvals.html', user=session)

@admin_bp.route('/api/leaves/pending', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User', 'Employee')
def get_pending_leaves():
    """Rest API to fetch all active pending leave applications."""
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    approver_id = session.get('employee_id')
    role = session.get('role')
    try:
        return jsonify(service.fetch_pending_leave_applications(approver_id, role)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leaves/history', methods=['GET'])
@role_required('Admin', 'Payroll User', 'Attendance User', 'Employee')
def get_leave_history():
    """Retrieves processed (approved/rejected) leave applications for the History Tab."""
    month = request.args.get('month')
    year = request.args.get('year')

    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        month_int = int(month) if month and month != 'ALL' else None
        year_int = int(year) if year and year != 'ALL' else None
        return jsonify(service.fetch_processed_leave_applications(month_int, year_int)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/leaves/process', methods=['POST'])
@role_required('Admin', 'Payroll User', 'Attendance User', 'Employee')
def process_leave():
    """Rest API to Approve or Reject an active leave request."""
    data = request.json
    approver_id = session.get('employee_id')

    # Robustly handle both Javascript casing styles to prevent missing ID errors
    application_id = data.get('application_id') or data.get('ApplicationID')
    status = data.get('status') or data.get('Status') # 'Approved' or 'Rejected'

    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        result = service.process_leave_application(int(application_id), status, approver_id)
        return jsonify({
            "message": f"Leave application successfully {status.lower()}!",
            "data": result
        }), 200
    except ValueError as ve:
        # Gracefully catch insufficient balance or application states and show to manager
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": "An internal server error occurred."}), 500

#--------------SATURDAY & SUNDAY WEEKLY OFF CONFIGURATION ROUTES----------------
@admin_bp.route('/api/weekly-offs', methods=['GET'])
@role_required('Admin')
def get_weekly_offs():
    """API to fetch the active Weekend off rules."""
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        return jsonify(service.fetch_weekly_offs()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/weekly-offs', methods=['POST'])
@role_required('Admin')
def update_weekly_offs():
    """API to completely overwrite the Weekend off rules."""
    repo = SqlTimeActionRepository(db.session)
    service = TimeActionService(repo)
    try:
        service.save_weekly_offs(request.json)
        return jsonify({"message": "Weekend Configuration saved successfully! Leave calculations will now use these rules."}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# PAYROLL & COMPENSATION (NEW UI ROUTE ADDED HERE)
# ---------------------------------------------------------
@admin_bp.route('/payroll-master', methods=['GET'])
@role_required('Admin', 'Payroll User')
def payroll_master_page():
    """Renders the Dynamic Payroll & Compensation Dashboard."""
    # Ensure session data is available to avoid template indexing errors
    return render_template('admin/payroll_master.html', user=session)

@admin_bp.route('/api/payroll/salaries', methods=['GET'])
@role_required('Admin', 'Payroll User')
def get_salaries():
    year = request.args.get('year', default=datetime.datetime.now().year, type=int)
    month = request.args.get('month', default=datetime.datetime.now().month, type=int)
    
    service = PayrollService(SqlPayrollRepository(db.session))
    # This acts as the PREVIEW generator
    ledger = service.generate_monthly_payroll(year, month)
    return jsonify({"ledger": ledger}), 200

@admin_bp.route('/api/payroll/status', methods=['GET'])
@role_required('Admin', 'Payroll User')
def get_payroll_status():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    service = PayrollService(SqlPayrollRepository(db.session))
    try:
        return jsonify(service.get_payroll_status(year, month)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/payroll/finalize', methods=['POST'])
@role_required('Admin', 'Payroll User')
def finalize_payroll():
    data = request.json
    year = data.get('year')
    month = data.get('month')
    processed_by = session.get('username', 'Admin')
    
    service = PayrollService(SqlPayrollRepository(db.session))
    try:
        result = service.finalize_payroll(year, month, processed_by)
        return jsonify({"message": f"Payroll for {month}/{year} has been finalized and locked!", "data": result}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/payroll/employee/<int:emp_id>/basic', methods=['PUT'])
@role_required('Admin', 'Payroll User')
def update_basic_pay(emp_id):
    try:
        PayrollService(SqlPayrollRepository(db.session)).update_basic_pay(emp_id, request.json.get('BasicPay'))
        return jsonify({"message": "Basic pay updated successfully!"}), 200
    except ValueError as ve: return jsonify({"error": str(ve)}), 400
    except Exception as e: return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/payroll/config', methods=['GET', 'PUT'])
@role_required('Admin', 'Payroll User')
def manage_allowance_config():
    service = PayrollService(SqlPayrollRepository(db.session))
    if request.method == 'GET':
        return jsonify(service.get_allowances_config()), 200
    try:
        service.update_allowances_config(request.json.get('DA'), request.json.get('HRA'), request.json.get('MA'))
        return jsonify({"message": "Global allowances updated. All salaries recalculated!"}), 200
    except ValueError as ve: return jsonify({"error": str(ve)}), 400
    except Exception as e: return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/payroll/saturday-rates', methods=['GET'])
@role_required('Admin', 'Payroll User')
def get_saturday_rates():
    service = PayrollService(SqlPayrollRepository(db.session))
    try:
        return jsonify(service.get_saturday_allowance_rates()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/payroll/saturday-rates', methods=['PUT'])
@role_required('Admin', 'Payroll User')
def update_saturday_rate():
    service = PayrollService(SqlPayrollRepository(db.session))
    data = request.json
    try:
        # Robustly handle different casing for rate_id
        rate_id = data.get('rate_id') or data.get('RateID') or 0
        service.update_saturday_allowance_rate(
            designation=data.get('designation') or data.get('Designation'), 
            rate=data.get('rate') or data.get('Rate'),
            rate_id=int(rate_id),
            old_designation=data.get('old_designation') or data.get('OldDesignation')
        )
        return jsonify({"message": "Saturday allowance rate updated successfully!"}), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# DYNAMIC USER ROLE MANAGEMENT
# ---------------------------------------------------------
@admin_bp.route('/user-roles', methods=['GET'])
@role_required('Admin')
def user_roles_page():
    return render_template('admin/user_roles.html', user=session)

@admin_bp.route('/api/user-roles', methods=['GET'])
@role_required('Admin')
def get_employees_with_roles():
    branch_id = request.args.get('branch_id')
    if not branch_id:
        return jsonify({"error": "branch_id is required"}), 400
    
    sql = text("EXEC sp_GetEmployeesWithUserRoles @BranchID = :branch_id")
    try:
        result = db.session.execute(sql, {"branch_id": branch_id}).mappings().all()
        return jsonify([dict(row) for row in result]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/user-roles/<int:user_id>', methods=['PUT'])
@role_required('Admin')
def update_user_role(user_id):
    new_role = request.json.get('Role')
    if not new_role:
        return jsonify({"error": "Role is required"}), 400
        
    sql = text("EXEC sp_UpdateUserRole @UserID = :user_id, @NewRole = :new_role")
    try:
        db.session.execute(sql, {"user_id": user_id, "new_role": new_role})
        db.session.commit()
        return jsonify({"message": "Role updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/user-roles/create-account', methods=['POST'])
@role_required('Admin')
def create_account_for_employee():
    emp_id = request.json.get('EmployeeID')
    if not emp_id:
        return jsonify({"error": "EmployeeID is required"}), 400
        
    try:
        repo = SqlCoreHrRepository(db.session)
        service = CoreHrService(repo)
        emp = service.get_employee_details(emp_id)
        if not emp:
            return jsonify({"error": "Employee not found"}), 404
            
        username = emp['EmployeeCode']
        password = 'DefaultPassword@123'
        
        sql = text("EXEC sp_CreateUserForExistingEmployee @EmployeeID = :emp_id, @Username = :username, @PasswordHash = :password")
        db.session.execute(sql, {"emp_id": emp_id, "username": username, "password": password})
        db.session.commit()
        
        return jsonify({"message": "Account created", "Username": username, "Password": password}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/user-roles/<int:user_id>/password', methods=['PUT'])
@role_required('Admin')
def update_user_password(user_id):
    new_password = request.json.get('Password')
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400
        
    # In a real app, hash the password here before saving
    # e.g., hashed_pwd = generate_password_hash(new_password)
    hashed_pwd = new_password 
    
    sql = text("EXEC sp_UpdateUserPassword @UserID = :user_id, @NewPasswordHash = :new_password")
    try:
        db.session.execute(sql, {"user_id": user_id, "new_password": hashed_pwd})
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500