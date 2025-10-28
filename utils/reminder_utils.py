"""
Reminder Utility Functions - Helper functions for reminder operations
"""
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import pytz


# ==========================================
# REMINDER RULES BY CATEGORY
# ==========================================

REMINDER_RULES = {
    'expiry': [
        {'days_before': 90, 'urgency': 'info'},
        {'days_before': 30, 'urgency': 'normal'},
        {'days_before': 7, 'urgency': 'important'},
        {'days_before': 1, 'urgency': 'critical'},
    ],
    'recurring_payment': [
        {'days_before': 7, 'urgency': 'normal'},
        {'days_before': 3, 'urgency': 'important'},
        {'days_before': 1, 'urgency': 'critical'},
    ],
    'maturity': [
        {'days_before': 30, 'urgency': 'info'},
        {'days_before': 7, 'urgency': 'normal'},
        {'days_before': 1, 'urgency': 'important'},
    ],
    'renewal': [
        {'days_before': 60, 'urgency': 'info'},
        {'days_before': 30, 'urgency': 'normal'},
        {'days_before': 7, 'urgency': 'important'},
    ],
    'health': [
        {'days_before': 7, 'urgency': 'normal'},
        {'days_before': 1, 'urgency': 'important'},
    ],
    'custom': [
        {'days_before': 7, 'urgency': 'normal'},
    ]
}


# ==========================================
# DATE FIELD MAPPING
# ==========================================

DATE_FIELD_CATEGORY_MAP = {
    # Expiry fields
    'expiry_date': 'expiry',
    'expiration_date': 'expiry',
    'valid_until': 'expiry',
    'passport_expiry': 'expiry',
    'license_expiry': 'expiry',
    'visa_expiry': 'expiry',
    
    # Payment fields
    'payment_date': 'recurring_payment',
    'due_date': 'recurring_payment',
    'payment_due': 'recurring_payment',
    'next_payment': 'recurring_payment',
    'emi_date': 'recurring_payment',
    
    # Maturity fields
    'maturity_date': 'maturity',
    'fd_maturity': 'maturity',
    'bond_maturity': 'maturity',
    
    # Renewal fields
    'renewal_date': 'renewal',
    'policy_renewal': 'renewal',
    'subscription_renewal': 'renewal',
    'insurance_renewal': 'renewal',
    
    # Health fields
    'next_checkup': 'health',
    'next_dose_date': 'health',
    'vaccination_date': 'health',
    'appointment_date': 'health',
}


# ==========================================
# CALCULATE REMINDER DATES
# ==========================================

def calculate_reminder_dates(
    trigger_date: date,
    category: str
) -> List[Dict]:
    """
    Calculate all reminder dates for a given trigger date and category.
    
    Returns list of dicts with reminder_date, urgency_level
    """
    rules = REMINDER_RULES.get(category, REMINDER_RULES['custom'])
    reminders = []
    
    for rule in rules:
        reminder_date = trigger_date - timedelta(days=rule['days_before'])
        
        # Only create reminders for future dates
        if reminder_date >= date.today():
            reminders.append({
                'reminder_date': reminder_date,
                'urgency_level': rule['urgency'],
                'days_before': rule['days_before']
            })
    
    return reminders


def get_category_from_field_name(field_name: str) -> str:
    """
    Map field name to reminder category.
    
    Example: 'passport_expiry' -> 'expiry'
    """
    field_lower = field_name.lower()
    
    # Direct mapping
    if field_lower in DATE_FIELD_CATEGORY_MAP:
        return DATE_FIELD_CATEGORY_MAP[field_lower]
    
    # Fuzzy matching
    if 'expir' in field_lower or 'valid' in field_lower:
        return 'expiry'
    elif 'payment' in field_lower or 'due' in field_lower or 'emi' in field_lower:
        return 'recurring_payment'
    elif 'matur' in field_lower:
        return 'maturity'
    elif 'renew' in field_lower:
        return 'renewal'
    elif 'health' in field_lower or 'checkup' in field_lower or 'dose' in field_lower:
        return 'health'
    
    return 'custom'


# ==========================================
# MESSAGE GENERATION
# ==========================================

def generate_reminder_message(
    field_name: str,
    trigger_date: date,
    days_before: int,
    category: str
) -> Tuple[str, str]:
    """
    Generate reminder title and message.
    
    Returns: (title, message)
    """
    days_remaining = (trigger_date - date.today()).days
    
    # Format field name nicely
    field_display = field_name.replace('_', ' ').title()
    
    # Category-specific messages
    if category == 'expiry':
        if days_before == 1:
            title = f"{field_display} Expires Tomorrow"
            message = f"Your {field_display.lower()} expires in 1 day on {trigger_date.strftime('%B %d, %Y')}"
        else:
            title = f"{field_display} Expiring Soon"
            message = f"Your {field_display.lower()} expires in {days_remaining} days on {trigger_date.strftime('%B %d, %Y')}"
    
    elif category == 'recurring_payment':
        if days_before == 1:
            title = f"Payment Due Tomorrow"
            message = f"{field_display} payment due in 1 day on {trigger_date.strftime('%B %d, %Y')}"
        else:
            title = f"Upcoming Payment"
            message = f"{field_display} payment due in {days_remaining} days on {trigger_date.strftime('%B %d, %Y')}"
    
    elif category == 'maturity':
        title = f"{field_display} Maturing Soon"
        message = f"Your {field_display.lower()} matures in {days_remaining} days on {trigger_date.strftime('%B %d, %Y')}"
    
    elif category == 'renewal':
        title = f"{field_display} Renewal Due"
        message = f"{field_display} renewal due in {days_remaining} days on {trigger_date.strftime('%B %d, %Y')}"
    
    elif category == 'health':
        title = f"Health Appointment Reminder"
        message = f"{field_display} scheduled in {days_remaining} days on {trigger_date.strftime('%B %d, %Y')}"
    
    else:
        title = f"Reminder: {field_display}"
        message = f"{field_display} scheduled for {trigger_date.strftime('%B %d, %Y')}"
    
    return title, message


# ==========================================
# TIMEZONE HANDLING
# ==========================================

def convert_to_user_timezone(dt: datetime, timezone_str: str) -> datetime:
    """Convert datetime to user's timezone"""
    try:
        user_tz = pytz.timezone(timezone_str)
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        return dt.astimezone(user_tz)
    except:
        return dt


def is_in_quiet_hours(
    current_time: time,
    quiet_start: time,
    quiet_end: time
) -> bool:
    """
    Check if current time is within quiet hours.
    
    Handles cases where quiet hours span midnight.
    """
    if quiet_start <= quiet_end:
        # Normal case: 23:00 to 06:00 doesn't span midnight in reverse
        return quiet_start <= current_time <= quiet_end
    else:
        # Quiet hours span midnight (e.g., 23:00 to 06:00)
        return current_time >= quiet_start or current_time <= quiet_end


# ==========================================
# URGENCY HELPERS
# ==========================================

def get_urgency_from_days_remaining(days: int) -> str:
    """
    Determine urgency level from days remaining.
    """
    if days <= 1:
        return 'critical'
    elif days <= 3:
        return 'important'
    elif days <= 7:
        return 'normal'
    else:
        return 'info'


def should_escalate_urgency(current_urgency: str) -> str:
    """
    Escalate urgency level.
    
    info -> normal -> important -> critical
    """
    escalation_map = {
        'info': 'normal',
        'normal': 'important',
        'important': 'critical',
        'critical': 'critical'  # Can't escalate further
    }
    
    return escalation_map.get(current_urgency, 'normal')


# ==========================================
# DATE EXTRACTION FROM FORM DATA
# ==========================================

def extract_date_fields(form_data: Dict) -> List[Tuple[str, date]]:
    """
    Extract all date fields from decrypted form data.
    
    Returns list of (field_name, date_value) tuples.
    """
    date_fields = []
    
    for field_name, field_value in form_data.items():
        # Skip non-date fields
        if not field_value or not isinstance(field_value, str):
            continue
        
        # Try to parse as date
        try:
            # Try multiple date formats
            for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    parsed_date = datetime.strptime(field_value, date_format).date()
                    
                    # Only include future dates
                    if parsed_date >= date.today():
                        date_fields.append((field_name, parsed_date))
                    break
                except ValueError:
                    continue
        except:
            continue
    
    return date_fields


# ==========================================
# EMAIL SUBJECT GENERATION
# ==========================================

def generate_email_subject(urgency_level: str, category: str) -> str:
    """Generate email subject based on urgency and category"""
    urgency_prefix = {
        'critical': '🔴 URGENT',
        'important': '⚠️ Important',
        'normal': '📅',
        'info': 'ℹ️'
    }
    
    category_name = {
        'expiry': 'Expiry',
        'recurring_payment': 'Payment',
        'maturity': 'Maturity',
        'renewal': 'Renewal',
        'health': 'Health',
        'custom': 'Reminder'
    }
    
    prefix = urgency_prefix.get(urgency_level, '📅')
    cat_name = category_name.get(category, 'Reminder')
    
    return f"{prefix} {cat_name} Reminder"