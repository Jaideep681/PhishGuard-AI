import os
import re
import sys
import smtplib
import tempfile
from pathlib import Path
from functools import wraps
from email.message import EmailMessage
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth

# PROJECT PATHS AND ENVIRONMENT
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FLASK_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"
ENV_FILE = DATA_DIR / "Credentials.env"

# Load local environment variables.
# Render will provide production variables through its dashboard.
load_dotenv(ENV_FILE, override=False)

# Allow Python to import existing files inside Data/.
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

""" FIREBASE ADMIN SDK CREDENTIALS
 Local development uses the existing JSON file.
 Production can provide a different path through FIREBASE_CREDENTIALS."""
firebase_key_value = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    "phishguard-ai-2ba75-firebase-adminsdk-fbsvc-bc54c13171.json"
)

FIREBASE_KEY_PATH = Path(firebase_key_value).expanduser()

# Resolve relative paths from Flask_App.
if not FIREBASE_KEY_PATH.is_absolute():
    FIREBASE_KEY_PATH = FLASK_DIR / FIREBASE_KEY_PATH

# FLASK CONFIGURATION
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
frontend_origin = os.getenv(
    "FRONTEND_ORIGIN",
    "http://localhost:5500"
).rstrip("/")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                frontend_origin,
                "http://localhost:5500",
                "http://127.0.0.1:5500",
                "https://your-project.vercel.app",
                "https://fkjqlc5w-5500.inc1.devtunnels.ms/"
            ]
        }
    },
    methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

# FIREBASE ADMIN INITIALIZATION
if not FIREBASE_KEY_PATH.is_file():
    raise FileNotFoundError(
        f"Firebase service account key was not found: {FIREBASE_KEY_PATH}"
    )

if not firebase_admin._apps:
    firebase_credential = credentials.Certificate(str(FIREBASE_KEY_PATH))
    firebase_admin.initialize_app(firebase_credential)

# IMPORT EXISTING PROJECT MODULES
from scan_service_analysis import get_scan_service
from dns_analysis import analyze_domain_dns
from QRCode_Detector import decode_qr_code

# Existing scan service singleton.
scan_service = get_scan_service()

# COMMON RESPONSE HELPERS
def success_response(data=None, message="Success", status_code=200):
    return jsonify({
        "success": True,
        "message": message,
        "data": data
    }), status_code


def error_response(message, status_code=400):
    return jsonify({
        "success": False,
        "message": message
    }), status_code


def get_json_body():
    """Read and validate a JSON request body."""
    if not request.is_json:
        return None
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else None

# FIREBASE AUTHENTICATION DECORATOR
def require_auth(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        authorization_header = request.headers.get("Authorization", "")
        if not authorization_header.startswith("Bearer "):
            return error_response(
                "Authentication token is missing.",401
            )
        id_token = authorization_header.split(" ", 1)[1].strip()
        if not id_token:
            return error_response(
                "Authentication token is empty.",401
            )
        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user_id = decoded_token["uid"]
        except Exception:
            return error_response(
                "Invalid or expired authentication token.",401
            )
        return route_function(*args, **kwargs)
    return wrapper

# HOME AND HEALTH CHECK
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "application": "PhishGuard AI",
        "message": "PhishGuard AI backend is running."
    })
@app.route("/api/health", methods=["GET"])
def health_check():
    return success_response({
        "api": "running",
        "firebase": "initialized",
        "scan_service": "initialized"
    }, "Backend health check successful.")

# URL PHISHING SCAN
@app.route("/api/scan", methods=["POST"])
@require_auth
def scan_url():
    body = get_json_body()
    if body is None:
        return error_response("Please send a valid JSON request.")
    url = body.get("url")
    if not isinstance(url, str) or not url.strip():
        return error_response("A valid URL is required.")
    url = url.strip()
    try:
        result = scan_service.scan_url(
            url=url,
            user_id=request.user_id,
            save_history=True
        )
        if not isinstance(result, dict):
            return error_response(
                "The scanning service returned an unexpected response.",500
            )
        return success_response(
            result,"URL scan completed successfully."
        )
    except Exception:
        app.logger.exception("URL scanning failed.")
        return error_response(
            "An error occurred while scanning the URL.",500
        )

# DNS ANALYSIS
@app.route("/api/dns-analysis", methods=["POST"])
@require_auth
def dns_analysis():
    body = get_json_body()
    if body is None:
        return error_response("Please send a valid JSON request.")
    url = body.get("url")
    if not isinstance(url, str) or not url.strip():
        return error_response("A valid URL is required.")
    try:
        result = analyze_domain_dns(url.strip())
        return success_response(
            result,"DNS analysis completed."
        )
    except Exception:
        app.logger.exception("DNS analysis failed.")
        return error_response(
            "An error occurred during DNS analysis.",500
        )

# QRCODE SCANNING
@app.route("/api/qr-scan", methods=["POST"])
@require_auth
def qr_scan():
    if "file" not in request.files:
        return error_response("Please upload an image containing a QR code.")
    uploaded_file = request.files["file"]
    if not uploaded_file.filename:
        return error_response("No file was selected.")
    allowed_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
    extension = Path(uploaded_file.filename).suffix.lower()
    if extension not in allowed_extensions:
        return error_response(
            "Unsupported image format. Use PNG, JPG, JPEG, BMP or WEBP."
        )
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=extension,delete=False) as temporary_file:
            temporary_path = temporary_file.name
            uploaded_file.save(temporary_path)
        if os.path.getsize(temporary_path) == 0:
            return error_response("The uploaded image is empty.")
        if os.path.getsize(temporary_path) > 10 * 1024 * 1024:
            return error_response("Image size must not exceed 10 MB.", 413)
        result = decode_qr_code(temporary_path)
        if not isinstance(result, dict):
            return error_response(
                "The QR detector returned an unexpected response.",500
            )
        return success_response(
            result,
            "QR code processing completed."
        )
    except Exception:
        app.logger.exception("QR code scanning failed.")
        return error_response(
            "An error occurred while processing the QR image.",500
        )
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                app.logger.warning("Could not remove temporary QR image.")

# USER SCAN HISTORY
@app.route("/api/history", methods=["GET"])
@require_auth
def get_history():
    try:
        limit = request.args.get("limit", default=20, type=int)
        offset = request.args.get("offset", default=0, type=int)
        if limit is None or offset is None:
            return error_response("Limit and offset must be integers.")
        if limit < 1 or limit > 100:
            return error_response("Limit must be between 1 and 100.")
        if offset < 0:
            return error_response("Offset cannot be negative.")
        result = scan_service.get_history(
            user_id=request.user_id,
            limit=limit,
            offset=offset
        )
        return success_response(
            result, "Scan history retrieved successfully."
        )

    except Exception:
        app.logger.exception("Could not retrieve scan history.")
        return error_response(
            "Unable to retrieve scan history.",500
        )

# GET ONE HISTORY RECORD
@app.route("/api/history/<int:scan_id>", methods=["GET"])
@require_auth
def get_history_record(scan_id):
    try:
        result = scan_service.get_scan(
            user_id=request.user_id,
            scan_id=scan_id
        )
        if result is None:
            return error_response("Scan record not found.", 404)
        return success_response(
            result, "Scan record retrieved successfully."
        )
    except Exception:
        app.logger.exception("Could not retrieve scan record.")
        return error_response(
            "Unable to retrieve the scan record.",500
        )

# DELETE ONE HISTORY RECORD
@app.route("/api/history/<int:scan_id>", methods=["DELETE"])
@require_auth
def delete_history_record(scan_id):
    try:
        result = scan_service.delete_history_item(
            user_id=request.user_id,
            scan_id=scan_id
        )
        if not result:
            return error_response(
                "Scan record not found or could not be deleted.",404
            )
        return success_response(
            {"scan_id": scan_id}, "Scan history record deleted successfully."
        )
    except Exception:
        app.logger.exception("Could not delete scan record.")
        return error_response(
            "Unable to delete the scan record.",500
        )

# USER SCAN STATISTICS
@app.route("/api/statistics", methods=["GET"])
@require_auth
def get_statistics():
    try:
        result = scan_service.get_statistics(
            user_id=request.user_id
        )
        return success_response(
            result, "Scan statistics retrieved successfully."
        )
    except Exception:
        app.logger.exception("Could not retrieve scan statistics.")
        return error_response(
            "Unable to retrieve scan statistics.",500
        )

# REQUEST SIZE ERROR
@app.errorhandler(413)
def request_too_large(error):
    return error_response(
        "Uploaded content exceeds the 10 MB limit.",413
    )

# GENERAL ERROR HANDLER
@app.errorhandler(500)
def internal_server_error(error):
    return error_response(
        "An internal server error occurred.",500
    )

#CONTACT EMAIL HANDLER
@app.route("/api/contact", methods=["POST"])
def contact_message():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "message": "Invalid request."
        }), 400

    # Honeypot field: ordinary users should leave this empty.
    if data.get("website"):
        return jsonify({
            "success": True,
            "message": "Your message has been submitted successfully."
        }), 200
    name = str(data.get("fullName", "")).strip()
    sender_email = str(data.get("email", "")).strip()
    subject = str(data.get("subject", "")).strip()
    message = str(data.get("message", "")).strip()

    # Basic input validation
    if not name or not sender_email or not subject or not message:
        return jsonify({
            "success": False,
            "message": "Please complete all required fields."
        }), 400
    if len(name) > 100 or len(sender_email) > 254:
        return jsonify({
            "success": False,
            "message": "One or more fields are too long."
        }), 400
    if len(subject) > 100 or len(message) > 5000:
        return jsonify({
            "success": False,
            "message": "Subject or message is too long."
        }), 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", sender_email):
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address."
        }), 400
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")
    receiver_email = os.getenv("CONTACT_RECEIVER_EMAIL")
    if not all([smtp_host, smtp_email, smtp_password, receiver_email]):
        app.logger.error("Contact email configuration is incomplete.")
        return jsonify({
            "success": False,
            "message": "Email service is temporarily unavailable."
        }), 503
    email_message = EmailMessage()
    email_message["Subject"] = f"PhishGuard AI Contact: {subject}"
    email_message["From"] = smtp_email
    email_message["To"] = receiver_email
    email_message["Reply-To"] = sender_email
    email_message.set_content(
        f"""New Contact Us submission - PhishGuard AI
        Name: {name}
        Email: {sender_email}
        Subject: {subject}
        Message: {message}
        """
    )
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_email, smtp_password)
            server.send_message(email_message)
        return jsonify({
            "success": True,
            "message": "Your message has been submitted successfully!"
        }), 200
    except (smtplib.SMTPException, OSError):
        app.logger.exception("Contact email delivery failed.")
        return jsonify({
            "success": False,
            "message": "Unable to send your message right now. Please try again later."
        }), 502

# RUN APPLICATION
if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    app.run(
        host=host,
        port=port,
        debug=False
    )
