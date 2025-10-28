"""
Reminder Escalator - 4-hourly cron job to escalate unacknowledged reminders
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import logging

from app.database import SessionLocal
from app.models.reminder import Reminder
from app.models.user import User
from app.utils.email_client import email_client
from app.utils.reminder_utils import should_escalate_urgency

logger = logging.getLogger(__name__)


class ReminderEscalator:
    """Escalate unacknowledged reminders"""
    
    # Escalation rules: hours after sending before each escalation level
    ESCALATION_RULES = {
        1: 24,   # Level 1: After 24 hours
        2: 48,   # Level 2: After 48 hours
        3: 72,   # Level 3: After 72 hours
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.escalated_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def run(self):
        """Main escalator execution"""
        logger.info("Starting reminder escalator...")
        start_time = datetime.now()
        
        try:
            # Get all sent reminders that haven't been acknowledged
            reminders = self.db.query(Reminder).filter(
                and_(
                    Reminder.status == 'sent',
                    Reminder.acknowledged_at.is_(None),
                    Reminder.completed_at.is_(None),
                    Reminder.dismissed_at.is_(None)
                )
            ).all()
            
            logger.info(f"Found {len(reminders)} sent reminders to check for escalation")
            
            for reminder in reminders:
                try:
                    self._process_reminder(reminder)
                except Exception as e:
                    logger.error(f"Error escalating reminder {reminder.id}: {str(e)}")
                    self.error_count += 1
            
            # Commit all changes
            self.db.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Reminder escalator completed in {elapsed:.2f}s. "
                f"Escalated: {self.escalated_count}, Skipped: {self.skipped_count}, Errors: {self.error_count}"
            )
            
        except Exception as e:
            logger.error(f"Escalator failed: {str(e)}")
            self.db.rollback()
    
    def _process_reminder(self, reminder: Reminder):
        """Check and escalate single reminder if needed"""
        
        # Calculate hours since sent
        hours_since_sent = self._hours_since_sent(reminder)
        
        if hours_since_sent is None:
            self.skipped_count += 1
            return
        
        # Determine next escalation level
        next_level = reminder.escalation_level + 1
        
        # Check if we should escalate
        if next_level not in self.ESCALATION_RULES:
            # Max escalation reached
            self.skipped_count += 1
            return
        
        required_hours = self.ESCALATION_RULES[next_level]
        
        if hours_since_sent < required_hours:
            # Not yet time to escalate
            self.skipped_count += 1
            return
        
        # Check if already escalated recently (avoid duplicate escalations)
        if reminder.last_escalated_at:
            hours_since_last_escalation = (
                datetime.now() - reminder.last_escalated_at
            ).total_seconds() / 3600
            
            if hours_since_last_escalation < 4:  # Don't escalate more than once per 4 hours
                self.skipped_count += 1
                return
        
        # Perform escalation
        self._escalate_reminder(reminder, next_level)
    
    def _hours_since_sent(self, reminder: Reminder) -> float:
        """Calculate hours since reminder was sent"""
        if not reminder.email_sent_at:
            return None
        
        delta = datetime.now() - reminder.email_sent_at
        return delta.total_seconds() / 3600
    
    def _escalate_reminder(self, reminder: Reminder, new_level: int):
        """Escalate reminder to next level"""
        
        # Get user
        user = self.db.query(User).filter(User.id == reminder.user_id).first()
        if not user:
            logger.error(f"User {reminder.user_id} not found for reminder {reminder.id}")
            return
        
        # Upgrade urgency level
        old_urgency = reminder.urgency_level
        new_urgency = should_escalate_urgency(old_urgency)
        
        # Update reminder
        reminder.urgency_level = new_urgency
        reminder.escalation_level = new_level
        reminder.last_escalated_at = datetime.now()
        
        logger.info(
            f"Escalating reminder {reminder.id} to level {new_level} "
            f"(urgency: {old_urgency} → {new_urgency})"
        )
        
        # Send escalation email
        self._send_escalation_email(user, reminder, new_level)
        
        self.escalated_count += 1
    
    def _send_escalation_email(self, user: User, reminder: Reminder, escalation_level: int):
        """Send escalation email"""
        try:
            success = email_client.send_escalation_email(
                to_email=user.email,
                to_name=user.display_name or user.email,
                title=reminder.title,
                message=reminder.message,
                reminder_id=str(reminder.id),
                escalation_level=escalation_level
            )
            
            if success:
                logger.info(f"Sent escalation email for reminder {reminder.id}")
            else:
                logger.error(f"Failed to send escalation email for reminder {reminder.id}")
                
        except Exception as e:
            logger.error(f"Error sending escalation email: {str(e)}")


def run_escalator():
    """Entry point for escalator (called by cron)"""
    db = SessionLocal()
    try:
        escalator = ReminderEscalator(db)
        escalator.run()
    finally:
        db.close()


if __name__ == "__main__":
    # For manual testing
    logging.basicConfig(level=logging.INFO)
    run_escalator()