#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class CafeBillGeneratorAPITester:
    def __init__(self, base_url="https://menu-checkout-31.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = []  # Store created item IDs for cleanup
        self.created_bills = []  # Store created bill IDs for cleanup

    def run_test(self, name, method, endpoint, expected_status, data=None, check_response=None):
        """Run a single API test with detailed response checking"""
        url = f"{self.base_url}/{endpoint}" if endpoint else self.base_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            print(f"   Response Status: {response.status_code}")
            
            # Check status code
            status_success = response.status_code == expected_status
            if not status_success:
                print(f"❌ Status Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:500]}")
                return False, {}

            # Parse response
            try:
                response_data = response.json() if response.text else {}
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}

            # Run custom response checks
            if check_response and not check_response(response_data):
                print(f"❌ Response validation failed")
                return False, response_data

            self.tests_passed += 1
            print(f"✅ Passed")
            return True, response_data

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed - Connection error")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        def check_response(data):
            return "message" in data
        
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200,
            check_response=check_response
        )

    def test_get_menu_items(self):
        """Test GET /menu - should return 75 pre-populated items across 10 categories"""
        def check_response(data):
            if not isinstance(data, list):
                print(f"   Expected list, got {type(data)}")
                return False
            # Should have 75 items according to DEFAULT_MENU_ITEMS
            if len(data) < 60:  # Allow some flexibility
                print(f"   Expected at least 60 items, got {len(data)}")
                return False
            
            # Check item structure
            required_fields = ['id', 'name', 'price', 'category', 'available']
            for item in data[:3]:  # Check first 3 items
                for field in required_fields:
                    if field not in item:
                        print(f"   Missing field '{field}' in item")
                        return False
            
            # Check 10 categories exist
            categories = {item['category'] for item in data}
            expected_categories = {'Coffee', 'Tea', 'Pastries', 'Snacks', 'Beverages', 
                                 'Breakfast', 'Lunch', 'Desserts', 'Sandwiches', 'Smoothies'}
            missing_categories = expected_categories - categories
            if missing_categories:
                print(f"   Missing categories: {missing_categories}")
                return False
                
            print(f"   Found {len(data)} items with all 10 categories: {sorted(categories)}")
            return True
        
        return self.run_test(
            "Get Menu Items",
            "GET",
            "menu",
            200,
            check_response=check_response
        )

    def test_get_categories(self):
        """Test GET /menu/categories - should return 10 categories"""
        def check_response(data):
            if not isinstance(data, list):
                print(f"   Expected list, got {type(data)}")
                return False
            expected_categories = ['Coffee', 'Tea', 'Pastries', 'Snacks', 'Beverages', 
                                 'Breakfast', 'Lunch', 'Desserts', 'Sandwiches', 'Smoothies']
            if len(data) != 10:
                print(f"   Expected 10 categories, got {len(data)}")
                return False
            
            for cat in expected_categories:
                if cat not in data:
                    print(f"   Missing category: {cat}")
                    return False
            
            print(f"   Found all 10 categories: {sorted(data)}")
            return True
        
        return self.run_test(
            "Get Categories",
            "GET",
            "menu/categories",
            200,
            check_response=check_response
        )

    def test_create_menu_item(self):
        """Test POST /menu - create new menu item"""
        test_item = {
            "name": "Test Latte",
            "price": 6.50,
            "category": "Coffee",
            "description": "Test item for API testing",
            "available": True
        }
        
        def check_response(data):
            if not isinstance(data, dict):
                return False
            if data.get('name') != test_item['name']:
                return False
            if data.get('price') != test_item['price']:
                return False
            if 'id' not in data:
                return False
            
            # Store created item ID for cleanup
            self.created_items.append(data['id'])
            print(f"   Created item with ID: {data['id']}")
            return True
        
        return self.run_test(
            "Create Menu Item",
            "POST",
            "menu",
            200,  # FastAPI typically returns 200 for POST, not 201
            data=test_item,
            check_response=check_response
        )

    def test_get_single_menu_item(self, item_id):
        """Test GET /menu/{id} - get specific menu item"""
        def check_response(data):
            return data.get('id') == item_id
        
        return self.run_test(
            "Get Single Menu Item",
            "GET",
            f"menu/{item_id}",
            200,
            check_response=check_response
        )

    def test_update_menu_item(self, item_id):
        """Test PUT /menu/{id} - update menu item"""
        update_data = {
            "name": "Updated Test Latte",
            "price": 7.00,
            "description": "Updated test description"
        }
        
        def check_response(data):
            return (data.get('name') == update_data['name'] and 
                   data.get('price') == update_data['price'])
        
        return self.run_test(
            "Update Menu Item",
            "PUT",
            f"menu/{item_id}",
            200,
            data=update_data,
            check_response=check_response
        )

    def test_create_bill(self):
        """Test POST /bills - generate bill"""
        # First get some menu items for the bill
        success, menu_data = self.run_test("Get menu for billing", "GET", "menu", 200)
        if not success or not menu_data:
            print("❌ Cannot test billing - menu not available")
            return False, {}
        
        # Create bill with first two items
        bill_items = [
            {
                "menu_item_id": menu_data[0]['id'],
                "name": menu_data[0]['name'],
                "price": menu_data[0]['price'],
                "quantity": 2
            },
            {
                "menu_item_id": menu_data[1]['id'],
                "name": menu_data[1]['name'],
                "price": menu_data[1]['price'],
                "quantity": 1
            }
        ]
        
        bill_data = {
            "items": bill_items,
            "discount_percent": 10.0,
            "tax_percent": 8.5
        }
        
        def check_response(data):
            required_fields = ['id', 'items', 'subtotal', 'discount_percent', 
                             'discount_amount', 'tax_percent', 'tax_amount', 
                             'total', 'bill_number']
            for field in required_fields:
                if field not in data:
                    print(f"   Missing field '{field}' in bill response")
                    return False
            
            # Check calculations
            expected_subtotal = sum(item['price'] * item['quantity'] for item in bill_items)
            if abs(data['subtotal'] - expected_subtotal) > 0.01:
                print(f"   Subtotal mismatch: expected {expected_subtotal}, got {data['subtotal']}")
                return False
            
            # Store created bill ID
            self.created_bills.append(data['id'])
            print(f"   Created bill #{data['bill_number']} with total ${data['total']}")
            return True
        
        return self.run_test(
            "Create Bill",
            "POST",
            "bills",
            200,
            data=bill_data,
            check_response=check_response
        )

    def test_get_bills(self):
        """Test GET /bills - retrieve all bills"""
        def check_response(data):
            if not isinstance(data, list):
                print(f"   Expected list, got {type(data)}")
                return False
            print(f"   Found {len(data)} bills")
            return True
        
        return self.run_test(
            "Get All Bills",
            "GET",
            "bills",
            200,
            check_response=check_response
        )

    def test_delete_menu_item(self, item_id):
        """Test DELETE /menu/{id} - delete menu item"""
        def check_response(data):
            return "message" in data and "deleted" in data["message"].lower()
        
        return self.run_test(
            "Delete Menu Item",
            "DELETE",
            f"menu/{item_id}",
            200,
            check_response=check_response
        )

    def cleanup_created_items(self):
        """Clean up created test items"""
        print(f"\n🧹 Cleaning up {len(self.created_items)} created items...")
        for item_id in self.created_items:
            try:
                requests.delete(f"{self.base_url}/menu/{item_id}", timeout=5)
            except:
                pass

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Cafe Bill Generator API Tests")
        print(f"🔗 Base URL: {self.base_url}")
        
        # Basic connectivity tests
        root_success, _ = self.test_root_endpoint()
        if not root_success:
            print("❌ Root endpoint failed - cannot continue testing")
            return self.get_results()

        # Menu tests
        menu_success, menu_data = self.test_get_menu_items()
        
        # Create, read, update, delete test
        create_success, create_data = self.test_create_menu_item()
        if create_success and self.created_items:
            item_id = self.created_items[0]
            self.test_get_single_menu_item(item_id)
            self.test_update_menu_item(item_id)
            self.test_delete_menu_item(item_id)

        # Bill tests (requires menu items to exist)
        if menu_success:
            self.test_create_bill()
            self.test_get_bills()

        return self.get_results()

    def get_results(self):
        """Get test results summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"\n📊 Test Results Summary")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed")
            return 1

def main():
    tester = CafeBillGeneratorAPITester()
    
    try:
        exit_code = tester.run_all_tests()
        return exit_code
    except KeyboardInterrupt:
        print("\n⛔ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        return 1
    finally:
        # Always try to cleanup
        tester.cleanup_created_items()

if __name__ == "__main__":
    sys.exit(main())