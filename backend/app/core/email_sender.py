import logging
import os
import requests
from typing import List

logger = logging.getLogger(__name__)

EMAIL_SERVICE_URL = "http://localhost:3001"

def send_results_email(submission_id: str, recipient_email: str, docx_files: List[str]) -> dict:
    """
    Send results email via Node.js email service.
    The Node.js service handles Gmail API and Google Drive integration via Replit connectors.
    
    Args:
        submission_id: Submission ID
        recipient_email: Recipient email address
        docx_files: List of absolute paths to DOCX files
    
    Returns:
        dict: Response status
    """
    try:
        logger.info(f"📧 Sending results via email service for submission {submission_id} to {recipient_email}")
        logger.info(f"📦 Files to send: {len(docx_files)}")
        
        response = requests.post(
            f"{EMAIL_SERVICE_URL}/send-results",
            json={
                "submissionId": submission_id,
                "recipientEmail": recipient_email,
                "docxFiles": docx_files
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Email service response: {result}")
            return {
                "success": True,
                "files_uploaded": result.get("filesUploaded", len(docx_files)),
                "email_sent": result.get("emailSent", True),
                "drive_files": result.get("driveFiles", [])
            }
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {"error": response.text}
            logger.error(f"❌ Email service error: {error_data}")
            return {
                "success": False,
                "error": error_data.get("error", "Unknown error from email service")
            }
    
    except requests.exceptions.ConnectionError:
        logger.error("❌ Cannot connect to email service on port 3001")
        return {
            "success": False,
            "error": "Email service not available"
        }
    except requests.exceptions.Timeout:
        logger.error("❌ Email service request timed out")
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
    """Check if Node.js email service is available and healthy"""
    try:
        response = requests.get(f"{EMAIL_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "ok"
        return False
    except Exception as e:
        logger.warning(f"Email service health check failed: {e}")
        return False
