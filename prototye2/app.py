
from flask import jsonify
from flask_cors import CORS
import traceback
import os
from werkzeug.utils import secure_filename
import brain
import markdown2 # type: ignore
import json
import subprocess
import re
import markdown
from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2 import sql
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from werkzeug.security import check_password_hash
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from flask import session
import os
import secrets  # For OTP generation
from datetime import datetime


app = Flask(__name__, static_folder='static')

load_dotenv()

# app.secret_key = 'your_secret_key'  # Required for session flash messages
app.secret_key = os.getenv("SECRET_KEY")
bcrypt = Bcrypt(app)

conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "user_auth"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv("POSTGRES_PORT", "5432")
)
cursor = conn.cursor()

def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "user_auth"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv("POSTGRES_PORT", "5432")  # Default PostgreSQL port
    )
    return conn


# Email configuration (use a test email service like Gmail or SendGrid)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # You can also use other SMTP servers
MTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # Replace with your email
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # Replace with your email password or app-specific password
RECIPIENT_EMAIL = ""  # Will be set dynamically

# OTP Generation
def generate_otp():
    return str(random.randint(100000, 999999))  # Generates a 6-digit OTP

# Send OTP email
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


from datetime import datetime, timedelta, timezone
OTP_EXPIRY_TIME = 5
OTP_RESEND_DELAY = 120
# Enable CORS for all routes
CORS(app)



# Configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Utility function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text)

    
# Home route renders the form
# Default route redirects to the signup page
@app.route("/")
def index():
    return render_template("signup.html")

# Signup page
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert into database
        try:
            cursor.execute(
                sql.SQL("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)"),
                (full_name, email, hashed_password)
            )
            conn.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Email already exists. Try logging in.", "danger")

    return render_template("signup.html")



@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # ❌ Do NOT encode yet

        print(f"\n[DEBUG] Received Login Request - Email: {email}, Password: {password}")

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute('SELECT id, full_name, email, password_hash, created_at FROM users WHERE email = %s', (email,))
            user = cur.fetchone()

            print(f"[DEBUG] Retrieved user record: {user}")

            if user:
                user_id, full_name, user_email, stored_hash, created_at = user

                if stored_hash is None:
                    print("[ERROR] Password hash is None! Possible database corruption.")
                    flash('Something went wrong. Please contact support.', 'danger')
                    return redirect(url_for('login'))

                print(f"[DEBUG] Raw Stored Hash: '{stored_hash}'")
                print(f"[DEBUG] Hash Length: {len(stored_hash)}")
                print(f"[DEBUG] Hash Type: {type(stored_hash)}")

                if isinstance(stored_hash, bytes):  # Ensure stored hash is string
                    stored_hash = stored_hash.decode('utf-8')

                print(f"[DEBUG] Cleaned Stored Hash: '{stored_hash}'")

                # ✅ Use Flask-Bcrypt for password checking
                if bcrypt.check_password_hash(stored_hash, password):  
                    print("[DEBUG] ✅ Password Matched!")
                    # ✅ FIX Set session before redirecting
                    session['user_id'] = user_id
                    session['full_name'] = full_name
                    session.modified = True
                    print(f"[DEBUG] ✅ Session Set: user_id = {session.get('user_id')}")
                    flash('Login successful!', 'success')
                    print(f"[DEBUG] ✅ User logged in, session user_id = {session['user_id']}")  # ✅ Debug print

                    return redirect(url_for('chat'))
                else:
                    print("[DEBUG] ❌ Password Mismatch!")
                    flash('Invalid email or password, please try again.', 'danger')

            else:
                print("[DEBUG] ❌ No User Found!")
                flash('Invalid email or password, please try again.', 'danger')

        except Exception as e:
            print(f"[ERROR] Database error: {e}")
            flash('Internal server error. Please try again later.', 'danger')

        finally:
            cur.close()
            conn.close()

    return render_template("login.html")
# Password reset page
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
            session["otp"] = otp  # Store OTP in session for verification
            session["email"] = email  # Store email in session
            session["otp_time"] = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')  # Store OTP time


            if send_otp_email(email, otp):
                flash("OTP sent to your email. Please check your inbox.", "success")
                return redirect(url_for("verify_otp"))  # Redirect to OTP page
            else:
                flash("Failed to send OTP. Try again later.", "danger")
        else:
            flash("Email not found. Please check and try again.", "danger")
    return render_template("password.html")
#for otp veirfy
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

        if entered_otp == session.get("otp"):  # Check if OTP matches
            flash("OTP verified! You can now reset your password.", "success")
            return redirect(url_for("reset_password"))  # Redirect to reset password page
        else:
            flash("Invalid OTP. Please try again.", "danger")

    return render_template("verify.html")  # Render OTP verification page

#password reset route
@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        conn = get_db_connection()
        cur = conn.cursor()

        # Update password in database
        cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed_password, session.get("email")))
        conn.commit()
        cur.close()
        conn.close()

        session.pop("otp", None)  # Remove OTP from session after use
        session.pop("email", None)  # Remove email from session

        flash("Password successfully reset! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset-password.html")  # Render reset password page

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
        flash("New OTP sent to your email.", "success")
    else:
        flash("Failed to resend OTP. Try again later.", "danger")

    return redirect(url_for("verify_otp"))


@app.route('/chat', methods=["GET", "POST"])
def chat():
    user_id = session.get('user_id')
    print(f"[DEBUG] ✅ Flask user_id before rendering chat: {user_id}")
    # print(f"[DEBUG] Chat Route - Session User ID: {session.get('user_id')}")
    if 'user_id' not in session:
        flash("Session expired! Please log in again.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "SELECT session_id FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        
        chat_session = cur.fetchone()

        if not chat_session:
            flash("No previous chat session found.", "info")
            cur.execute(
            "INSERT INTO chat_sessions (user_id, created_at) VALUES (%s, NOW()) RETURNING session_id",
            (user_id,)
            )
            chat_session_id = cur.fetchone()[0]
            return render_template("chat.html", messages=[])


        chat_session_id = chat_session[0]
        print(f"[DEBUG] Active Chat Session ID: {chat_session_id}")

        # 🔹 Fetch messages for this session
        cur.execute(
            "SELECT message, sender, created_at FROM chat_history WHERE chat_session_id = %s ORDER BY created_at ASC",
            (chat_session_id,)
        )
        messages = cur.fetchall()

        formatted_messages = [
            {"message": msg[0], "sender": msg[1], "timestamp": msg[2].strftime("%Y-%m-%d %H:%M:%S")}
            for msg in messages
        ]



        # return render_template("chat.html", messages=formatted_messages)

    except Exception as e:
        # flash("Error retrieving chat history", "danger")
        # return redirect(url_for('chat'))
        print(f"[ERROR] Database error: {e}")  # Log the error
        flash("Error retrieving chat history. Please try again later.", "danger")
        formatted_messages = []  # Show an empty chat instead of redirecting

    finally:
        cur.close()
        conn.close()
    # return render_template("chat.html", messages=formatted_messages, user_id=user_id)
    return render_template("chat.html", user_id=user_id)

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.json
    user_id = session.get("user_id")
    message = data.get("message").strip()
    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401
   

    
    is_new_session = False
    session_name = None
    created_at = None
    # message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Check if a session exists for this user in the current chat instance
    chat_session_id = session.get("chat_session_id")
    conn = get_db_connection()
    cur = conn.cursor()
    if not chat_session_id:
        
        
        # Create a new session since none exists
        session_name = message[:40]
        cur.execute(
            "INSERT INTO chat_sessions (user_id, created_at) VALUES (%s, NOW()) RETURNING session_id, created_at",
            (user_id,)
        )
        chat_session = cur.fetchone()
        # chat_session_id = chat_session[0]
        # chat_session_id, created_at = chat_session
        chat_session_id = chat_session[0]
        session["chat_session_id"] = chat_session_id
        conn.commit()
        is_new_session = True  # ✅ Mark it as a new session
    else:
        is_new_session = False

        # Store session ID in user session
        
        
        cur.close()
        conn.close()
    

    # Store message in chat_history table
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chat_history (chat_session_id, user_id, message, created_at) VALUES (%s, %s, %s, NOW())",
        (chat_session_id, user_id, message)
    )
    conn.commit()
    cur.close()
    conn.close()

    # response_data = {"chat_session_id": chat_session_id}
    # if session_name:  # If it's a new session, return session_name and created_at
    #     response_data["session_name"] = session_name
    #     response_data["created_at"] = chat_session[1].isoformat()

    # return jsonify(response_data)
    return jsonify({
    "chat_session_id": chat_session_id,
    "session_name": session_name,  # This is just for the frontend display
    "created_at": created_at.isoformat() if created_at else None,
    "is_new_session": is_new_session
})


@app.route("/get_user_chat_sessions", methods=["GET"])
def get_user_chat_sessions():
    user_id = session.get("user_id")  # Ensure user is logged in

    if not user_id:
        return jsonify({"error": "User not authenticated"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # ✅ Fetch session_id and created_at, plus session name as the first message in chat_history
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

        # ✅ Ensure correct tuple indexing
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

@app.route('/get_chat_history', methods=['GET', "POST"])
def get_chat_history():
    """Fetches all chat sessions and messages for a user."""
    print(f"[DEBUG] Request args: {request.args}")  # Print GET parameters
    print(f"[DEBUG] Request form: {request.form}")  # Print POST form data
    chat_session_id = request.args.get('session_id')
    print(f"[DEBUG] Extracted chat_session_id: {chat_session_id}")

    if not chat_session_id or chat_session_id == "undefined" or not chat_session_id.isdigit():
        return jsonify({"error": "Invalid session ID"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        
        cur.execute("""
            SELECT message, sender, created_at 
            FROM chat_history 
            WHERE chat_session_id = %s 
            ORDER BY created_at ASC
        """, (int(chat_session_id),))    
        messages = cur.fetchall()
        print(f"[DEBUG] Messages found for session {chat_session_id}: {messages}")

        
        cur.close()
        conn.close()

        if not messages:
            print("[DEBUG] No messages found, returning empty list.")  # Debug log

            return jsonify([])
        formatted_messages = [
            {"message": markdown2.markdown(row[0]) if row[1] == "bot" else row[0], "sender": row[1], "timestamp": row[2].isoformat()}
            for row in messages
        ]
        print("[DEBUG] Chat history response:", formatted_messages)

        return jsonify(formatted_messages), 200  # ✅ Return only messages for the session

    except Exception as e:
        print(f"[ERROR] Failed to fetch chat history: {e}")  # ✅ Log the error

        return jsonify({"error": str(e)}), 500


@app.route('/start_new_chat', methods=['POST'])
def start_new_chat():
    """Creates a new chat session for the user."""
    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur = conn.cursor()

        # Insert a new chat session
        cur.execute("""
            INSERT INTO chat_sessions (user_id, created_at) 
            VALUES (%s, NOW()) RETURNING session_id
        """, (user_id,))
        
        new_session_id = cur.fetchone()[0]
        conn.commit()
        cur.close()

        return jsonify({"session_id": new_session_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/get_last_chat_session', methods=['GET'])
def get_last_chat_session():
    """Fetch the last active chat session for the user."""
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    try:
        cur = conn.cursor()

        # Fetch the last created session for the user
        cur.execute("""
            SELECT session_id FROM chat_sessions 
            WHERE user_id = %s ORDER BY created_at DESC LIMIT 1
        """, (user_id,))
        
        last_session = cur.fetchone()
        cur.close()

        if last_session:
            return jsonify({"session_id": last_session[0]}), 200
        else:
            return jsonify({"session_id": None}), 200  # No previous sessions found
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route('/store_message', methods=['POST'])
def store_message():
    """Stores a chat message under the correct chat session."""
    data = request.json
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    message = data.get('message')
    sender = data.get('sender')

    if not session_id or not user_id or not message or not sender:
        return jsonify({"error": "All fields are required"}), 400

    try:
        cur = conn.cursor()

        # Insert message into chat_history table
        cur.execute("""
            INSERT INTO chat_history (chat_session_id, user_id, message, sender, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
        """, (session_id, user_id, message, sender))

        conn.commit()
        cur.close()

        return jsonify({"message": "Message stored successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_chat_sessions', methods=['GET'])
def get_chat_sessions():
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


# Upload endpoint for PDFs
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['filename'] = filename  # Save filename in session
        return jsonify({"message": "PDF uploaded successfully", "filename": filename})

    return jsonify({"error": "File type not allowed"})

# Ask endpoint for questions
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
    
if __name__ == '__main__': 
    app.run(debug=True)  # Disable auto-reload for debugging

