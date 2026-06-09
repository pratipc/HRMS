# File Name: time_action_service.py
# Location: kpcb_hrms/app/services/time_action_service.py

from datetime import datetime
from typing import Dict, Any, List
from app.repositories.interfaces import ITimeActionRepository
import json
class TimeActionService:
    def __init__(self, time_repo: ITimeActionRepository):
        self.time_repo = time_repo
    
    # --- BIOMETRIC & ATTENDANCE SWEPES (UPDATED) ---
    def process_biometric_upload(self, file) -> tuple:
        """
        Bespoke ETL Parser for KPCB's 'Monthly Basic Report' biometric exports.
        Scans metadata, extracts headers, maps daily P/A statuses, and formats Employee IDs.
        Handles both raw CSVs and Pandas-parsed XLS DataFrames seamlessly.
        """
        import csv
        import re
        import json
        from datetime import datetime

        rows = []
        filename = file.filename.lower()
        
        # --- EXCEL / CSV HANDLING LOGIC ---
        if filename.endswith(('.xls', '.xlsx')):
            try:
                import pandas as pd
                # Read Excel forcing all columns to be strings.
                # NOTE: Pandas may convert date cells to 'YYYY-MM-DD HH:MM:SS' strings.
                df = pd.read_excel(file, header=None, dtype=str).fillna('')
                rows = df.values.tolist()
            except Exception:
                # Fallback: Biometric machines often output HTML/CSV with a fake .xls extension.
                file.stream.seek(0)
                content = file.stream.read().decode('utf-8-sig', errors='replace').splitlines()
                delimiter = '\t' if content and '\t' in content[0] else ','
                reader = csv.reader(content, delimiter=delimiter)
                rows = list(reader)
        else:
            content = file.stream.read().decode('utf-8-sig', errors='replace').splitlines()
            reader = csv.reader(content)
            rows = list(reader)

        year = datetime.now().year
        
        # 1. Extract exact year from the report metadata
        for row in rows[:15]:
            for cell in row:
                match = re.search(r'\d{2}-[A-Za-z]{3}-(\d{4})', str(cell))
                if match:
                    year = int(match.group(1))
                    break

        # 2. Find the header row and map the date columns
        header_row_idx = -1
        day_columns = {}  # { col_index: "YYYY-MM-DD" }
        
        for i, row in enumerate(rows):
            date_count = 0
            temp_day_cols = {}
            
            for col_idx, cell in enumerate(row):
                cell_str = str(cell).strip()
                if not cell_str:
                    continue
                    
                # Format A: Standard String ('01-May')
                match_str = re.search(r'^(\d{1,2}-[A-Za-z]{3})', cell_str)
                # Format B: Pandas Datetime ('2026-05-01 00:00:00')
                match_dt = re.match(r'^(\d{4}-\d{2}-\d{2})', cell_str)
                
                if match_str:
                    try:
                        date_obj = datetime.strptime(f"{match_str.group(1)[:6]}-{year}", "%d-%b-%Y")
                        temp_day_cols[col_idx] = date_obj.strftime("%Y-%m-%d")
                        date_count += 1
                    except Exception:
                        pass
                elif match_dt:
                    temp_day_cols[col_idx] = match_dt.group(1)
                    date_count += 1

            # A valid header row should have at least 20 date columns mapped
            if date_count >= 20:
                header_row_idx = i
                day_columns = temp_day_cols
                break

        if header_row_idx == -1 or not day_columns:
            raise ValueError("Could not detect the date headers (e.g., '01-May' or 'YYYY-MM-DD') in the uploaded file.")

        # 3. Dynamically locate the 'Emp Code' column (Pandas and CSV shift columns differently)
        emp_code_col_idx = -1
        
        # Scan the rows around the header for the Employee Code label
        for i in range(max(0, header_row_idx - 3), header_row_idx + 2):
            for col_idx, cell in enumerate(rows[i]):
                clean_val = re.sub(r'[^a-z]', '', str(cell).strip().lower())
                if clean_val in ['ecode', 'empcode', 'employeecode']:
                    emp_code_col_idx = col_idx
                    break
            if emp_code_col_idx != -1:
                break
                
        # Fallback if label is missing
        if emp_code_col_idx == -1:
            emp_code_col_idx = 1 if filename.endswith(('.xls', '.xlsx')) else 2

        # 4. Parse Employee Rows (Data Matrix)
        records = []
        
        for row in rows[header_row_idx + 1:]:
            if len(row) < 5:
                continue
                
            # Safely grab the employee code
            emp_code_raw = ""
            if emp_code_col_idx < len(row):
                emp_code_raw = str(row[emp_code_col_idx]).strip()
                
            # Clean up Pandas float conversion (e.g., '2.0' -> '2')
            if emp_code_raw.endswith('.0'):
                emp_code_raw = emp_code_raw[:-2]
            
            # Skip empty rows or summary rows
            if not emp_code_raw or not emp_code_raw.isdigit():
                continue
                
            emp_code = f"KPCB-{int(emp_code_raw):03d}"
            
            # Extract daily statuses mapped precisely to the correct index!
            for col_idx, date_str in day_columns.items():
                if col_idx < len(row):
                    status_raw = str(row[col_idx]).strip().upper()
                    
                    status_mapped = None
                    if status_raw == 'P': status_mapped = 'Present'
                    elif status_raw == 'A': status_mapped = 'Absent'
                    elif status_raw == 'WO': status_mapped = 'Weekly Off'
                    elif status_raw == 'L': status_mapped = 'Leave'
                    elif status_raw == 'HD': status_mapped = 'Half-Day'
                        
                    if status_mapped:
                        records.append({
                            "EmployeeCode": emp_code,
                            "PunchDate": date_str,
                            "Status": status_mapped
                        })

        if not records:
            raise ValueError("No valid attendance punch data could be extracted. Please ensure the format matches the standard report.")

        # 5. Dump to JSON and dispatch to repository
        json_payload = json.dumps(records)
        self.time_repo.ingest_biometric_data(json_payload)
        
        return len(records), []

    def fetch_monthly_register(self, month_str: str) -> List[Dict[str, Any]]:
        """
        Fetches flat SQL data and aggregates it into a nested JSON structure.
        """
        if not month_str:
            month_str = datetime.now().strftime("%Y-%m")
            
        flat_data = self.time_repo.get_monthly_attendance_register(month_str)
        employees = {}
        
        for row in flat_data:
            emp_id = row['EmployeeID']
            
            if emp_id not in employees:
                employees[emp_id] = {
                    "EmployeeID": emp_id,
                    "EmployeeCode": row.get('EmployeeCode', ''),
                    "EmployeeName": row.get('EmployeeName', ''),
                    "Designation": row.get('Designation', ''),
                    "Department": row.get('Department', ''),
                    "Attendance": {},
                    "AuditLogs": {}, # #CODE CHANGE: Safe dictionary to hold the audit/timestamp data
                    "TotalPresent": 0,
                    "TotalAbsent": 0,
                    "TotalLeave": 0,
                    "TotalOffs": 0
                }
            
            day = row.get('DayOfMonth')
            status = row.get('Status')
            
            if day and status and status != 'Unmarked':
                day_str = str(day)
                employees[emp_id]["Attendance"][day_str] = status
                
                # #CODE CHANGE: Pack the exact audit and time data into the response safely!
                employees[emp_id]["AuditLogs"][day_str] = {
                    "InTime": row.get('InTime'),
                    "OutTime": row.get('OutTime'),
                    "CreatedDTime": row.get('CreatedDTime'),
                    "UpdatedDTime": row.get('UpdatedDTime')
                }
                
                if status == 'Present' or status == 'Half-Day':
                    employees[emp_id]["TotalPresent"] += 1
                elif status == 'Absent':
                    employees[emp_id]["TotalAbsent"] += 1
                elif status == 'Leave':
                    employees[emp_id]["TotalLeave"] += 1
                elif status in ['Weekly Off', 'Holiday']:
                    employees[emp_id]["TotalOffs"] += 1
                    
        return list(employees.values())

    def fetch_daily_register(self, date_str: str) -> List[Dict[str, Any]]:
        """Ensures sweep is processed and returns the complete daily attendance register."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return self.time_repo.get_daily_attendance_register(date_str)

    def set_cash_counter_duty(self, employee_id: int, date_str: str, is_assigned: bool) -> None:
        if not employee_id or not date_str:
            raise ValueError("EmployeeID and Date are required properties.")
        self.time_repo.assign_cash_counter(employee_id, date_str, is_assigned)

    # ---------------------------------------------------------
    # ATTENDANCE LOGIC
    # ---------------------------------------------------------
    def record_punch_in(self, employee_id: int) -> Dict[str, Any]:
        """Records employee daily punch-in via biometric or fallback channels."""
        if not employee_id:
            raise ValueError("Employee ID is required to punch in.")
        try:
            return self.time_repo.punch_in(employee_id)
        except Exception as e:
            if 'already punched in' in str(e):
                raise ValueError("You have already punched in for today.")
            raise RuntimeError(f"Database error during punch in: {str(e)}")

    # ---------------------------------------------------------
    # LEAVE APPLICATION & INQUIRY LOGIC
    # ---------------------------------------------------------
    def submit_leave_application(self, employee_id: int, leave_data: dict) -> Dict[str, Any]:
        """Submits a new pending leave request with strict chronological and balance validation."""
        if not employee_id:
            raise ValueError("Employee ID is required to apply for leave.")
            
        required_fields = ['LeaveTypeID', 'StartDate', 'EndDate', 'Reason']
        missing = [field for field in required_fields if not leave_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        leave_data['EmployeeID'] = employee_id
            
        try:
            return self.time_repo.apply_leave(leave_data)
        except Exception as e:
            error_msg = str(e)
            
            # Catch strict SQL Raiserror validations (like early end dates or balance overdrafts)
            if 'earlier than Start Date' in error_msg:
                raise ValueError("End Date cannot be earlier than Start Date.")
            elif 'Insufficient leave balance' in error_msg:
                # Scrape out the SQL error block cleanly to display to the user
                clean_msg = error_msg.split(']')[-1].strip() if ']' in error_msg else error_msg
                raise ValueError(clean_msg)
                
            raise RuntimeError(f"Database error during leave application: {error_msg}")

    def fetch_employee_leave_balances_by_id(self, employee_id: int, year: int) -> List[Dict[str, Any]]:
        """Retrieves active leave balances for a specific employee in a given calendar year."""
        if not employee_id:
            raise ValueError("Employee ID is required.")
        target_year = year if year else datetime.now().year
        return self.time_repo.get_employee_leave_balances_by_id(employee_id, target_year)

    def get_leave_summary(self, employee_id: int, year: int) -> Dict[str, Any]:
        """Fetches high-level leave metrics (Taken, Left, Pending) for the dashboard."""
        if not employee_id:
            raise ValueError("Employee ID is required.")
        target_year = year if year else datetime.now().year
        return self.time_repo.get_employee_leave_summary(employee_id, target_year)

    def fetch_pending_leave_applications(self) -> List[Dict[str, Any]]:
        """Retrieves all active, unprocessed 'Pending' leave applications for manager review."""
        return self.time_repo.get_pending_leave_applications()

    def fetch_processed_leave_applications(self) -> List[Dict[str, Any]]:
        """Retrieves historical approved/rejected leave applications for audit."""
        return self.time_repo.get_processed_leave_applications()

    def process_leave_application(self, application_id: int, status: str) -> Dict[str, Any]:
        """Approves or Rejects a leave request and triggers live ledger recalculations."""
        if not application_id:
            raise ValueError("Application ID is required.")
        if status not in ['Approved', 'Rejected']:
            raise ValueError("Status must be either Approved or Rejected.")
            
        try:
            return self.time_repo.process_leave_application(application_id, status)
        except Exception as e:
            error_msg = str(e)
            
            # Catch ANY strict SQL Raiserror validation from SQL Server
            if '[SQL Server]' in error_msg:
                # 1. Extract the raw message after the last [SQL Server] tag
                clean_msg = error_msg.split('[SQL Server]')[-1]
                
                # 2. Strip trailing database driver metadata (e.g. "(50000) (SQLExecDirectW)")
                if ' (' in clean_msg:
                    clean_msg = clean_msg.split(' (')[0]
                
                # 3. Remove trailing parenthesis/quotes left from the pyodbc tuple string
                clean_msg = clean_msg.replace("')", "").strip()
                
                # Raise as ValueError so Flask returns a 400 Bad Request to the Admin UI
                raise ValueError(clean_msg)
                
            raise RuntimeError(f"Failed to process leave application: {error_msg}")

    # ---------------------------------------------------------
    # LEAVE POLICY CONFIGURATION
    # ---------------------------------------------------------
    def fetch_leave_types(self) -> List[Dict[str, Any]]:
        """Fetches all globally configured leave types."""
        return self.time_repo.get_leave_types()

    def create_leave_policy(self, type_data: dict) -> Dict[str, Any]:
        """Creates a new global leave type category."""
        required_fields = ['TypeName', 'QtyPerYear', 'CreditPeriod']
        missing = [field for field in required_fields if not type_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        try:
            qty = float(type_data['QtyPerYear'])
            max_cf = float(type_data.get('MaxCarryForward', 0))
            
            if qty <= 0:
                raise ValueError("Total Days/Year must be greater than zero.")
            if max_cf < 0:
                raise ValueError("Carry-Forward limit cannot be negative.")
                
            type_data['QtyPerYear'] = qty
            type_data['MaxCarryForward'] = max_cf
            return self.time_repo.add_add_leave_type(type_data)
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise RuntimeError(f"Failed to create leave policy: {str(e)}")

    def modify_leave_policy(self, type_id: int, type_data: dict) -> Dict[str, Any]:
        """Updates configurations for an existing leave type."""
        required_fields = ['TypeName', 'QtyPerYear', 'CreditPeriod']
        missing = [field for field in required_fields if not type_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        try:
            qty = float(type_data['QtyPerYear'])
            max_cf = float(type_data.get('MaxCarryForward', 0))
            
            if qty <= 0:
                raise ValueError("Total Days/Year must be greater than zero.")
            if max_cf < 0:
                raise ValueError("Carry-Forward limit cannot be negative.")
                
            type_data['QtyPerYear'] = qty
            type_data['MaxCarryForward'] = max_cf
            return self.time_repo.update_leave_type(type_id, type_data)
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise RuntimeError(f"Failed to update leave policy: {str(e)}")

    # ---------------------------------------------------------
    # LEAVE CAPPING ENGINE LOGIC
    # ---------------------------------------------------------
    def run_year_end_processing(self, year: int, processed_by: str) -> Dict[str, Any]:
        """Executes the year-end carry-forward capping process if not already locked."""
        if not year or year < 2000 or year > 2100:
            raise ValueError("Provide a valid calendar year for processing.")
        
        # Guard Check: Prevent re-execution if already closed
        if self.time_repo.is_year_locked(year):
            raise ValueError(f"Year-end processing for {year} has already been closed and locked.")
            
        try:
            return self.time_repo.execute_year_end_processing(year, processed_by)
        except Exception as e:
            raise RuntimeError(f"Engine failure during year-end process: {str(e)}")

    def fetch_employee_leave_balances(self, year: int) -> List[Dict[str, Any]]:
        """Retrieves global leave balances for all active bank personnel."""
        return self.time_repo.get_employee_leave_balances(year)

    def check_if_year_locked(self, year: int) -> bool:
        """Determines if a year-end process has been executed and closed."""
        return self.time_repo.is_year_locked(year)

    # ---------------------------------------------------------
    # HOLIDAY CALENDAR LOGIC
    # ---------------------------------------------------------
    def fetch_holidays(self, year: int) -> List[Dict[str, Any]]:
        """Fetches the bank holiday calendar for a specific year."""
        target_year = year if year else datetime.now().year
        return self.time_repo.get_holidays_by_year(target_year)

    def create_holiday(self, holiday_data: dict) -> Dict[str, Any]:
        """Registers a new bank holiday date."""
        required_fields = ['HolidayDate', 'HolidayName']
        missing = [field for field in required_fields if not holiday_data.get(field)]
        
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        try:
            return self.time_repo.add_holiday(holiday_data)
        except Exception as e:
            if 'already exists' in str(e):
                raise ValueError("A holiday is already registered on this specific date.")
            raise RuntimeError(f"Database error while adding holiday: {str(e)}")

    def modify_holiday(self, holiday_id: int, holiday_data: dict) -> Dict[str, Any]:
        """Alters parameters for an existing calendar holiday."""
        required_fields = ['HolidayDate', 'HolidayName']
        missing = [field for field in required_fields if not holiday_data.get(field)]
        
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        try:
            return self.time_repo.update_holiday(holiday_id, holiday_data)
        except Exception as e:
            if 'already exists' in str(e):
                raise ValueError("Another holiday is already registered on this date.")
            raise RuntimeError(f"Database error while updating holiday: {str(e)}")

    def process_bulk_upload(self, csv_reader) -> tuple:
        """Processes and inserts a bulk batch of calendar holidays from CSV."""
        success_count = 0
        errors = []
        row_num = 1
        
        for row in csv_reader:
            row_num += 1
            try:
                holiday_data = {
                    "HolidayDate": row.get('HolidayDate', '').strip(),
                    "HolidayName": row.get('HolidayName', '').strip(),
                    "HolidayType": row.get('HolidayType', 'Public Holiday').strip() or 'Public Holiday'
                }
                
                if not holiday_data['HolidayDate'] or not holiday_data['HolidayName']:
                    errors.append(f"Row {row_num}: Missing Date or Name.")
                    continue
                    
                self.create_holiday(holiday_data)
                success_count += 1
            except ValueError as ve:
                errors.append(f"Row {row_num}: {str(ve)}")
            except Exception as e:
                errors.append(f"Row {row_num}: Failed to process.")
                
        return success_count, errors

#----- WEEKLY OFF CONFIGURATION LOGIC (Optional) -----#
    def fetch_weekly_offs(self) -> List[Dict[str, Any]]:
        """Fetches current weekend rules."""
        return self.time_repo.get_weekly_offs()

    def save_weekly_offs(self, config_list: List[Dict[str, Any]]) -> bool:
        """Validates and converts the configuration to JSON for the SQL Engine."""
        for item in config_list:
            if 'DayOfWeek' not in item or 'WeekOfMonth' not in item:
                raise ValueError("Invalid format. Expected DayOfWeek and WeekOfMonth.")
        return self.time_repo.update_weekly_offs(json.dumps(config_list))