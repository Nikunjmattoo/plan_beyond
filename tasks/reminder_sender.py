"""
Reminder Sender - Hourly cron job to send reminder emails
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, time as dt_time
import logging

from app.database import SessionLocal
from app.models.reminder import Reminder
from app.models.reminder_preference import ReminderPreference
from app.models.user import User
from app.utils.email_client import email_client
from app.utils.reminder_utils import (
    is_in_quiet_hours,
    convert_to_user_timezone,
    generate_email_subject
)

logger = logging.getLogger(__name__)


class ReminderSender:
    """Send reminder emails to users"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sent_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def run(self):
        """Main sender execution"""
        logger.info("Starting reminder sender...")
        start_time = datetime.now()
        
        try:
            # Get all pending reminders due today or earlier
            reminders = self.db.query(Reminder).filter(
                and_(
                    Reminder.status == 'pending',
                    Reminder.reminder_date <= date.today()
                )
            ).all()
            
            logger.info(f"Found {len(reminders)} pending reminders to process")
            
            for reminder in reminders:
                try:
                    self._process_reminder(reminder)
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder.id}: {str(e)}")
                    self.error_count += 1
            
            # Commit all changes
            self.db.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Reminder sender completed in {elapsed:.2f}s. "
                f"Sent: {self.sent_count}, Skipped: {self.skipped_count}, Errors: {self.error_count}"
            )
            
        except Exception as e:
            logger.error(f"Sender failed: {str(e)}")
            self.db.rollback()
    
    def _process_reminder(self, reminder: Reminder):
        """Process and send single reminder"""
        
        # Get user
        user = self.db.query(User).filter(User.id == reminder.user_id).first()
        if not user:
            logger.error(f"User {reminder.user_id} not found for reminder {reminder.id}")
            return
        
        # Get user preferences
        preferences = self.db.query(ReminderPreference).filter(
            ReminderPreference.user_id == reminder.user_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = ReminderPreference(user_id=reminder.user_id)
            self.db.add(preferences)
            self.db.flush()
        
        # Check if email is enabled for this category
        if not self._is_email_enabled(reminder.reminder_category, preferences):
            logger.debug(f"Email disabled for category {reminder.reminder_category}")
            self.skipped_count += 1
            return
        
        # Check quiet hours
        if self._is_in_quiet_hours(preferences):
            logger.debug(f"In quiet hours for user {user.id}, skipping")
            self.skipped_count += 1
            return
        
        # Send email
        if self._send_email(user, reminder, preferences):
            # Update reminder status
            reminder.status = 'sent'
            reminder.email_sent = True
            reminder.email_sent_at = datetime.now()
            self.sent_count += 1
            logger.info(f"Sent reminder {reminder.id} to {user.email}")
        else:
            self.error_count += 1
    
    def _is_email_enabled(self, category: str, preferences: ReminderPreference) -> bool:
        """Check if email is enabled for this reminder category"""
        category_email_map = {
            'expiry': preferences.expiry_email,
            'recurring_payment': preferences.recurring_payment_email,
            'maturity': preferences.maturity_email,
            'renewal': preferences.renewal_email,
            'health': preferences.health_email,
            'custom': preferences.custom_email
        }
        
        return category_email_map.get(category, True)
    
    def _is_in_quiet_hours(self, preferences: ReminderPreference) -> bool:
        """Check if current time is in user's quiet hours"""
        try:
            # Get current time in user's timezone
            now = datetime.now()
            user_now = convert_to_user_timezone(now, preferences.timezone)
            current_time = user_now.time()
            
            return is_in_quiet_hours(
                current_time,
                preferences.quiet_hours_start,
                preferences.quiet_hours_end
            )
        except:
            return False
    
    def _send_email(
        self,
        user: User,
        reminder: Reminder,
        preferences: ReminderPreference
    ) -> bool:
        """Send reminder email"""
        try:
            # Generate subject
            subject = generate_email_subject(
                reminder.urgency_level,
                reminder.reminder_category
            )
            
            # Format trigger date
            trigger_date_str = reminder.trigger_date.strftime('%B %d, %Y')
            
            # Send email
            success = email_client.send_reminder_email(
                to_email=user.email,
                to_name=user.display_name or user.email,
                subject=subject,
                title=reminder.title,
                message=reminder.message,
                reminder_id=str(reminder.id),
                urgency_level=reminder.urgency_level,
                trigger_date=trigger_date_str
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


def run_sender():
    """Entry point for sender (called by cron)"""
    db = SessionLocal()
    try:
        sender = ReminderSender(db)
        sender.run()
    finally:
        db.close()


if __name__ == "__main__":
    # For manual testing
    logging.basicConfig(level=logging.INFO)
    run_sender()