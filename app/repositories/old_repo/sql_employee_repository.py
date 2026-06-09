# File Name: sql_employee_repository.py
# Location: kpcb_hrms/app/repositories/sql_employee_repository.py

from sqlalchemy import text
from typing import List, Dict, Any
from app.repositories.interfaces import IEmployeeRepository

class SqlEmployeeRepository(IEmployeeRepository):
    """
    Handles data access for Employee operations using SQL Server Stored Procedures.
    """

    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_active_employees(self) -> List[Dict[str, Any]]:
        # Execute the SP to get active employees
        sql = text("EXEC sp_GetActiveEmployees")
        result = self.db_session.execute(sql).mappings().all()
        
        return [dict(row) for row in result]

    def create_employee(self, employee_data: dict) -> Dict[str, Any]:
        # Execute the SP to create an employee and generate the Employee Code
        sql = text("""
            EXEC sp_CreateEmployee 
                @FirstName = :FirstName, 
                @LastName = :LastName, 
                @Email = :Email, 
                @Department = :Department, 
                @Designation = :Designation, 
                @DateOfJoining = :DateOfJoining
        """)
        
        result = self.db_session.execute(sql, {
            "FirstName": employee_data.get('FirstName'),
            "LastName": employee_data.get('LastName'),
            "Email": employee_data.get('Email'),
            "Department": employee_data.get('Department'),
            "Designation": employee_data.get('Designation'),
            "DateOfJoining": employee_data.get('DateOfJoining')
        }).mappings().fetchone()
        
        # Commit the transaction to save changes to the database
        self.db_session.commit()
        
        # Return the generated NewEmployeeID and GeneratedEmployeeCode
        return dict(result) if result else {}