
import json
from app import create_app, db
from app.repositories.sql_payroll_repository import SqlPayrollRepository
from app.services.payroll_service import PayrollService

app = create_app()
app.config['TESTING'] = True
with app.app_context():
    repo = SqlPayrollRepository(db.session)
    service = PayrollService(repo)
    
    # 1. Preview June 2026 Payroll
    print("=== Testing Payroll Engine Preview (June 2026) ===")
    try:
        ledger = service.generate_monthly_payroll(2026, 6)
        print(f"Total Employees Processed: {len(ledger)}")
        if len(ledger) > 0:
            # Look for a specific employee like 'John Admin' (ID 41) or just the first one
            emp = next((e for e in ledger if e.get('EmployeeCode') == 'KPCB-002'), ledger[0])
            print(f"\nSample Employee: {emp['EmployeeCode']} - {emp['EmployeeName']} ({emp['Designation']})")
            print(f"Basic Pay: {emp['BasicPay']}")
            print(f"DA: {emp['DA']}, HRA: {emp['HRA']}, MA: {emp['MA']}")
            print(f"Sat. Rate: {emp['SaturdayRate']}, Eligible Sat.: {emp['EligibleSaturdays']}, Sat. Allowance: {emp['SaturdayAllowance']}")
            print(f"Total Gross: {emp['TotalGross']}")
            print(f"--- Deductions ---")
            print(f"PF: {emp['PF']}, IT: {emp['IT']}, E/Cess: {emp['ECess']}, GSLIS: {emp['GSLIS']}")
            print(f"Loan EMI: {emp['LoanEMI']}, Advance: {emp['SalaryAdvance']}, LIC: {emp['LICPremium']}, Prof Tax: {emp['ProfessionalTax']}")
            print(f"Total Deductions: {emp['TotalDeductions']}")
            print(f"==> FINAL NET PAY: {emp['FinalNetPay']}")
        else:
            print("No employees found in ledger.")
    except Exception as e:
        import traceback
        print("ERROR:")
        print(traceback.format_exc())
