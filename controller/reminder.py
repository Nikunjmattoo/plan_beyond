"""
Reminder Controller - Business logic for reminder operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from datetime import datetime, timedelta, date
from uuid import UUID
import logging

from app.models.reminder import Reminder
from app.models.reminder_preference import ReminderPreference
from app.schemas.reminder_schemas import (
    ReminderCreateRequest,
    ReminderFilterRequest,
    ReminderPreferenceUpdateRequest
)
from app.schemas.reminder_errors import (
    ReminderNotFoundException,
    ReminderAccessDeniedException,
    ReminderAlreadyExistsException,
    ReminderDatabaseException,
    PreferenceNotFoundException,
    ReminderValidationException
)

logger = logging.getLogger(__name__)


class ReminderController:
    """Business logic for reminders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==========================================
    # CREATE OPERATIONS
    # ==========================================
    
    def create_reminder(
        self,
        user_id: str,
        reminder_data: ReminderCreateRequest
    ) -> Reminder:
        """Create a new reminder"""
        reminder = Reminder(
            user_id=int(user_id),  # Convert to int for DB
            vault_file_id=reminder_data.vault_file_id,
            field_name=reminder_data.field_name,
            reminder_category=reminder_data.reminder_category,
            trigger_date=reminder_data.trigger_date,
            reminder_date=reminder_data.reminder_date,
            title=reminder_data.title,
            message=reminder_data.message,
            urgency_level=reminder_data.urgency_level,
            status='pending'
        )
        
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    # ==========================================
    # READ OPERATIONS
    # ==========================================
    
    def get_reminder_by_id(self, reminder_id: UUID, user_id: str) -> Optional[Reminder]:
        """Get single reminder by ID (user must own it)"""
        return self.db.query(Reminder).filter(
            and_(
                Reminder.id == reminder_id,
                Reminder.user_id == int(user_id)  # Convert to int for DB
            )
        ).first()
    
    def list_reminders(
        self,
        user_id: str,
        filters: Optional[ReminderFilterRequest] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Reminder]:
        """List reminders with filters"""
        query = self.db.query(Reminder).filter(Reminder.user_id == int(user_id))  # Convert to int
        
        if filters:
            if filters.status:
                query = query.filter(Reminder.status == filters.status)
            
            if filters.category:
                query = query.filter(Reminder.reminder_category == filters.category)
            
            if filters.urgency_level:
                query = query.filter(Reminder.urgency_level == filters.urgency_level)
            
            if filters.from_date:
                query = query.filter(Reminder.reminder_date >= filters.from_date)
            
            if filters.to_date:
                query = query.filter(Reminder.reminder_date <= filters.to_date)
            
            if filters.vault_file_id:
                query = query.filter(Reminder.vault_file_id == filters.vault_file_id)
        
        # Order by reminder date (ascending) and urgency
        query = query.order_by(
            Reminder.reminder_date.asc(),
            Reminder.urgency_level.desc()
        )
        
        return query.limit(limit).offset(offset).all()
    
    def get_pending_count(self, user_id: str) -> dict:
        """Get count of pending and critical reminders"""
        pending_count = self.db.query(Reminder).filter(
            and_(
                Reminder.user_id == int(user_id),  # Convert to int
                Reminder.status.in_(['pending', 'sent'])
            )
        ).count()
        
        critical_count = self.db.query(Reminder).filter(
            and_(
                Reminder.user_id == int(user_id),  # Convert to int
                Reminder.status.in_(['pending', 'sent']),
                Reminder.urgency_level == 'critical'
            )
        ).count()
        
        return {
            'pending_count': pending_count,
            'critical_count': critical_count
        }
    
    def get_stats(self, user_id: str) -> dict:
        """Get reminder statistics for user"""
        all_reminders = self.db.query(Reminder).filter(Reminder.user_id == int(user_id)).all()  # Convert to int
        
        stats = {
            'total_reminders': len(all_reminders),
            'pending': 0,
            'sent': 0,
            'acknowledged': 0,
            'completed': 0,
            'dismissed': 0,
            'snoozed': 0,
            'by_category': {},
            'by_urgency': {},
            'upcoming_7_days': 0,
            'upcoming_30_days': 0
        }
        
        today = date.today()
        week_later = today + timedelta(days=7)
        month_later = today + timedelta(days=30)
        
        for reminder in all_reminders:
            # Count by status
            stats[reminder.status] = stats.get(reminder.status, 0) + 1
            
            # Count by category
            stats['by_category'][reminder.reminder_category] = \
                stats['by_category'].get(reminder.reminder_category, 0) + 1
            
            # Count by urgency
            stats['by_urgency'][reminder.urgency_level] = \
                stats['by_urgency'].get(reminder.urgency_level, 0) + 1
            
            # Count upcoming
            if reminder.reminder_date <= week_later and reminder.status in ['pending', 'sent']:
                stats['upcoming_7_days'] += 1
            
            if reminder.reminder_date <= month_later and reminder.status in ['pending', 'sent']:
                stats['upcoming_30_days'] += 1
        
        return stats
    
    # ==========================================
    # UPDATE OPERATIONS (USER ACTIONS)
    # ==========================================
    
    def acknowledge_reminder(
        self,
        reminder_id: UUID,
        user_id: str,
        acknowledged_by: str = "user"
    ) -> Optional[Reminder]:
        """Mark reminder as acknowledged"""
        reminder = self.get_reminder_by_id(reminder_id, user_id)
        
        if not reminder:
            return None
        
        reminder.status = 'acknowledged'
        reminder.acknowledged_at = datetime.now()
        reminder.acknowledged_by = acknowledged_by
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def snooze_reminder(
        self,
        reminder_id: UUID,
        user_id: str,
        snooze_hours: int
    ) -> Optional[Reminder]:
        """Snooze reminder for specified hours"""
        reminder = self.get_reminder_by_id(reminder_id, user_id)
        
        if not reminder:
            return None
        
        now = datetime.now()
        reminder.status = 'snoozed'
        reminder.snoozed_at = now
        reminder.snoozed_until = now + timedelta(hours=snooze_hours)
        reminder.snooze_count += 1
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def complete_reminder(
        self,
        reminder_id: UUID,
        user_id: str,
        completion_action: str
    ) -> Optional[Reminder]:
        """Mark reminder as completed"""
        reminder = self.get_reminder_by_id(reminder_id, user_id)
        
        if not reminder:
            return None
        
        reminder.status = 'completed'
        reminder.completed_at = datetime.now()
        reminder.completion_action = completion_action
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    def dismiss_reminder(
        self,
        reminder_id: UUID,
        user_id: str
    ) -> Optional[Reminder]:
        """Dismiss reminder"""
        reminder = self.get_reminder_by_id(reminder_id, user_id)
        
        if not reminder:
            return None
        
        reminder.status = 'dismissed'
        reminder.dismissed_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(reminder)
        
        return reminder
    
    # ==========================================
    # DELETE OPERATIONS
    # ==========================================
    
    def delete_reminder(self, reminder_id: UUID, user_id: str) -> bool:
        """Delete reminder"""
        reminder = self.get_reminder_by_id(reminder_id, user_id)
        
        if not reminder:
            return False
        
        self.db.delete(reminder)
        self.db.commit()
        
        return True
    
    # ==========================================
    # PREFERENCE OPERATIONS
    # ==========================================
    
    def get_user_preferences(self, user_id: str) -> Optional[ReminderPreference]:
        """Get user's reminder preferences"""
        pref = self.db.query(ReminderPreference).filter(
            ReminderPreference.user_id == int(user_id)  # Convert to int
        ).first()
        
        # Create default preferences if not exist
        if not pref:
            pref = self.create_default_preferences(user_id)
        
        return pref
    
    def create_default_preferences(self, user_id: str) -> ReminderPreference:
        """Create default reminder preferences for user"""
        pref = ReminderPreference(user_id=int(user_id))  # Convert to int
        
        self.db.add(pref)
        self.db.commit()
        self.db.refresh(pref)
        
        return pref
    
    def update_preferences(
        self,
        user_id: str,
        updates: ReminderPreferenceUpdateRequest
    ) -> ReminderPreference:
        """Update user's reminder preferences"""
        pref = self.get_user_preferences(user_id)
        
        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(pref, field):
                setattr(pref, field, value)
        
        self.db.commit()
        self.db.refresh(pref)
        
        return pref
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    def check_duplicate_reminder(
        self,
        user_id: str,
        vault_file_id: str,
        field_name: str,
        reminder_date: date
    ) -> bool:
        """Check if reminder already exists"""
        existing = self.db.query(Reminder).filter(
            and_(
                Reminder.user_id == int(user_id),  # Convert to int
                Reminder.vault_file_id == vault_file_id,
                Reminder.field_name == field_name,
                Reminder.reminder_date == reminder_date,
                Reminder.status != 'completed'
            )
        ).first()
        
        return existing is not None
    
    def get_snoozed_reminders_to_reactivate(self) -> List[Reminder]:
        """Get snoozed reminders that should be reactivated"""
        now = datetime.now()
        
        return self.db.query(Reminder).filter(
            and_(
                Reminder.status == 'snoozed',
                Reminder.snoozed_until <= now
            )
        ).all()
    
    def reactivate_snoozed_reminder(self, reminder: Reminder):
        """Reactivate a snoozed reminder"""
        reminder.status = 'pending'
        reminder.snoozed_until = None
        
        self.db.commit()