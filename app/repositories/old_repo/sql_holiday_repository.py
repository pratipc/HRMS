# File Name: sql_holiday_repository.py
# Location: kpcb_hrms/app/repositories/sql_holiday_repository.py

from sqlalchemy import text
from typing import Dict, Any
from app.repositories.interfaces import IHolidayRepository

class SqlHolidayRepository(IHolidayRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    def get_holidays_by_year(self, year: int) -> list:
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