from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/api")
# router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["Eshop"]
items = db["merchs"]


class Item(BaseModel):
    name: str
    summary : str
    price: int
    quantity: int


@router.post("/create_item")
async def create_item(create: Item):
    create_data = {
        "name": create.name,
        "summary": create.summary,
        "price": create.price,
        "quantity": create.quantity
    }

    result = items.insert_one(create_data)

    return {
        "id": str(result.inserted_id),
        "name": create_data["name"],
        "summary": create_data["summary"],
        "price": create_data["price"],
        "quantity": create_data["quantity"]
    }


@router.get("/read_item/{item_id}")
async def read_item(item_id: str):
    item = items.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "summary": item["summary"],
        "price": item["price"]
    }


@router.put("/update_item/{item_id}")
async def update_item(item_id: str, item: Item):
    existing_item = items.find_one({"_id": ObjectId(item_id)})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")

    item_data = {
        "name": item.name,
        "summary": item.summary,
        "price": item.price,
    }

    items.update_one({"_id":ObjectId(item_id)}, {"$set": item_data})

    return {
        "id": item_id,
        "name": item_data["name"],
        "summary": item_data["summary"],
        "price": item_data["price"]
    }


@router.delete("/delete_item/{item_id}")
async def delete_item(item_id: str):
    delete = items.delete_one({"_id": ObjectId(item_id)})
    if not delete:
        raise HTTPException(status_code=404, detail="Item not found")
    items.delete_one({"_id": ObjectId(item_id)})
    return {
        "id": item_id,
        "message": "Item deleted"
    }

