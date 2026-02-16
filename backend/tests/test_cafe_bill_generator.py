"""
Comprehensive test suite for Cafe Bill Generator API
Tests: Menu, Categories, Bills, Modifiers, Theme configuration, and Sales Reports
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMenuCategories:
    """Test all 23 menu categories are properly configured"""
    
    def test_categories_returns_all_23_categories(self):
        """Verify all 23 categories including Pizza, Pasta, Burgers are present"""
        response = requests.get(f"{BASE_URL}/api/menu/categories")
        assert response.status_code == 200
        
        categories = response.json()
        expected_categories = [
            "Coffee", "Tea", "Pastries", "Snacks", "Beverages",
            "Breakfast", "Lunch", "Desserts", "Sandwiches", "Smoothies",
            "Starters", "Mains", "Steaks", "Seafood", "Vegetarian",
            "Salads", "Sides", "Soups", "Beers", "Wines",
            "Pizza", "Pasta", "Burgers"
        ]
        
        assert len(categories) == 23, f"Expected 23 categories, got {len(categories)}"
        
        for expected in expected_categories:
            assert expected in categories, f"Category '{expected}' not found in response"
        
        print(f"✓ All 23 categories verified: {categories}")


class TestMenuAPI:
    """Test Menu CRUD operations"""
    
    def test_get_menu_items(self):
        """Get all menu items"""
        response = requests.get(f"{BASE_URL}/api/menu")
        assert response.status_code == 200
        
        items = response.json()
        assert isinstance(items, list)
        print(f"✓ Got {len(items)} menu items")
    
    def test_create_menu_item_with_pizza_category(self):
        """Create a menu item with Pizza category"""
        payload = {
            "name": "TEST_Margherita Pizza",
            "price": 12.99,
            "category": "Pizza",
            "description": "Classic margherita with fresh basil",
            "available": True
        }
        response = requests.post(f"{BASE_URL}/api/menu", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["category"] == "Pizza"
        assert data["price"] == 12.99
        assert "id" in data
        
        # Cleanup
        item_id = data["id"]
        requests.delete(f"{BASE_URL}/api/menu/{item_id}")
        print(f"✓ Created and cleaned up Pizza item: {data['name']}")
    
    def test_create_menu_item_with_pasta_category(self):
        """Create a menu item with Pasta category"""
        payload = {
            "name": "TEST_Spaghetti Carbonara",
            "price": 14.50,
            "category": "Pasta",
            "description": "Creamy pasta with bacon",
            "available": True
        }
        response = requests.post(f"{BASE_URL}/api/menu", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["category"] == "Pasta"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/menu/{data['id']}")
        print(f"✓ Created and cleaned up Pasta item")
    
    def test_create_menu_item_with_burgers_category(self):
        """Create a menu item with Burgers category"""
        payload = {
            "name": "TEST_Classic Cheeseburger",
            "price": 11.99,
            "category": "Burgers",
            "description": "Angus beef with cheddar",
            "available": True
        }
        response = requests.post(f"{BASE_URL}/api/menu", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["category"] == "Burgers"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/menu/{data['id']}")
        print(f"✓ Created and cleaned up Burgers item")


class TestThemeConfiguration:
    """Test dynamic theme functionality"""
    
    def test_get_current_theme(self):
        """Get the current theme configuration"""
        response = requests.get(f"{BASE_URL}/api/config/theme")
        assert response.status_code == 200
        
        theme = response.json()
        assert "primary_color" in theme
        assert "accent_color" in theme
        assert "background_color" in theme
        assert "card_color" in theme
        assert "text_color" in theme
        assert "muted_color" in theme
        assert "border_color" in theme
        
        print(f"✓ Current theme: {theme.get('name', 'Unknown')} - Primary: {theme['primary_color']}")
    
    def test_update_theme(self):
        """Update theme and verify it's saved"""
        # First, get current theme to restore later
        original_response = requests.get(f"{BASE_URL}/api/config/theme")
        original_theme = original_response.json()
        
        # Update to a new theme
        new_theme = {
            "id": "default",
            "name": "TEST_Ocean Blue Theme",
            "primary_color": "#1E3A5F",
            "accent_color": "#0EA5E9",
            "background_color": "#F0F9FF",
            "card_color": "#FFFFFF",
            "text_color": "#1E3A5F",
            "muted_color": "#64748B",
            "border_color": "#E2E8F0",
            "success_color": "#3F6212",
            "error_color": "#991B1B"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/config/theme", json=new_theme)
        assert update_response.status_code == 200
        
        # Verify the theme was updated
        verify_response = requests.get(f"{BASE_URL}/api/config/theme")
        assert verify_response.status_code == 200
        updated_theme = verify_response.json()
        assert updated_theme["primary_color"] == "#1E3A5F"
        assert updated_theme["name"] == "TEST_Ocean Blue Theme"
        
        # Restore original theme
        requests.put(f"{BASE_URL}/api/config/theme", json=original_theme)
        print(f"✓ Theme update and restore successful")
    
    def test_reset_theme(self):
        """Test theme reset to default"""
        response = requests.post(f"{BASE_URL}/api/config/theme/reset")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Espresso & Crema"
        assert data["primary_color"] == "#2C1A1D"
        print(f"✓ Theme reset to default: {data['name']}")


class TestBillGeneration:
    """Test bill creation with customer details and modifiers"""
    
    def test_create_bill_with_customer_details(self):
        """Create a bill with customer name, table, and NIF"""
        payload = {
            "items": [
                {
                    "menu_item_id": "test-item-1",
                    "name": "Espresso",
                    "price": 2.50,
                    "quantity": 2,
                    "modifiers": []
                },
                {
                    "menu_item_id": "test-item-2",
                    "name": "Croissant",
                    "price": 3.00,
                    "quantity": 1,
                    "modifiers": []
                }
            ],
            "discount_percent": 10,
            "tax_percent": 23,
            "customer_name": "TEST_João Silva",
            "table_number": "T5",
            "nif": "123456789",
            "currency": "EUR"
        }
        
        response = requests.post(f"{BASE_URL}/api/bills", json=payload)
        assert response.status_code == 200
        
        bill = response.json()
        assert bill["customer_name"] == "TEST_João Silva"
        assert bill["table_number"] == "T5"
        assert bill["nif"] == "123456789"
        assert bill["currency"] == "EUR"
        assert "bill_number" in bill
        assert bill["subtotal"] == 8.00  # (2*2.50 + 3.00)
        assert bill["discount_percent"] == 10
        
        print(f"✓ Bill #{bill['bill_number']} created with total: €{bill['total']}")
    
    def test_create_bill_with_modifiers(self):
        """Create a bill with item modifiers"""
        payload = {
            "items": [
                {
                    "menu_item_id": "test-item-3",
                    "name": "Cappuccino",
                    "price": 3.50,
                    "quantity": 1,
                    "modifiers": [
                        {
                            "modifier_name": "Milk Option",
                            "option_name": "Oat Milk",
                            "price_adjustment": 0.50
                        },
                        {
                            "modifier_name": "Size",
                            "option_name": "Large",
                            "price_adjustment": 1.50
                        }
                    ]
                }
            ],
            "discount_percent": 0,
            "tax_percent": 23,
            "customer_name": "",
            "table_number": "",
            "nif": "",
            "currency": "EUR"
        }
        
        response = requests.post(f"{BASE_URL}/api/bills", json=payload)
        assert response.status_code == 200
        
        bill = response.json()
        # Subtotal should be 3.50 + 0.50 + 1.50 = 5.50
        assert bill["subtotal"] == 5.50
        print(f"✓ Bill with modifiers created, subtotal: €{bill['subtotal']}")
    
    def test_create_bill_with_different_currency(self):
        """Create a bill with USD currency"""
        payload = {
            "items": [
                {
                    "menu_item_id": "test-item-4",
                    "name": "Latte",
                    "price": 4.00,
                    "quantity": 1,
                    "modifiers": []
                }
            ],
            "discount_percent": 0,
            "tax_percent": 10,
            "customer_name": "",
            "table_number": "",
            "nif": "",
            "currency": "USD"
        }
        
        response = requests.post(f"{BASE_URL}/api/bills", json=payload)
        assert response.status_code == 200
        
        bill = response.json()
        assert bill["currency"] == "USD"
        print(f"✓ Bill created with USD currency")


class TestBillHistory:
    """Test bill retrieval and filtering"""
    
    def test_get_all_bills(self):
        """Get all bills"""
        response = requests.get(f"{BASE_URL}/api/bills")
        assert response.status_code == 200
        
        bills = response.json()
        assert isinstance(bills, list)
        print(f"✓ Got {len(bills)} bills from history")
    
    def test_search_bills_by_customer(self):
        """Search bills by customer name"""
        response = requests.get(f"{BASE_URL}/api/bills?search=TEST_João")
        assert response.status_code == 200
        
        bills = response.json()
        print(f"✓ Search returned {len(bills)} bills")


class TestModifiers:
    """Test modifier API"""
    
    def test_get_modifiers(self):
        """Get all modifiers"""
        response = requests.get(f"{BASE_URL}/api/modifiers")
        assert response.status_code == 200
        
        modifiers = response.json()
        assert isinstance(modifiers, list)
        
        # Check for expected default modifiers
        modifier_names = [m["name"] for m in modifiers]
        expected_modifiers = ["Size", "Cooking Preference", "Milk Option", "Extras"]
        
        for expected in expected_modifiers:
            assert expected in modifier_names, f"Modifier '{expected}' not found"
        
        print(f"✓ Got {len(modifiers)} modifiers")


class TestSalesReports:
    """Test sales report endpoints"""
    
    def test_daily_report(self):
        """Get daily sales report"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/reports/daily?date={today}")
        assert response.status_code == 200
        
        report = response.json()
        assert "total_bills" in report
        assert "total_revenue" in report
        assert "total_items_sold" in report
        assert "avg_bill_value" in report
        assert "top_items" in report
        
        print(f"✓ Daily report for {today}: {report['total_bills']} bills, €{report['total_revenue']} revenue")
    
    def test_range_report(self):
        """Get date range sales report"""
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/reports/range?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        
        report = response.json()
        assert "total_bills" in report
        assert "total_revenue" in report
        assert "daily_breakdown" in report
        assert "top_items" in report
        
        print(f"✓ Range report ({start_date} to {end_date}): {report['total_bills']} bills")


class TestAPIRoot:
    """Test API root endpoint"""
    
    def test_api_root(self):
        """Test API root returns proper message"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print(f"✓ API root: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
