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
    from db.models.department import Department
    from db.models.employee import Employee


class Role(SQLModel, table=True):
    id: Optional[str] = Field(default_factory=uuid_generator, primary_key=True)
    employee_id: str = Field(foreign_key="employee.id")
    company_id: str = Field(foreign_key="company.id")
    department_id: str = Field(foreign_key="department.id")
    name: str
    duties: str
    employee_company_id: Optional[str]
    start_date: date
    end_date: Optional[date]

    employee: "Employee" = Relationship()
    company: "Company" = Relationship()
    department: "Department" = Relationship()

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), default=func.now())
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), default=func.now()
        )
    )


class RoleDTO(BaseModel):
    id: Optional[str] = pydantic.Field(default=None)
    employee_id: Optional[str] = pydantic.Field(default=None)
    company_name: str
    department_name: str
    name: str
    duties: str
    employee_company_id: Optional[str] = pydantic.Field(default=None)
    start_date: date
    end_date: Optional[date] = pydantic.Field(default=None)


class RoleValidator(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Role name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Role name is required"},
    )

    company_name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Company name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Company name is required"},
    )

    department_name = fields.Str(
        required=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Department name must be between 1 and 255 characters",
        ),
        error_messages={"required": "Department name is required"},
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
    employee_company_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(
            min=1,
            max=255,
            error="Employee company id must be between 1 and 255 characters",
        ),
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
