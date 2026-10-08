from datetime import timedelta
from typing import Annotated
import time

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from database import engine, get_db
from dependencies import get_current_user
from models import Base, Contact, User
from schemas import ContactCreate, ContactUpdate, UserCreate
from security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time

    print(
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{process_time:.4f}s"
    )

    return response

def authenticate_user(
    db: Session,
    username: str,
    password: str
):
    user = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if user is None:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user

@app.post("/register")
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.username == user_data.username)
        .first()
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    return {
        "message": "User created successfully",
        "username": user.username
    }


@limiter.limit("5/minute")
@app.post("/token")
def login_for_access_token(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me")
def read_users_me(
    current_user=Depends(get_current_user)
):
    return {
        "username": current_user.username
    }


@app.get("/contacts")
def get_contacts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: str | None = None,
    sort: str = "id",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    query = db.query(Contact)

    if city:
        query = query.filter(Contact.city == city)

    if sort == "name":
        query = query.order_by(Contact.name.asc())

    elif sort == "-name":
        query = query.order_by(Contact.name.desc())

    elif sort == "city":
        query = query.order_by(Contact.city.asc())

    elif sort == "-city":
        query = query.order_by(Contact.city.desc())

    else:
        query = query.order_by(Contact.id.asc())

    offset = (page - 1) * limit

    contacts = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return contacts


@app.get("/contacts/{name}")
def get_contact(
    name: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    contact = (
        db.query(Contact)
        .filter(Contact.name == name)
        .first()
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found"
        )

    return contact


@limiter.limit("30/minute")
@app.post("/contacts")
def create_contact(
    request: Request,
    contact_data: ContactCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    contact = Contact(
        name=contact_data.name,
        phone=contact_data.phone,
        city=contact_data.city
    )

    try:
        db.add(contact)
        db.commit()
        db.refresh(contact)

    except Exception:
        db.rollback()
        raise

    return contact

@app.put("/contacts/{name}")
def update_contact(
    name: str,
    contact_data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    contact = (
        db.query(Contact)
        .filter(Contact.name == name)
        .first()
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found"
        )

    try:
        contact.phone = contact_data.phone
        contact.city = contact_data.city

        db.commit()
        db.refresh(contact)

    except Exception:
        db.rollback()
        raise

    return contact


@app.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db)
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id)
        .first()
    )

    if contact is None:
        raise HTTPException(
            status_code=404,
            detail="Contact not found"
        )

    try:
        db.delete(contact)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Contact deleted",
        "id": contact_id
    }
