from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from passlib.context import CryptContext
from typing import Annotated, Union
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from app.dbservice import *

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
RESET_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(email: str):
    db = SessionLocal()
    user = db.query(Employee).filter(Employee.employee_email == email).first()
    db.close()
    return user



def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
async def get_token_auth_header(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=403, detail="Invalid authentication scheme")
    return credentials.credentials


async def get_current_user(token: Annotated[str, Depends(get_token_auth_header)]):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401, detail="Could not validate credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
            raise HTTPException(status_code=401,detail="invalid token")
    user = get_user(email)
    if user is None:
        raise HTTPException(status_code=401,detail=" user not found")
    return user

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

## creating the reset token using jwt
def create_reset_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# verifying reset token
def verify_reset_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError()
        return email
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
def send_reset_email(email: str, reset_token: str):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "ivymaundu03@gmail.com"
    smtp_password = "houi jjkd wsdx vgjd"

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email
    msg['Subject'] = "Password Reset Request"


    reset_link = f"http://localhost:8000/reset_password/{reset_token}"
    body = f"Click the link to reset your password: {reset_link}"
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)