import pymongo
import json


from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from bson import ObjectId, json_util

router = APIRouter()

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["fhsh_shop"]
collection = db["items"]


class Product(BaseModel):
    name: str = ""
    category: List[str] = Field(default_factory=list)
    sort_by: str = ""

@router.post ("/products")
async def search_products(data : Product):

    search_params = {}
    sort_params = {}

    if data.name:
        search_params["name"] = {"$regex": data.name, "$options": "i"}

    if data.category:
        search_params["category"] = {"$in": [data.category]}


    if data.sort_by == "price_desc": 
        sort_params["price"] = pymongo.DESCENDING
    elif data.sort_by == "price_asc":  
        sort_params["price"] = pymongo.ASCENDING
    elif data.sort_by == "name_desc": 
        sort_params["name"] = pymongo.DESCENDING
        sort_params["collation"] = Collation(locale="zh")
    elif data.sort_by == "name_asc": 
        sort_params["name"] = pymongo.ASCENDING
        sort_params["collation"] = Collation(locale="zh")

    if search_params:
        result = collection.find(search_params).sort(list(sort_params.items()))
        count = collection.count_documents(search_params)
        result = json.loads(json_util.dumps(result)) 
    return {"count": count, "products": list(result)}