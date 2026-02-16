from fastapi import FastAPI, APIRouter, HTTPException, Query, UploadFile, File, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
import shutil
from passlib.context import CryptContext
from jose import JWTError, jwt

ROOT_DIR = Path(__file__).parent
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'cafe-brew-house-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

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

# User Models
class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"

class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: UserRole = UserRole.STAFF

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole = UserRole.STAFF
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Inventory Models
class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SupplierCreate(BaseModel):
    name: str
    contact_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    notes: Optional[str] = ""

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    menu_item_id: str
    menu_item_name: str
    current_stock: int = 0
    min_stock_level: int = 10  # Reorder alert threshold
    max_stock_level: int = 100
    cost_price: float = 0.0
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = ""
    unit: str = "units"  # units, kg, liters, etc.
    last_restocked: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class InventoryCreate(BaseModel):
    menu_item_id: str
    current_stock: int = 0
    min_stock_level: int = 10
    max_stock_level: int = 100
    cost_price: float = 0.0
    supplier_id: Optional[str] = None
    unit: str = "units"

class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    cost_price: Optional[float] = None
    supplier_id: Optional[str] = None
    unit: Optional[str] = None

class StockTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inventory_id: str
    menu_item_name: str
    transaction_type: str  # "restock", "sale", "adjustment", "waste"
    quantity: int
    previous_stock: int
    new_stock: int
    cost_per_unit: Optional[float] = None
    total_cost: Optional[float] = None
    notes: Optional[str] = ""
    created_by: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class StockAdjustment(BaseModel):
    quantity: int
    transaction_type: str  # "restock", "adjustment", "waste"
    notes: Optional[str] = ""

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

# Auth Helper Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(allowed_roles: List[UserRole]):
    async def role_checker(current_user: dict = Depends(get_current_active_user)):
        if current_user.get("role") not in [r.value for r in allowed_roles]:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return role_checker

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if email already exists
    existing = await db.users.find_one({"email": user_data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email.lower(),
        name=user_data.name,
        role=user_data.role
    )
    hashed_password = get_password_hash(user_data.password)
    
    user_doc = user.model_dump()
    user_doc["hashed_password"] = hashed_password
    await db.users.insert_one(user_doc)
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    return Token(
        access_token=access_token,
        user={"id": user.id, "email": user.email, "name": user.name, "role": user.role.value}
    )

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email.lower()})
    if not user or not verify_password(credentials.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    access_token = create_access_token(data={"sub": user["id"]})
    return Token(
        access_token=access_token,
        user={"id": user["id"], "email": user["email"], "name": user["name"], "role": user["role"]}
    )

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_active_user)):
    return current_user

@api_router.get("/auth/users")
async def get_users(current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(100)
    return users

@api_router.put("/auth/users/{user_id}/deactivate")
async def deactivate_user(user_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deactivated"}

# Supplier Routes
@api_router.get("/suppliers")
async def get_suppliers():
    suppliers = await db.suppliers.find({}, {"_id": 0}).to_list(100)
    return suppliers

@api_router.post("/suppliers")
async def create_supplier(supplier: SupplierCreate):
    sup = Supplier(**supplier.model_dump())
    await db.suppliers.insert_one(sup.model_dump())
    return sup

@api_router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, update: SupplierCreate):
    result = await db.suppliers.update_one(
        {"id": supplier_id},
        {"$set": update.model_dump()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    updated = await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})
    return updated

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str):
    result = await db.suppliers.delete_one({"id": supplier_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted"}

# Inventory Routes
@api_router.get("/inventory")
async def get_inventory():
    inventory = await db.inventory.find({}, {"_id": 0}).to_list(1000)
    return inventory

@api_router.get("/inventory/low-stock")
async def get_low_stock():
    # Find items where current_stock <= min_stock_level
    pipeline = [
        {"$match": {"$expr": {"$lte": ["$current_stock", "$min_stock_level"]}}},
        {"$project": {"_id": 0}}
    ]
    low_stock = await db.inventory.aggregate(pipeline).to_list(100)
    return low_stock

@api_router.get("/inventory/{inventory_id}")
async def get_inventory_item(inventory_id: str):
    item = await db.inventory.find_one({"id": inventory_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item

@api_router.post("/inventory")
async def create_inventory_item(inv: InventoryCreate):
    # Check if menu item exists
    menu_item = await db.menu_items.find_one({"id": inv.menu_item_id})
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    # Check if inventory already exists for this menu item
    existing = await db.inventory.find_one({"menu_item_id": inv.menu_item_id})
    if existing:
        raise HTTPException(status_code=400, detail="Inventory already exists for this menu item")
    
    # Get supplier name if provided
    supplier_name = ""
    if inv.supplier_id:
        supplier = await db.suppliers.find_one({"id": inv.supplier_id})
        supplier_name = supplier["name"] if supplier else ""
    
    inventory_item = InventoryItem(
        menu_item_id=inv.menu_item_id,
        menu_item_name=menu_item["name"],
        current_stock=inv.current_stock,
        min_stock_level=inv.min_stock_level,
        max_stock_level=inv.max_stock_level,
        cost_price=inv.cost_price,
        supplier_id=inv.supplier_id,
        supplier_name=supplier_name,
        unit=inv.unit
    )
    await db.inventory.insert_one(inventory_item.model_dump())
    return inventory_item

@api_router.put("/inventory/{inventory_id}")
async def update_inventory_item(inventory_id: str, update: InventoryUpdate):
    existing = await db.inventory.find_one({"id": inventory_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    # Update supplier name if supplier_id changed
    if "supplier_id" in update_data and update_data["supplier_id"]:
        supplier = await db.suppliers.find_one({"id": update_data["supplier_id"]})
        update_data["supplier_name"] = supplier["name"] if supplier else ""
    
    if update_data:
        await db.inventory.update_one({"id": inventory_id}, {"$set": update_data})
    
    updated = await db.inventory.find_one({"id": inventory_id}, {"_id": 0})
    return updated

@api_router.delete("/inventory/{inventory_id}")
async def delete_inventory_item(inventory_id: str):
    result = await db.inventory.delete_one({"id": inventory_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Inventory item deleted"}

@api_router.post("/inventory/{inventory_id}/adjust")
async def adjust_stock(inventory_id: str, adjustment: StockAdjustment, current_user: dict = Depends(get_current_active_user)):
    inventory = await db.inventory.find_one({"id": inventory_id})
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    previous_stock = inventory["current_stock"]
    
    if adjustment.transaction_type == "restock":
        new_stock = previous_stock + adjustment.quantity
    elif adjustment.transaction_type == "waste":
        new_stock = max(0, previous_stock - adjustment.quantity)
    else:  # adjustment
        new_stock = max(0, adjustment.quantity)
    
    # Create transaction record
    transaction = StockTransaction(
        inventory_id=inventory_id,
        menu_item_name=inventory["menu_item_name"],
        transaction_type=adjustment.transaction_type,
        quantity=adjustment.quantity,
        previous_stock=previous_stock,
        new_stock=new_stock,
        cost_per_unit=inventory.get("cost_price", 0),
        total_cost=adjustment.quantity * inventory.get("cost_price", 0) if adjustment.transaction_type == "restock" else None,
        notes=adjustment.notes,
        created_by=current_user.get("name", "")
    )
    await db.stock_transactions.insert_one(transaction.model_dump())
    
    # Update inventory
    update_data = {"current_stock": new_stock}
    if adjustment.transaction_type == "restock":
        update_data["last_restocked"] = datetime.now(timezone.utc).isoformat()
    
    await db.inventory.update_one({"id": inventory_id}, {"$set": update_data})
    
    updated = await db.inventory.find_one({"id": inventory_id}, {"_id": 0})
    return {"inventory": updated, "transaction": transaction.model_dump()}

@api_router.get("/inventory/{inventory_id}/history")
async def get_stock_history(inventory_id: str, limit: int = Query(50, le=200)):
    transactions = await db.stock_transactions.find(
        {"inventory_id": inventory_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    return transactions

@api_router.get("/stock-transactions")
async def get_all_transactions(limit: int = Query(100, le=500)):
    transactions = await db.stock_transactions.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return transactions

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

# Image Upload Route
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@api_router.post("/upload/image")
async def upload_image(file: UploadFile = File(...)):
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Read and check file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB")
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Return the URL path
    return {
        "filename": unique_filename,
        "url": f"/api/uploads/{unique_filename}"
    }

@api_router.get("/")
async def root():
    return {"message": "Cafe Bill Generator API"}

app.include_router(api_router)

# Mount static files for uploaded images
app.mount("/api/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

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
