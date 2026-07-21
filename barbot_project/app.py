from flask import Flask
import threading

# Importiere unsere neuen Blueprints
from routes.user import user_bp
from routes.admin import admin_bp

# --- INITIALISIERUNG DER BEIDEN FLASK APPS ---
app_user = Flask(__name__)
app_admin = Flask(__name__)

# Blueprints an die jeweilige App heften
app_user.register_blueprint(user_bp)
app_admin.register_blueprint(admin_bp)

# ==============================================================================
# MULTITHREADING SERVER LAUNCHER
# ==============================================================================

def run_user_app():
    """Startet den Server für die Gäste-UI auf Port 5000."""
    app_user.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def run_admin_app():
    """Startet den Server für das Admin-Backend auf Port 1337."""
    app_admin.run(host='0.0.0.0', port=1337, debug=True, use_reloader=False)

if __name__ == '__main__':
    user_thread = threading.Thread(target=run_user_app, daemon=True)
    admin_thread = threading.Thread(target=run_admin_app, daemon=True)
    
    print("[SYSTEM] Starte BarBot Server...")
    user_thread.start()
    admin_thread.start()
    
    user_thread.join()
    admin_thread.join()