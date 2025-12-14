import jwt
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY = "10df1b675bf04e6e9331194ccc2b21146909ef21e92018f92af67c945eda2050"
ALGORITHM = "HS256"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"sub": "access_token"})
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
