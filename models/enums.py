from enum import Enum

class EventType(str, Enum):
    trigger = "trigger"
    time = "time"
    after_death = "after_death"
    event = "event"

class TrusteeStatus(str, Enum):
    invited = "invited"
    accepted = "accepted"
    rejected = "rejected"
    removed = "removed"
    blocked = "blocked"

class ApprovalStatus(str, Enum):
    approved = "approved"
    retracted = "retracted"

class AssignmentRole(str, Enum):
    branch = "branch"
    leaf = "leaf"

class ReleaseScope(str, Enum):
    memory_file = "memory_file"
    category_section = "category_section"
    memory_collection = "memory_collection"

class ReleaseReason(str, Enum):
    after_death = "after_death"
    time_trigger = "time_trigger"
    manual_trigger = "manual_trigger"

class FolderStatus(str, Enum):
    incomplete = "incomplete"
    complete = "complete"

# ✅ NEW: branch invite lifecycle for Memory assignments
class BranchInviteStatus(str, Enum):
    sent = "sent"
    accepted = "accepted"
    declined = "declined"
