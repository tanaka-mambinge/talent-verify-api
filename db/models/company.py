from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

import pydantic
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, validate
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from utils.uuid_generator import uuid_generator

if TYPE_CHECKING:
    from db.models.department import Department
    from db.models.employee import Employee


class Company(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=uuid_generator, primary_key=True)
    name: str
    registration_number: str
    registration_date: date
    address: str
    contact_person: str
    contact_phone: str
    email: str

    departments: list["Department"] = Relationship()

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )


class CompanyDTO(BaseModel):
    id: Optional[str] = pydantic.Field(default=None)
    name: str
    registration_date: date
    registration_number: str
    address: str
    contact_person: str
    contact_phone: str
    email: str


class CompanyValidator(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Company name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Company name is required"},
    )
    registration_date = fields.Date(
        required=True,
        error_messages={"required": "Registration date is required"},
    )
    registration_number = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Registration number must be between 1 and 255 characters",
        ),
        error_messages={"required": "Registration number is required"},
    )
    address = fields.Str(
        required=True,
        validate=validate.Length(
            min=1, max=255, error="Address must be between 1 and 255 characters"
        ),
        error_messages={"required": "Address is required"},
    )
    contact_person = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Contact person must be between 1 and 255 characters",
        ),
        error_messages={"required": "Contact person is required"},
    )
    contact_phone = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Contact phone must be between 1 and 255 characters",
        ),
        error_messages={"required": "Contact phone is required"},
    )
    email = fields.Email(
        required=True,
        validate=validate.Email(error="Invalid email address"),
        error_messages={"required": "Email is required"},
    )
