from fastapi import FastAPI
from app.api import auth


app = FastAPI(title="Kristobell School API", description="API for Kristobell School")

app.include_router(auth.router)
