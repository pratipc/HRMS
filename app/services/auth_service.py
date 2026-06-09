# File Name: auth_service.py
# Location: kpcb_hrms/app/services/auth_service.py

from app.repositories.interfaces import IAuthRepository

class AuthService:
    """
    Dependency Inversion Principle (DIP): 
    The service depends on the IAuthRepository abstraction, not the SQL implementation.
    """
    
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    def login(self, username: str, password: str) -> dict:
        """
        Orchestrates the login process. 
        If you needed to hash passwords, validate strict business rules, 
        or log login attempts, it happens here, NOT in the API.
        """
        if not username or not password:
            raise ValueError("Username and password are required")

        # In a real scenario, you might hash the password here before sending to repo
        # hashed_password = hash_function(password)
        
        user_data = self.auth_repo.authenticate_user(username, password)
        
        if not user_data:
            raise PermissionError("Invalid username or password, or account inactive")
            
        return user_data
    
    def register(self, data: dict) -> dict:
        """
        Validates input and orchestrates the registration process.
        """
        # 1. Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"'{field}' is a required field.")
                
        # 2. Delegate to Repository to persist data
        try:
            return self.auth_repo.register_user(data)
        except Exception as e:
            error_msg = str(e)
            # Catch the specific RAISERROR messages from our SQL Server procedure
            if 'Email already exists' in error_msg:
                raise ValueError("An account with this email address already exists.")
            if 'Username already exists' in error_msg:
                raise ValueError("This username is already taken. Please choose another.")
                
            raise RuntimeError(f"Database error during registration: {error_msg}")

