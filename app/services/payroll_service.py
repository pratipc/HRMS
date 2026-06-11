# File Name: payroll_service.py
# Location: kpcb_hrms/app/services/payroll_service.py

from typing import List, Dict, Any
from app.repositories.interfaces import IPayrollRepository

class PayrollService:
    """
    Business Logic Layer for Payroll Operations.
    Enforces rules and guards before database execution.
    """
    
    def __init__(self, payroll_repo: IPayrollRepository):
        self.payroll_repo = payroll_repo

    def generate_monthly_payroll(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Retrieves the dynamic salary ledger including Saturday and Cash allowances."""
        if not year or not month:
            from datetime import datetime
            now = datetime.now()
            year = now.year
            month = now.month
        return self.payroll_repo.generate_monthly_payroll(year, month)

    def update_basic_pay(self, employee_id: int, basic_pay: float) -> None:
        """Validates bounds and updates an employee's basic pay."""
        if basic_pay < 0:
            raise ValueError("Basic pay cannot be a negative amount.")
        
        if not employee_id:
            raise ValueError("An Employee ID must be specified.")
            
        self.payroll_repo.update_employee_basic(employee_id, basic_pay)

    def get_allowances_config(self) -> Dict[str, float]:
        """Retrieves global allowances for the UI."""
        return self.payroll_repo.get_global_allowances()

    def update_allowances_config(self, da: float, hra: float, ma: float) -> None:
        """Validates bounds and updates the global allowance rules."""
        if da < 0 or hra < 0 or ma < 0:
            raise ValueError("Allowance percentages and values cannot be negative.")
            
        # Optional: You could add max limits here (e.g. DA shouldn't exceed 100%)
        if da > 200 or hra > 100:
            raise ValueError("Allowance percentage exceeds maximum permissible business thresholds.")
            
        self.payroll_repo.update_global_allowances(da, hra, ma)

    def get_saturday_allowance_rates(self) -> List[Dict[str, Any]]:
        """Retrieves the revamped designation-based Saturday allowance rates."""
        return self.payroll_repo.get_saturday_allowance_rates()

    def update_saturday_allowance_rate(self, designation: str, rate: float, rate_id: int = 0, old_designation: str = None) -> None:
        """Validates and updates a specific Saturday allowance rate."""
        if rate < 0:
            raise ValueError("Saturday allowance rate cannot be negative.")
        self.payroll_repo.update_saturday_allowance_rate(designation, rate, rate_id, old_designation)

    def get_payroll_status(self, year: int, month: int) -> Dict[str, Any]:
        """Retrieves status of attendance and payroll finalization."""
        return self.payroll_repo.get_payroll_status(year, month)

    def finalize_payroll(self, year: int, month: int, processed_by: str) -> Dict[str, Any]:
        """Validates and locks the payroll ledger for a specific month."""
        status = self.payroll_repo.get_payroll_status(year, month)
        if not status.get('AttendanceUploaded'):
            raise ValueError("Cannot finalize payroll: Attendance has not been uploaded for this month.")
        
        if status.get('PayrollFinalized'):
            raise ValueError("Payroll for this month is already finalized.")
            
        return self.payroll_repo.finalize_monthly_payroll(year, month, processed_by)