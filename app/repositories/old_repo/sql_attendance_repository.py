# File Name: sql_attendance_repository.py
# Location: kpcb_hrms/app/repositories/sql_attendance_repository.py

from sqlalchemy import text
from app.repositories.interfaces import IAttendanceRepository

class SqlAttendanceRepository(IAttendanceRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    def punch_in(self, employee_id: int) -> dict:
        sql = text("EXEC sp_EmployeePunchIn @EmployeeID = :EmployeeID")
        
        result = self.db_session.execute(sql, {"EmployeeID": employee_id}).mappings().fetchone()
        self.db_session.commit()
        
        return dict(result) if result else {}