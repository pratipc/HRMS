# File Name: sql_leave_repository.py
# Location: kpcb_hrms/app/repositories/sql_leave_repository.py

from sqlalchemy import text
from typing import Dict, Any
from app.repositories.interfaces import ILeaveRepository

class SqlLeaveRepository(ILeaveRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    def apply_leave(self, leave_data: Dict[str, Any]) -> Dict[str, Any]:
        sql = text("""
            EXEC sp_ApplyLeave 
                @EmployeeID = :EmployeeID,
                @LeaveTypeID = :LeaveTypeID,
                @StartDate = :StartDate,
                @EndDate = :EndDate,
                @Reason = :Reason
        """)
        
        result = self.db_session.execute(sql, {
            "EmployeeID": leave_data.get('EmployeeID'),
            "LeaveTypeID": leave_data.get('LeaveTypeID'), # E.g., 1 for Casual Leave, 2 for Sick Leave
            "StartDate": leave_data.get('StartDate'),
            "EndDate": leave_data.get('EndDate'),
            "Reason": leave_data.get('Reason')
        }).mappings().fetchone()
        
        self.db_session.commit()
        return dict(result) if result else {}