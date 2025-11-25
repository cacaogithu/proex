import logging
import os
from typing import List
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)

def send_results_email(submission_id: str, recipient_email: str, docx_files: List[str]) -> dict:
    """
    Send results email with DOCX files via Gmail API.
    
    Args:
        submission_id: Submission ID
        recipient_email: Recipient email address
        docx_files: List of absolute paths to DOCX files
    
    Returns:
        dict: Response status
    """
    try:
        logger.info(f"📧 Sending results email via Gmail for submission {submission_id} to {recipient_email}")
        logger.info(f"📦 Files to send: {len(docx_files)}")
        
        # Get Gmail API credentials from environment
        gmail_credentials = os.getenv('GMAIL_CREDENTIALS_JSON')
        sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        
        if not gmail_credentials or not sender_email:
            logger.warning("Gmail credentials not configured - using fallback email service")
            return {
                "success": False,
                "error": "Gmail integration not configured. Using local email service fallback."
            }
        
        # Parse credentials
        import json
        creds_dict = json.loads(gmail_credentials)
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        # Create email message
        message = MIMEMultipart()
        message['to'] = recipient_email
        message['from'] = sender_email
        message['subject'] = f"EB-2 NIW Recommendation Letters - Submission {submission_id}"
        
        # Email body
        body = f"""
Hello,

Your EB-2 NIW recommendation letters have been generated successfully.

Submission ID: {submission_id}
Generated Letters: {len(docx_files)}

Please find the attached recommendation letters in DOCX format. You can open and edit them as needed.

Best regards,
PROEX System
"""
        
        message.attach(MIMEText(body, 'plain'))
        
        # Attach DOCX files
        for file_path in docx_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(file_path)}')
                        message.attach(part)
                        logger.info(f"   ✓ Attached: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not attach {file_path}: {e}")
        
        # Encode and send via Gmail API
        import base64
        from googleapiclient.discovery import build
        
        service = build('gmail', 'v1', credentials=credentials)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = {'raw': raw_message}
        
        result = service.users().messages().send(userId='me', body=send_message).execute()
        
        logger.info(f"✅ Email sent successfully via Gmail. Message ID: {result.get('id')}")
        return {
            "success": True,
            "files_uploaded": len(docx_files),
            "email_sent": True,
            "message_id": result.get('id')
        }
    
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_email_service_health() -> bool:
    """Check if Gmail integration is available"""
    try:
        gmail_credentials = os.getenv('GMAIL_CREDENTIALS_JSON')
        sender_email = os.getenv('GMAIL_SENDER_EMAIL')
        return gmail_credentials is not None and sender_email is not None
    except Exception:
        return False
