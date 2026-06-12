import json
from app import create_app, db

app = create_app()
app.config['TESTING'] = True
client = app.test_client()

with app.app_context():
    # Let's mock the session to bypass auth
    with client.session_transaction() as sess:
        sess['role'] = 'Admin'
        sess['username'] = 'Admin'

    # Get the rates to see what the API returns
    response = client.get('/admin/api/payroll/saturday-rates')
    rates = response.get_json()
    print("GET Rates:")
    print(json.dumps(rates, indent=2))
    
    # Pick the one with 'Manager' or the first one with RateID > 0
    target_rate = None
    for r in rates:
        if r.get('rate_id') > 0:
            target_rate = r
            break
            
    if target_rate:
        print(f"Attempting to update RateID {target_rate['rate_id']} ({target_rate['designation']}) to 'Updated Designation Test'")
        payload = {
            'Designation': 'Updated Designation Test',
            'Rate': 999.0,
            'RateID': target_rate['rate_id'],
            'OldDesignation': target_rate['designation']
        }
        
        response = client.put('/admin/api/payroll/saturday-rates', 
                             data=json.dumps(payload),
                             content_type='application/json')
        print(f"PUT Response Status: {response.status_code}")
        print("PUT Response Data:")
        print(response.get_json())
        
        # Verify
        response = client.get('/admin/api/payroll/saturday-rates')
        rates = response.get_json()
        print("GET Rates AFTER:")
        print(json.dumps(rates, indent=2))
    else:
        print("No existing rate found to update.")
