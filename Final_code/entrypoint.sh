#!/bin/sh
if [ "$FLASK_ENV" = "production" ]; then
    exec gunicorn -w 4 -b 0.0.0.0:5000 app:app
else
    exec python app.py
fi