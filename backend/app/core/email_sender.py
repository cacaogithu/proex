import requests
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

# Configuration: Email service URL from environment variable
# For development: http://localhost:3001
# For production: Set EMAIL_SERVICE_URL environment variable
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://localhost:3001")

def send_results_email(submission_id: str, recipient_email: str, docx_files: List[str]) -> dict:
    """
    Send results email with Google Drive links via Node.js email service.
    
    Args:
        submission_id: Submission ID
        recipient_email: Recipient email address
        docx_files: List of absolute paths to DOCX files
    
    Returns:
        dict: Response from email service
    """
    try:
        logger.info(f"📧 Sending results email for submission {submission_id} to {recipient_email}")
        logger.info(f"📦 Files to send: {len(docx_files)}")
        
        payload = {
            "submissionId": submission_id,
            "recipientEmail": recipient_email,
            "docxFiles": docx_files
        }
        
        response = requests.post(
            f"{EMAIL_SERVICE_URL}/send-results",
            json=payload,
            timeout=300  # 5 minutes timeout for large files
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Email sent successfully: {result}")
            return {
                "success": True,
                "files_uploaded": result.get("filesUploaded", 0),
                "email_sent": result.get("emailSent", False)
            }
        else:
            logger.error(f"❌ Email service error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Email service returned {response.status_code}"
            }
    
    except requests.exceptions.Timeout:
        logger.error("❌ Email service timeout")
        return {
            "success": False,
            "error": "Email service timeout"
        }
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def check_email_service_health() -> bool:
    """Check if email service is running"""
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/health", timeout=5)
        return response.status_code == 200
    except (requests.RequestException, Exception):
        # Email service is not available
        return False
