# Cafe Brew House - Bill Generator Software

## Original Problem Statement
Build a bill generator software for a cafe with:
- Menu item management (add/edit/delete items)
- Bill generation with tax/discount calculations
- Customer details (Name, Table #, NIF - Portuguese Tax ID)
- Currency selector
- Print/download bill functionality
- Bill history and sales reports
- Item modifiers (size, cooking preference, extras)
- Dynamic theme customization (color scheme configuration)
- Menu items scraped from restaurant websites

## Target User
Portuguese cafe/restaurant owners needing a modern billing system with tax compliance (IVA/NIF support).

## Core Requirements
1. **Menu Management**: CRUD operations for menu items with categories, prices, descriptions, images
2. **Billing**: Create bills with subtotals, tax, discounts, and customer details
3. **Modifiers**: Support for item customization (sizes, extras, preferences)
4. **Reports**: Daily/weekly sales analytics with CSV export
5. **Theme System**: Customizable color schemes with preset themes

---

## What's Been Implemented

### Date: 2024-02-16

#### Backend (FastAPI + MongoDB)
- Complete CRUD APIs for menu items, bills, modifiers, themes
- 23 menu categories: Coffee, Tea, Pastries, Snacks, Beverages, Breakfast, Lunch, Desserts, Sandwiches, Smoothies, Starters, Mains, Steaks, Seafood, Vegetarian, Salads, Sides, Soups, Beers, Wines, **Pizza, Pasta, Burgers**
- 335+ menu items scraped from 7+ restaurant websites
- Dynamic theme storage and retrieval API
- Sales reports with daily/range queries

#### Frontend (React + TailwindCSS + Shadcn/UI)
- Dashboard with menu display and bill creation
- Category filtering with all 23 categories
- Item modifier dialogs for customizable items
- Customer details input (Name, Table #, NIF)
- Currency selector (EUR, USD, GBP, BRL, CHF)
- Bill history page with search and filters
- Sales reports page with analytics
- **Dynamic theme system** - CSS variables loaded from backend on app init
- 8 preset themes (Espresso & Crema, Ocean Blue, Forest Green, Royal Purple, Sunset Orange, Midnight Dark, Rose Gold, Slate Modern)

#### Key Files
- `/app/backend/server.py` - All backend logic
- `/app/frontend/src/App.js` - Theme loading on init
- `/app/frontend/src/App.css` - CSS theme variables
- `/app/frontend/src/pages/Dashboard.jsx` - Main billing UI
- `/app/frontend/src/pages/Settings.jsx` - Theme customization

---

## Prioritized Backlog

### P0 (Completed)
- [x] Core billing functionality
- [x] Menu management CRUD
- [x] Bill history and reports
- [x] Item modifiers system
- [x] Dynamic theme customization
- [x] All 23 categories (including Pizza, Pasta, Burgers)

### P1 (Completed)
- [x] Image upload functionality for custom menu item photos
- [x] Add images to all 335 menu items (was 182 without images)

### P2 (Future)
- [ ] Refactor Dashboard.jsx into smaller components (MenuList, BillPanel, ModifierDialog)
- [ ] User authentication and multi-user support
- [ ] Inventory management
- [ ] Table reservation system
- [ ] Mobile-responsive improvements

---

## API Endpoints
- `GET, POST, PUT, DELETE /api/menu` - Menu items CRUD
- `GET /api/menu/categories` - Get all categories
- `GET, POST /api/bills` - Bills CRUD
- `GET, POST, PUT, DELETE /api/modifiers` - Modifiers CRUD
- `GET, PUT /api/config/theme` - Theme configuration
- `POST /api/config/theme/reset` - Reset theme to default
- `GET /api/reports/daily` - Daily sales report
- `GET /api/reports/range` - Date range report

## Database Schema
- **menu_items**: {id, name, price, category, description, image_url, available, modifiers[], created_at}
- **bills**: {bill_number, customer_name, table_number, nif, items[], subtotal, tax_percent, tax_amount, discount_percent, discount_amount, total, currency, created_at}
- **modifiers**: {id, name, type, required, options[{name, price_adjustment}]}
- **theme**: {id, name, primary_color, accent_color, background_color, card_color, text_color, muted_color, border_color}

## Test Reports
- `/app/test_reports/iteration_3.json` - Latest: 100% pass rate (backend + frontend)
