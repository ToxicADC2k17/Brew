from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import shutil

ROOT_DIR = Path(__file__).parent
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
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
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DESSERTS = "Desserts"
    SANDWICHES = "Sandwiches"
    SMOOTHIES = "Smoothies"
    STARTERS = "Starters"
    MAINS = "Mains"
    STEAKS = "Steaks"
    SEAFOOD = "Seafood"
    VEGETARIAN = "Vegetarian"
    SALADS = "Salads"
    SIDES = "Sides"
    SOUPS = "Soups"
    BEERS = "Beers"
    WINES = "Wines"
    PIZZA = "Pizza"
    PASTA = "Pasta"
    BURGERS = "Burgers"

# Models
class ModifierOption(BaseModel):
    name: str
    price_adjustment: float = 0

class Modifier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Size", "Cooking", "Extras"
    type: str = "single"  # single or multiple
    required: bool = False
    options: List[ModifierOption]

class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    category: MenuCategory
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    available: bool = True
    modifiers: List[str] = []  # List of modifier IDs
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: MenuCategory
    description: Optional[str] = ""
    image_url: Optional[str] = ""
    available: bool = True
    modifiers: List[str] = []

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[MenuCategory] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    available: Optional[bool] = None
    modifiers: Optional[List[str]] = None

class BillItemModifier(BaseModel):
    modifier_name: str
    option_name: str
    price_adjustment: float

class BillItem(BaseModel):
    menu_item_id: str
    name: str
    price: float
    quantity: int
    modifiers: List[BillItemModifier] = []

class BillCreate(BaseModel):
    items: List[BillItem]
    discount_percent: float = 0
    tax_percent: float = 5.0
    customer_name: Optional[str] = ""
    table_number: Optional[str] = ""
    nif: Optional[str] = ""
    currency: str = "EUR"

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
    customer_name: str = ""
    table_number: str = ""
    nif: str = ""
    currency: str = "EUR"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    bill_number: int

class ThemeConfig(BaseModel):
    id: str = "default"
    name: str = "Espresso & Crema"
    primary_color: str = "#2C1A1D"
    accent_color: str = "#D97706"
    background_color: str = "#FDFCF8"
    card_color: str = "#FFFFFF"
    text_color: str = "#2C1A1D"
    muted_color: str = "#6B5E5F"
    border_color: str = "#E5E0D8"
    success_color: str = "#3F6212"
    error_color: str = "#991B1B"

class ModifierCreate(BaseModel):
    name: str
    type: str = "single"
    required: bool = False
    options: List[ModifierOption]

# Default Modifiers
DEFAULT_MODIFIERS = [
    {
        "id": "size",
        "name": "Size",
        "type": "single",
        "required": False,
        "options": [
            {"name": "Small", "price_adjustment": -1.00},
            {"name": "Regular", "price_adjustment": 0},
            {"name": "Large", "price_adjustment": 1.50},
            {"name": "Extra Large", "price_adjustment": 2.50}
        ]
    },
    {
        "id": "cooking",
        "name": "Cooking Preference",
        "type": "single",
        "required": False,
        "options": [
            {"name": "Rare", "price_adjustment": 0},
            {"name": "Medium Rare", "price_adjustment": 0},
            {"name": "Medium", "price_adjustment": 0},
            {"name": "Medium Well", "price_adjustment": 0},
            {"name": "Well Done", "price_adjustment": 0}
        ]
    },
    {
        "id": "milk",
        "name": "Milk Option",
        "type": "single",
        "required": False,
        "options": [
            {"name": "Regular Milk", "price_adjustment": 0},
            {"name": "Oat Milk", "price_adjustment": 0.50},
            {"name": "Almond Milk", "price_adjustment": 0.50},
            {"name": "Soy Milk", "price_adjustment": 0.40},
            {"name": "Coconut Milk", "price_adjustment": 0.50},
            {"name": "No Milk", "price_adjustment": 0}
        ]
    },
    {
        "id": "extras",
        "name": "Extras",
        "type": "multiple",
        "required": False,
        "options": [
            {"name": "Extra Cheese", "price_adjustment": 1.50},
            {"name": "Bacon", "price_adjustment": 2.00},
            {"name": "Avocado", "price_adjustment": 2.50},
            {"name": "Fried Egg", "price_adjustment": 1.50},
            {"name": "Mushrooms", "price_adjustment": 1.50},
            {"name": "Jalapeños", "price_adjustment": 0.75},
            {"name": "Extra Sauce", "price_adjustment": 0.50}
        ]
    },
    {
        "id": "sides",
        "name": "Side Choice",
        "type": "single",
        "required": False,
        "options": [
            {"name": "French Fries", "price_adjustment": 0},
            {"name": "Sweet Potato Fries", "price_adjustment": 1.00},
            {"name": "Salad", "price_adjustment": 0},
            {"name": "Rice", "price_adjustment": 0},
            {"name": "Mashed Potato", "price_adjustment": 0.50},
            {"name": "Vegetables", "price_adjustment": 0}
        ]
    },
    {
        "id": "spice",
        "name": "Spice Level",
        "type": "single",
        "required": False,
        "options": [
            {"name": "Mild", "price_adjustment": 0},
            {"name": "Medium", "price_adjustment": 0},
            {"name": "Hot", "price_adjustment": 0},
            {"name": "Extra Hot", "price_adjustment": 0}
        ]
    }
]

# Default Theme
DEFAULT_THEME = {
    "id": "default",
    "name": "Espresso & Crema",
    "primary_color": "#2C1A1D",
    "accent_color": "#D97706",
    "background_color": "#FDFCF8",
    "card_color": "#FFFFFF",
    "text_color": "#2C1A1D",
    "muted_color": "#6B5E5F",
    "border_color": "#E5E0D8",
    "success_color": "#3F6212",
    "error_color": "#991B1B"
}

# Menu Routes
@api_router.get("/menu", response_model=List[MenuItem])
async def get_menu():
    items = await db.menu_items.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.get("/menu/categories")
async def get_categories():
    return [cat.value for cat in MenuCategory]

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

# Modifier Routes
@api_router.get("/modifiers")
async def get_modifiers():
    modifiers = await db.modifiers.find({}, {"_id": 0}).to_list(100)
    return modifiers

@api_router.post("/modifiers")
async def create_modifier(modifier: ModifierCreate):
    mod = Modifier(**modifier.model_dump())
    doc = mod.model_dump()
    await db.modifiers.insert_one(doc)
    return mod

@api_router.put("/modifiers/{modifier_id}")
async def update_modifier(modifier_id: str, modifier: ModifierCreate):
    existing = await db.modifiers.find_one({"id": modifier_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Modifier not found")
    
    update_data = modifier.model_dump()
    await db.modifiers.update_one({"id": modifier_id}, {"$set": update_data})
    updated = await db.modifiers.find_one({"id": modifier_id}, {"_id": 0})
    return updated

@api_router.delete("/modifiers/{modifier_id}")
async def delete_modifier(modifier_id: str):
    result = await db.modifiers.delete_one({"id": modifier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Modifier not found")
    return {"message": "Modifier deleted successfully"}

# Theme/Config Routes
@api_router.get("/config/theme")
async def get_theme():
    theme = await db.config.find_one({"id": "theme"}, {"_id": 0})
    if not theme:
        return DEFAULT_THEME
    return theme

@api_router.put("/config/theme")
async def update_theme(theme: ThemeConfig):
    theme_data = theme.model_dump()
    theme_data["id"] = "theme"
    await db.config.update_one(
        {"id": "theme"},
        {"$set": theme_data},
        upsert=True
    )
    return theme_data

@api_router.post("/config/theme/reset")
async def reset_theme():
    theme_data = DEFAULT_THEME.copy()
    theme_data["id"] = "theme"
    await db.config.update_one(
        {"id": "theme"},
        {"$set": theme_data},
        upsert=True
    )
    return theme_data

# Bill Routes
@api_router.post("/bills", response_model=Bill)
async def create_bill(bill_data: BillCreate):
    last_bill = await db.bills.find_one(sort=[("bill_number", -1)])
    bill_number = (last_bill["bill_number"] + 1) if last_bill else 1001
    
    # Calculate totals including modifiers
    subtotal = 0
    for item in bill_data.items:
        item_total = item.price * item.quantity
        for mod in item.modifiers:
            item_total += mod.price_adjustment * item.quantity
        subtotal += item_total
    
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
        customer_name=bill_data.customer_name or "",
        table_number=bill_data.table_number or "",
        nif=bill_data.nif or "",
        currency=bill_data.currency,
        bill_number=bill_number
    )
    
    doc = bill.model_dump()
    await db.bills.insert_one(doc)
    return bill

@api_router.get("/bills", response_model=List[Bill])
async def get_bills(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
):
    query = {}
    
    if start_date and end_date:
        query["created_at"] = {
            "$gte": start_date,
            "$lte": end_date + "T23:59:59"
        }
    elif start_date:
        query["created_at"] = {"$gte": start_date}
    elif end_date:
        query["created_at"] = {"$lte": end_date + "T23:59:59"}
    
    if search:
        query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"nif": {"$regex": search, "$options": "i"}},
            {"table_number": {"$regex": search, "$options": "i"}}
        ]
    
    bills = await db.bills.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return bills

@api_router.get("/bills/{bill_id}", response_model=Bill)
async def get_bill(bill_id: str):
    bill = await db.bills.find_one({"id": bill_id}, {"_id": 0})
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

# Sales Report Routes
@api_router.get("/reports/daily")
async def get_daily_sales_report(date: Optional[str] = None):
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    start = f"{date}T00:00:00"
    end = f"{date}T23:59:59"
    
    bills = await db.bills.find(
        {"created_at": {"$gte": start, "$lte": end}},
        {"_id": 0}
    ).to_list(1000)
    
    if not bills:
        return {
            "date": date,
            "total_bills": 0,
            "total_revenue": 0,
            "total_items_sold": 0,
            "avg_bill_value": 0,
            "top_items": [],
            "currency": "EUR"
        }
    
    total_revenue = sum(b["total"] for b in bills)
    total_items = sum(sum(i["quantity"] for i in b["items"]) for b in bills)
    
    item_counts = {}
    for bill in bills:
        for item in bill["items"]:
            name = item["name"]
            if name not in item_counts:
                item_counts[name] = {"name": name, "quantity": 0, "revenue": 0}
            item_counts[name]["quantity"] += item["quantity"]
            item_counts[name]["revenue"] += item["price"] * item["quantity"]
    
    top_items = sorted(item_counts.values(), key=lambda x: x["quantity"], reverse=True)[:10]
    
    return {
        "date": date,
        "total_bills": len(bills),
        "total_revenue": round(total_revenue, 2),
        "total_items_sold": total_items,
        "avg_bill_value": round(total_revenue / len(bills), 2) if bills else 0,
        "top_items": top_items,
        "currency": bills[0].get("currency", "EUR") if bills else "EUR"
    }

@api_router.get("/reports/range")
async def get_sales_report_range(start_date: str, end_date: str):
    start = f"{start_date}T00:00:00"
    end = f"{end_date}T23:59:59"
    
    bills = await db.bills.find(
        {"created_at": {"$gte": start, "$lte": end}},
        {"_id": 0}
    ).to_list(10000)
    
    if not bills:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_bills": 0,
            "total_revenue": 0,
            "total_items_sold": 0,
            "avg_bill_value": 0,
            "daily_breakdown": [],
            "top_items": [],
            "currency": "EUR"
        }
    
    total_revenue = sum(b["total"] for b in bills)
    total_items = sum(sum(i["quantity"] for i in b["items"]) for b in bills)
    
    daily_data = {}
    item_counts = {}
    
    for bill in bills:
        day = bill["created_at"][:10]
        if day not in daily_data:
            daily_data[day] = {"date": day, "bills": 0, "revenue": 0}
        daily_data[day]["bills"] += 1
        daily_data[day]["revenue"] += bill["total"]
        
        for item in bill["items"]:
            name = item["name"]
            if name not in item_counts:
                item_counts[name] = {"name": name, "quantity": 0, "revenue": 0}
            item_counts[name]["quantity"] += item["quantity"]
            item_counts[name]["revenue"] += item["price"] * item["quantity"]
    
    daily_breakdown = sorted(daily_data.values(), key=lambda x: x["date"])
    for d in daily_breakdown:
        d["revenue"] = round(d["revenue"], 2)
    
    top_items = sorted(item_counts.values(), key=lambda x: x["quantity"], reverse=True)[:10]
    for item in top_items:
        item["revenue"] = round(item["revenue"], 2)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_bills": len(bills),
        "total_revenue": round(total_revenue, 2),
        "total_items_sold": total_items,
        "avg_bill_value": round(total_revenue / len(bills), 2) if bills else 0,
        "daily_breakdown": daily_breakdown,
        "top_items": top_items,
        "currency": bills[0].get("currency", "EUR") if bills else "EUR"
    }

# Seed data on startup
@app.on_event("startup")
async def seed_data():
    # Seed modifiers
    mod_count = await db.modifiers.count_documents({})
    if mod_count == 0:
        for mod in DEFAULT_MODIFIERS:
            await db.modifiers.insert_one(mod)
        logging.info(f"Seeded {len(DEFAULT_MODIFIERS)} default modifiers")
    
    # Seed theme
    theme = await db.config.find_one({"id": "theme"})
    if not theme:
        theme_data = DEFAULT_THEME.copy()
        theme_data["id"] = "theme"
        await db.config.insert_one(theme_data)
        logging.info("Seeded default theme")

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
