"""
Reminder Scheduler - Daily cron job to create reminders from vault files
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime
import logging

from app.database import SessionLocal
from app.models.vault import VaultFile
from app.models.reminder import Reminder
from app.encryption_module.core.vault_decryptor import decrypt_vault_file
from app.encryption_module.core.db_operations import VaultDatabaseOperations
from app.encryption_module.exceptions import UnauthorizedAccessException  # ADD THIS LINE
from app.utils.reminder_utils import (
    extract_date_fields,
    get_category_from_field_name,
    calculate_reminder_dates,
    generate_reminder_message
)
logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Create reminders from vault files"""
    
    def __init__(self, db: Session):
        self.db = db
        self.created_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def run(self):
        """Main scheduler execution"""
        logger.info("Starting reminder scheduler...")
        start_time = datetime.now()
        
        try:
            # Get all active vault files
            vault_files = self.db.query(VaultFile).filter(
                VaultFile.status == 'active'
            ).all()
            
            logger.info(f"Processing {len(vault_files)} vault files")
            
            for vault_file in vault_files:
                try:
                    self._process_vault_file(vault_file)
                except Exception as e:
                    logger.error(f"Error processing vault file {vault_file.file_id}: {str(e)}")
                    self.error_count += 1
            
            # Commit all changes
            self.db.commit()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Reminder scheduler completed in {elapsed:.2f}s. "
                f"Created: {self.created_count}, Skipped: {self.skipped_count}, Errors: {self.error_count}"
            )
            
        except Exception as e:
            logger.error(f"Scheduler failed: {str(e)}")
            self.db.rollback()
    
    def _process_vault_file(self, vault_file: VaultFile):
        """Process single vault file and create reminders"""
        try:
            # Decrypt form data to extract date fields
            db_ops = VaultDatabaseOperations(self.db)
            
            # Skip if owner user doesn't exist (safety check)
            from app.models.user import User
            owner = self.db.query(User).filter(User.id == vault_file.owner_user_id).first()
            if not owner:
                logger.warning(f"Owner user {vault_file.owner_user_id} not found for file {vault_file.file_id}")
                return
            
            try:
                decrypted = decrypt_vault_file(
                    file_id=vault_file.file_id,
                    user_id=str(vault_file.owner_user_id),
                    db_operations=db_ops,
                    decrypt_source_file=False  # We only need form data
                )
            except UnauthorizedAccessException as e:
                # Owner should always have access - log and skip
                logger.warning(f"Access denied for owner {vault_file.owner_user_id} on file {vault_file.file_id}: {e}")
                return
            except Exception as e:
                logger.error(f"Failed to decrypt {vault_file.file_id}: {e}")
                raise
            
            # Extract all date fields
            date_fields = extract_date_fields(decrypted.form_data)
            
            if not date_fields:
                logger.debug(f"No date fields found in {vault_file.file_id}")
                return
            
            # Create reminders for each date field
            for field_name, trigger_date in date_fields:
                self._create_reminders_for_field(
                    vault_file=vault_file,
                    field_name=field_name,
                    trigger_date=trigger_date
                )
                
        except Exception as e:
            logger.error(f"Failed to process {vault_file.file_id}: {str(e)}")
            raise
    
    def _create_reminders_for_field(
        self,
        vault_file: VaultFile,
        field_name: str,
        trigger_date: date
    ):
        """Create all reminders for a specific date field"""
        
        # Determine category
        category = get_category_from_field_name(field_name)
        
        # Calculate all reminder dates
        reminder_dates = calculate_reminder_dates(trigger_date, category)
        
        for reminder_info in reminder_dates:
            reminder_date = reminder_info['reminder_date']
            urgency_level = reminder_info['urgency_level']
            days_before = reminder_info['days_before']
            
            # Check if reminder already exists
            if self._reminder_exists(
                vault_file.owner_user_id,
                vault_file.file_id,
                field_name,
                reminder_date
            ):
                self.skipped_count += 1
                continue
            
            # Generate message
            title, message = generate_reminder_message(
                field_name=field_name,
                trigger_date=trigger_date,
                days_before=days_before,
                category=category
            )
            
            # Create reminder
            reminder = Reminder(
                user_id=vault_file.owner_user_id,
                vault_file_id=vault_file.file_id,
                field_name=field_name,
                reminder_category=category,
                trigger_date=trigger_date,
                reminder_date=reminder_date,
                title=title,
                message=message,
                urgency_level=urgency_level,
                status='pending'
            )
            
            self.db.add(reminder)
            self.created_count += 1
            
            logger.debug(
                f"Created reminder: {title} for user {vault_file.owner_user_id} "
                f"(due {reminder_date}, urgency: {urgency_level})"
            )
    
    def _reminder_exists(
        self,
        user_id: int,
        vault_file_id: str,
        field_name: str,
        reminder_date: date
    ) -> bool:
        """Check if reminder already exists"""
        existing = self.db.query(Reminder).filter(
            and_(
                Reminder.user_id == user_id,
                Reminder.vault_file_id == vault_file_id,
                Reminder.field_name == field_name,
                Reminder.reminder_date == reminder_date,
                Reminder.status.in_(['pending', 'sent', 'snoozed'])
            )
        ).first()
        
        return existing is not None


def run_scheduler():
    """Entry point for scheduler (called by cron)"""
    db = SessionLocal()
    try:
        scheduler = ReminderScheduler(db)
        scheduler.run()
    finally:
        db.close()


if __name__ == "__main__":
    # For manual testing
    logging.basicConfig(level=logging.INFO)
    run_scheduler()