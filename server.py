# ==========================================
# SERVER-SIDE API (Flask) - PYTHONANYWHERE
# ==========================================
from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# Absolute path ensures licenses.json is found in /home/heresmajid/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "licenses.json")

def load_licenses():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_licenses(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route('/verify-license', methods=['POST'])
def verify_license():
    data = request.json or {}
    key = str(data.get("license_key", "")).strip()
    hwid = str(data.get("hwid", "")).strip()

    licenses = load_licenses()

    print(f"\n[VERIFY REQUEST] Key: '{key}' | Client HWID: '{hwid}'")

    # 1. Key Check
    if not key or key not in licenses:
        print(f"❌ DENIED: Key '{key}' not found in database.")
        return jsonify({"status": "DENIED", "message": f"Key '{key}' not found in database."}), 503

    client_info = licenses[key]

    # 2. Active Status Check
    if not client_info.get("is_active", False):
        print("❌ DENIED: License is inactive.")
        return jsonify({"status": "DENIED", "message": "License account is deactivated."}), 503

    # 3. Expiry Date Check
    expiry_str = client_info.get("expiry_date")
    if expiry_str:
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            if datetime.now() > expiry_date:
                print(f"❌ DENIED: License expired on {expiry_str}.")
                return jsonify({"status": "DENIED", "message": f"License expired on {expiry_str}"}), 503
        except ValueError:
            pass

    # 4. HWID Binding
    saved_hwid = client_info.get("hwid")
    
    if saved_hwid is None or saved_hwid == "":
        client_info["hwid"] = hwid
        save_licenses(licenses)
        print(f"✅ SUCCESS: Bound HWID '{hwid}' to key '{key}'")
        return jsonify({"status": "APPROVED", "message": "Access Granted (HWID Bound)"}), 200
        
    if saved_hwid != hwid:
        print(f"❌ DENIED: HWID mismatch! Saved in DB: '{saved_hwid}', Client sent: '{hwid}'")
        return jsonify({
            "status": "DENIED", 
            "message": f"HWID Mismatch! Reset 'hwid': null in licenses.json to allow this PC."
        }), 503

    print("✅ SUCCESS: Access Granted!")
    return jsonify({"status": "APPROVED", "message": "Access Granted"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)