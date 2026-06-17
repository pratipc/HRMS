import json
from sqlalchemy import text
from app import create_app, db
from app.repositories.sql_payroll_repository import SqlPayrollRepository
from app.services.payroll_service import PayrollService

app = create_app()
app.config['TESTING'] = True
with app.app_context():
    repo = SqlPayrollRepository(db.session)
    service = PayrollService(repo)
    
    print("\n=======================================================")
    print(" 🕒 TIME TRAVEL SIMULATION: JULY 2026 PAYROLL PREVIEW")
    print("=======================================================\n")
    print("Context:")
    print(" - June Payroll was finalized on June 22nd.")
    print(" - Employee KPCB-002 took 3 unapproved days off (LWP) on June 25, 26, and 27 (Post-Cutoff).")
    print(" - We are now previewing July's Payroll.\n")
    
    try:
        # Generate July Payroll
        ledger = service.generate_monthly_payroll(2026, 7)
        emp = next((e for e in ledger if e.get('EmployeeCode') == 'KPCB-002'), None)
        
        if emp:
            print(f"Employee: {emp['EmployeeName']} ({emp['EmployeeCode']})")
            print(f"Gross Earnings (July): ₹ {emp['TotalGross']:,.2f}")
            print("--- Deductions ---")
            print(f"Standard Deductions (PF, Tax, etc.): ₹ {emp['TotalDeductions'] - emp['ArrearDeduction']:,.2f}")
            print(f"🚨 ARREAR / LWP DEDUCTION (from June absences): ₹ {emp['ArrearDeduction']:,.2f}")
            print(f"Total Deductions: ₹ {emp['TotalDeductions']:,.2f}")
            print("------------------")
            print(f"💰 FINAL NET PAY: ₹ {emp['FinalNetPay']:,.2f}\n")
            
            # Now Finalize July Payroll
            print("\n=======================================================")
            print(" 🔒 EXECUTING: JULY 2026 PAYROLL FINALIZATION")
            print("=======================================================\n")
            
            result = service.finalize_payroll(2026, 7, 'Admin Test Script')
            print(f"System Response: {result['Status']}")
            
            # Manually update the cutoff date to simulate finalization happening on July 25th
            db.session.execute(text("UPDATE PayrollProcessLog SET CutoffDate = '2026-07-25' WHERE PayrollYear = 2026 AND PayrollMonth = 7"))
            db.session.commit()
            print("✅ Payroll officially locked. July Cutoff Date set to: 2026-07-25.")
            
        else:
            print("Employee not found in ledger.")
            
    except Exception as e:
        import traceback
        print("ERROR:")
        print(traceback.format_exc())
