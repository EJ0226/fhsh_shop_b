from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, conlist

router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["fhsh_shop"]
orders = db["orders"]
users = db["users"]
products = db["products"]

class OrderItem(BaseModel):
    product_id: str
    quantity: int

class Order(BaseModel):
    user_id: str
    items: conlist(OrderItem, min_items=1)

def validate_order(order: Order) -> Dict[str, int]:
    errors = {}
    user = users.find_one({"_id": order.user_id})
    if not user:
        errors["user"] = 404
    for item in order.items:
        product = products.find_one({"_id": item.product_id})
        if not product:
            errors[item.product_id] = 404
        elif product["quantity"] < item.quantity:
            errors[item.product_id] = 400
    return errors

@router.post("/orders")
async def create_order(order: Order):
    errors = validate_order(order)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    total_price = 0
    for item in order.items:
        product = products.find_one({"_id": item.product_id})
        total_price += product["price"] * item.quantity

    new_order = {
        "user_id": order.user_id,
        "items": [item.dict() for item in order.items],
        "total_price": total_price,
        "status": "pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    result = orders.insert_one(new_order)

    users.update_one({"_id": order.user_id}, {"$set": {"cart.items": []}})

    return {
        "id": str(result.inserted_id),
        "user_id": new_order["user_id"],
        "items": new_order["items"],
        "total_price": new_order["total_price"],
        "status": new_order["status"],
        "created_at": new_order["created_at"],
        "updated_at": new_order["updated_at"]
    }
