from app.models.admin import Admin
from app.models.card import SectionItemTemplate, UserSectionItem
from app.models.category import CategoryMaster, CategorySectionMaster, UserCategory, UserCategorySection, CategoryFile, CategoryLeafAssignment
from app.models.contact import Contact
from app.models.death_approval import DeathApproval
from app.models.death import DeathAck, DeathDeclaration, DeathLock, LegendLifecycle, DeathReview, Contest, Broadcast, Config, AuditLog
from app.models.file import File
from app.models.folder import Folder, FolderBranch, FolderLeaf, FolderTrigger
# from app.models.forms import StepMaster, StepOption, UserSectionProgress, UserStepAnswer
from app.models.memory import MemoryCollection, MemoryFile, MemoryFileAssignment, MemoryCollectionAssignment
from app.models.relationship import RelationshipRequest
from app.models.release import Release, ReleaseRecipient
from app.models.reminder import Reminder
from app.models.reminder_preference import ReminderPreference
from app.models.step import FormStep, StepOption
from app.models.trustee import Trustee
from app.models.user_forms import UserSectionProgress, UserStepAnswer
from app.models.user import User, UserProfile
from app.models.vault import VaultFile, VaultFileAccess  # ← ADD THIS LINE
from app.models.verification import IdentityVerification, UserStatusHistory