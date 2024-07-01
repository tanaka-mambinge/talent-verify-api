from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

import pydantic
from marshmallow import EXCLUDE, Schema, ValidationError, fields, post_load, validate
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, Relationship, SQLModel

from utils.uuid_generator import uuid_generator

if TYPE_CHECKING:
    from db.models.company import Company
    from db.models.role import Role


class Employee(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=uuid_generator, primary_key=True)
    name: str

    roles: list["Role"] = Relationship()

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )


class EmployeeDTO(BaseModel):
    # employee
    id: Optional[str] = pydantic.Field(default=None)
    employee_name: str


class NewEmployeeDTO(BaseModel):
    # employee
    employee_name: str

    # first role
    company_id: str
    employee_company_id: Optional[str] = pydantic.Field(default=None)
    department_name: str
    role_name: str
    duties: str
    start_date: date
    end_date: Optional[date] = pydantic.Field(default=None)


class EmployeeValidator(Schema):
    class Meta:
        unknown = EXCLUDE

    employee_name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Employee name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Employee name is required"},
    )


class NewEmployeeValidator(Schema):
    class Meta:
        unknown = EXCLUDE

    employee_name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Employee name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Employee name is required"},
    )
    employee_company_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Employee company id must be between 1 and 255 characters",
        ),
    )
    role_name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Employee name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Employee name is required"},
    )
    duties = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=1024,
            error="Duties must be between 1 and 1024 characters",
        ),
        error_messages={"required": "Duties are required"},
    )
    start_date = fields.Date(
        required=True,
        error_messages={"required": "Start date is required"},
    )
    end_date = fields.Date(
        required=False,
        allow_none=True,
        error_messages={"required": "End date is required"},
    )
