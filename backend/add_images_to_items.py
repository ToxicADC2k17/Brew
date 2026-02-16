#!/usr/bin/env python3
"""Script to add images to menu items that don't have one"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / '.env')

# Category to image URL mapping
CATEGORY_IMAGES = {
    "Pizza": [
        "https://images.unsplash.com/photo-1680405620826-83b0f0f61b28?w=400",
        "https://images.unsplash.com/photo-1588988949118-c86ba9c9c225?w=400",
        "https://images.unsplash.com/photo-1652539616341-93a908bcca2e?w=400",
        "https://images.unsplash.com/photo-1649688423692-308d2fc1027d?w=400",
    ],
    "Pasta": [
        "https://images.unsplash.com/photo-1630563775062-bbaf8ad3d73c?w=400",
        "https://images.unsplash.com/photo-1734356959885-54fe2e99c1cd?w=400",
        "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=400",
        "https://images.unsplash.com/photo-1693609929945-b01ae4f2d602?w=400",
    ],
    "Burgers": [
        "https://images.unsplash.com/photo-1632898657953-f41f81bfa892?w=400",
        "https://images.unsplash.com/photo-1632898658005-af95f6fa589c?w=400",
        "https://images.unsplash.com/photo-1632898658030-ead731d252d4?w=400",
        "https://images.unsplash.com/photo-1632898657999-ae6920976661?w=400",
    ],
    "Desserts": [
        "https://images.unsplash.com/photo-1514424350208-755887f7b374?w=400",
        "https://images.unsplash.com/photo-1636871522968-9de4fa3a5702?w=400",
        "https://images.unsplash.com/photo-1562281556-0f8c259a9f3a?w=400",
    ],
    "Starters": [
        "https://images.unsplash.com/photo-1761315412730-a6f67208b78d?w=400",
        "https://images.unsplash.com/photo-1770660332407-701bc44a84ad?w=400",
        "https://images.unsplash.com/photo-1715187935352-728a800d663d?w=400",
    ],
    "Seafood": [
        "https://images.unsplash.com/photo-1764397514672-63b1a7a79110?w=400",
        "https://images.unsplash.com/photo-1594038751037-dfb64bfe1ea5?w=400",
        "https://images.unsplash.com/photo-1758184665571-6c64f6d19db6?w=400",
    ],
    "Salads": [
        "https://images.unsplash.com/photo-1769638913684-87c75872fda7?w=400",
        "https://images.unsplash.com/photo-1758721218560-aec50748d450?w=400",
        "https://images.unsplash.com/photo-1657835838278-b371d0fc454a?w=400",
    ],
    "Sides": [
        "https://images.unsplash.com/photo-1599975744981-48d63c8f38af?w=400",
        "https://images.unsplash.com/photo-1761545832737-bc8d52aa2001?w=400",
        "https://images.unsplash.com/photo-1723763246578-99e614b2a91b?w=400",
    ],
    "Smoothies": [
        "https://images.unsplash.com/photo-1648071597664-ffabc1e1c13b?w=400",
        "https://images.unsplash.com/photo-1553787499-6f9133860278?w=400",
        "https://images.unsplash.com/photo-1689358459793-48a913791616?w=400",
    ],
    "Steaks": [
        "https://images.unsplash.com/photo-1654879259483-af42804bd2bb?w=400",
        "https://images.unsplash.com/photo-1732763897987-ce7e63a94d7c?w=400",
        "https://images.unsplash.com/photo-1682159173065-2b49ffd61adb?w=400",
    ],
    "Mains": [
        "https://images.unsplash.com/photo-1633964913295-ceb43826e7c9?w=400",
        "https://images.unsplash.com/photo-1693609929945-b01ae4f2d602?w=400",
        "https://images.unsplash.com/photo-1540809515-ad1349c4bb8d?w=400",
    ],
    "Vegetarian": [
        "https://images.unsplash.com/photo-1540809515-ad1349c4bb8d?w=400",
        "https://images.unsplash.com/photo-1768849352399-86a2fdbe226a?w=400",
        "https://images.unsplash.com/photo-1736928633626-5c35e5677874?w=400",
    ],
    "Lunch": [
        "https://images.unsplash.com/photo-1716959669858-11d415bdead6?w=400",
        "https://images.unsplash.com/photo-1665594051407-7385d281ad76?w=400",
        "https://images.unsplash.com/photo-1699005575488-49ebcecdc794?w=400",
    ],
    "Soups": [
        "https://images.unsplash.com/photo-1716959669858-11d415bdead6?w=400",
        "https://images.unsplash.com/photo-1665594051407-7385d281ad76?w=400",
    ],
    "Snacks": [
        "https://images.unsplash.com/photo-1770660332407-701bc44a84ad?w=400",
        "https://images.unsplash.com/photo-1715187935352-728a800d663d?w=400",
    ],
}


async def add_images():
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    # Get items without images
    items = await db.menu_items.find(
        {"$or": [{"image_url": ""}, {"image_url": None}, {"image_url": {"$exists": False}}]}
    ).to_list(1000)
    
    print(f"Found {len(items)} items without images")
    
    # Track which image to use for each category (rotating through available images)
    category_counters = {cat: 0 for cat in CATEGORY_IMAGES}
    updated_count = 0
    
    for item in items:
        category = item.get("category")
        if category in CATEGORY_IMAGES:
            images = CATEGORY_IMAGES[category]
            idx = category_counters[category] % len(images)
            image_url = images[idx]
            category_counters[category] += 1
            
            # Update the item
            await db.menu_items.update_one(
                {"id": item["id"]},
                {"$set": {"image_url": image_url}}
            )
            updated_count += 1
            print(f"Updated {item['name']} ({category}) with image")
    
    print(f"\nTotal updated: {updated_count} items")
    client.close()


if __name__ == "__main__":
    asyncio.run(add_images())
