# Implementation Guide: Real JWT Authentication

This guide provides the full implementation for replacing the temporary `get_current_user` stub with a production-ready JWT authentication system, following your established clean architecture.

## 📂 New & Modified Files

You will need to create or modify the following files:

-   **`app/core/config.py`**: Add settings for JWT secrets.
-   **`app/core/security.py`**: Add functions to create and verify access tokens.
-   **`app/schemas/apikeys.py`**: Add schemas for tokens and user login (or a new `app/schemas/users.py` and `app/schemas/tokens.py`).
-   **`app/repositories/users.py`**: A new repository to find users by email.
-   **`app/services/users.py`**: A new service to handle the authentication logic.
-   **`app/api/routers/auth.py`**: A new router for the `/login` endpoint.
-   **`app/core/deps.py`**: The final, real implementation of `get_current_user`.

---

## 🛠️ Step-by-Step Implementation

### 1\. Update Core Configuration (`app/core/config.py`)

Add the necessary settings for your JWTs.

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ... existing settings ...
    SECRET_KEY: str = "your_super_secret_key_that_should_be_in_a_env_file"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2\. Update Security Helpers (`app/core/security.py`)

Add functions to create and verify passwords and JWTs.

```python
# app/core/security.py
import secrets
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from .config import settings

# ... existing ApiKeyGenerator and hash_api_key ...

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT Token Creation ---
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
```

### 3\. Add New Schemas (`app/schemas/`)

It's good practice to separate schemas by their domain.

#### `app/schemas/users.py`

```python
# app/schemas/users.py
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
```

#### `app/schemas/tokens.py`

```python
# app/schemas/tokens.py
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
```

### 4\. Create User Repository (`app/repositories/users.py`)

This new repository will handle finding users in the database.

```python
# app/repositories/users.py
from sqlmodel import Session, select
from app.models.user import User
from app.schemas.users import UserCreate
from app.core.security import get_password_hash

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def create(self, user_create: UserCreate) -> User:
        hashed_password = get_password_hash(user_create.password)
        user = User(email=user_create.email, hashed_password=hashed_password)
        self.session.add(user)
        self.session.flush()
        return user
```

### 5\. Create User Service (`app/services/users.py`)

This new service will handle the business logic for authentication.

```python
# app/services/users.py
from sqlmodel import Session
from app.repositories.users import UserRepository
from app.core.security import verify_password
from app.schemas.users import UserCreate
from app.models.user import User

class UserService:
    def __init__(self, session: Session):
        self.repo = UserRepository(session)
        self.session = session

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user_create: UserCreate) -> User:
        user = self.repo.create(user_create)
        self.session.commit()
        self.session.refresh(user)
        return user
```

### 6\. Create Auth Router (`app/api/routers/auth.py`)

This new router will contain the public `/login` and `/register` endpoints.

```python
# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core.deps import get_db
from app.services.users import UserService
from app.schemas.tokens import Token
from app.schemas.users import UserCreate, UserRead
from app.core.security import create_access_token

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    svc = UserService(db)
    if svc.repo.get_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = svc.create_user(user_in)
    return user

@router.post("/login", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    svc = UserService(db)
    user = svc.authenticate(email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

### 7\. Finalize Dependencies (`app/core/deps.py`)

This is the final step: replace the stub with the real `get_current_user`.

```python
# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.db.session import engine
from app.repositories.users import UserRepository
from app.schemas.tokens import TokenData
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    with Session(engine) as session:
        yield session

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(email=token_data.email)

    if user is None:
        raise credentials_exception
    return user
```

### 8\. Update `main.py`

Finally, include your new `auth` router in your main application.

```python
# app/main.py
# ... other imports
from app.api.routers import users_apikeys, auth

# ... app setup ...

# Include the new routers
app.include_router(auth.router)
app.include_router(users_apikeys.router)
```
