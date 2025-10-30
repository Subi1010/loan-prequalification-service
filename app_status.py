from enum import Enum


class ApplicationStatus(Enum):
    PENDING = "pending"
    PRE_APPROVED = "pre_approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"
