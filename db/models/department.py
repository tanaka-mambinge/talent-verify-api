from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

import pydantic
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, validate
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from utils.uuid_generator import uuid_generator

if TYPE_CHECKING:
    from db.models import Company


class Department(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=uuid_generator, primary_key=True)
    company_id: str = Field(foreign_key="company.id")
    name: str

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )


class DepartmentDTO(BaseModel):
    id: Optional[str] = pydantic.Field(default=None)
    company_id: str
    name: str


class DepartmentValidator(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Department name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Department name is required"},
    )
