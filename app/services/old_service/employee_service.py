# File Name: employee_service.py
# Location: kpcb_hrms/app/services/employee_service.py

from typing import List, Dict, Any
from app.repositories.interfaces import IEmployeeRepository

class EmployeeService:
    """
    Business logic layer for Employee operations. 
    Validates data and applies business rules before talking to the repository.
    """

    def __init__(self, employee_repo: IEmployeeRepository):
        self.employee_repo = employee_repo

    def get_active_employees(self) -> List[Dict[str, Any]]:
        """Retrieves the list of active employees."""
        # We can add business logic here in the future if needed
        # (e.g., masking emails, calculating tenure)
        return self.employee_repo.get_all_active_employees()

    def create_new_employee(self, employee_data: dict) -> Dict[str, Any]:
        """Validates input and creates a new employee."""
        
        # 1. Business Validation
        required_fields = ['FirstName', 'LastName', 'Email', 'DateOfJoining']
        missing_fields = [field for field in required_fields if not employee_data.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # (Optional) Future enhancement: Check if email format is valid here using Regex
        
        # 2. Delegate to Repository to persist data
        try:
            return self.employee_repo.create_employee(employee_data)
        except Exception as e:
            # Catching potential DB constraints (like duplicate email)
            raise RuntimeError(f"Failed to create employee: {str(e)}")