# File Name: auth_decorators.py
# Location: kpcb_hrms/app/utils/auth_decorators.py

from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    """Ensures the user is logged in before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            # Redirect to the login page blueprint route
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Ensures the user has one of the specific roles required for the route."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('logged_in'):
                return redirect(url_for('auth.login_page'))
            if session.get('role') not in allowed_roles:
                # In a production app, you might render a specific 403 HTML page here
                return "Unauthorized Access: You do not have permission to view this page.", 403
            return f(*args, **kwargs)
        return decorated_function  # <-- FIX: This was incorrectly returning 'decorator'
    return decorator