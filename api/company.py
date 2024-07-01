from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import create_engine
from sqlmodel import Session, select

from db import db_url
from db.models import company
from db.models.company import Company, CompanyDTO, CompanyValidator
from db.models.department import Department
from db.models.employee import Employee
from db.models.role import Role

router = APIRouter(
    prefix="/company",
    tags=["company"],
)


def query_company_by_reg_num(reg_number: str) -> Company:
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Company).where(Company.registration_number == reg_number)
        company = session.exec(statememt).one_or_none()
        return company


def query_company_by_name(name: str) -> Company:
    """
    Check if company name exists in the database
    """
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Company).where(Company.name == name)
        company = session.exec(statememt).one_or_none()
        return company


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_company(company_dto: CompanyDTO):
    # validate company details

    errors = CompanyValidator().validate(
        {
            **company_dto.model_dump(),
            "registration_date": company_dto.registration_date.isoformat(),
        }
    )

    # check if reg number, company name is unique
    if query_company_by_name(company_dto.name) is not None:
        errors["name"] = ["Company name already exists"]

    if query_company_by_reg_num(company_dto.registration_number) is not None:
        errors["registration_number"] = ["Registration number already exists"]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)
    company = Company(**company_dto.model_dump())

    with Session(engine) as session:
        session.add(company)
        session.commit()
        session.refresh(company)

    return company.model_dump()


@router.put("/{company_id}", status_code=status.HTTP_200_OK)
async def update_company(company_id: str, company_dto: CompanyDTO):
    # validate company details
    errors = CompanyValidator().validate(
        {
            **company_dto.model_dump(),
            "registration_date": company_dto.registration_date.isoformat(),
        }
    )

    # check if company name and reg number belongs to the current company
    company = query_company_by_name(company_dto.name)
    if company is not None and company.id != company_id:
        errors["name"] = ["Company name already exists"]

    company = query_company_by_reg_num(company_dto.registration_number)
    if company is not None and company.id != company_id:
        errors["registration_number"] = ["Registration number already exists"]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Company).where(Company.id == company_id)
        company = session.exec(statement).one_or_none()

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        for key, value in company_dto.model_dump().items():
            if key not in ["id"]:
                setattr(company, key, value)

        session.add(company)
        session.commit()
        session.refresh(company)

    return company.model_dump()


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: str):
    engine = create_engine(db_url)

    # check if there are roles or departments associated with the company
    with Session(engine) as session:
        statement = select(Role).where(Role.company_id == company_id)
        roles = session.exec(statement).all()

        if roles:
            raise HTTPException(
                status_code=400,
                detail="Company has roles associated with it. Cannot delete",
            )

        statement = select(Department).where(Department.company_id == company_id)
        departments = session.exec(statement).all()

        if departments:
            raise HTTPException(
                status_code=400,
                detail="Company has departments associated with it. Cannot delete",
            )

    # delete company
    with Session(engine) as session:
        statement = select(Company).where(Company.id == company_id)
        company = session.exec(statement).one_or_none()

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        session.delete(company)
        session.commit()

    return None


@router.get("", status_code=status.HTTP_200_OK)
async def get_companies():
    # paginate
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Company)
        companies = session.exec(statement).all()

        return [company.model_dump() for company in companies]


@router.get("/{company_id}", status_code=status.HTTP_200_OK)
async def get_company_by_id(company_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statememt = select(Company).where(Company.id == company_id)
        company = session.exec(statememt).one_or_none()

        # get number of employees as well

        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")

        return company.model_dump()


@router.get("/{company_id}/employees", status_code=status.HTTP_200_OK)
async def get_company_employees(company_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        # get all employees who've worked at company x
        statement = select(Role).where(Role.company_id == company_id)
        roles = session.exec(statement).all()
        employees = [role.employee for role in roles]

        # get employees who's last role was at company x
        current_employees = []
        current_employee_ids = []

        for employee in employees:
            if not employee:
                continue

            employee.roles.sort(key=lambda x: x.start_date, reverse=True)

            if employee.roles[0].company_id == company_id:
                if employee.id not in current_employee_ids:
                    current_employee_ids.append(employee.id)
                    current_employees.append(employee)

        return [employee.model_dump() for employee in current_employees]


@router.get("/{company_id}/departments", status_code=status.HTTP_200_OK)
async def get_company_departments(company_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Department).where(Department.company_id == company_id)
        departments = session.exec(statement).all()

        return [department.model_dump() for department in departments]
