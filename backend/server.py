from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Enums
class MenuCategory(str, Enum):
    COFFEE = "Coffee"
    TEA = "Tea"
    PASTRIES = "Pastries"
    SNACKS = "Snacks"
    BEVERAGES = "Beverages"

# Models
class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    category: MenuCategory
    description: Optional[str] = ""
    available: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: MenuCategory
    description: Optional[str] = ""
    available: bool = True

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[MenuCategory] = None
    description: Optional[str] = None
    available: Optional[bool] = None

class BillItem(BaseModel):
    menu_item_id: str
    name: str
    price: float
    quantity: int

class BillCreate(BaseModel):
    items: List[BillItem]
    discount_percent: float = 0
    tax_percent: float = 5.0

class Bill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    items: List[BillItem]
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    bill_number: int

# Default menu items
DEFAULT_MENU_ITEMS = [
    {"name": "Espresso", "price": 3.50, "category": "Coffee", "description": "Rich & bold single shot"},
    {"name": "Americano", "price": 4.00, "category": "Coffee", "description": "Espresso with hot water"},
    {"name": "Cappuccino", "price": 4.50, "category": "Coffee", "description": "Espresso with steamed milk foam"},
    {"name": "Latte", "price": 5.00, "category": "Coffee", "description": "Espresso with creamy steamed milk"},
    {"name": "Mocha", "price": 5.50, "category": "Coffee", "description": "Espresso with chocolate & milk"},
    {"name": "Cold Brew", "price": 4.50, "category": "Coffee", "description": "Slow-steeped, smooth & refreshing"},
    {"name": "Green Tea", "price": 3.00, "category": "Tea", "description": "Classic Japanese green tea"},
    {"name": "Earl Grey", "price": 3.00, "category": "Tea", "description": "Black tea with bergamot"},
    {"name": "Chai Latte", "price": 4.50, "category": "Tea", "description": "Spiced tea with steamed milk"},
    {"name": "Matcha Latte", "price": 5.00, "category": "Tea", "description": "Premium matcha with milk"},
    {"name": "Croissant", "price": 3.50, "category": "Pastries", "description": "Buttery, flaky French classic"},
    {"name": "Chocolate Muffin", "price": 3.00, "category": "Pastries", "description": "Rich chocolate chip muffin"},
    {"name": "Blueberry Scone", "price": 3.50, "category": "Pastries", "description": "Fresh blueberry scone"},
    {"name": "Cinnamon Roll", "price": 4.00, "category": "Pastries", "description": "Warm cinnamon swirl"},
    {"name": "Avocado Toast", "price": 7.50, "category": "Snacks", "description": "Smashed avocado on sourdough"},
    {"name": "Grilled Cheese", "price": 6.00, "category": "Snacks", "description": "Classic melted cheese sandwich"},
    {"name": "Caesar Salad", "price": 8.00, "category": "Snacks", "description": "Crisp romaine with Caesar dressing"},
    {"name": "Orange Juice", "price": 4.00, "category": "Beverages", "description": "Fresh squeezed orange juice"},
    {"name": "Lemonade", "price": 3.50, "category": "Beverages", "description": "House-made lemonade"},
    {"name": "Sparkling Water", "price": 2.50, "category": "Beverages", "description": "Refreshing sparkling water"},
]

# Menu Routes
@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    items = await db.menu_items.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/menu/{item_id}", response_model=MenuItem)
async def get_menu_item(item_id: str):
    item = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return item

@api_router.post("/menu", response_model=MenuItem)
async def create_menu_item(item: MenuItemCreate):
    menu_item = MenuItem(**item.model_dump())
    doc = menu_item.model_dump()
    await db.menu_items.insert_one(doc)
    return menu_item

@api_router.put("/menu/{item_id}", response_model=MenuItem)
async def update_menu_item(item_id: str, update: MenuItemUpdate):
    existing = await db.menu_items.find_one({"id": item_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.menu_items.update_one({"id": item_id}, {"$set": update_data})
    
    updated = await db.menu_items.find_one({"id": item_id}, {"_id": 0})
    return updated

@api_router.delete("/menu/{item_id}")
async def delete_menu_item(item_id: str):
    result = await db.menu_items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return {"message": "Item deleted successfully"}

# Bill Routes
@api_router.post("/bills", response_model=Bill)
async def create_bill(bill_data: BillCreate):
    # Get next bill number
    last_bill = await db.bills.find_one(sort=[("bill_number", -1)])
    bill_number = (last_bill["bill_number"] + 1) if last_bill else 1001
    
    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in bill_data.items)
    discount_amount = subtotal * (bill_data.discount_percent / 100)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * (bill_data.tax_percent / 100)
    total = taxable_amount + tax_amount
    
    bill = Bill(
        items=[item.model_dump() for item in bill_data.items],
        subtotal=round(subtotal, 2),
        discount_percent=bill_data.discount_percent,
        discount_amount=round(discount_amount, 2),
        tax_percent=bill_data.tax_percent,
        tax_amount=round(tax_amount, 2),
        total=round(total, 2),
        bill_number=bill_number
    )
    
    doc = bill.model_dump()
    await db.bills.insert_one(doc)
    return bill

@api_router.get("/bills", response_model=List[Bill])
async def get_bills():
    bills = await db.bills.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return bills

@api_router.get("/bills/{bill_id}", response_model=Bill)
async def get_bill(bill_id: str):
    bill = await db.bills.find_one({"id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

# Seed menu on startup
@app.on_event("startup")
async def seed_menu():
    count = await db.menu_items.count_documents({})
    if count == 0:
        for item_data in DEFAULT_MENU_ITEMS:
            menu_item = MenuItem(**item_data)
            await db.menu_items.insert_one(menu_item.model_dump())
        logging.info("Seeded default menu items")

@api_router.get("/")
async def root():
    return {"message": "Cafe Bill Generator API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
