# File Name: sql_payroll_repository.py
# Location: kpcb_hrms/app/repositories/sql_payroll_repository.py

from sqlalchemy import text
from typing import List, Dict, Any
from app.repositories.interfaces import IPayrollRepository

class SqlPayrollRepository(IPayrollRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    def generate_monthly_payroll(self, year: int, month: int) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GenerateMonthlyPayroll @Year = :Year, @Month = :Month")
        result = self.db_session.execute(sql, {"Year": year, "Month": month}).mappings().all()
        return [dict(row) for row in result]

    def update_employee_basic(self, employee_id: int, basic_pay: float):
        sql = text("EXEC sp_UpdateEmployeeBasicPay @EmployeeID = :EmpID, @BasicPay = :BasicPay")
        self.db_session.execute(sql, {"EmpID": employee_id, "BasicPay": basic_pay})
        self.db_session.commit()

    def get_global_allowances(self) -> Dict[str, float]:
        sql = text("EXEC sp_GetGlobalAllowances")
        result = self.db_session.execute(sql).mappings().all()
        return {row['ComponentName']: float(row['ComponentValue']) for row in result}

    def update_global_allowances(self, da: float, hra: float, ma: float):
        sql = text("EXEC sp_UpdateGlobalAllowances @DA = :DA, @HRA = :HRA, @MA = :MA")
        self.db_session.execute(sql, {"DA": da, "HRA": hra, "MA": ma})
        self.db_session.commit()

    def get_saturday_allowance_rates(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetSaturdayAllowanceRates")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def update_saturday_allowance_rate(self, designation: str, rate: float, rate_id: int = 0, old_designation: str = None) -> None:
        sql = text("EXEC sp_UpdateSaturdayAllowanceRate @rate_id = :rate_id, @old_designation = :old_designation, @designation = :designation, @rate = :rate")
        self.db_session.execute(sql, {"rate_id": rate_id, "old_designation": old_designation, "designation": designation, "rate": rate})
        self.db_session.commit()

    def get_payroll_status(self, year: int, month: int) -> Dict[str, Any]:
        sql = text("EXEC sp_GetPayrollStatus @Year = :Year, @Month = :Month")
        result = self.db_session.execute(sql, {"Year": year, "Month": month}).mappings().fetchone()
        return dict(result) if result else {"AttendanceUploaded": False, "PayrollFinalized": False}

    def finalize_monthly_payroll(self, year: int, month: int, processed_by: str) -> Dict[str, Any]:
        sql = text("EXEC sp_FinalizeMonthlyPayroll @Year = :Year, @Month = :Month, @ProcessedBy = :ProcessedBy")
        result = self.db_session.execute(sql, {"Year": year, "Month": month, "ProcessedBy": processed_by}).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {"Status": "Failed"}