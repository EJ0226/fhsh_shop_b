from fastapi import APIRouter, Depends, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, Field

router = APIRouter()

client = MongoClient("mongodb://localhost:27017/")
db = client["fhsh_shop"]
users = db["users"]
items = db["items"]

class Cart(BaseModel):
    user_id: str
    item_name: str
    quantity: int

class Remove(BaseModel):
    user_id: str
    item_name: str

def get_user_cart(user_id):
    cart = users.find_one({"_id": ObjectId(user_id)}, {"cart": 1})
    if not cart:
        users.update_one({"_id": ObjectId(user_id)}, {"$set": {"cart": {"items": []}}})
        cart = users.find_one({"_id": ObjectId(user_id)}, {"cart": 1})
    return cart["cart"]

@router.post("/add-to-cart")
async def add_to_cart(carts : Cart):
    item = items.find_one({"name": carts.item_name})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if carts.quantity <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    cart = get_user_cart(carts.user_id)
    for cart_item in cart["items"]:
        if cart_item["name"] == carts.carts.item_name:
            cart_item["quantity"] += carts.quantity
            break
    else:
        cart["items"].append({
            "name": carts.item_name,
            "quantity": carts.quantity,
        })
    users.update_one({"_id": ObjectId(carts.user_id)}, {"$set": {"cart": cart}})
    return cart

@router.post("/remove-from-cart")
async def remove_from_cart(remove : Remove):
    cart = get_user_cart(remove.user_id)
    for i, cart_item in enumerate(cart["items"]):
        if cart_item["name"] == remove.item_name:
            del cart["items"][i]
            users.update_one({"_id": ObjectId(remove.user_id)}, {"$set": {"cart": cart}})
            return cart
    else:
        raise HTTPException(status_code=404, detail="Item not found in cart")
