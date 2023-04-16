from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.user import router as user
from router.cart import router as cart
from router.admin import router as admin
from router.products import router as products
from router.item import router as item

app = FastAPI()

origins = [
    
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user)
app.include_router(cart)
app.include_router(admin)
app.include_router(products)
app.include_router(item)

@app.options("/api/{path:path}")
async def options_route(path: str):
    return {"method": "OPTIONS"}