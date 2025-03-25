# WEB WORK

```markdown
# AI Chat Application

A modern web-based chat application with AI capabilities, featuring real-time messaging, session management, and a responsive interface.

## Project Structure

```
project/
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── chat.js
├── templates/
│   ├── chat.html
│   ├── login.html
│   ├── signup.html
│   ├── password.html
│   ├── verify.html
│   └── reset-password.html
├── app.py
└── requirements.txt
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
SECRET_KEY=your_secret_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_email_password
RECAPTCHA_SECRET_KEY=your_recaptcha_key
```

3. **Database Setup:**
```bash
# Create PostgreSQL database
createdb user_auth

# Run the SQL commands to create tables
psql -d user_auth -f schema.sql
```

4. **Run Application:**
```bash
python app.py
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

