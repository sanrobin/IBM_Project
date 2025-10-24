from flask import Flask, request, jsonify, send_from_directory, redirect
import sqlite3, os, datetime, jwt, hashlib, hmac, secrets
from functools import wraps
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
SECRET_KEY = os.environ.get("IBM_FE_SECRET", "dev-secret-please-change")

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["SECRET_KEY"] = SECRET_KEY
CORS(app)

# --- Database helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        otp TEXT,
        otp_expiry INTEGER
    );
    """)
    conn.commit()
    # create demo user
    try:
        pw = hash_password("password123")
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                    ("admin@ibm.com", pw, "admin"))
        conn.commit()
    except Exception:
        pass
    conn.close()

def hash_password(password: str) -> str:
    # simple salted hash (PBKDF2)
    salt = b"ibm-demo-salt"
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return dk.hex()

def verify_password(password: str, hash_hex: str) -> bool:
    return hmac.compare_digest(hash_password(password), hash_hex)

# --- JWT helpers ---
def generate_jwt(payload, exp_minutes=60):
    payload = payload.copy()
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(minutes=exp_minutes)
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            parts = request.headers["Authorization"].split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
        if not token:
            return jsonify({"success": False, "message": "Token is missing"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data
        except Exception as e:
            return jsonify({"success": False, "message": "Token is invalid or expired"}), 401
        return f(*args, **kwargs)
    return decorated

# --- Routes ---
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/register")
def register_page():
    return send_from_directory("static", "register.html")

@app.route("/mfa")
def mfa_page():
    return send_from_directory("static", "mfa.html")

@app.route("/dashboard")
def dashboard_page():
    return send_from_directory("static", "dashboard.html")

@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory("assets", filename)

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    password = data.get("password","")
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters"}), 400
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, hash_password(password)))
        conn.commit()
        return jsonify({"success": True, "message": "Account created successfully! Redirecting to login..."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Email already exists"}), 409
    finally:
        conn.close()

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    password = data.get("password","")
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    if not verify_password(password, row["password_hash"]):
        conn.close()
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    # generate OTP for MFA (demo)
    otp = "%06d" % secrets.randbelow(1000000)
    expiry = int((datetime.datetime.utcnow() + datetime.timedelta(minutes=5)).timestamp())
    cur.execute("UPDATE users SET otp = ?, otp_expiry = ? WHERE id = ?", (otp, expiry, row["id"]))
    conn.commit()
    conn.close()
    # In production, send OTP via email/SMS. Here we return it in response for demo.
    return jsonify({"success": True, "message": "OTP generated", "otp_preview": otp}), 200

@app.route("/api/verify-otp", methods=["POST"])
def api_verify_otp():
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    otp = data.get("otp","").strip()
    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP required"}), 400
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "Invalid email or OTP"}), 401
    now_ts = int(datetime.datetime.utcnow().timestamp())
    if not row["otp"] or row["otp"] != otp or (row["otp_expiry"] or 0) < now_ts:
        conn.close()
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 401
    # clear otp
    cur.execute("UPDATE users SET otp = NULL, otp_expiry = NULL WHERE id = ?", (row["id"],))
    conn.commit()
    # generate JWT
    token = generate_jwt({"sub": row["email"], "role": row["role"]}, exp_minutes=60)
    conn.close()
    return jsonify({"success": True, "message": "Verified", "token": token}), 200

@app.route("/api/dashboard", methods=["GET"])
@token_required
def api_dashboard():
    user = request.user
    return jsonify({"success": True, "message": f"Welcome {user.get('sub')}", "role": user.get("role")}), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
