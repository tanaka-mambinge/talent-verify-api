from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import company, department, employee, role

app = FastAPI()
app.include_router(company.router)
app.include_router(department.router)
app.include_router(employee.router)
app.include_router(role.router)

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
