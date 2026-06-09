# File Name: sql_time_action_repo.py
# Location: kpcb_hrms/app/repositories/sql_time_action_repo.py

from sqlalchemy import text
from typing import Dict, Any, List
import datetime
from app.repositories.interfaces import ITimeActionRepository

class SqlTimeActionRepository(ITimeActionRepository):
    def __init__(self, db_session):
        self.db_session = db_session

# =====================================================================
    # #CODE CHANGE: Helper method to prevent 500 Internal Server Errors!
    # Flask jsonify() crashes on datetime objects. This converts all
    # SQL datetimes, dates, and times (like CreatedDTime) into safe strings.
    # =====================================================================
    def _sanitize_row(self, row: dict) -> Dict[str, Any]:
        sanitized = dict(row)
        for k, v in sanitized.items():
            if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
                sanitized[k] = str(v)
        return sanitized

    # --- BIOMETRIC INGESTION & ROSTER ---
    def get_monthly_attendance_register(self, month_str: str) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetMonthlyAttendanceRegister @TargetMonth = :MonthStr")
        result = self.db_session.execute(sql, {"MonthStr": month_str}).mappings().all()
        # #CODE CHANGE: Pass result through the sanitizer to prevent 500 errors
        return [self._sanitize_row(row) for row in result]
    
    def ingest_biometric_data(self, json_punches: str) -> dict:
        sql = text("EXEC sp_IngestBiometricPunches @JsonData = :JsonPunches")
        result = self.db_session.execute(sql, {"JsonPunches": json_punches}).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {"status": "success"}

    def get_daily_attendance_register(self, date_str: str) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetDailyAttendanceRegister @RegisterDate = :RegDate")
        result = self.db_session.execute(sql, {"RegDate": date_str}).mappings().all()
        return [self._sanitize_row(row) for row in result]

    def assign_cash_counter(self, employee_id: int, date_str: str, is_assigned: bool) -> None:
        sql = text("EXEC sp_AssignCashCounter @EmployeeID = :EmpID, @Date = :Date, @IsAssigned = :IsAssigned")
        self.db_session.execute(sql, {
            "EmpID": employee_id, "Date": date_str, "IsAssigned": 1 if is_assigned else 0
        })
        self.db_session.commit()

    # --- ATTENDANCE ---
    def punch_in(self, employee_id: int) -> Dict[str, Any]:
        sql = text("EXEC sp_EmployeePunchIn @EmployeeID = :EmployeeID")
        result = self.db_session.execute(sql, {"EmployeeID": employee_id}).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    # --- LEAVES ---
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
            "LeaveTypeID": leave_data.get('LeaveTypeID'),
            "StartDate": leave_data.get('StartDate'),
            "EndDate": leave_data.get('EndDate'),
            "Reason": leave_data.get('Reason')
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}
    

    def get_leave_types(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetLeaveTypes")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def add_leave_type(self, type_data: Dict[str, Any]) -> Dict[str, Any]:
        sql = text("""
            EXEC sp_InsertLeaveType 
                @TypeName = :TypeName,
                @QtyPerYear = :QtyPerYear,
                @CreditPeriod = :CreditPeriod,
                @IsCarryForward = :IsCarryForward,
                @MaxCarryForward = :MaxCarryForward
        """)
        result = self.db_session.execute(sql, {
            "TypeName": type_data.get('TypeName'),
            "QtyPerYear": type_data.get('QtyPerYear'),
            "CreditPeriod": type_data.get('CreditPeriod'),
            "IsCarryForward": type_data.get('IsCarryForward', False),
            "MaxCarryForward": type_data.get('MaxCarryForward', 0.0)
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    def update_leave_type(self, type_id: int, type_data: Dict[str, Any]) -> Dict[str, Any]:
        sql = text("""
            EXEC sp_UpdateLeaveType 
                @LeaveTypeID = :LeaveTypeID,
                @TypeName = :TypeName,
                @QtyPerYear = :QtyPerYear,
                @CreditPeriod = :CreditPeriod,
                @IsCarryForward = :IsCarryForward,
                @MaxCarryForward = :MaxCarryForward
        """)
        result = self.db_session.execute(sql, {
            "LeaveTypeID": type_id,
            "TypeName": type_data.get('TypeName'),
            "QtyPerYear": type_data.get('QtyPerYear'),
            "CreditPeriod": type_data.get('CreditPeriod'),
            "IsCarryForward": type_data.get('IsCarryForward', False),
            "MaxCarryForward": type_data.get('MaxCarryForward', 0.0)
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    # --- LEAVE CAPPING ENGINE ---
    def execute_year_end_processing(self, current_year: int, processed_by: str) -> Dict[str, Any]:
        sql = text("EXEC sp_ExecuteLeaveYearEndProcessing @CurrentYear = :CurrentYear, @ProcessedBy = :ProcessedBy")
        result = self.db_session.execute(sql, {"CurrentYear": current_year, "ProcessedBy": processed_by}).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    def get_employee_leave_balances(self, year: int) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetEmployeeLeaveBalances @CalendarYear = :CalendarYear")
        result = self.db_session.execute(sql, {"CalendarYear": year}).mappings().all()
        return [dict(row) for row in result]

    def is_year_locked(self, year: int) -> bool:
        # Replaced inline SELECT query with a database stored procedure execution block
        sql = text("EXEC sp_CheckYearEndProcessLock @ProcessedYear = :Year")
        result = self.db_session.execute(sql, {"Year": year}).fetchone()
        return True if result and result[0] == 1 else False

    # --- HOLIDAYS ---
    def get_holidays_by_year(self, year: int) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetHolidaysByYear @CalendarYear = :CalendarYear")
        result = self.db_session.execute(sql, {"CalendarYear": year}).mappings().all()
        return [dict(row) for row in result]

    def add_holiday(self, holiday_data: Dict[str, Any]) -> Dict[str, Any]:
        sql = text("""
            EXEC sp_AddHoliday 
                @HolidayDate = :HolidayDate,
                @HolidayName = :HolidayName,
                @HolidayType = :HolidayType
        """)
        result = self.db_session.execute(sql, {
            "HolidayDate": holiday_data.get('HolidayDate'),
            "HolidayName": holiday_data.get('HolidayName'),
            "HolidayType": holiday_data.get('HolidayType', 'Public Holiday')
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    def update_holiday(self, holiday_id: int, holiday_data: Dict[str, Any]) -> Dict[str, Any]:
        sql = text("""
            EXEC sp_UpdateHoliday 
                @HolidayID = :HolidayID,
                @HolidayDate = :HolidayDate,
                @HolidayName = :HolidayName,
                @HolidayType = :HolidayType
        """)
        result = self.db_session.execute(sql, {
            "HolidayID": holiday_id,
            "HolidayDate": holiday_data.get('HolidayDate'),
            "HolidayName": holiday_data.get('HolidayName'),
            "HolidayType": holiday_data.get('HolidayType', 'Public Holiday')
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}

    # --- LEAVE TRANSACTIONS & APPROVALS ---
    def get_pending_leave_applications(self) -> List[Dict[str, Any]]:
        sql = text("EXEC sp_GetPendingLeaveApplications")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def get_processed_leave_applications(self) -> List[Dict[str, Any]]:
        """Fetches approved/rejected leaves for the Admin audit history."""
        sql = text("EXEC sp_GetProcessedLeaveApplications")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def process_leave_application(self, application_id: int, status: str) -> Dict[str, Any]:
        sql = text("EXEC sp_ProcessLeaveApplication @ApplicationID = :ApplicationID, @Status = :Status")
        result = self.db_session.execute(sql, {
            "ApplicationID": application_id,
            "Status": status
        }).mappings().fetchone()
        self.db_session.commit()
        return dict(result) if result else {}
    
    def get_employee_leave_balances_by_id(self, employee_id: int, year: int) -> list:
        """Retrieves active leave balances for a specific employee via Stored Procedure."""
        sql = text("EXEC sp_GetEmployeeLeaveBalancesByID @EmployeeID = :EmployeeID, @CalendarYear = :CalendarYear")
        result = self.db_session.execute(sql, {
            "EmployeeID": employee_id,
            "CalendarYear": year
        }).mappings().all()
        return [dict(row) for row in result]

    def get_employee_leave_summary(self, employee_id: int, year: int) -> Dict[str, Any]:
        """Fetches high-level leave summary metrics for the employee dashboard."""
        sql = text("EXEC sp_GetEmployeeLeaveSummary @EmployeeID = :EmpID, @CalendarYear = :Year")
        result = self.db_session.execute(sql, {"EmpID": employee_id, "Year": year}).mappings().fetchone()
        return dict(result) if result else {
            "LeavesTaken": 0.0,
            "LeavesLeft": 0.0,
            "PendingApprovals": 0
        }

# ----- Weekly Offs Management -----

    def get_weekly_offs(self) -> List[Dict[str, Any]]:
        """Retrieves active weekly off configurations via Stored Procedure."""
        sql = text("EXEC sp_GetWeeklyOffs")
        result = self.db_session.execute(sql).mappings().all()
        return [dict(row) for row in result]

    def update_weekly_offs(self, config_json: str) -> bool:
        """Passes a JSON string of rules to SQL Server to wipe and replace configs."""
        sql = text("EXEC sp_UpdateWeeklyOffs @JsonConfig = :JsonConfig")
        self.db_session.execute(sql, {"JsonConfig": config_json})
        self.db_session.commit()
        return True