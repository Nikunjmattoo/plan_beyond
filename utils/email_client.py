"""
Email Client - Send reminder emails via SMTP
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailClient:
    """Email sender for reminder notifications"""
    
    def __init__(self):
        # Load from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_user)
        self.from_name = os.getenv('FROM_NAME', 'The Plan Beyond')
        
        # Base URL for your application
        self.app_base_url = os.getenv('APP_BASE_URL', 'https://theplanbeyond.com')
    
    def send_reminder_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        title: str,
        message: str,
        reminder_id: str,
        urgency_level: str = 'normal',
        trigger_date: Optional[str] = None
    ) -> bool:
        """
        Send reminder email to user.
        
        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            title: Reminder title
            message: Reminder message
            reminder_id: Reminder UUID
            urgency_level: Urgency level (info, normal, important, critical)
            trigger_date: Formatted trigger date string
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Generate HTML email body
            html_body = self._generate_html_email(
                to_name=to_name,
                title=title,
                message=message,
                reminder_id=reminder_id,
                urgency_level=urgency_level,
                trigger_date=trigger_date
            )
            
            # Generate plain text email body (fallback)
            text_body = self._generate_text_email(
                to_name=to_name,
                title=title,
                message=message,
                reminder_id=reminder_id
            )
            
            # Attach both parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Reminder email sent to {to_email} (Reminder ID: {reminder_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _generate_html_email(
        self,
        to_name: str,
        title: str,
        message: str,
        reminder_id: str,
        urgency_level: str,
        trigger_date: Optional[str]
    ) -> str:
        """Generate HTML email body"""
        
        # Urgency color mapping
        urgency_colors = {
            'critical': '#dc3545',  # Red
            'important': '#fd7e14',  # Orange
            'normal': '#0d6efd',    # Blue
            'info': '#6c757d'       # Gray
        }
        
        urgency_color = urgency_colors.get(urgency_level, '#0d6efd')
        
        # Action URLs (magic links)
        view_url = f"{self.app_base_url}/reminders/{reminder_id}"
        complete_url = f"{self.app_base_url}/api/reminders/{reminder_id}/complete"
        snooze_url = f"{self.app_base_url}/api/reminders/{reminder_id}/snooze"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td style="padding: 20px 0;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" align="center" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: {urgency_color}; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: bold;">
                                {title}
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px; line-height: 1.5;">
                                Hi {to_name},
                            </p>
                            
                            <p style="margin: 0 0 20px 0; color: #333333; font-size: 16px; line-height: 1.5;">
                                {message}
                            </p>
                            
                            {f'<p style="margin: 0 0 30px 0; color: #666666; font-size: 14px;">Trigger Date: <strong>{trigger_date}</strong></p>' if trigger_date else ''}
                            
                            <!-- Action Buttons -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                <tr>
                                    <td align="center" style="padding-bottom: 10px;">
                                        <a href="{view_url}" style="display: inline-block; padding: 12px 30px; background-color: {urgency_color}; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold;">
                                            View Details
                                        </a>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center">
                                        <a href="{snooze_url}" style="display: inline-block; padding: 10px 20px; color: {urgency_color}; text-decoration: none; border: 2px solid {urgency_color}; border-radius: 5px; margin-right: 10px;">
                                            Snooze
                                        </a>
                                        <a href="{complete_url}" style="display: inline-block; padding: 10px 20px; color: #28a745; text-decoration: none; border: 2px solid #28a745; border-radius: 5px;">
                                            Mark as Done
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #f8f9fa; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                This is an automated reminder from The Plan Beyond<br>
                                <a href="{self.app_base_url}/reminders/preferences" style="color: #0d6efd; text-decoration: none;">Manage your reminder preferences</a>
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        return html
    
    def _generate_text_email(
        self,
        to_name: str,
        title: str,
        message: str,
        reminder_id: str
    ) -> str:
        """Generate plain text email body (fallback)"""
        
        view_url = f"{self.app_base_url}/reminders/{reminder_id}"
        
        text = f"""
{title}

Hi {to_name},

{message}

View Details: {view_url}

---
This is an automated reminder from The Plan Beyond
Manage your preferences: {self.app_base_url}/reminders/preferences
"""
        return text
    
    def send_escalation_email(
        self,
        to_email: str,
        to_name: str,
        title: str,
        message: str,
        reminder_id: str,
        escalation_level: int
    ) -> bool:
        """
        Send escalated reminder email.
        """
        subject = f"🔴 ESCALATED REMINDER - {title}"
        
        escalation_message = f"""
⚠️ This is escalation level {escalation_level}.

{message}

Please take action on this reminder as soon as possible.
"""
        
        return self.send_reminder_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            title=title,
            message=escalation_message,
            reminder_id=reminder_id,
            urgency_level='critical'
        )
    
    def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
            logger.info("SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {str(e)}")
            return False


# Singleton instance
email_client = EmailClient()