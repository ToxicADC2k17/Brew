"""
Test suite for JWT Authentication and Inventory Management features
Tests: Auth (login, register, logout), Suppliers, Inventory, Stock Adjustments, Transactions
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@cafebrew.com"
ADMIN_PASSWORD = "admin123"

class TestAuthentication:
    """Test JWT authentication flows"""
    
    def test_login_success(self):
        """Test login with valid admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert data["token_type"] == "bearer"
        print(f"SUCCESS: Admin login - token received, user role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        print(f"SUCCESS: Invalid credentials correctly rejected")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "somepassword"
        })
        assert response.status_code == 401
        print(f"SUCCESS: Non-existent user correctly rejected")
    
    def test_register_new_user(self):
        """Test user registration"""
        test_email = f"TEST_user_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "name": "Test User"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_email.lower()
        assert data["user"]["name"] == "Test User"
        print(f"SUCCESS: User registered - {test_email}")
        
        # Cleanup - delete test user (not implemented in API, so just note it)
    
    def test_register_duplicate_email(self):
        """Test registration with existing email"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "somepassword",
            "name": "Duplicate User"
        })
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()
        print(f"SUCCESS: Duplicate email registration correctly rejected")
    
    def test_auth_me_endpoint(self):
        """Test /auth/me with valid token"""
        # First login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Test /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"SUCCESS: /auth/me returns current user info")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without authorization"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
        print(f"SUCCESS: /auth/me correctly rejects unauthenticated requests")


class TestSuppliers:
    """Test supplier CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_suppliers(self):
        """Test fetching suppliers list"""
        response = requests.get(f"{BASE_URL}/api/suppliers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: GET /api/suppliers returns list ({len(response.json())} suppliers)")
    
    def test_create_supplier(self):
        """Test creating a new supplier"""
        supplier_data = {
            "name": f"TEST_Supplier_{uuid.uuid4().hex[:8]}",
            "contact_name": "John Doe",
            "email": "john@supplier.com",
            "phone": "+1234567890",
            "address": "123 Test St",
            "notes": "Test supplier"
        }
        response = requests.post(
            f"{BASE_URL}/api/suppliers",
            json=supplier_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        
        data = response.json()
        assert data["name"] == supplier_data["name"]
        assert "id" in data
        print(f"SUCCESS: Supplier created with ID: {data['id']}")
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/suppliers")
        suppliers = get_response.json()
        assert any(s["id"] == data["id"] for s in suppliers)
        print(f"SUCCESS: Supplier persisted and visible in list")
        
        # Cleanup
        delete_response = requests.delete(
            f"{BASE_URL}/api/suppliers/{data['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        print(f"SUCCESS: Test supplier cleaned up")
    
    def test_update_supplier(self):
        """Test updating a supplier"""
        # Create supplier first
        create_response = requests.post(
            f"{BASE_URL}/api/suppliers",
            json={"name": f"TEST_Update_{uuid.uuid4().hex[:8]}"},
            headers=self.headers
        )
        supplier_id = create_response.json()["id"]
        
        # Update
        update_response = requests.put(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            json={"name": "Updated Name", "phone": "999-999-9999"},
            headers=self.headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Name"
        print(f"SUCCESS: Supplier updated")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/suppliers/{supplier_id}", headers=self.headers)
    
    def test_delete_supplier(self):
        """Test deleting a supplier"""
        # Create supplier first
        create_response = requests.post(
            f"{BASE_URL}/api/suppliers",
            json={"name": f"TEST_Delete_{uuid.uuid4().hex[:8]}"},
            headers=self.headers
        )
        supplier_id = create_response.json()["id"]
        
        # Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/suppliers/{supplier_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        
        # Verify deleted
        suppliers = requests.get(f"{BASE_URL}/api/suppliers").json()
        assert not any(s["id"] == supplier_id for s in suppliers)
        print(f"SUCCESS: Supplier deleted and verified")


class TestInventory:
    """Test inventory management"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and menu items for tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get menu items
        menu_response = requests.get(f"{BASE_URL}/api/menu")
        self.menu_items = menu_response.json()
    
    def test_get_inventory(self):
        """Test fetching inventory list"""
        response = requests.get(f"{BASE_URL}/api/inventory")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: GET /api/inventory returns list ({len(response.json())} items)")
    
    def test_get_low_stock(self):
        """Test fetching low stock items"""
        response = requests.get(f"{BASE_URL}/api/inventory/low-stock")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: GET /api/inventory/low-stock returns {len(response.json())} items")
    
    def test_create_inventory_item(self):
        """Test creating inventory for a menu item"""
        # Get existing inventory to find an available menu item
        existing = requests.get(f"{BASE_URL}/api/inventory").json()
        existing_menu_ids = [i["menu_item_id"] for i in existing]
        
        # Find a menu item not in inventory
        available_items = [m for m in self.menu_items if m["id"] not in existing_menu_ids]
        
        if not available_items:
            # Create a test menu item
            menu_response = requests.post(
                f"{BASE_URL}/api/menu",
                json={
                    "name": f"TEST_MenuItem_{uuid.uuid4().hex[:8]}",
                    "price": 5.99,
                    "category": "Coffee"
                }
            )
            menu_item = menu_response.json()
        else:
            menu_item = available_items[0]
        
        # Create inventory
        inventory_data = {
            "menu_item_id": menu_item["id"],
            "current_stock": 50,
            "min_stock_level": 10,
            "max_stock_level": 100,
            "cost_price": 2.50,
            "unit": "units"
        }
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json=inventory_data,
            headers=self.headers
        )
        
        # May return 400 if already exists
        if response.status_code == 400:
            print(f"INFO: Inventory already exists for this menu item")
            return
        
        assert response.status_code == 200, f"Create inventory failed: {response.text}"
        data = response.json()
        assert data["current_stock"] == 50
        assert data["menu_item_name"] == menu_item["name"]
        print(f"SUCCESS: Inventory item created for {menu_item['name']}")
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/inventory/{data['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["current_stock"] == 50
        print(f"SUCCESS: Inventory item persisted")
    
    def test_create_duplicate_inventory(self):
        """Test that duplicate inventory for same menu item is rejected"""
        # Get existing inventory
        existing = requests.get(f"{BASE_URL}/api/inventory").json()
        
        if not existing:
            pytest.skip("No existing inventory to test duplicate check")
        
        # Try to create duplicate
        response = requests.post(
            f"{BASE_URL}/api/inventory",
            json={
                "menu_item_id": existing[0]["menu_item_id"],
                "current_stock": 10
            },
            headers=self.headers
        )
        assert response.status_code == 400
        print(f"SUCCESS: Duplicate inventory creation correctly rejected")


class TestStockAdjustment:
    """Test stock adjustment functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and inventory for tests"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get inventory
        inv_response = requests.get(f"{BASE_URL}/api/inventory")
        self.inventory = inv_response.json()
    
    def test_restock_adjustment(self):
        """Test restock operation"""
        if not self.inventory:
            pytest.skip("No inventory items to test restock")
        
        inv_item = self.inventory[0]
        original_stock = inv_item["current_stock"]
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/{inv_item['id']}/adjust",
            json={
                "quantity": 10,
                "transaction_type": "restock",
                "notes": "Test restock"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"Restock failed: {response.text}"
        
        data = response.json()
        assert data["inventory"]["current_stock"] == original_stock + 10
        assert data["transaction"]["transaction_type"] == "restock"
        print(f"SUCCESS: Restock - {original_stock} -> {original_stock + 10}")
    
    def test_waste_adjustment(self):
        """Test waste (remove) operation"""
        if not self.inventory:
            pytest.skip("No inventory items to test waste")
        
        # Refresh inventory to get current stock
        inv_response = requests.get(f"{BASE_URL}/api/inventory")
        inventory = inv_response.json()
        inv_item = inventory[0]
        original_stock = inv_item["current_stock"]
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/{inv_item['id']}/adjust",
            json={
                "quantity": 5,
                "transaction_type": "waste",
                "notes": "Test waste"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["inventory"]["current_stock"] == max(0, original_stock - 5)
        assert data["transaction"]["transaction_type"] == "waste"
        print(f"SUCCESS: Waste - {original_stock} -> {data['inventory']['current_stock']}")
    
    def test_exact_adjustment(self):
        """Test setting exact stock amount"""
        if not self.inventory:
            pytest.skip("No inventory items to test adjustment")
        
        # Refresh inventory
        inv_response = requests.get(f"{BASE_URL}/api/inventory")
        inventory = inv_response.json()
        inv_item = inventory[0]
        
        response = requests.post(
            f"{BASE_URL}/api/inventory/{inv_item['id']}/adjust",
            json={
                "quantity": 25,
                "transaction_type": "adjustment",
                "notes": "Set exact amount"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["inventory"]["current_stock"] == 25
        print(f"SUCCESS: Adjustment - set to exact 25 units")


class TestStockTransactions:
    """Test stock transaction history"""
    
    def test_get_all_transactions(self):
        """Test fetching all transactions"""
        response = requests.get(f"{BASE_URL}/api/stock-transactions?limit=50")
        assert response.status_code == 200
        transactions = response.json()
        assert isinstance(transactions, list)
        print(f"SUCCESS: GET /api/stock-transactions returns {len(transactions)} transactions")
    
    def test_get_item_history(self):
        """Test fetching transaction history for specific item"""
        # Get inventory
        inv_response = requests.get(f"{BASE_URL}/api/inventory")
        inventory = inv_response.json()
        
        if not inventory:
            pytest.skip("No inventory to get history for")
        
        response = requests.get(f"{BASE_URL}/api/inventory/{inventory[0]['id']}/history")
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        print(f"SUCCESS: Item history returns {len(history)} transactions")


class TestBillingIntegration:
    """Verify existing billing functionality still works after auth changes"""
    
    def test_create_bill(self):
        """Test bill creation still works"""
        # Get menu items
        menu_response = requests.get(f"{BASE_URL}/api/menu")
        menu_items = menu_response.json()
        
        if not menu_items:
            pytest.skip("No menu items for billing test")
        
        # Create a bill
        bill_data = {
            "items": [{
                "menu_item_id": menu_items[0]["id"],
                "name": menu_items[0]["name"],
                "price": menu_items[0]["price"],
                "quantity": 2,
                "modifiers": []
            }],
            "discount_percent": 0,
            "tax_percent": 5.0,
            "customer_name": "TEST_Customer",
            "table_number": "T1",
            "currency": "EUR"
        }
        
        response = requests.post(f"{BASE_URL}/api/bills", json=bill_data)
        assert response.status_code == 200, f"Bill creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["customer_name"] == "TEST_Customer"
        assert data["total"] > 0
        print(f"SUCCESS: Bill created - Total: €{data['total']}")
    
    def test_get_bills(self):
        """Test fetching bills"""
        response = requests.get(f"{BASE_URL}/api/bills")
        assert response.status_code == 200
        bills = response.json()
        assert isinstance(bills, list)
        print(f"SUCCESS: GET /api/bills returns {len(bills)} bills")
    
    def test_menu_operations(self):
        """Test menu CRUD still works"""
        # Get categories
        cat_response = requests.get(f"{BASE_URL}/api/menu/categories")
        assert cat_response.status_code == 200
        categories = cat_response.json()
        assert len(categories) >= 10
        print(f"SUCCESS: {len(categories)} categories available")
        
        # Get menu items
        menu_response = requests.get(f"{BASE_URL}/api/menu")
        assert menu_response.status_code == 200
        print(f"SUCCESS: Menu items fetched ({len(menu_response.json())} items)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
