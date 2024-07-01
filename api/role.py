from calendar import c

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import create_engine
from sqlmodel import Session, select

from db import db_url
from db.models.company import Company, CompanyDTO, CompanyValidator
from db.models.department import Department, DepartmentDTO, DepartmentValidator
from db.models.employee import Employee
from db.models.role import Role, RoleDTO, RoleValidator

router = APIRouter(
    prefix="/role",
    tags=["role"],
)


def query_company_by_name(name: str) -> Company:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Company).where(Company.name == name)
        company = session.exec(statememt).one_or_none()

        return company


def query_department_by_name(name: str, company_id: str) -> Department:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Department).where(
            Department.name == name, Department.company_id == company_id
        )
        department = session.exec(statememt).one_or_none()

        return department


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(role_dto: RoleDTO):
    # validate employee details
    errors = RoleValidator().validate(
        {
            **role_dto.model_dump(),
            "start_date": role_dto.start_date.isoformat(),
            "end_date": role_dto.end_date.isoformat() if role_dto.end_date else None,
        }
    )

    # check if company exists
    company = query_company_by_name(role_dto.company_name)
    if company is None:
        errors["company_name"] = ["Company does not exist"]

    # check if department exists
    if company is not None:
        department = query_department_by_name(role_dto.department_name, company.id)

        if department is None:
            errors["department_name"] = [
                f"Department does not exist for {company.name}"
            ]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)
    role = Role(
        **role_dto.model_dump(), company_id=company.id, department_id=department.id
    )

    with Session(engine) as session:
        session.add(role)
        session.commit()
        session.refresh(role)

    return role.model_dump()


@router.put("/{role_id}", status_code=status.HTTP_200_OK)
async def update_role(role_id: str, role_dto: RoleDTO):
    # validate employee details
    errors = RoleValidator().validate(
        {
            **role_dto.model_dump(),
            "start_date": role_dto.start_date.isoformat(),
            "end_date": role_dto.end_date.isoformat() if role_dto.end_date else None,
        }
    )

    # check if company exists
    company = query_company_by_name(role_dto.company_name)
    if company is None:
        errors["company_name"] = ["Company does not exist"]

    # check if department exists
    if company is not None:
        department = query_department_by_name(role_dto.department_name, company.id)

        if department is None:
            errors["department_name"] = [
                f"Department does not exist for {company.name}"
            ]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Role).where(Role.id == role_id)
        role = session.exec(statement).one_or_none()

        if role is None:
            raise HTTPException(status_code=404, detail="Role not found")

        role.company_id = company.id
        role.department_id = department.id
        role.name = role_dto.name
        role.duties = role_dto.duties
        role.start_date = role_dto.start_date
        role.end_date = role_dto.end_date
        role.employee_company_id = role_dto.employee_company_id

        session.add(role)
        session.commit()
        session.refresh(role)

    return role.model_dump()


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str):
    engine = create_engine(db_url)

    # get employee by role_id
    with Session(engine) as session:
        statement = select(Role).where(Role.id == role_id)
        role = session.exec(statement).one_or_none()
        employee_roles = role.employee.roles

        # employee should have at least 1 role
        if len(employee_roles) < 2:
            raise HTTPException(
                status_code=400, detail="Employee should have at least 1 role"
            )

        # delete role
        session.delete(role)
        session.commit()

    return None
