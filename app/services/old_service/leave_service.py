# File Name: leave_service.py
# Location: kpcb_hrms/app/services/leave_service.py

from typing import Dict, Any
from app.repositories.interfaces import ILeaveRepository

class LeaveService:
    def __init__(self, leave_repo: ILeaveRepository):
        self.leave_repo = leave_repo

    def submit_leave_application(self, employee_id: int, leave_data: dict) -> Dict[str, Any]:
        if not employee_id:
            raise ValueError("Employee ID is required to apply for leave.")
            
        required_fields = ['LeaveTypeID', 'StartDate', 'EndDate', 'Reason']
        missing = [field for field in required_fields if not leave_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        # Attach the secure session employee_id to the data payload
        leave_data['EmployeeID'] = employee_id
            
        try:
            return self.leave_repo.apply_leave(leave_data)
        except Exception as e:
            if 'earlier than Start Date' in str(e):
                raise ValueError("End Date cannot be earlier than Start Date.")
            raise RuntimeError(f"Database error during leave application: {str(e)}")