# File Name: sql_core_hr_repository.py
# Location: kpcb_hrms/app/repositories/sql_core_hr_repository.py

from sqlalchemy import text
from typing import List, Dict, Any, Optional
from app.repositories.interfaces import ICoreHrRepository

class SqlCoreHrRepository(ICoreHrRepository):
    """
    Handles data access for Core HR operations (Employee Master) using SQL Server Stored Procedures.
    """

    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_active_employees(self, branch_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetches the lightweight directory list for the main grid, with optional branch filtering."""
        sql = text("EXEC sp_GetActiveEmployees @BranchID = :BranchID")
        result = self.db_session.execute(sql, {"BranchID": branch_id}).mappings().all()
        return [dict(row) for row in result]

    def get_employee_full_profile(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Fetches detailed KYC, banking, and payroll details of a specific employee."""
        # Using your existing stored procedure as requested!
        sql = text("EXEC sp_GetEmployeeDetailsById @EmployeeID = :EmpID")
        result = self.db_session.execute(sql, {"EmpID": employee_id}).mappings().first()
        return dict(result) if result else None

    # Keeping this for backward compatibility in case other services call it by this name
    def get_employee_by_id(self, employee_id: int) -> Dict[str, Any]:
        result = self.get_employee_full_profile(employee_id)
        return result if result else {}

    def create_employee(self, employee_data: dict) -> Dict[str, Any]:
        """Creates a new employee and natively links their initial Basic Pay."""
        sql = text("""
            EXEC sp_CreateEmployee 
                @FirstName = :FirstName, 
                @LastName = :LastName, 
                @Email = :Email, 
                @Department = :Department, 
                @Designation = :Designation, 
                @DateOfJoin = :DateOfJoin,
                @Phone = :Phone,
                @AadharNumber = :AadharNumber,
                @PANNumber = :PANNumber,
                @BankAccountNumber = :BankAccountNumber,
                @BankIFSCCode = :BankIFSCCode,
                @BranchID = :BranchID,
                @BasicPay = :BasicPay
        """)

        result = self.db_session.execute(sql, {
            "FirstName": employee_data.get('FirstName'),
            "LastName": employee_data.get('LastName'),
            "Email": employee_data.get('Email'),
            "Department": employee_data.get('Department'),
            "Designation": employee_data.get('Designation'),
            "DateOfJoin": employee_data.get('DateOfJoin') or employee_data.get('DateOfJoining'),
            "Phone": employee_data.get('Phone'),
            "AadharNumber": employee_data.get('AadharNumber'),
            "PANNumber": employee_data.get('PANNumber'),
            "BankAccountNumber": employee_data.get('BankAccountNumber'),
            "BankIFSCCode": employee_data.get('BankIFSCCode'),
            "BranchID": employee_data.get('BranchID'),
            "BasicPay": float(employee_data.get('BasicPay', 0.00))
        }).mappings().fetchone()

        self.db_session.commit()
        return dict(result) if result else {"status": "success"}

    def bulk_create_employees(self, employees_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes sp_CreateEmployee for a batch of employees to support bulk CSV upload.
        Maps the expanded KYC, banking, and Basic Pay columns from the CSV data.
        """
        sql = text("""
            EXEC sp_CreateEmployee 
                @FirstName = :FirstName, 
                @LastName = :LastName, 
                @Email = :Email, 
                @Department = :Department, 
                @Designation = :Designation, 
                @DateOfJoin = :DateOfJoin,
                @Phone = :Phone,
                @AadharNumber = :AadharNumber,
                @PANNumber = :PANNumber,
                @BankAccountNumber = :BankAccountNumber,
                @BankIFSCCode = :BankIFSCCode,
                @BranchID = :BranchID,
                @BasicPay = :BasicPay
        """)

        results = []
        try:
            for emp in employees_data:
                result = self.db_session.execute(sql, {
                    "FirstName": emp.get('FirstName'),
                    "LastName": emp.get('LastName'),
                    "Email": emp.get('Email'),
                    "Department": emp.get('Department'),
                    "Designation": emp.get('Designation'),
                    "DateOfJoin": emp.get('DateOfJoining') or emp.get('DateOfJoin'),
                    "Phone": emp.get('Phone'),
                    "AadharNumber": emp.get('AadharNumber'),
                    "PANNumber": emp.get('PANNumber'),
                    "BankAccountNumber": emp.get('BankAccountNumber'),
                    "BankIFSCCode": emp.get('BankIFSCCode'),
                    "BranchID": emp.get('BranchID'),
                    "BasicPay": float(emp.get('BasicPay', 0.00))
                }).mappings().fetchone()

                if result:
                    results.append(dict(result))

            # Commit the entire batch as a single transactional block
            self.db_session.commit()
            return results
        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Database Transaction Failed: {str(e)}")

    def update_employee(self, employee_id: int, employee_data: dict) -> Dict[str, Any]:
        """Updates employee profile and their basic compensation via the HR dashboard."""
        sql = text("""
            EXEC sp_UpdateEmployee
                @EmployeeID = :EmployeeID,
                @FirstName = :FirstName,
                @LastName = :LastName,
                @Email = :Email,
                @Department = :Department,
                @Designation = :Designation,
                @DateOfJoin = :DateOfJoin,
                @Phone = :Phone,
                @AadharNumber = :AadharNumber,
                @PANNumber = :PANNumber,
                @BankAccountNumber = :BankAccountNumber,
                @BankIFSCCode = :BankIFSCCode,
                @BranchID = :BranchID,
                @BasicPay = :BasicPay
        """)

        result = self.db_session.execute(sql, {
            "EmployeeID": employee_id,
            "FirstName": employee_data.get('FirstName'),
            "LastName": employee_data.get('LastName'),
            "Email": employee_data.get('Email'),
            "Department": employee_data.get('Department'),
            "Designation": employee_data.get('Designation'),
            "DateOfJoin": employee_data.get('DateOfJoin') or employee_data.get('DateOfJoining'),
            "Phone": employee_data.get('Phone'),
            "AadharNumber": employee_data.get('AadharNumber'),
            "PANNumber": employee_data.get('PANNumber'),
            "BankAccountNumber": employee_data.get('BankAccountNumber'),
            "BankIFSCCode": employee_data.get('BankIFSCCode'),
            "BranchID": employee_data.get('BranchID'),
            "BasicPay": float(employee_data.get('BasicPay', 0.00))
        }).mappings().fetchone()

        self.db_session.commit()
        return dict(result) if result else {"status": "success"}

    # --- Dashboard Metrics ---
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        sql = text("EXEC sp_GetAdminDashboardMetrics")
        result = self.db_session.execute(sql).mappings().fetchone()
        return dict(result) if result else {
            "TotalEmployees": 0,
            "TodayPresent": 0,
            "PendingLeaves": 0,
            "TotalBranches": 0
        }

    def get_branches(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetBranches")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def create_branch(self, branch_data: dict) -> Dict[str, Any]:
        sql = text("EXEC sp_InsertBranch @BranchName = :BranchName, @BranchCode = :BranchCode, @Location = :Location")
        result = self.db_session.execute(sql, {
            "BranchName": branch_data.get('BranchName'),
            "BranchCode": branch_data.get('BranchCode'),
            "Location": branch_data.get('Location')
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    def update_branch(self, branch_id: int, branch_data: dict) -> None:
        sql = text("""
            EXEC sp_UpdateBranch 
                @BranchID = :BranchID, 
                @BranchName = :BranchName, 
                @BranchCode = :BranchCode, 
                @Location = :Location, 
                @IsActive = :IsActive
        """)
        self.db_session.execute(sql, {
            "BranchID": branch_id,
            "BranchName": branch_data.get('BranchName'),
            "BranchCode": branch_data.get('BranchCode'),
            "Location": branch_data.get('Location'),
            "IsActive": 1 if branch_data.get('IsActive') else 0
        })
        self.db_session.commit()