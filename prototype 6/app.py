from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import traceback
from werkzeug.utils import secure_filename
import brain
import markdown2
import json
import subprocess
import re
import requests
import markdown
import psycopg2
from psycopg2 import sql
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import subprocess   
from PyPDF2 import PdfReader 

app = Flask(__name__, static_folder='static')

load_dotenv()

# Configuration
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.secret_key = os.environ.get('SECRET_KEY')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Flask-Bcrypt
bcrypt = Bcrypt(app)

# Enable CORS
CORS(app)

# reCAPTCHA configuration
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
# Email configuration

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# OTP configuration
OTP_EXPIRY_TIME = 5  # minutes
OTP_RESEND_DELAY = 120  # seconds

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "user_auth"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

# Utility functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_password_strong(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[@$!%*?&]", password):
        return False
    return True

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(user_email, otp):
    try:
        subject = "Password Reset OTP"
        body = f"Your OTP for password reset is: {otp}"
        msg = MIMEText(body)
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email
        msg["Subject"] = subject

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending OTP: {e}")
        return False

def verify_recaptcha(recaptcha_response):
    verification_url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": RECAPTCHA_SECRET_KEY,
        "response": recaptcha_response
    }
    response = requests.post(verification_url, data=data)
    result = response.json()
    return result.get("success", False)

# Template filters
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text)

# Routes
@app.route("/")
def index():
    return render_template("signup.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response or not verify_recaptcha(recaptcha_response):
            flash("Recaptcha is invalid.", "danger")
            return redirect(url_for('signup'))
            
        full_name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form.get('confirm-password')
        
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('signup'))

        if not is_password_strong(password):
            flash("Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Insert into database
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                (full_name, email, hashed_password)
            )
            conn.commit()
            cur.close()
            conn.close()

            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Email already exists. Try logging in.", "danger")
            return redirect(url_for('signup'))

    return render_template("signup.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute('SELECT id, full_name, email, password_hash FROM users WHERE email = %s', (email,))
            user = cur.fetchone()

            if user and bcrypt.check_password_hash(user[3], password):
                # Set session
                session['user_id'] = user[0]
                session['full_name'] = user[1]
                session.modified = True
                
                # flash('Login successful!', 'success')
                return redirect(url_for('chat'))
            else:
                flash('Invalid email or password, please try again.', 'danger')
                return redirect(url_for('login'))
        except Exception as e:
            flash('Internal server error. Please try again later.', 'danger')
            return redirect(url_for('login'))
        finally:
            cur.close()
            conn.close()

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/password", methods=["GET", "POST"])
def password():
    if request.method == "POST":
        email = request.form["email"]

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if email exists
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            otp = generate_otp()
            session["otp"] = otp
            session["email"] = email
            session["otp_time"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please check your inbox.", "success")
                return redirect(url_for("verify_otp"))
            else:
                flash("Failed to send OTP. Try again later.", "danger")
        else:
            flash("Email not found. Please use a valid email", "danger")
            return redirect(url_for("password"))
            
    return render_template("password.html")

@app.route("/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form["otp"]
        otp_time_str = session.get("otp_time")

        if not otp_time_str:
            flash("OTP expired! Please request a new one.", "danger")
            return redirect(url_for("password"))
        
        otp_time = datetime.strptime(otp_time_str, '%Y-%m-%d %H:%M:%S')
        otp_time = otp_time.replace(tzinfo=timezone.utc)
        
        if datetime.now(timezone.utc) - otp_time > timedelta(minutes=OTP_EXPIRY_TIME):
            flash("OTP expired! Please request a new one.", "danger")
            session.pop("otp", None)
            session.pop("otp_time", None)
            return redirect(url_for("password"))

        if entered_otp == session.get("otp"):
            flash("OTP verified! You can now reset your password.", "success")
            return redirect(url_for("reset_password"))
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template("verify.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]
        
        if not is_password_strong(new_password):
            flash("Password must be at least 8 characters long and include: 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character.", "danger")
            return redirect(url_for('reset_password'))
            
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()

        # Update password in database
        cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, session.get("email")))
        conn.commit()
        cur.close()
        conn.close()

        session.pop("otp", None)
        session.pop("email", None)

        flash("Password successfully reset! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset-password.html")

@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    last_otp_time_str = session.get("otp_time")

    if last_otp_time_str:
        last_otp_time = datetime.strptime(last_otp_time_str, '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() - last_otp_time < timedelta(seconds=OTP_RESEND_DELAY):
            flash("Please wait before requesting a new OTP.", "warning")
            return redirect(url_for("verify_otp"))

    otp = generate_otp()
    session["otp"] = otp  
    session["otp_time"] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')  

    if send_otp_email(session.get("email"), otp):
        return jsonify(success=True, message="New OTP sent to your email.")
    else:
        return jsonify(success=False, message="Failed to resend OTP. Try again later.")

@app.route("/check-session", methods=["GET"])
def check_session():
    return jsonify(active='user_id' in session)

@app.route('/chat', methods=["GET"])
def chat():
    if 'user_id' not in session:
        flash("Please log in to access the chat.", "warning")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    return render_template("chat.html", user_id=user_id)

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Upload endpoint hit")  # Debug log
    if 'file' not in request.files:
        print("No file in request")  # Debug log
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    print(f"Received file: {file.filename}")  # Debug log
    
    if file.filename == '':
        print("No filename")  # Debug log
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f"File saved to: {filepath}")  # Debug log
                    
            # Extract text from PDF
            pdf_text = extract_pdf_text(filepath)
            print("PDF text extracted successfully")  # Debug log
                    
            # Store in session for context
            session['pdf_context'] = pdf_text
                    
            return jsonify({
                    "success": True,
                        "filename": filename,
                        "context": pdf_text
                    })

        except Exception as e:
            print(f"Error in upload: {str(e)}")  # Debug log
            return jsonify({"error": str(e)}), 500
    
    print("Invalid file type")  # Debug log
    return jsonify({"error": "Invalid file type"}), 400
    
def extract_pdf_text(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        raise
    
@app.route('/ask', methods=["POST"])
def ask_question():
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    message = data.get('message')
    session_id = data.get('session_id')
    file_context = data.get('file_context')

    if not message:
        return jsonify({"error": "No message provided"})

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # Store user message
        cur.execute(
        "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (session_id, session['user_id'], "user", message)
        )

        # Generate AI response with context if available
        if file_context:
            print("Using file context for response") # Debug log
            # Use the file context to generate a response
            ai_response = brain.generate_response_with_context(message, file_context)
            print("Generated response with context") # Debug log
        else:
            print("No file context, using standard response") # Debug log
            # Normal response without context
            ai_response = brain.generate_response(message)
        
        # Convert AIMessage to string if needed
        answer_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
        
        # Store bot response
        cur.execute(
            "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (session_id, session['user_id'], "bot", answer_text)
        )
        
        conn.commit()
        return jsonify({"answer": answer_text})

    except Exception as e:
        print(f"Error processing request: {e}")
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

@app.route('/get_user_chat_sessions', methods=['GET'])
def get_user_chat_sessions():
    """Fetches all chat sessions for the user to show in the history panel."""
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    user_id = session.get("user_id")
    print(f"Fetching sessions for user_id: {user_id}")  # Debug log

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch chat sessions with their titles
        cur.execute("""
            SELECT 
                session_id,
                COALESCE(title, 'New Chat') as session_name,
                created_at
            FROM chat_sessions 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))

        sessions = cur.fetchall()
        print(f"Found {len(sessions)} sessions")  # Debug log

        # Convert to list of dicts
        session_list = [{
            "session_id": str(row[0]),
                    "session_name": row[1], 
            "created_at": row[2].isoformat() if row[2] else None
        } for row in sessions]

        return jsonify(session_list)

    except Exception as e:
        print(f"Error fetching chat sessions: {e}")  # Debug log
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

@app.route('/store_message', methods=['POST'])
def store_message():
    """Store a message and create a new chat session if needed."""
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    message = data.get('message', '')
    is_new_session = data.get('is_new_session', False)
    session_name = data.get('session_name', 'New Chat')
    
    # Create a new chat session or use existing one
    conn = get_db_connection()
    cur = conn.cursor()
    
    chat_session_id = None
    created_at = None
    
    if is_new_session:
        # Create a new chat session
        cur.execute(
            "INSERT INTO chat_sessions (user_id, title, created_at) VALUES (%s, %s, NOW()) RETURNING session_id, created_at",
            (user_id, session_name)
        )
        chat_session_id, created_at = cur.fetchone()
        conn.commit()
    else:
        # Use the most recent chat session or create a new one if none exists
        cur.execute(
            "SELECT session_id, created_at FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        chat_session = cur.fetchone()
        
        if chat_session:
            chat_session_id, created_at = chat_session
        else:
            # Create a new chat session if none exists
            cur.execute(
                "INSERT INTO chat_sessions (user_id, title, created_at) VALUES (%s, %s, NOW()) RETURNING session_id, created_at", 
                (user_id, session_name)
            )
            chat_session_id, created_at = cur.fetchone()
            conn.commit()
            is_new_session = True
    
    # Store message if not empty
    if message:
        cur.execute(
            "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (chat_session_id, user_id, "user", message)
        )
        conn.commit()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "chat_session_id": chat_session_id,
        "session_name": session_name,
        "created_at": created_at.isoformat() if created_at else None,
        "is_new_session": is_new_session
    })

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    chat_session_id = request.args.get('session_id')
    if not chat_session_id:
        return jsonify({"error": "No session ID provided"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get all messages for the session
        cur.execute("""
            SELECT message, sender, created_at
            FROM chat_history
            WHERE chat_session_id = %s
            ORDER BY created_at ASC
        """, (chat_session_id,))

        messages = cur.fetchall()

        # Format messages
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                'message': msg[0],
                'sender': msg[1],
                'created_at': msg[2].isoformat() if msg[2] else None
            })

        return jsonify(formatted_messages)

    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/rename_chat_session', methods=['POST'])
def rename_chat_session():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Not authenticated"}), 401

    data = request.get_json()
    session_id = data.get('session_id')
    new_name = data.get('new_name')

    if not session_id or not new_name:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update the session name with proper transaction handling
        cur.execute("""
            UPDATE chat_sessions 
            SET title = %s 
            WHERE session_id = %s AND user_id = %s
            RETURNING session_id, title, created_at
        """, (new_name, session_id, session['user_id']))
        
        updated_session = cur.fetchone()
        conn.commit()

        if updated_session:
            return jsonify({
                "success": True,
                "session_id": str(updated_session[0]),
                "new_name": updated_session[1],
                "created_at": updated_session[2].isoformat() if updated_session[2] else None
            })
        else:
            return jsonify({"success": False, "error": "Session not found"}), 404

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error renaming chat session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_chat_session', methods=['POST'])
def delete_chat_session():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Delete chat history first due to foreign key constraint
        cur.execute(
            "DELETE FROM chat_history WHERE chat_session_id = %s AND user_id = %s",
            (session_id, session['user_id'])
        )
        cur.execute(
            "DELETE FROM chat_sessions WHERE session_id = %s AND user_id = %s",
            (session_id, session['user_id'])
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
        

       
@app.route('/start_new_chat', methods=['POST'])
def start_new_chat():
    """Creates a new chat session for the user."""
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
        
    data = request.json
    user_id = session['user_id']
    initial_message = data.get('initial_message', '')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Create session name from initial message
        words = initial_message.split()[:4]  # Get first 4 words
        session_name = ' '.join(words)
        if len(session_name) > 30:
            session_name = session_name[:27] + '...'
        
        if not session_name:
            session_name = 'New Chat'
        
        # Create new chat session
        cur.execute("""
            INSERT INTO chat_sessions (user_id, title, created_at) 
            VALUES (%s, %s, NOW()) RETURNING session_id
        """, (user_id, session_name))
        
        new_session_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            "session_id": new_session_id,
            "session_name": session_name
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating new chat: {e}")
        return jsonify({"error": str(e)}), 500
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=True) 
