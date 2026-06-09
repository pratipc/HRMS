# File Name: holiday_service.py
# Location: kpcb_hrms/app/services/holiday_service.py

from datetime import datetime
from app.repositories.interfaces import IHolidayRepository

class HolidayService:
    def __init__(self, holiday_repo: IHolidayRepository):
        self.holiday_repo = holiday_repo

    def fetch_holidays(self, year: int) -> list:
        target_year = year if year else datetime.now().year
        return self.holiday_repo.get_holidays_by_year(target_year)

    def create_holiday(self, holiday_data: dict) -> dict:
        required_fields = ['HolidayDate', 'HolidayName']
        missing = [field for field in required_fields if not holiday_data.get(field)]
        
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
        try:
            return self.holiday_repo.add_holiday(holiday_data)
        except Exception as e:
            if 'already exists' in str(e):
                raise ValueError("A holiday is already registered on this specific date.")
            raise RuntimeError(f"Database error while adding holiday: {str(e)}")

    def process_bulk_upload(self, csv_reader) -> tuple:
        """Processes a list of dictionaries from a CSV for bulk upload."""
        success_count = 0
        errors = []
        row_num = 1 # Accounting for the header row
        
        for row in csv_reader:
            row_num += 1
            try:
                # Safely extract data, defaulting to 'Public Holiday' if the category column is empty
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