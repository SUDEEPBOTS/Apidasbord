from flask import Flask, redirect, request, render_template_string, session, url_for
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_sudeep_key") # Session ke liye

# 🛠️ DATABASE CONNECTION
# Vercel pe Env Var 'MONGO_DB_URI' daalna mat bhoolna
MONGO_URL = os.getenv("MONGO_DB_URI")
client = MongoClient(MONGO_URL)
db = client["Switchboard_DB"]
config_col = db["settings"]

# 🔐 ADMIN CREDENTIALS
ADMIN_USER = "SUDEEP"
ADMIN_PASS = "ADMIN123"

# Default Config (Agar DB khali ho)
DEFAULT_CONFIG = {
    "id": "main_config",
    "master_url": "https://tera-api.onrender.com",
    "maintenance": False,
    "maintenance_msg": "🚧 Server Upgrading... Please wait!"
}

def get_config():
    data = config_col.find_one({"id": "main_config"})
    if not data:
        config_col.insert_one(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    return data

# ==========================================
# 🚀 1. THE REDIRECT MAGIC (Dosto ke liye)
# ==========================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    # Agar Admin Panel khol rahe ho to rok lo
    if path.startswith("admin") or path.startswith("login") or path.startswith("logout"):
        return redirect(url_for('login'))

    conf = get_config()
    
    # Check 1: Maintenance Mode
    if conf.get("maintenance"):
        return {
            "status": 503,
            "error": "Maintenance Mode",
            "message": conf.get("maintenance_msg")
        }, 503

    # Check 2: Redirect Logic
    target_base = conf.get("master_url").rstrip("/")
    
    # Query Parameters (jaise ?query=song) ko saath le jao
    query_string = request.query_string.decode("utf-8")
    
    if query_string:
        destination = f"{target_base}/{path}?{query_string}"
    else:
        destination = f"{target_base}/{path}"

    # 307 Redirect (Temporary Redirect) - Dost ka bot samjhega nahi ki redirect hua
    return redirect(destination, code=307)


# ==========================================
# 🔐 2. LOGIN PAGE (Mast Lock)
# ==========================================
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        user = request.form.get("username")
        pwd = request.form.get("password")
        
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            msg = "❌ Chal nikal! Wrong Password."

    # Login UI
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔒 Secure Access</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { background: #0f0f0f; color: #00ff41; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { border: 1px solid #00ff41; padding: 40px; box-shadow: 0 0 20px #00ff41; text-align: center; background: #000; }
            input { display: block; width: 100%; margin: 10px 0; padding: 10px; background: #111; border: 1px solid #333; color: white; }
            button { width: 100%; padding: 10px; background: #00ff41; border: none; font-weight: bold; cursor: pointer; }
            button:hover { background: #00cc33; }
            h2 { margin-bottom: 20px; letter-spacing: 2px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>☠️ RESTRICTED AREA</h2>
            <p style="color:red">{{ msg }}</p>
            <form method="POST">
                <input type="text" name="username" placeholder="IDENTITY" required>
                <input type="password" name="password" placeholder="ACCESS CODE" required>
                <button type="submit">>> ENTER SYSTEM</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, msg=msg)

@app.route('/admin/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# ==========================================
# 🎛️ 3. DASHBOARD (Control Panel)
# ==========================================
@app.route('/admin/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conf = get_config()
    msg = ""

    if request.method == 'POST':
        new_url = request.form.get("master_url")
        m_msg = request.form.get("maintenance_msg")
        is_maint = "maintenance" in request.form
        
        config_col.update_one(
            {"id": "main_config"},
            {"$set": {
                "master_url": new_url,
                "maintenance": is_maint,
                "maintenance_msg": m_msg
            }}
        )
        conf = get_config()
        msg = "✅ System Updated!"

    # Dashboard UI
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎛️ Switchboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: 'Courier New', monospace; background: #121212; color: white; padding: 20px; }
            .container { max-width: 600px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 10px; border: 1px solid #333; }
            input, textarea { width: 95%; padding: 12px; margin: 10px 0; background: #252525; color: #fff; border: 1px solid #444; border-radius: 5px; }
            button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; font-weight: bold; font-size: 16px; cursor: pointer; border-radius: 5px; margin-top: 20px;}
            button:hover { background: #0056b3; }
            .status { text-align: center; padding: 10px; margin-bottom: 20px; border-radius: 5px; font-weight: bold; }
            .online { background: #155724; color: #d4edda; border: 1px solid #c3e6cb; }
            .maint { background: #856404; color: #fff3cd; border: 1px solid #ffeeba; }
            label { font-weight: bold; color: #aaa; margin-top: 15px; display: block; }
            .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 20px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>⚡ INFINITY CONTROL</h2>
                <a href="/admin/logout" style="color: red; text-decoration: none;">LOGOUT</a>
            </div>

            {% if conf.maintenance %}
                <div class="status maint">⚠️ MAINTENANCE MODE ACTIVE</div>
            {% else %}
                <div class="status online">🟢 SYSTEM ONLINE & REDIRECTING</div>
            {% endif %}

            <p style="text-align:center; color: #00ff41;">{{ msg }}</p>
            
            <form method="POST">
                <label>🔗 TARGET URL (Render/Railway/Heroku)</label>
                <input type="text" name="master_url" value="{{ conf.master_url }}" placeholder="https://..." required>

                <label>📢 MAINTENANCE MESSAGE</label>
                <textarea name="maintenance_msg" rows="3">{{ conf.maintenance_msg }}</textarea>

                <div style="margin-top: 20px; background: #2a2a2a; padding: 15px; border-radius: 5px; display: flex; align-items: center;">
                    <input type="checkbox" name="maintenance" style="width: 20px; height: 20px; margin: 0;" {% if conf.maintenance %}checked{% endif %}>
                    <span style="margin-left: 10px; color: #ff4444; font-weight: bold;">ENABLE MAINTENANCE MODE?</span>
                </div>

                <button type="submit">💾 SAVE CONFIGURATION</button>
            </form>
            
            <div style="margin-top: 30px; font-size: 12px; color: gray; text-align: center;">
                LOGGED IN AS: {{ user }}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, conf=conf, msg=msg, user="SUDEEP")
  
