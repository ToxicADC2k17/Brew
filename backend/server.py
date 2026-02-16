from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
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

class DailySalesReport(BaseModel):
    date: str
    total_bills: int
    total_revenue: float
    total_items_sold: int
    avg_bill_value: float
    top_items: List[dict]
    currency: str

# Default menu items - Extended with more categories
DEFAULT_MENU_ITEMS = [
    # Coffee
    {"name": "Espresso", "price": 2.50, "category": "Coffee", "description": "Rich & bold single shot"},
    {"name": "Americano", "price": 3.00, "category": "Coffee", "description": "Espresso with hot water"},
    {"name": "Cappuccino", "price": 3.50, "category": "Coffee", "description": "Espresso with steamed milk foam"},
    {"name": "Latte", "price": 4.00, "category": "Coffee", "description": "Espresso with creamy steamed milk"},
    {"name": "Mocha", "price": 4.50, "category": "Coffee", "description": "Espresso with chocolate & milk"},
    {"name": "Cold Brew", "price": 3.50, "category": "Coffee", "description": "Slow-steeped, smooth & refreshing"},
    {"name": "Flat White", "price": 3.80, "category": "Coffee", "description": "Double espresso with velvety milk"},
    {"name": "Macchiato", "price": 3.00, "category": "Coffee", "description": "Espresso with a dash of foam"},
    # Tea
    {"name": "Green Tea", "price": 2.50, "category": "Tea", "description": "Classic Japanese green tea"},
    {"name": "Earl Grey", "price": 2.50, "category": "Tea", "description": "Black tea with bergamot"},
    {"name": "Chai Latte", "price": 3.80, "category": "Tea", "description": "Spiced tea with steamed milk"},
    {"name": "Matcha Latte", "price": 4.50, "category": "Tea", "description": "Premium matcha with milk"},
    {"name": "Chamomile", "price": 2.50, "category": "Tea", "description": "Calming herbal infusion"},
    {"name": "English Breakfast", "price": 2.50, "category": "Tea", "description": "Classic strong black tea"},
    # Pastries
    {"name": "Croissant", "price": 2.80, "category": "Pastries", "description": "Buttery, flaky French classic"},
    {"name": "Chocolate Muffin", "price": 2.50, "category": "Pastries", "description": "Rich chocolate chip muffin"},
    {"name": "Blueberry Scone", "price": 2.80, "category": "Pastries", "description": "Fresh blueberry scone"},
    {"name": "Cinnamon Roll", "price": 3.20, "category": "Pastries", "description": "Warm cinnamon swirl"},
    {"name": "Pain au Chocolat", "price": 3.00, "category": "Pastries", "description": "Chocolate-filled croissant"},
    {"name": "Pastel de Nata", "price": 1.80, "category": "Pastries", "description": "Portuguese custard tart"},
    {"name": "Almond Croissant", "price": 3.50, "category": "Pastries", "description": "Croissant with almond cream"},
    # Breakfast
    {"name": "Avocado Toast", "price": 7.50, "category": "Breakfast", "description": "Smashed avocado on sourdough"},
    {"name": "Eggs Benedict", "price": 9.50, "category": "Breakfast", "description": "Poached eggs with hollandaise"},
    {"name": "Pancakes", "price": 8.00, "category": "Breakfast", "description": "Fluffy pancakes with maple syrup"},
    {"name": "Granola Bowl", "price": 6.50, "category": "Breakfast", "description": "Yogurt with granola & fresh fruit"},
    {"name": "French Toast", "price": 7.50, "category": "Breakfast", "description": "Brioche with berries & cream"},
    {"name": "Full English", "price": 12.00, "category": "Breakfast", "description": "Eggs, bacon, sausage, beans, toast"},
    # Lunch
    {"name": "Caesar Salad", "price": 9.00, "category": "Lunch", "description": "Crisp romaine with Caesar dressing"},
    {"name": "Soup of the Day", "price": 5.50, "category": "Lunch", "description": "Fresh homemade soup with bread"},
    {"name": "Quiche Lorraine", "price": 7.50, "category": "Lunch", "description": "Classic French quiche with salad"},
    {"name": "Poke Bowl", "price": 11.00, "category": "Lunch", "description": "Fresh salmon with rice & veggies"},
    {"name": "Pasta Salad", "price": 8.50, "category": "Lunch", "description": "Mediterranean pasta with feta"},
    # Sandwiches
    {"name": "Grilled Cheese", "price": 5.50, "category": "Sandwiches", "description": "Classic melted cheese sandwich"},
    {"name": "Club Sandwich", "price": 8.50, "category": "Sandwiches", "description": "Triple-decker with chicken & bacon"},
    {"name": "BLT", "price": 7.00, "category": "Sandwiches", "description": "Bacon, lettuce, tomato on toast"},
    {"name": "Tuna Melt", "price": 7.50, "category": "Sandwiches", "description": "Tuna salad with melted cheese"},
    {"name": "Veggie Wrap", "price": 7.00, "category": "Sandwiches", "description": "Grilled vegetables in tortilla"},
    {"name": "Ham & Cheese", "price": 6.00, "category": "Sandwiches", "description": "Classic ham & cheese toastie"},
    # Snacks
    {"name": "Chips & Guac", "price": 5.50, "category": "Snacks", "description": "Tortilla chips with guacamole"},
    {"name": "Cheese Board", "price": 12.00, "category": "Snacks", "description": "Selection of artisan cheeses"},
    {"name": "Bruschetta", "price": 6.00, "category": "Snacks", "description": "Tomato & basil on toasted bread"},
    {"name": "Mixed Nuts", "price": 4.00, "category": "Snacks", "description": "Roasted salted mixed nuts"},
    # Desserts
    {"name": "Cheesecake", "price": 5.50, "category": "Desserts", "description": "New York style cheesecake"},
    {"name": "Chocolate Cake", "price": 5.00, "category": "Desserts", "description": "Rich dark chocolate layer cake"},
    {"name": "Tiramisu", "price": 6.00, "category": "Desserts", "description": "Classic Italian coffee dessert"},
    {"name": "Apple Pie", "price": 5.00, "category": "Desserts", "description": "Warm apple pie with cream"},
    {"name": "Ice Cream", "price": 4.00, "category": "Desserts", "description": "Two scoops, choice of flavors"},
    {"name": "Brownie", "price": 4.50, "category": "Desserts", "description": "Warm chocolate brownie"},
    # Beverages
    {"name": "Orange Juice", "price": 3.50, "category": "Beverages", "description": "Fresh squeezed orange juice"},
    {"name": "Lemonade", "price": 3.00, "category": "Beverages", "description": "House-made lemonade"},
    {"name": "Sparkling Water", "price": 2.00, "category": "Beverages", "description": "Refreshing sparkling water"},
    {"name": "Still Water", "price": 1.50, "category": "Beverages", "description": "Premium still water"},
    {"name": "Apple Juice", "price": 3.00, "category": "Beverages", "description": "Fresh pressed apple juice"},
    {"name": "Hot Chocolate", "price": 3.50, "category": "Beverages", "description": "Rich Belgian hot chocolate"},
    # Smoothies
    {"name": "Berry Blast", "price": 5.50, "category": "Smoothies", "description": "Mixed berries with yogurt"},
    {"name": "Tropical Paradise", "price": 5.50, "category": "Smoothies", "description": "Mango, pineapple & coconut"},
    {"name": "Green Machine", "price": 6.00, "category": "Smoothies", "description": "Spinach, banana & apple"},
    {"name": "Banana Protein", "price": 6.50, "category": "Smoothies", "description": "Banana, peanut butter & protein"},
    {"name": "Açaí Bowl", "price": 8.00, "category": "Smoothies", "description": "Açaí blend with toppings"},
]

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
    
    # Count item sales
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
    
    # Daily breakdown
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

# Seed menu on startup
@app.on_event("startup")
async def seed_menu():
    count = await db.menu_items.count_documents({})
    if count == 0:
        for item_data in DEFAULT_MENU_ITEMS:
            menu_item = MenuItem(**item_data)
            await db.menu_items.insert_one(menu_item.model_dump())
        logging.info(f"Seeded {len(DEFAULT_MENU_ITEMS)} default menu items")

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
