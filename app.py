import os
from flask import Flask, request, Response
from celery import Celery
from smtplib import SMTP, SMTPException
import logging
from datetime import datetime
from dotenv import load_dotenv


app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
app.config['CELERY_RESULT_BACKEND'] = 'rpc://'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Setup logging
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

@celery.task
def send_email_task(to_email):
    try:
        with SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.sendmail(EMAIL_ADDRESS, to_email, "Test email from Flask app with Celery")
            logging.info(f"Email sent to {to_email}")
    except SMTPException as e:
        logging.error(f"Failed to send email to {to_email}. Error: {str(e)}")

@app.route('/')
def index():
    sendmail = request.args.get('sendmail')
    talktome = request.args.get('talktome')

    if sendmail:
        try:
            send_email_task.delay(sendmail)
            return f"Email sending task queued for {sendmail}"
        except Exception as e:
            logging.error(f"Failed to queue email sending task for {sendmail}. Error: {str(e)}")
            return "Failed to queue email sending task.", 500

    elif talktome:
        logging.info(f"Current time logged: {datetime.now()}")
        return "Current time logged."

    return "No action specified."

@app.route('/logs')
def get_logs():
    try:
        with open('/var/log/messaging_system.log', 'r') as f:
            logs = f.read()
        return Response(logs, mimetype='text/plain')
    except Exception as e:
        return f"Failed to read log file. Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)