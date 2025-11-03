"""
Pydantic schemas for loan application API requests and responses.
"""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ApplicationCreate(BaseModel):
    """Request schema for creating a new loan application."""

    pan_number: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$",
        examples=["ABCDE1234F"],
        description="PAN number in format: 5 uppercase letters, 4 digits, 1 uppercase letter",
    )
    applicant_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["John Doe"],
        description="Full name of the applicant",
    )
    monthly_income_inr: float = Field(
        ...,
        gt=0,
        examples=[50000.00],
        description="Monthly income in Indian Rupees (must be positive)",
    )
    loan_amount_inr: float = Field(
        ...,
        gt=0,
        examples=[200000.00],
        description="Requested loan amount in Indian Rupees (must be positive)",
    )
    loan_type: str = Field(
        ...,
        examples=["PERSONAL", "HOME", "AUTO"],
        description="Type of loan requested (e.g., PERSONAL, HOME, AUTO)",
    )

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        """Validate and normalize loan type to uppercase."""
        return v.upper()

    @field_validator("applicant_name")
    @classmethod
    def validate_applicant_name(cls, v: str) -> str:
        """Validate applicant name is not just whitespace."""
        if not v.strip():
            raise ValueError("Applicant name cannot be empty or just whitespace")
        return v.strip()


class ApplicationResponse(BaseModel):
    """Response schema after creating a loan application."""

    message: str = Field(..., examples=["Application created successfully"])
    application_id: UUID = Field(
        ..., description="Unique identifier for the application"
    )
    status: str = Field(
        ..., examples=["pending"], description="Current status of the application"
    )

    model_config = {"from_attributes": True}


class ApplicationStatusResponse(BaseModel):
    """Response schema for checking application status."""

    application_id: UUID = Field(
        ..., description="Unique identifier for the application"
    )
    status: str = Field(
        ..., examples=["pending", "pre_approved", "rejected", "manual_review"]
    )

    model_config = {"from_attributes": True}
