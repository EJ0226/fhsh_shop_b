import re
from datetime import datetime, timedelta
from typing import Optional, Union
from starlette.requests import Request
from fastapi_sso.sso.google import GoogleSSO
from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from bson import ObjectId
from bson.objectid import ObjectId
from pydantic import BaseModel, EmailStr, Field, validator

router = APIRouter()

google_sso = GoogleSSO("892706411850-rf3ia8msmej9m4jieku73lj7a99jtoo8.apps.googleusercontent.com",
 "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",
 "https://my.awesome-web.com/google/callback")

client = MongoClient("mongodb://localhost:27017/?directConnection=true")
db = client["Eshop"]
users = db["users"]

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

EMAIL_REGEX = re.compile(
    r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
)

class UserCreate(BaseModel):
    """."""
    email: EmailStr
    username: str = Field(min_length=6, max_length=17)
    password: str = Field(min_length=7, max_length=16)
    checkpassword: str = Field(min_length=7, max_length=16)

    @validator("email")
    def email_validator(cls, email):
        """."""
        if not email:
            raise ValueError("Email is required")
        if not EMAIL_REGEX.match(email):
            raise ValueError("Invalid email format")
        return email.lower()

    @validator("username")
    def username_validator(cls, username):
        """."""
        if not username.isalnum():
            raise ValueError("Username should be alphanumeric")
        return username

    @validator("password")
    def password_validator(cls, password):
        """."""
        if not any(char.isdigit() for char in password):
            raise ValueError("Password should contain at least 1 digit")
        if not any(char.isalpha() for char in password):
            raise ValueError("Password should contain at least 1 letter")
        return password
    @validator("checkpassword")
    def checkpassword_validator(cls, checkpassword, values):
        if "password" in values and checkpassword != values["password"]:
            raise ValueError("Passwords do not match")
        return checkpassword

    class Config:
        """."""
        arbitrary_types_allowed = True

class User(BaseModel):
    """."""
    email: EmailStr
    username: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

    class Config:
        """."""
        allow_population_by_field_name = True

class UserUpdate(BaseModel):
    name: str
    email: Optional[str] = ''
    password: Optional[str] = ''
    updated_at: Optional[datetime] = datetime.now()

    # 驗證 email 格式是否正確
    @validator('email', always=True)
    def validate_email(cls, v):
        if v and not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v

    # 驗證密碼是否為至少 7 個字元
    @validator('password', always=True)
    def validate_password(cls, v):
        if len(v) < 7:
            raise ValueError("Password must be at least 7 characters")
        if len(v) > 16:
            raise ValueError("Password can be at most 16 characters")
        return pwd_context.hash(v) if v else None

    # 驗證名字是否為非空字串
    @validator('name', always=True)
    def validate_name(cls, v):
        if not v:
            raise ValueError("Name cannot be empty")
        return v

    # 如果更新時間為 None，則回傳現在的時間
    @validator('updated_at', always=True)
    def validate_updated_at(cls, v):
        return v or datetime.now()

    # 回傳要更新的欄位資料
    def to_dict(self):
        update_data = self.dict(exclude_unset=True)
        update_data['password'] = pwd_context.hash(update_data['password']) if update_data.get('password') else None
        return update_data


def update_user(user_id: str, user_update: UserUpdate):
    # 取得要更新的欄位資料
    update_data = user_update.to_dict()
    if not update_data:
        raise ValueError("No data to update")
    # 更新使用者資料
    users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})

class UserInDB(User):
    """."""
    email: str
    password: str

    class Config:
        """."""
        allow_population_by_field_name = False

async def get_user(email: str):
    """."""
    user = users.find_one({"email": email})
    return user

def get_password_hash(password: str):
    """."""
    return pwd_context.hash(password)


def sign_JWT(data: dict, expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    """."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
def verify_password(plain_password, hashed_password):
    """."""
    return pwd_context.verify(plain_password, hashed_password)

def get_passwordhash(password):
    """."""
    return pwd_context.hash(password)

@router.post("/api/register")
async def user_register(user: UserCreate):
    """."""
    print({"user":user})
    user_found = await get_user(user.email)
    if user_found:
        raise HTTPException(status_code=409, detail="User already registered")
    user_dict = user.dict()
    user_dict["created_at"] = datetime.utcnow()
    user_dict["password"] = get_password_hash(user.password)
    result = users.insert_one(user_dict)
    return {"Registration successful":True}

async def authenticate_user(email: str, password: str) -> Union[UserInDB, bool]:
    """."""
    user = await get_user(email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

@router.post("/api/login")
async def user_login(form_data: OAuth2PasswordRequestForm = Depends()):
    """."""
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = sign_JWT({"user_id": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/login")
async def google_login():
    """Generate login url and redirect"""
    return await google_sso.get_login_redirect()


@router.get("/google/callback")
async def google_callback(request: Request):
    """Process login response from Google and return user info"""
    user = await google_sso.verify_and_process(request)
    return {
        "id": user.id,
        "picture": user.picture,
        "display_name": user.display_name,
        "email": user.email,
        "provider": user.provider,
    }

# 取得使用者資料
@router.get("/api/{user_id}", response_model=User)
async def getuser(user_id: str):
    """
    Retrieve user information.

    Args:
        user_id (str): The ID of the user to retrieve.

    Returns:
        User: The User object representing the retrieved user.

    Raises:
        HTTPException: If the specified user ID is not found.
    """
    user = users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)


# 取得所有使用者
@router.get("/api/users")
async def get_all_users():
    """."""
    result = users.find(limit=10)
    print(result)




# 更新使用者資料
@router.put("/api/{user_id}")
async def update_user(user_id: str, user_update: UserUpdate):
    """."""
    userid = ObjectId(user_id)
    user_update = user_update.dict()
    print(user_id,userid)
    result = users.update_one({"_id": userid}, {"$set": user_update})
    if not result.modified_count:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"}


# 刪除使用者資料
@router.delete("/api/{user_id}")
async def delete_user(user_id: str):
    """."""
    result = users.delete_one({"_id": ObjectId(user_id)})
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success"}
