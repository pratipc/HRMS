# File Name: core_hr_service.py
# Location: kpcb_hrms/app/services/core_hr_service.py

from typing import List, Dict, Any, Optional
from app.repositories.interfaces import ICoreHrRepository

class CoreHrService:
    """
    Business logic layer for Core HR operations. 
    Validates data and applies business rules before talking to the repository.
    """

    def __init__(self, hr_repo: ICoreHrRepository):
        self.hr_repo = hr_repo

    def get_active_employees(self, branch_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves the list of active employees, optionally filtered by branch."""
        # We can add business logic here in the future if needed
        # (e.g., masking emails, calculating tenure)
        return self.hr_repo.get_all_active_employees(branch_id)

    def get_employee_full_profile(self, employee_id: int) -> Dict[str, Any]:
        """Lazy-loads complete decrypted KYC, banking, and compensation details of a specific employee."""
        if not employee_id:
            raise ValueError("Employee ID must be provided.")
        return self.hr_repo.get_employee_full_profile(employee_id)

    def create_new_employee(self, employee_data: dict) -> Dict[str, Any]:
        """Validates input and creates a new employee."""

        # 1. Business Validation
        required_fields = ['FirstName', 'LastName', 'Email', 'DateOfJoining', 'BranchID']
        missing_fields = [field for field in required_fields if not employee_data.get(field)]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # (Optional) Future enhancement: Check if email format is valid here using Regex

        # 2. Delegate to Repository to persist data
        try:
            return self.hr_repo.create_employee(employee_data)
        except Exception as e:
            # Catching potential DB constraints (like duplicate email)
            raise RuntimeError(f"Failed to create employee: {str(e)}")

    def get_employee_details(self, employee_id: int) -> Dict[str, Any]:
        """Retrieves and validates detailed profile information."""
        if not employee_id:
            raise ValueError("Employee ID is required.")
        return self.hr_repo.get_employee_by_id(employee_id)

    def update_employee_profile(self, employee_id: int, employee_data: dict) -> Dict[str, Any]:
        """Validates parameters and updates the employee record with Stored Procedure exception handling."""
        required_fields = ['FirstName', 'LastName', 'Email', 'DateOfJoining', 'BranchID']
        missing_fields = [field for field in required_fields if not employee_data.get(field)]

        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        try:
            return self.hr_repo.update_employee(employee_id, employee_data)
        except Exception as e:
            error_msg = str(e)
            # Safely parse Raiserror exceptions from the SQL Transaction layer
            if '[SQL Server]' in error_msg:
                clean_msg = error_msg.split('[SQL Server]')[-1]
                if ' (' in clean_msg:
                    clean_msg = clean_msg.split(' (')[0]
                clean_msg = clean_msg.replace("')", "").strip()
                raise ValueError(clean_msg)
            raise RuntimeError(f"Database error: {error_msg}")

    # --- Branch Management ---
    def get_branches(self) -> List[Dict[str, Any]]:
        """Retrieves all active bank branches."""
        return self.hr_repo.get_branches()

    def create_branch(self, branch_data: dict) -> Dict[str, Any]:
        """Validates and creates a new branch."""
        if not branch_data.get('BranchName') or not branch_data.get('BranchCode'):
            raise ValueError("Branch Name and Branch Code are required.")
        try:
            return self.hr_repo.create_branch(branch_data)
        except Exception as e:
            if 'UNIQUE' in str(e).upper():
                raise ValueError("Branch Code already exists.")
            raise RuntimeError(f"Failed to create branch: {str(e)}")

    def update_branch(self, branch_id: int, branch_data: dict) -> None:
        """Validates and updates an existing branch."""
        if not branch_id:
            raise ValueError("Branch ID is required.")
        if not branch_data.get('BranchName') or not branch_data.get('BranchCode'):
            raise ValueError("Branch Name and Branch Code are required.")
        try:
            self.hr_repo.update_branch(branch_id, branch_data)
        except Exception as e:
            if 'UNIQUE' in str(e).upper():
                raise ValueError("Branch Code already exists.")
            raise RuntimeError(f"Failed to update branch: {str(e)}")

    # --- Dashboard Metrics ---
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Fetches summarized KPI metrics for the Admin Dashboard."""
        return self.hr_repo.get_dashboard_metrics()