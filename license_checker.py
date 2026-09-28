# =============================================================
# CLIENT-SIDE LICENSE CHECKER (WITH HWID SUPPORT)
# =============================================================
import hashlib
import platform
import uuid
import requests

# Aapka PythonAnywhere Live Server URL:
SERVER_URL = "https://heresmajid.pythonanywhere.com/verify-license"


def get_hwid():
  """Permanently Stable HWID Jo VPN ya Wi-Fi change hone par bhi change nahi hota."""
  hwid_raw = ""

  # 1. Windows OS ke liye: Registry se permanent MachineGuid lein
  if platform.system() == "Windows":
    try:
      import winreg

      registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
      key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
      hwid_raw, _ = winreg.QueryValueEx(key, "MachineGuid")
    except Exception:
      pass

  # 2. Agar Linux/Mac ho ya Registry fail ho jaye (Fallback):
  if not hwid_raw:
    hwid_raw = f"{platform.node()}-{platform.processor()}-{uuid.getnode()}"

  # SHA256 se clean 16-character HWID String banayein
  return hashlib.sha256(hwid_raw.encode()).hexdigest()[:16].upper()


def verify_client_access(license_key: str):
  clean_key = str(license_key or "").strip()

  if not clean_key:
    raise PermissionError("ERROR : License key missing.")

  # Client PC ka HWID
  current_hwid = get_hwid()

  payload = {"license_key": clean_key, "hwid": current_hwid}

  try:
    # Server ko key aur HWID dono bhejein
    response = requests.post(SERVER_URL, json=payload, timeout=5)
    res_data = response.json() if response.status_code == 200 else {}

    # Agar status APPROVED hai to True return karein
    if response.status_code == 200 and res_data.get("status") == "APPROVED":
      return True
    else:
      error_msg = res_data.get("message", "Access Denied")
      print("❌ LICENSE ERROR")

  except Exception as e:
    print("❌ LICENSE ERROR")
    raise PermissionError("License Error")