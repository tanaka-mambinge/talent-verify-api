from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import create_engine
from sqlmodel import Session, select

from db import db_url
from db.models.company import Company, CompanyDTO, CompanyValidator
from db.models.department import Department, DepartmentDTO, DepartmentValidator
from db.models.employee import Employee
from db.models.role import Role

router = APIRouter(
    prefix="/department",
    tags=["department"],
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


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_department(department_dto: DepartmentDTO):
    # validate department details
    errors = DepartmentValidator().validate(department_dto.model_dump())

    # check if company exists and if department exists for the particular company
    if query_department_by_name(department_dto.company_id, department_dto.name):
        errors["name"] = ["Department name already exists"]

    if query_company_by_id(department_dto.company_id) is None:
        errors["name"] = ["Company does not exist"]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)
    department = Department(**department_dto.model_dump())

    with Session(engine) as session:
        session.add(department)
        session.commit()
        session.refresh(department)

    return department.model_dump()


@router.put("/{department_id}", status_code=status.HTTP_200_OK)
async def update_departmernt(department_id: str, department_dto: DepartmentDTO):
    # validate department details
    errors = DepartmentValidator().validate(department_dto.model_dump())

    # check if department name belongs to the current company
    department = query_department_by_name(
        department_dto.company_id, department_dto.name
    )
    if department is not None and department.id != department_id:
        errors["name"] = ["Department name already exists"]

    # return errors if any
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    # save to db
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Department).where(Department.id == department_id)
        department = session.exec(statement).one_or_none()

        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        for key, value in department_dto.model_dump().items():
            if key not in ["id", "company_id"]:
                setattr(department, key, value)

        session.add(department)
        session.commit()
        session.refresh(department)

    return department.model_dump()


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(department_id: str):
    engine = create_engine(db_url)

    # check if there are roles associated with the department
    with Session(engine) as session:
        statement = select(Role).where(Role.department_id == department_id)
        roles = session.exec(statement).all()

        if roles:
            raise HTTPException(
                status_code=400,
                detail="Department has roles associated with it. Cannot delete",
            )

    # delete department
    with Session(engine) as session:
        statement = select(Department).where(Department.id == department_id)
        department = session.exec(statement).one_or_none()

        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        session.delete(department)
        session.commit()

    return None


@router.get("/{department_id}", status_code=status.HTTP_200_OK)
async def get_department_by_id(department_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Department).where(Department.id == department_id)
        department = session.exec(statement).one_or_none()

        if department is None:
            raise HTTPException(status_code=404, detail="Department not found")

        return department.model_dump()


@router.get("/{department_id}/employees", status_code=status.HTTP_200_OK)
async def get_department_employees(department_id: str):
    engine = create_engine(db_url)

    with Session(engine) as session:
        statement = select(Role).where(Role.department_id == department_id)
        roles = session.exec(statement).all()

        employees = []
        for role in roles:
            if role.end_date is None:
                employees.append(role.employee)

        return employees
