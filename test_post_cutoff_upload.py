import json
from sqlalchemy import text
from app import create_app, db
from app.repositories.sql_time_action_repo import SqlTimeActionRepository
from app.repositories.sql_payroll_repository import SqlPayrollRepository
from app.services.payroll_service import PayrollService

app = create_app()
app.config['TESTING'] = True
with app.app_context():
    print("\n=======================================================")
    print(" 🧪 TESTING POST-CUTOFF ATTENDANCE UPLOADS")
    print("=======================================================\n")

    # 1. Verify July Cutoff Date
    cutoff = db.session.execute(text("SELECT CutoffDate FROM PayrollProcessLog WHERE PayrollYear=2026 AND PayrollMonth=7 AND IsFinalized=1")).scalar()
    print(f"1. Verified July 2026 Payroll Cutoff Date is: {cutoff}")

    # 2. Simulate HR uploading the biometric sheet on August 1st (containing July 26-31 data)
    print("\n2. Simulating HR Biometric Upload for July 28th (KPCB-002 marked as Absent)...")
    repo_time = SqlTimeActionRepository(db.session)
    json_punches = json.dumps([{"EmployeeCode": "KPCB-002", "PunchDate": "2026-07-28", "Status": "Absent"}])
    
    try:
        repo_time.ingest_biometric_data(json_punches)
        status = db.session.execute(text("SELECT Status FROM Attendance WHERE EmployeeID=2 AND Date='2026-07-28'")).scalar()
        print(f"   -> SUCCESS! Database accepted the upload. Status for 2026-07-28 is now: '{status}'")
    except Exception as e:
        print(f"   -> FAILED! Upload was blocked: {e}")

    # 3. Simulate August Payroll Preview to see if the arrears system catches it
    print("\n3. Generating August 2026 Payroll Preview...")
    repo_pay = SqlPayrollRepository(db.session)
    service_pay = PayrollService(repo_pay)
    
    try:
        ledger = service_pay.generate_monthly_payroll(2026, 8)
        emp = next((e for e in ledger if e.get('EmployeeCode') == 'KPCB-002'), None)
        if emp:
            print(f"   -> August Gross Pay: ₹ {emp['TotalGross']:,.2f}")
            print(f"   -> 🚨 August Arrear Deduction (For July 28th): ₹ {emp['ArrearDeduction']:,.2f}")
        else:
            print("Employee not found.")
    except Exception as e:
        print("Error during payroll generation:", e)
