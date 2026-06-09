# File Name: interfaces.py
# Location: kpcb_hrms/app/repositories/interfaces.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

# ---------------------------------------------------------
# AUTHENTICATION DOMAIN
# ---------------------------------------------------------
class IAuthRepository(ABC):
    """Handles authentication and user registration."""
    @abstractmethod
    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def register_user(self, user_data: dict) -> Dict[str, Any]:
        pass

# ---------------------------------------------------------
# CORE HR DOMAIN
# ---------------------------------------------------------
class ICoreHrRepository(ABC):
    """
    Domain: Core HR
    Handles Employee Master, Designations, Departments, and basic profile data.
    """
    @abstractmethod
    def get_all_active_employees(self, branch_id: Optional[int] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_employee(self, employee_data: dict) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_employee_by_id(self, employee_id: int) -> Dict[str, Any]:
        """Fetches complete detailed profile of an employee."""
        pass

    @abstractmethod
    def update_employee(self, employee_id: int, employee_data: dict) -> Dict[str, Any]:
        """Updates the database profile details for an existing employee."""
        pass

    # --- Branch Management ---
    @abstractmethod
    def get_branches(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_branch(self, branch_data: dict) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_branch(self, branch_id: int, branch_data: dict) -> None:
        pass

    # --- Dashboard Metrics ---
    @abstractmethod
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        pass
# ---------------------------------------------------------
# TIME & ACTION DOMAIN
# ---------------------------------------------------------
class ITimeActionRepository(ABC):
    """
    Domain: Time & Action
    Handles Biometric/Web Attendance, Leaves, Holidays, and Shifts.
    """
    # --- BIOMETRIC ---
    # Biometric & Roster
    @abstractmethod
    def get_monthly_attendance_register(self, month_str: str) -> List[Dict[str, Any]]: pass
    
    @abstractmethod
    def ingest_biometric_data(self, json_punches: str) -> dict: pass

    # --- Attendance ---
    @abstractmethod
    def punch_in(self, employee_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_monthly_attendance_register(self, month_str: str) -> List[Dict[str, Any]]: 
        """Fetches flat monthly attendance records for Python aggregation."""
        pass
        
    # --- Leave Management ---
    @abstractmethod
    def apply_leave(self, leave_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_leave_types(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_leave_type(self, type_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_leave_type(self, type_id: int, type_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    # --- Leave Transactions & Approvals ---
    @abstractmethod
    def get_pending_leave_applications(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def process_leave_application(self, application_id: int, status: str) -> Dict[str, Any]:
        pass

    # --- Leave Capping Engine ---
    @abstractmethod
    def execute_year_end_processing(self, current_year: int, processed_by: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_employee_leave_balances(self, year: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_employee_leave_balances_by_id(self, employee_id: int, year: int) -> List[Dict[str, Any]]:
        """Fetches leave balances for a specific employee and calendar year."""
        pass

    @abstractmethod
    def get_employee_leave_summary(self, employee_id: int, year: int) -> Dict[str, Any]:
        """Fetches high-level leave summary metrics for the employee dashboard."""
        pass

    @abstractmethod
    def is_year_locked(self, year: int) -> bool:
        """Checks if a year-end processing run is finalized and locked."""
        pass


    # --- Holiday Calendar ---
    @abstractmethod
    def get_holidays_by_year(self, year: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def add_holiday(self, holiday_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update_holiday(self, holiday_id: int, holiday_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

# ---------------------------------------------------------
# PAYROLL & COMPENSATION DOMAIN
# ---------------------------------------------------------
class IPayrollRepository(ABC):
    """Handles Payroll calculations, scales, and global allowance parameters."""
    @abstractmethod
    def get_salary_ledger(self) -> List[Dict[str, Any]]: 
        """Returns the real-time dynamic salary ledger for all active employees."""
        pass
        
    @abstractmethod
    def update_employee_basic(self, employee_id: int, basic_pay: float) -> None: 
        """Assigns a custom base scale directly to a specific employee profile."""
        pass
        
    @abstractmethod
    def get_global_allowances(self) -> Dict[str, float]: 
        """Retrieves global banking allowances (DA, HRA, MA)."""
        pass
        
    @abstractmethod
    def update_global_allowances(self, da: float, hra: float, ma: float) -> None: 
        """Overwrites global banking allowances, instantly triggering ledger recalculations."""
        pass