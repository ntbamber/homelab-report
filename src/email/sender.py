import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")

def send_report(report_data):
    #Renders HTML template with the report data and sends it.
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO]):
        print("Email Config Missing in .env")
        return

    # 1. Render HTML
    env = Environment(loader=FileSystemLoader("src/email"))
    template = env.get_template("template.html")
    
    html_content = template.render(
        services=report_data,
        date=datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    # 2. Build Message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Homelab Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    # Attach HTML
    msg.attach(MIMEText(html_content, "html"))

    # 3. Send
    try:
        context = ssl.create_default_context()
        print(f"Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
            
        print("Email Sent Successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")