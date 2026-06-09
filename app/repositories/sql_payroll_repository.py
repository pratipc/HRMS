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

    def get_global_allowances(self):
        sql = text("SELECT ComponentName, ComponentValue FROM GlobalPayrollConfig")
        rows = self.db_session.execute(sql).mappings().all()
        return {row['ComponentName']: float(row['ComponentValue']) for row in rows}

    def update_global_allowances(self, da: float, hra: float, ma: float):
        sql = text("EXEC sp_UpdateGlobalAllowances @DA = :DA, @HRA = :HRA, @MA = :MA")
        self.db_session.execute(sql, {"DA": da, "HRA": hra, "MA": ma})
        self.db_session.commit()