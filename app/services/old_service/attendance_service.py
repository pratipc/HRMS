# File Name: attendance_service.py
# Location: kpcb_hrms/app/services/attendance_service.py

from app.repositories.interfaces import IAttendanceRepository

class AttendanceService:
    def __init__(self, attendance_repo: IAttendanceRepository):
        self.attendance_repo = attendance_repo

    def record_punch_in(self, employee_id: int) -> dict:
        if not employee_id:
            raise ValueError("Employee ID is required to punch in.")
            
        try:
            return self.attendance_repo.punch_in(employee_id)
        except Exception as e:
            # Catch the RAISERROR from our Stored Procedure
            if 'already punched in' in str(e):
                raise ValueError("You have already punched in for today.")
            raise RuntimeError(f"Database error during punch in: {str(e)}")