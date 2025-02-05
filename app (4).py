
'''from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import brain
from flask import Flask, render_template
app = Flask(__name__, static_folder='static')

# app = Flask(__name__)

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

# Home route renders the form
@app.route('/')
def home():
    return render_template('chat.html')

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
    
    # Check if a PDF is uploaded
    filename = session.get('filename')
    if filename:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        answer = brain.get_answer_from_pdf(pdf_path, question)
    else:
        # If no PDF is uploaded, answer the general question
        answer = brain.get_answer_from_ollama(question)
    
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
'''
# from flask import Flask, render_template, request, jsonify, session
# from flask_cors import CORS
# from werkzeug.utils import secure_filename
# import os
# import markdown  # For Markdown rendering
# import brain

# app = Flask(__name__, static_folder='static')

# # Enable CORS for all routes
# CORS(app)

# # Configurations
# UPLOAD_FOLDER = 'uploads'
# ALLOWED_EXTENSIONS = {'pdf'}
# app.secret_key = os.urandom(24)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# # Ensure the upload folder exists
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# # Markdown filter function
# @app.template_filter('markdown')
# def markdown_filter(text):
#     """Render text as Markdown."""
#     return markdown.markdown(text)

# # Utility function to check file extensions
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # Home route renders the form
# @app.route('/')
# def home():
#     return render_template('chat.html')

# # Upload endpoint for PDFs
# @app.route('/upload', methods=['POST'])
# def upload_pdf():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"})
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"})
    
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(file_path)
#         session['filename'] = filename  # Save filename in session
#         return jsonify({"message": "PDF uploaded successfully", "filename": filename})
    
#     return jsonify({"error": "File type not allowed"})

# # Ask endpoint for questions
# @app.route('/ask', methods=['POST'])
# def ask_question():
#     question = request.json.get('question')
#     if not question:
#         return jsonify({"error": "No question provided"})
    
#     # Check if a PDF is uploaded
#     filename = session.get('filename')
#     if filename:
#         pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         answer = brain.get_answer_from_pdf(pdf_path, question)
#     else:
#         # If no PDF is uploaded, answer the general question
#         answer = brain.get_answer_from_ollama(question)
    
#     return jsonify({"answer": answer})

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import brain
import markdown
import markdown2
import json
import subprocess
import re

app = Flask(__name__, static_folder='static')

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

# Add Markdown filter to Jinja2
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown.markdown(text)

# Home route renders the form
@app.route('/')
def home():
    initial_message = {"content": "Welcome! Ask me anything to get started."}
    return render_template('chat.html', message=initial_message)


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
            subprocess.run(['scrapy', 'crawl', 'ebay_items', '-O', filename], check=True)
            
            # Read the contents of the scraped file
            with open(filename, 'r') as f:
                scraped_data = json.load(f)
            
            return jsonify({"scraped_data": scraped_data})
        
        except subprocess.CalledProcessError as e:
            return jsonify({"error": "Error during scraping", "message": str(e)})
    
    else:
        # Check if a PDF is uploaded
        filename = session.get('filename')
        if filename:
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            answer = brain.get_answer_from_pdf(pdf_path, question)
        else:
            # If no PDF is uploaded, answer the general question
            answer = brain.get_answer_from_ollama(question)
        
        # Convert the answer to Markdown
        answer_markdown = markdown2.markdown(answer)
        return jsonify({"answer": answer_markdown})


if __name__ == '__main__':
    app.run(debug=True)
