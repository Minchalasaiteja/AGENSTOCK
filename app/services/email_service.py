import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

async def send_verification_email(email: str, verification_code: str):
    """Send email verification code to user"""
    
    subject = "AGENSTOCK - Email Verification"
    
    body = f"""
    <html>
    <body>
        <h2>Email Verification</h2>
        <p>Thank you for registering with AGENSTOCK!</p>
        <p>Your verification code is: <strong>{verification_code}</strong></p>
        <p>Enter this code in the application to verify your email address.</p>
        <p>This code will expire in 24 hours.</p>
        <br>
        <p>Best regards,<br>AGENSTOCK Team</p>
    </body>
    </html>
    """
    
    return await send_email(email, subject, body)

async def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP"""
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.email_username
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add body to email
        msg.attach(MIMEText(body, 'html'))

        # Create server connection
        server = smtplib.SMTP(settings.smtp_server, settings.smtp_port)
        server.starttls()
        server.login(settings.email_username, settings.email_password)

        # Send email
        text = msg.as_string()
        server.sendmail(settings.email_username, to_email, text)
        server.quit()

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Bubble up the exception so callers can handle or log accordingly
        raise