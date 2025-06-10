# WEB WORK


# AI Chat Application

A modern web-based chat application with AI capabilities, featuring real-time messaging, session management, and a responsive interface.

## Project Structure

```
project/ ├── static/
│   ├── css/ 
│   │   └── styles.css
│   │   └── style.css 
│   └── js/ 
│       └── chat.js
│       └── script.js 
├── templates/ 
│   ├── chat.html 
│   ├── login.html 
│   ├── signup.html 
│   ├── password.html 
│   ├── verify.html 
│   └── reset-password.html 
├── app.py
├── brain.py
├── entrypoint.sh 
├── requirements.txt 
├── Dockerfile 
├── docker-compose.yml 
└── .env
```

## Features

- User Authentication (Login/Signup)
- Password Reset with Email Verification
- Real-time Chat Interface
- Chat Session Management
- Dark/Light Theme Toggle
- Message History
- File Upload Support
- Responsive Design

## Technology Stack

- **Frontend:**
  - HTML5
  - CSS3
  - JavaScript (Vanilla)
  - Font Awesome Icons
  - Bootstrap 5
  - Marked.js (Markdown parsing)

- **Backend:**
  - Python (Flask)
  - PostgreSQL
  - Flask-Bcrypt
  - SMTP Email Service
  - Docker/Docker Compose

## Database Schema

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Sessions Table
CREATE TABLE chat_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    title VARCHAR(100) DEFAULT 'New Chat',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat History Table
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    chat_session_id INTEGER REFERENCES chat_sessions(session_id),
    user_id INTEGER REFERENCES users(id),
    sender VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 ```

## Setup Instructions

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Environment Variables:**
Create a `.env` file with:
```
FLASK_ENV= your_environment
POSTGRES_HOST=Your_host
POSTGRES_USER=your_set_user
POSTGRES_PASSWORD=your_password
SECRET_KEY=your_secret_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_email_password
RECAPTCHA_SECRET_KEY=your_recaptcha_key
SMTP_SERVER=smtp.gmail.co
SMTP_PORT= your port 
GROQ_API_KEY=your_api_key
OLLAMA_API_KEY=your_api_key

```

3. **Database Setup:**
```bash
# Create PostgreSQL database
createdb user_auth

# Run the SQL commands to create tables
psql -d user_auth -f schema.sql
```
4. **Setting environment variable on powershell if needed**
```bash
$env:POSTGRES_HOST="localhost"
$env:FLASK_ENV="development"
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="your_password"
$env:POSTGRES_DB="user_auth"
$env:SECRET_KEY="your_secret_key"
$env:SENDER_EMAIL="your_email@gmail.com"
$env:SENDER_PASSWORD="your_email_password"
$env:RECAPTCHA_SECRET_KEY="your_recaptcha_key"
$env:SMTP_SERVER="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:GROQ_API_KEY="your_groq_key"
$env:OLLAMA_API_KEY="your_ollama_key"
```   
5. **Run Application locally :**
```bash
$env:POSTGRES_HOST="localhost"
$env:FLASK_ENV="development"
python app.py
```

## DOCKER SETUP

Prerequisites:
- Docker
- Docker Compose

## Docker commands 

```bash
# Build and start containers
docker-compose up --build

# Start in detached mode
docker-compose up -d

# Stop containers
docker-compose down

# Build Docker image
docker build -t chat-app .

# Run Docker container
docker run -d -p 5000:5000 --name chat-app chat-app

# View logs
docker logs chat-app

# Enter container
docker exec -it chat-app bash
```

## Key Features Implementation

### Authentication System
- Secure password hashing with Bcrypt
- Email verification for password reset
- reCAPTCHA integration for security
- Session management

### Chat Interface
- Real-time message display
- Markdown support for messages
- Dynamic session management
- File upload capability
- Theme switching

### User Experience
- Responsive design for all devices
- Intuitive navigation
- Error handling and feedback
- Loading states and animations

## Frontend Components

### HTML Templates
- Modular template structure
- Bootstrap integration
- Font Awesome icons
- Responsive layouts

### CSS Features
- Custom CSS variables for theming
- Responsive design
- Smooth animations
- Dark/Light mode support

### JavaScript Functionality
- Dynamic content loading
- Real-time updates
- Event handling
- Form validation
- Theme management

## Backend Routes

### Authentication Routes
- `/signup` - User registration
- `/login` - User login
- `/logout` - User logout
- `/password` - Password reset initiation
- `/verify` - OTP verification
- `/reset-password` - Password reset completion

### Chat Routes
- `/chat` - Main chat interface
- `/ask` - Message processing
- `/upload` - File upload handling
- `/get_chat_history` - Retrieve chat history
- `/get_user_chat_sessions` - Get user's chat sessions
- `/start_new_chat` - Create new chat session
- `/rename_chat_session` - Rename existing session
- `/delete_chat_session` - Delete chat session

## Security Features

- Password hashing
- Session management
- CSRF protection
- Input validation
- Error handling
- Rate limiting

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Known Limitations

- File upload limited to PDFs
- Maximum message length: No specific limit
- Session timeout: 24 hours

## Future Improvements

- Real-time notifications
- Message search functionality
- Chat export functionality

