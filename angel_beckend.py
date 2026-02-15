from flask import Flask, request, jsonify
from flask_cors import CORS
from SmartApi import SmartConnect
import pyotp
import os
import json
from datetime import datetime

app = Flask(**name**)
CORS(app)

# Global session storage (in production, use Redis)

sessions = {}

# ========== HEALTH CHECK ==========

@app.route(’/health’, methods=[‘GET’])
def health():
“”“Health check endpoint”””
return jsonify({
‘status’: ‘ok’,
‘service’: ‘Angel SmartAPI Proxy’,
‘timestamp’: datetime.now().isoformat()
})

# ========== AUTHENTICATION ==========

@app.route(’/login’, methods=[‘POST’])
def login():
“””
Login to Angel SmartAPI with improved error handling

```
Request body:
{
    "apiKey": "your_api_key",
    "clientId": "your_client_id",
    "password": "your_password",
    "pin": "your_mpin",
    "totpToken": "6_digit_totp" (optional)
}
"""
try:
    data = request.json
    api_key = data.get('apiKey')
    client_id = data.get('clientId')
    password = data.get('password')
    pin = data.get('pin')
    totp_token = data.get('totpToken', '')
    
    if not all([api_key, client_id, password, pin]):
        return jsonify({
            'success': False,
            'message': 'Missing required fields'
        }), 400
    
    # Initialize SmartConnect
    smart_api = SmartConnect(api_key=api_key)
    
    # Generate session
    session_data = smart_api.generateSession(
        clientCode=client_id,
        password=password,
        totp=totp_token
    )
    
    if session_data and session_data.get('status'):
        # Extract tokens
        jwt_token = session_data['data']['jwtToken']
        refresh_token = session_data['data']['refreshToken']
        feed_token = session_data['data']['feedToken']
        
        # Store session
        sessions[client_id] = {
            'smart_api': smart_api,
            'jwt_token': jwt_token,
            'refresh_token': refresh_token,
            'feed_token': feed_token,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'jwtToken': jwt_token,
            'refreshToken': refresh_token,
            'feedToken': feed_token,
            'message': 'Login successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': session_data.get('message', 'Login failed')
        }), 401
        
except Exception as e:
    return jsonify({
        'success': False,
        'message': f'Login error: {str(e)}'
    }), 500
```

# ========== LOGOUT ==========

@app.route(’/logout’, methods=[‘POST’])
def logout():
“”“Logout from Angel SmartAPI”””
try:
data = request.json
client_id = data.get(‘clientId’)

```
    if client_id in sessions:
        smart_api = sessions[client_id]['smart_api']
        
        # Call logout
        logout_response = smart_api.terminateSession(client_id)
        
        # Clear session
        del sessions[client_id]
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No active session found'
        }), 404
        
except Exception as e:
    return jsonify({
        'success': False,
        'message': f'Logout error: {str(e)}'
    }), 500
```

# ========== GET QUOTES ==========

@app.route(’/quotes’, methods=[‘GET’])
def get_quotes():
“””
Get real-time quotes for multiple symbols

```
Query params:
- clientId: Your Angel client ID
- symbols: Comma-separated list (e.g., RELIANCE,TCS,INFY)

Authorization: Bearer <jwt_token>
"""
try:
    # Get authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization'}), 401
    
    client_id = request.args.get('clientId')
    symbols = request.args.get('symbols', '').split(',')
    
    if not client_id or client_id not in sessions:
        return jsonify({'error': 'Not authenticated'}), 401
    
    smart_api = sessions[client_id]['smart_api']
    
    # Fetch quotes for all symbols
    quotes_data = []
    
    for symbol in symbols:
        if not symbol.strip():
            continue
            
        try:
            # Get token for symbol (you'll need a token mapping)
            token = get_symbol_token(symbol)
            
            # Get LTP data
            ltp_response = smart_api.ltpData('NSE', symbol, token)
            
            if ltp_response and ltp_response.get('status'):
                ltp_data = ltp_response['data']
                
                quotes_data.append({
                    'symbol': symbol,
                    'ltp': ltp_data.get('ltp', 0),
                    'change': ltp_data.get('change', 0),
                    'pChange': ltp_data.get('pChange', 0),
                    'open': ltp_data.get('open', 0),
                    'high': ltp_data.get('high', 0),
                    'low': ltp_data.get('low', 0),
                    'close': ltp_data.get('close', 0),
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue
    
    return jsonify({
        'success': True,
        'quotes': quotes_data,
        'count': len(quotes_data)
    })
    
except Exception as e:
    return jsonify({'error': str(e)}), 500
```

# ========== GET PROFILE ==========

@app.route(’/profile’, methods=[‘GET’])
def get_profile():
“”“Get user profile”””
try:
auth_header = request.headers.get(‘Authorization’)
if not auth_header or not auth_header.startswith(’Bearer ’):
return jsonify({‘error’: ‘Missing authorization’}), 401

```
    client_id = request.args.get('clientId')
    
    if not client_id or client_id not in sessions:
        return jsonify({'error': 'Not authenticated'}), 401
    
    smart_api = sessions[client_id]['smart_api']
    
    # Get profile
    profile = smart_api.getProfile(sessions[client_id]['refresh_token'])
    
    return jsonify({
        'success': True,
        'profile': profile
    })
    
except Exception as e:
    return jsonify({'error': str(e)}), 500
```

# ========== HELPER FUNCTIONS ==========

def get_symbol_token(symbol):
“””
Get NSE token for a symbol

```
In production, load from a JSON file or database with all NSE symbols and tokens.
You can download the instrument list from Angel SmartAPI.
"""
# Sample token mapping (you need complete list)
token_map = {
    'RELIANCE': '2885',
    'TCS': '11536',
    'HDFCBANK': '1333',
    'INFY': '1594',
    'ICICIBANK': '4963',
    'HINDUNILVR': '1394',
    'SBIN': '3045',
    'BHARTIARTL': '10604',
    'BAJFINANCE': '317',
    'KOTAKBANK': '1922',
    'LT': '11483',
    'AXISBANK': '5900',
    'ITC': '1660',
    'ASIANPAINT': '236',
    'MARUTI': '10999',
    'TITAN': '3506',
    'SUNPHARMA': '3351',
    'ULTRACEMCO': '11532',
    'NESTLEIND': '17963',
    'TATAMOTORS': '3456',
    'TATASTEEL': '3499',
    'POWERGRID': '14977',
    'NTPC': '11630',
    'ONGC': '2475',
    'HCLTECH': '7229',
    'WIPRO': '3787',
    'TECHM': '13538',
    'INDUSINDBK': '5258',
    'BAJAJFINSV': '16675',
    'GRASIM': '1232',
    'DRREDDY': '881',
    'DIVISLAB': '10940',
    'CIPLA': '694',
    'EICHERMOT': '910',
    'HEROMOTOCO': '1348',
    'ADANIPORTS': '15083',
    'COALINDIA': '20374',
    'JSWSTEEL': '11723',
    'TATACONSUM': '3432',
    'BRITANNIA': '547',
    'APOLLOHOSP': '157',
    'HINDALCO': '1363',
    'SHREECEM': '3103',
    'VEDL': '3063',
    'ADANIENT': '25',
    'MANAPPURAM': '19061',
    'SAIL': '2963',
    'NMDC': '15332',
    'BANKBARODA': '4668',
    'PNB': '10666',
    'CANBK': '10794'
}

return token_map.get(symbol, '0')
```

# ========== STARTUP ==========

if **name** == ‘**main**’:
port = int(os.getenv(‘PORT’, 10000))
app.run(host=‘0.0.0.0’, port=port, debug=False)

# ========== DEPLOYMENT INSTRUCTIONS ==========

“””
DEPLOY TO RENDER.COM (FREE):

1. Create requirements.txt:
   Flask==2.3.0
   flask-cors==4.0.0
   SmartApi-Python==1.3.0
   pyotp==2.8.0
1. Create Render Web Service:
- Runtime: Python 3
- Build Command: pip install -r requirements.txt
- Start Command: python angel_backend.py
- Port: 10000
1. No environment variables needed (credentials come from app)
1. Deploy and get URL: https://your-app.onrender.com
1. Update HTML app with this URL!

NOTES:

- Free tier sleeps after 15 min of inactivity
- First request after sleep takes ~30 seconds
- Sufficient for personal use
  “””