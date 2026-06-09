# File Name: sql_auth_repositories.py
# Location: kpcb_hrms/app/repositories/sql_auth_repositories.py

from sqlalchemy import text
from app.repositories.interfaces import IAuthRepository

class SqlAuthRepository(IAuthRepository):
    def __init__(self, db_session):
        self.db_session = db_session

    def authenticate_user(self, username: str, password_hash: str) -> dict:
        sql = text("EXEC sp_AuthenticateUser @Username = :Username, @PasswordHash = :PasswordHash")
        result = self.db_session.execute(sql, {
            "Username": username,
            "PasswordHash": password_hash
        }).mappings().fetchone()
        
        return dict(result) if result else None

    def register_user(self, user_data: dict) -> dict:
        sql = text("""
            EXEC sp_RegisterEmployeeAndUser
                @FirstName = :FirstName,
                @LastName = :LastName,
                @Email = :Email,
                @Username = :Username,
                @PasswordHash = :PasswordHash
        """)
        
        result = self.db_session.execute(sql, {
            "FirstName": user_data['firstName'],
            "LastName": user_data['lastName'],
            "Email": user_data['email'],
            "Username": user_data['username'],
            "PasswordHash": user_data['password'] # Passwords should be hashed in production
        }).mappings().fetchone()
        
        self.db_session.commit()
        return dict(result) if result else {}