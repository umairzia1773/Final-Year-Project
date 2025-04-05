
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
RECAPTCHA_SECRET_KEY = "6LdhBOcqAAAAAF3yO9Oex4XsQsWi-gVuHMM_uYk7"

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# OTP configuration
OTP_EXPIRY_TIME = 5  # minutes
OTP_RESEND_DELAY = 120  # seconds

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname="user_auth",
        user="postgres",
        password="fypwork",
        host="localhost",
        port="5432"
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
                
                flash('Login successful!', 'success')
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
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        session['filename'] = filename
        return jsonify({"success": True, "filename": filename})
    
    return jsonify({"error": "Invalid file type"}), 400
    
@app.route('/ask', methods=["POST"])
def ask_question():
    print("🔍 [DEBUG] Received /ask request")
    data = request.get_json()
    question = data.get("question")
    print(f"✅ [DEBUG] Processing question: {question}")

    # ✅ Ensure user is logged in before processing
    if 'user_id' not in session:
        print("❌ [DEBUG] User not logged in")
        return jsonify({"error": "User not logged in"}), 401

    user_id = session['user_id']
    question = request.json.get('question')

    print(f"🔍 [DEBUG] Raw request data: {request.data}")  # Log raw request body
    print(f"🔍 [DEBUG] Request JSON: {request.json}")  # Log parsed JSON

    if not question:
        print("❌ [DEBUG] No question provided in request")
        return jsonify({"error": "No question provided"})

    print(f"✅ [DEBUG] Processing question: {question}")

    conn = get_db_connection()
    cur = conn.cursor()

    # ✅ Ensure user has an active chat session
    cur.execute("SELECT session_id FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1", (user_id,))

    chat_session = cur.fetchone()

    if chat_session:
        chat_session_id = chat_session[0]
        print(f"✅ [DEBUG] Found existing chat session: {chat_session_id}")
    else:
        print(f"⚠ [DEBUG] No existing chat session found. Creating a new one...")
        # ✅ Create a new chat session if none exists
        cur.execute("INSERT INTO chat_sessions (user_id) VALUES (%s) RETURNING session_id", (user_id,))
        chat_session_id = cur.fetchone()[0]
        conn.commit()

    # ✅ Store user question in chat_history
    try:
        print("✅ [DEBUG] Storing user question in chat_history")
        cur.execute(
        "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, NOW())",
        (chat_session_id, user_id, "user", question)
        )
        # cur.execute(
        # "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, NOW())",
        # (chat_session_id, user_id, "bot", ai_response)
        # )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERROR] Database error storing question: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    # ✅ Check if the question contains a URL and "scrape" keyword
    url_pattern = re.compile(r'https?://[^\s]+')
    scrape_command = "scrape"

    if re.search(url_pattern, question) and scrape_command in question.lower():
        url = re.search(url_pattern, question).group(0)
        filename = "file.json"
        print(f"✅ [DEBUG] Scraping requested for URL: {url}")
        try:
            subprocess.run(['scrapy', 'crawl', 'gas', '-O', filename, '-a', f'start_url={url}'], check=True)
            
            # ✅ Ensure the file is not empty before loading
            if os.path.exists(filename) and os.stat(filename).st_size > 0:
                with open(filename, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                print("✅ [DEBUG] Scraping successful")
                return jsonify({"scraped_data": scraped_data})
            else:
                return jsonify({"error": "Scraping completed, but no data was found in the file."})

        except subprocess.CalledProcessError as e:
            print(f"❌ [ERROR] Scraping failed: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Error during scraping", "message": str(e)})

    # ✅ Handle normal chatbot processing
    else:
        filename = session.get('filename')
        try:
            if filename:
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"✅ [DEBUG] Using RAG model with PDF: {pdf_path}")
                answer_text = brain.generate_response(question, pdf_text=pdf_path)
            else:
                print("✅ [DEBUG] Using general Llama model (no PDF provided)")
                answer_text = brain.generate_response(question)

            # Ensure response is string format
            if hasattr(answer_text, 'content'):
                answer_text = answer_text.content
            else:
                answer_text = str(answer_text)

            print(f"✅ [DEBUG] Model Response: {answer_text[:500]}")  # Print first 500 chars for debugging

        except Exception as e:
            print(f"❌ [ERROR] Error generating response: {e}")
            print(traceback.format_exc())
            return jsonify({"error": "Error generating response", "message": str(e)})

    # ✅ Convert response to Markdown
    try:
        answer_markdown = markdown2.markdown(answer_text)
    except Exception as e:
        print(f"❌ [ERROR] Markdown conversion failed: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Error converting answer to Markdown", "message": str(e)})

    # ✅ Store bot's response in the database under the same session
    try:
        print("✅ [DEBUG] Storing bot response in chat_history")
        cur.execute(
            "INSERT INTO chat_history (user_id, chat_session_id, sender, message) VALUES (%s, %s, %s, %s)",
            (user_id, chat_session_id, 'bot', answer_text)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ [ERROR] Database error storing bot response: {e}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

    print("✅ [DEBUG] Returning response to user")
    return jsonify({"answer": answer_markdown})

@app.route('/get_user_chat_sessions', methods=['GET'])
def get_user_chat_sessions():
    """Fetches all chat sessions for the user to show in the history panel."""
    user_id = session.get("user_id")  # Ensure user is logged in
    print(f"[DEBUG] Retrieved user_id: {user_id}")

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        

        # Optimized Query: Fetch chat sessions with their first message (or default name)
        cur.execute("""
            SELECT cs.session_id, 
                   COALESCE((
                       SELECT ch.message 
                       FROM chat_history ch 
                       WHERE ch.chat_session_id = cs.session_id 
                       ORDER BY ch.created_at ASC LIMIT 1
                   ), 'New Chat Session') AS session_name, 
                   cs.created_at
            FROM chat_sessions cs
            WHERE cs.user_id = %s
            ORDER BY cs.created_at DESC;
        """, (user_id,))

        sessions = cur.fetchall()

        if not sessions:
            print(f"[DEBUG] No chat sessions found for user {user_id}")
            return jsonify([]), 200  # Return empty list if no sessions found

        

        # Convert results into a JSON response
        session_list = []
        for row in sessions:
            if len(row) == 3:  # Check tuple has exactly 3 elements
                session_list.append({
                    "session_id": row[0], 
                    "session_name": row[1], 
                    "created_at": row[2].isoformat()
                })
            else:
                print(f"[ERROR] Unexpected row format: {row}")  # Debugging output

        return jsonify(session_list)

    except Exception as e:
        print("[ERROR] Failed to fetch user chat sessions:", e)
        return jsonify({"error": "Database error"}), 500

    finally:
        cur.close()
        conn.close()




@app.route('/store_message', methods=['POST'])
def store_message():
    """Store a message and create a new chat session if needed."""
    data = request.get_json()
    
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    message = data.get('message')
    sender = data.get('sender')
    timestamp = data.get('timestamp')
    is_first_message = data.get('is_first_message', False)

    if not all([user_id, message, sender]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # If no session_id, create a new chat session
        if not session_id:
            cur.execute("""
                INSERT INTO chat_sessions (user_id, created_at) 
                VALUES (%s, NOW()) 
                RETURNING session_id
            """, (user_id,))
            session_id = cur.fetchone()[0]

        # Store the message
        if timestamp:
            cur.execute(
                "INSERT INTO chat_history (chat_session_id, user_id, sender, message, created_at) VALUES (%s, %s, %s, %s, %s)",
                (session_id, user_id, sender, message, timestamp)
            )
        else:
            cur.execute(
                "INSERT INTO chat_history (chat_session_id, user_id, sender, message) VALUES (%s, %s, %s, %s)",
                (session_id, user_id, sender, message)
            )

        # If this is the first message in the chat, use it as the title
        if is_first_message and sender == 'user':
            # Truncate message if it's too long (keep first 50 chars)
            title = message[:50] + ('...' if len(message) > 50 else '')
            cur.execute(
                "UPDATE chat_sessions SET title = %s WHERE session_id = %s",
                (title, session_id)
            )

        conn.commit()
        return jsonify({"success": True, "session_id": session_id})

    except Exception as e:
        conn.rollback()
        print(f"Error storing message: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({"error": "User not authenticated"}), 401

    chat_session_id = request.args.get('session_id')
    
    if not chat_session_id:
        return jsonify({"error": "Invalid session ID"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get chat history with proper timestamp formatting
        cur.execute("""
            SELECT 
                ch.message,
                ch.sender,
                TO_CHAR(ch.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as created_at,
                cs.title
            FROM chat_history ch
            JOIN chat_sessions cs ON ch.chat_session_id = cs.session_id
            WHERE ch.chat_session_id = %s 
            ORDER BY ch.created_at ASC
        """, (chat_session_id,))

        messages = cur.fetchall()
        
        if not messages:
            return jsonify([])

        formatted_messages = [{
            "message": msg[0],
            "sender": msg[1],
            "timestamp": msg[2],  # ISO formatted timestamp
            "session_title": msg[3]
        } for msg in messages]
        
        return jsonify(formatted_messages)

    except Exception as e:
        print(f"Error fetching chat history: {e}")
        return jsonify({"error": "Failed to fetch chat history"}), 500

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()
                
@app.route('/rename_chat_session', methods=['POST'])
def rename_chat_session():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json()
    session_id = data.get('session_id')
    new_name = data.get('new_name')

    if not session_id or not new_name:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE chat_sessions SET title = %s WHERE session_id = %s AND user_id = %s",
            (new_name, session_id, session['user_id'])
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error renaming chat session: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
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
        return jsonify({"error": "User not authenticated"}), 401

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert a new chat session with a default title
        cur.execute("""
            INSERT INTO chat_sessions (user_id, title, created_at) 
            VALUES (%s, %s, NOW()) 
            RETURNING session_id
        """, (user_id, "New Chat"))
        
        new_session_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({
            "session_id": new_session_id,
            "success": True
        })
    except Exception as e:
        conn.rollback()
        print(f"Error creating new chat: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
        
if __name__ == '__main__':
    app.run(debug=True) 
