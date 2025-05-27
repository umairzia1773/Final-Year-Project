
from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
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
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    return conn


# Email configuration (use a test email service like Gmail or SendGrid)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")  # You can also use other SMTP servers
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")  # Replace with your email
ENDER_PASSWORD = os.getenv("SENDER_PASSWORD")  # Replace with your email password or app-specific password
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

# Login page
# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         print("Received login:", email, password)  # Debug print

#         # Connect to the database
#         conn = get_db_connection()
#         cur = conn.cursor()

#         # Query to fetch user with the given email
#         cur.execute('SELECT * FROM users WHERE email = %s', (email,))
#         user = cur.fetchone()
#         print("User record:", user)  # Debug print


#         # If user exists, check the password
#         if user and check_password_hash(user[3], password):  # Assuming password is stored in column 2
#             # Successful login
#             flash('Login successful!', 'success')
#             return redirect(url_for('chat'))  # Redirect to dashboard or main page
#         else:
#             # Invalid email or password
#             flash('Invalid email or password, please try again.', 'danger')

#         cur.close()
#         conn.close()

#     return render_template("login.html")




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
                    flash('Login successful!', 'success')
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
# Chat page
@app.route("/chat")
def chat():
    return render_template("chat.html")
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
@app.route('/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    if not question:
        return jsonify({"error": "No question provided"})

    # Check if the question contains a URL and "scrape" keyword
    url_pattern = re.compile(r'https?://[^\s]+')
    scrape_command = "scrape"  # This is an optional word to trigger scraping

    if re.search(url_pattern, question) and scrape_command in question.lower():
        url = re.search(url_pattern, question).group(0)

        # Trigger the Scrapy spider
        filename = "file.json"  # Assuming the Scrapy output is saved to file.json
        try:
            # Run Scrapy command
            subprocess.run(['scrapy', 'crawl', 'gas', '-O', filename, '-a', f'start_url={url}'], check=True)


            # Read the contents of the scraped file
            with open(filename, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)

            return jsonify({"scraped_data": scraped_data})

        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Error during scraping", "message": str(e)})

    else:
        # Check if a PDF is uploaded
        filename = session.get('filename')
    if filename:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # Get the answer from the PDF
        answer_text = brain.generate_response(question, pdf_text=pdf_path)
    else:
        # If no PDF is uploaded, answer the general question
        answer_text = brain.generate_response(question)

    # Ensure the answer is a string, extracting it from AIMessage if needed
    if hasattr(answer_text, 'content'):
        answer_text = answer_text.content  # Extract content from AIMessage
    else:
        answer_text = str(answer_text)  # Use directly if already a string

    # Convert the answer to Markdown
    # try:
    #     answer_markdown = markdown2.markdown(answer_text)
    # except Exception as e:
    #     return jsonify({"error": "Error converting answer to Markdown", "message": str(e)})
    try:
        if not isinstance(answer_text, str):
            answer_text = str(answer_text)  # Ensure it's a string
        answer_markdown = markdown2.markdown(answer_text)
    except Exception as e:
        return jsonify({"error": "Error converting answer to Markdown", "message": str(e)})

    return jsonify({"answer": answer_markdown})

    
if __name__ == '__main__':
    app.run(debug=True)
