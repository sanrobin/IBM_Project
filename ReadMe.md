IBM-FE-Login Authentication System - Prototype
------------------------------------------------

## Features
- User registration and login
- Multi-Factor Authentication (MFA) with OTP
- JWT-based session management
- Secure password hashing (PBKDF2)
- Clean, responsive UI

## How to run locally:
1. Create and activate a Python virtual environment (recommended):
   ```
   python -m venv venv
   source venv/bin/activate   (Windows: venv\Scripts\activate)
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the server:
   ```
   python app.py
   ```

4. Open http://127.0.0.1:5000 in your browser

## Demo credentials:
- Email: admin@ibm.com
- Password: password123

**Note:** The demo returns the OTP in the login response for testing purposes. In production, OTP would be sent via email/SMS.

## Testing
Run the test script to verify all endpoints:
```
python test_system.py
```

## API Endpoints
- `POST /api/register` - User registration
- `POST /api/login` - User login (generates OTP)
- `POST /api/verify-otp` - OTP verification (returns JWT)
- `GET /api/dashboard` - Protected dashboard (requires JWT)

## Security Features
- Password hashing with PBKDF2
- JWT tokens with expiration
- OTP-based MFA
- CORS protection
- Input validation
