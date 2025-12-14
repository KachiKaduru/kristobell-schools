from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import auth, admin, staff, students
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Kristobell School API",
    description="API for Kristobell School",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(staff.router)
app.include_router(students.router)
