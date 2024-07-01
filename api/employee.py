from datetime import date
from typing import Optional

import pydantic
from fastapi import APIRouter, HTTPException, Request, status
from marshmallow import EXCLUDE, Schema, fields, validate
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlmodel import Session, select

from db import db_url
from db.models.company import Company, CompanyDTO, CompanyValidator
from db.models.department import Department, DepartmentDTO, DepartmentValidator
from db.models.employee import (
    Employee,
    EmployeeDTO,
    EmployeeValidator,
    NewEmployeeDTO,
    NewEmployeeValidator,
)
from db.models.role import Role

router = APIRouter(
    prefix="/employee",
    tags=["employee"],
)


def query_company_by_id(id: str) -> bool:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Company).where(Company.id == id)
        company = session.exec(statememt).one_or_none()
        return company


def query_department_by_name(company_id, name: str) -> bool:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Department).where(
            Department.name == name, Department.company_id == company_id
        )
        department = session.exec(statememt).one_or_none()
        return department


def query_employee_by_id(id: str) -> bool:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Employee).where(Employee.id == id)
        employee = session.exec(statememt).one_or_none()
        return employee


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_employee(employee_dto: NewEmployeeDTO):
    # validate department details
    errors = NewEmployeeValidator().validate(
        {
            **employee_dto.model_dump(),
            "start_date": employee_dto.start_date.isoformat(),
            "end_date": (
                employee_dto.end_date.isoformat() if employee_dto.end_date else None
            ),
        }
    )

    # check if company exists
    company = query_company_by_id(employee_dto.company_id)
    if company is None:
        errors["company_id"] = ["Company does not exist"]

    # check if department exists for the particular company
    department = query_department_by_name(
        employee_dto.company_id, employee_dto.department_name
    )
    if department is None:
        errors["department_name"] = ["Department does not exist for the company"]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)
    employee = Employee(**employee_dto.model_dump(), name=employee_dto.employee_name)
    role = Role(
        **employee_dto.model_dump(),
        name=employee_dto.role_name,
        employee_id=employee.id,
        department_id=department.id,
    )

    with Session(engine) as session:
        session.add(employee)
        session.add(role)
        session.commit()
        session.refresh(employee)
        session.refresh(role)

    return employee.model_dump()


@router.put("/{employee_id}", status_code=status.HTTP_200_OK)
async def update_employee(employee_id: str, employee_dto: EmployeeDTO):
    # validate employee details
    errors = EmployeeValidator().validate(employee_dto.model_dump())

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Employee).where(Employee.id == employee_id)
        employee = session.exec(statement).one_or_none()

        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee.name = employee_dto.employee_name
        session.add(employee)
        session.commit()
        session.refresh(employee)

    return employee.model_dump()


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Employee).where(Employee.id == employee_id)
        employee = session.exec(statement).one_or_none()

        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        for role in employee.roles:
            session.delete(role)
        session.delete(employee)
        session.commit()

    return


@router.get("/{employee_id}", status_code=status.HTTP_200_OK)
async def get_employee_by_id(employee_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Employee).where(Employee.id == employee_id)
        employee = session.exec(statement).one_or_none()

        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        employee_roles = [
            {
                **role.model_dump(),
                "department": role.department,
                "company": role.company,
            }
            for role in employee.roles
        ]
        employee_roles.sort(key=lambda x: x["start_date"], reverse=True)

        return {
            **employee.model_dump(),
            "roles": employee_roles,
        }


@router.get("", status_code=status.HTTP_200_OK)
async def search_employee(request: Request):
    query_params = request.query_params
    employee_name = query_params.get("employee_name", "")
    department_name = query_params.get("department_name", "")
    role_name = query_params.get("role_name", "")
    start_year = query_params.get("start_year", "")
    end_year = query_params.get("end_year", "")

    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Employee)
        employees = session.exec(statement).all()

        if len(employee_name) > 0:
            employees = [
                employee for employee in employees if employee.name == employee_name
            ]

        if len(department_name) > 0:
            employees = [
                employee
                for employee in employees
                for role in employee.roles
                if role.department.name == department_name
            ]

        if len(role_name) > 0:
            employees = [
                employee
                for employee in employees
                for role in employee.roles
                if role.name == role_name
            ]

        if len(start_year) > 0:
            employees = [
                employee
                for employee in employees
                for role in employee.roles
                if role.start_date.year == int(start_year)
            ]

        if len(end_year) > 0:
            employees = [
                employee
                for employee in employees
                for role in employee.roles
                if role.end_date and role.end_date.year == int(end_year)
            ]

        return [employee.model_dump() for employee in employees]
