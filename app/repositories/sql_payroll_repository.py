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

    # --- Dynamic Payroll Slabs and Mandates ---
    def get_tax_slabs(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetTaxSlabs")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def save_tax_slab(self, slab_data: Dict[str, Any]) -> None:
        sql = text("""
            EXEC sp_SaveTaxSlab 
                @SlabID = :SlabID, 
                @TaxType = :TaxType, 
                @MinGross = :MinGross, 
                @MaxGross = :MaxGross, 
                @TaxAmount = :TaxAmount
        """)
        self.db_session.execute(sql, {
            "SlabID": slab_data.get('SlabID'),
            "TaxType": slab_data.get('TaxType', 'Professional Tax'),
            "MinGross": slab_data.get('MinGross'),
            "MaxGross": slab_data.get('MaxGross'),
            "TaxAmount": slab_data.get('TaxAmount')
        })
        self.db_session.commit()

    def delete_tax_slab(self, slab_id: int) -> None:
        sql = text("EXEC sp_DeleteTaxSlab @SlabID = :SlabID")
        self.db_session.execute(sql, {"SlabID": slab_id})
        self.db_session.commit()

    def get_designation_slabs(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetDesignationSlabs")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def save_designation_slab(self, designation_data: Dict[str, Any]) -> None:
        sql = text("""
            EXEC sp_SaveDesignationSlab 
                @Designation = :Designation, 
                @GSLISAmount = :GSLISAmount, 
                @SaturdayAllowanceAmount = :SaturdayAllowanceAmount
        """)
        self.db_session.execute(sql, {
            "Designation": designation_data.get('Designation'),
            "GSLISAmount": designation_data.get('GSLISAmount'),
            "SaturdayAllowanceAmount": designation_data.get('SaturdayAllowanceAmount')
        })
        self.db_session.commit()

    def delete_designation_slab(self, designation: str) -> None:
        sql = text("EXEC sp_DeleteDesignationSlab @Designation = :Designation")
        self.db_session.execute(sql, {"Designation": designation})
        self.db_session.commit()

    def get_employee_mandates(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetEmployeeMandates")
        result = self.db_session.execute(sql).mappings().all()

        # Format datetimes
        formatted_result = []
        for row in result:
            row_dict = dict(row)
            if row_dict.get('LastUpdated'):
                row_dict['LastUpdated'] = str(row_dict['LastUpdated'])
            formatted_result.append(row_dict)

        return formatted_result

    def save_employee_mandate(self, mandate_data: Dict[str, Any]) -> None:
        sql = text("""
            EXEC sp_SaveEmployeeMandate 
                @EmployeeID = :EmployeeID, 
                @IncomeTax = :IncomeTax, 
                @LoanEMI = :LoanEMI, 
                @SalaryAdvance = :SalaryAdvance, 
                @LICPremium = :LICPremium
        """)
        self.db_session.execute(sql, {
            "EmployeeID": mandate_data.get('EmployeeID'),
            "IncomeTax": mandate_data.get('IncomeTax', 0.0),
            "LoanEMI": mandate_data.get('LoanEMI', 0.0),
            "SalaryAdvance": mandate_data.get('SalaryAdvance', 0.0),
            "LICPremium": mandate_data.get('LICPremium', 0.0)
        })
        self.db_session.commit()

    def process_bulk_mandates(self, json_data: str) -> int:
        sql = text("EXEC sp_UpdateMandatesBulk @JsonData = :JsonData")
        result = self.db_session.execute(sql, {"JsonData": json_data})
        
        success_count = 0
        if result.returns_rows:
            row = result.mappings().fetchone()
            if row and row.get('SuccessCount'):
                success_count = row['SuccessCount']
                
        self.db_session.commit()
        return success_count