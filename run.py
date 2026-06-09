# File Name: app.py
# Location: kpcb_hrms/app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import urllib

# ---------------------------------------------------------
# 1. APPLICATION & DATABASE CONFIGURATION
# ---------------------------------------------------------
app = Flask(__name__)

# Database configuration based on Windows Authentication
SERVER = r'PRATIP\SQLEXPRESS'
DATABASE = 'KPCB_HRMS_DB'

# Formatting connection string for pyodbc
# Note: You may need to change 'ODBC Driver 17 for SQL Server' to the version installed on your machine.
params = urllib.parse.quote_plus(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------------------------------------------------
# 2. ROUTES & APIS (Using Stored Procedures)
# ---------------------------------------------------------

@app.route('/')
def index():
    return jsonify({
        "status": "success",
        "message": "Welcome to the KPCB HRMS API System"
    })

# API: Get all active employees via Stored Procedure
@app.route('/api/employees', methods=['GET'])
def get_employees():
    try:
        # Execute stored procedure
        result = db.session.execute(text("EXEC sp_GetActiveEmployees")).mappings().all()
        
        # Convert result rows to a list of dictionaries
        emp_list = [dict(row) for row in result]
        return jsonify(emp_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: Create a new Leave Type via Stored Procedure
@app.route('/api/leave-types', methods=['POST'])
def add_leave_type():
    data = request.json
    try:
        # Prepare the SP call with parameters
        sql = text("""
            EXEC sp_InsertLeaveType 
                @TypeName = :TypeName, 
                @QtyPerYear = :QtyPerYear, 
                @CreditPeriod = :CreditPeriod, 
                @IsCarryForward = :IsCarryForward, 
                @MaxCarryForward = :MaxCarryForward
        """)
        
        # Execute the SP
        result = db.session.execute(sql, {
            "TypeName": data['TypeName'],
            "QtyPerYear": data['QtyPerYear'],
            "CreditPeriod": data['CreditPeriod'],
            "IsCarryForward": data.get('IsCarryForward', False),
            "MaxCarryForward": data.get('MaxCarryForward', 0)
        })
        
        # Commit the transaction
        db.session.commit()
        
        # Fetch the ID returned by the stored procedure (SCOPE_IDENTITY)
        new_id_row = result.fetchone()
        new_id = new_id_row[0] if new_id_row else None
        
        return jsonify({"message": "Leave Type successfully added", "LeaveTypeID": float(new_id) if new_id else None}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------
# 3. INITIALIZATION
# ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)