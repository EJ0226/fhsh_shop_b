import uuid
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from datetime import datetime
from pydantic import BaseModel, EmailStr, constr

router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["fhsh_shop"]
users = db["users"]

class User(BaseModel):
    username:str
    password:str

@router.post("/register")
async def register(data:User):
    if users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="User already registered")
    user = {
        "username": data.username,
        "password": data.password,
        "access_token": str(uuid.uuid4()),
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "cart": {"items": []}
    }
    if data.username == "" or data.password == "":
        raise HTTPException(status_code=400, detail="No username or password entered")
    if data.username == "" and data.password == "":
        raise HTTPException(status_code=400, detail="No username or password entered")
    result =  users.insert_one(user)
    return {
        "id": str(result.inserted_id),
        "username": user["username"],
        "access_token": user["access_token"],
    }


@router.post("/signin")
async def signin(data:User):
    user = users.find_one({"username": data.username, "password": data.password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    new_access_token = str(uuid.uuid4())
    users.update_one({"_id": user["_id"]}, {"$set": {"access_token": new_access_token}})
    return {"access_token": new_access_token}
