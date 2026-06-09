# File Name: __init__.py
# Location: kpcb_hrms/app/__init__.py

import os
import urllib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 1. Initialize SQLAlchemy globally so other modules can import it (e.g., `from app import db`)
db = SQLAlchemy()

def create_app():
    """
    Application Factory function. 
    Constructs, configures, and returns the Flask application instance.
    """
    app = Flask(__name__)

    # Add a Secret Key for session management
    app.secret_key = os.urandom(24) 

    # Database configuration based on Windows Authentication
    SERVER = r'PRATIP\SQLEXPRESS'
    DATABASE = 'KPCB_HRMS_DB'

    params = urllib.parse.quote_plus(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind the database to the app
    db.init_app(app)

    # 2. Register Blueprints (Adhering to Single Responsibility Principle)
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.employee import employee_bp
    app.register_blueprint(employee_bp)

    return app