# File Name: auth.py
# Location: kpcb_hrms/app/auth.py

import traceback

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from sqlalchemy import text

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# ---------------------------------------------------------
# UI ROUTES
# ---------------------------------------------------------
@auth_bp.route('/', methods=['GET'])
def index():
    """Redirects the root URL to the login page."""
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/login', methods=['GET'])
def login_page():
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('auth/register.html')

# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

# Note: We will import 'db' directly where needed or attach it to the blueprint 
# to avoid circular imports. For simplicity, we import it from the main app.
from app import db 
from app.repositories.sql_auth_repositories import SqlAuthRepository
from app.services.auth_service import AuthService

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    auth_repo = SqlAuthRepository(db.session)
    auth_service = AuthService(auth_repo)

    try:
        # Delegate business logic to the Service layer
        user_data = auth_service.login(data.get('username'), data.get('password'))

        # Create Session (Login)
        session['logged_in'] = True
        session['user_id'] = user_data['UserID']
        session['employee_id'] = user_data['EmployeeID']
        session['role'] = user_data['Role'] 
        session['username'] = user_data['Username']
        session['full_name'] = f"{user_data['FirstName']} {user_data['LastName']}"
        session['designation'] = user_data.get('Designation', 'Unknown')
        session['branch_name'] = user_data.get('BranchName', 'Unknown')

        # Determine Dashboard URL based on Role
        if user_data['Role'] == 'Admin':
            redirect_url = '/admin/dashboard'
        else:
            redirect_url = '/employee/dashboard'

        return jsonify({
            "message": "Login successful",
            "redirect_url": redirect_url,
            "user": {
                "EmployeeID": user_data['EmployeeID'],
                "Name": f"{user_data['FirstName']} {user_data['LastName']}",
                "Role": user_data['Role']
            }
        }), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except PermissionError as pe:
        return jsonify({"error": str(pe)}), 401
    except Exception as e:
        return jsonify({"error": "An internal server error occurred"}), 500

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """
    Handles the registration POST request from the frontend.
    Delegates to AuthService for validation and SqlAuthRepository for database insertion.
    """
    data = request.json
    auth_repo = SqlAuthRepository(db.session)
    auth_service = AuthService(auth_repo)

    try:
        result = auth_service.register(data)
        return jsonify({
            "message": "Registration successful",
            "user": result
        }), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        # ---- DEBUGGING HELPERS ----
        print("\n=== REGISTRATION ERROR ===")
        traceback.print_exc()  # Prints the exact error and line number to your terminal
        print("==========================\n")
        return jsonify({"error": "An internal server error occurred"}), 500

@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    """
    Clears the user session.
    """
    session.clear()
    return jsonify({"status": "success", "message": "Successfully logged out"}), 200

@auth_bp.route('/api/me', methods=['GET'])
def current_user():
    """
    Helper route to check who is currently logged in and their role.
    """
    if 'logged_in' in session:
        return jsonify({
            "logged_in": True,
            "user_id": session.get('user_id'),
            "employee_id": session.get('employee_id'),
            "username": session.get('username'),
            "role": session.get('role')
        }), 200
    else:
        return jsonify({"logged_in": False, "message": "No active session"}), 401