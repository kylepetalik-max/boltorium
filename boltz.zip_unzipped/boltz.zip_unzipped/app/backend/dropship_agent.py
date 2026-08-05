"""
RMR Dropshipping Agent v2 — AI-powered marketplace product generator
- Uses GPT to create realistic product names + technical descriptions
- Uses CURATED Unsplash images per subcategory (no more blank cards)
- Pricing anchored to realistic market USD (with sensible MAP min/max ranges)
- Computes RMR price (~2x USD), CAD price, SOL price (USD/200 floor)
"""
import os
import sys
import json
import uuid
import asyncio
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage
from product_images import pick_image

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']
API_KEY = os.environ['EMERGENT_LLM_KEY']

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Realistic market USD price ranges per subcategory (min, max)
PRICE_RANGES = {
    "electric_dirtbike": (3800, 14000),
    "emtb": (2500, 9500),
    "skateboard": (650, 2400),
    "euc": (1400, 4500),
    "motors": (180, 1400),
    "batteries": (320, 1900),
    "helmets": (90, 650),
    "jerseys": (40, 180),
    "pants": (75, 320),
    "gloves": (28, 120),
    "protection": (60, 480),
    "spare_parts": (35, 480),
    "merch_kilovoltz": (18, 95),
    "merch_rmr": (18, 95),
}

PRODUCT_CATEGORIES = {
    "electric_dirtbike": {
        "label": "Electric Dirtbikes",
        "subcategory": "vehicles",
        "brands": ["Sur-Ron", "Talaria", "Segway", "KTM Freeride E-XC", "Stark Varg", "Cake Kalk", "Zero FX"],
        "products": [
            "Sur-Ron Light Bee X 60V 32Ah Electric Off-Road Bike",
            "Talaria Sting MX4 72V Electric Dirt Bike",
            "Segway X260 60V Electric Dirt Bike with Suspension",
            "Stark Varg EX 80hp Electric Motocross Bike",
            "Cake Kalk OR Off-Road Electric Trail Bike",
            "Talaria Sting R MX5 Electric Enduro Adult",
        ],
    },
    "emtb": {
        "label": "Electric Mountain Bikes",
        "subcategory": "vehicles",
        "brands": ["Specialized Turbo Levo", "Trek Rail", "Giant Trance X E+", "Canyon Spectral:ON", "YT Decoy", "Santa Cruz Heckler"],
        "products": [
            "Specialized Turbo Levo Comp Carbon Full-Suspension eMTB",
            "Trek Rail 9.7 eMTB 750Wh Bosch CX 5th-Gen",
            "Canyon Spectral:ON CF 8 Carbon eMTB",
            "YT Decoy Core 3 Carbon eMTB 160mm",
            "Giant Trance X Advanced E+ Elite eMTB",
            "Santa Cruz Heckler MX Carbon CC X0 AXS eMTB",
        ],
    },
    "skateboard": {
        "label": "Electric Skateboards",
        "subcategory": "vehicles",
        "brands": ["Boosted", "Evolve", "Meepo", "WowGo", "Backfire", "Exway", "Onsra"],
        "products": [
            "Evolve GTR Carbon Series 2-in-1 Electric Skateboard",
            "Boosted Stealth Belt-Drive Electric Longboard",
            "Onsra Black Carve 2 Direct-Drive Electric Skateboard",
            "Meepo V5 ER 1500W Dual-Hub Electric Skateboard",
            "WowGo AT2 Plus All-Terrain Electric Skateboard",
            "Exway Atlas Carbon 4WD Pneumatic Electric Skateboard",
        ],
    },
    "euc": {
        "label": "Electric Unicycles",
        "subcategory": "vehicles",
        "brands": ["Begode", "InMotion", "KingSong", "Veteran (Leaperkim)", "Extreme Bull"],
        "products": [
            "Begode EX30 134V 3600Wh Suspension Electric Unicycle",
            "Veteran Sherman-S 100V 3600Wh High-Speed EUC",
            "InMotion V13 Challenger 126V Touring EUC",
            "KingSong S22 Pro Suspension Electric Unicycle",
            "Begode Master 134V High-Performance EUC",
            "Extreme Bull Commander 1 Suspension EUC",
        ],
    },
    "motors": {
        "label": "Electric Motors",
        "subcategory": "parts",
        "brands": ["QS Motor", "MXUS", "Bafang", "Voilamart", "Cyclone"],
        "products": [
            "QS Motor 273 V3 8000W Hub Motor (Rear)",
            "QS 138 90H Mid-Drive Motor with Controller",
            "Bafang BBSHD 1000W 48V Mid-Drive Conversion Kit",
            "MXUS XF40 1000W Rear Hub Motor 48V",
            "QS Motor 205 V3 10kW Hub Motor",
            "Bafang BBS02B 750W Mid-Drive Kit",
            "Cyclone 3000W Mid-Drive Motor Kit 72V",
            "QS Motor 180 3000W Rear Hub Motor",
        ],
    },
    "batteries": {
        "label": "Lithium Batteries",
        "subcategory": "parts",
        "brands": ["Samsung", "LG", "Panasonic", "Molicel", "EVE"],
        "products": [
            "72V 40Ah Lithium Battery Pack (Samsung 50E cells)",
            "48V 20Ah Triangle Frame eBike Battery LG MJ1",
            "60V 32Ah Sur-Ron Replacement Battery (Molicel P42A)",
            "72V 50Ah High-Discharge Battery Pack",
            "52V 25Ah Rear Rack eBike Battery",
            "96V 40Ah EUC High-Performance Battery Pack",
            "36V 15Ah Skateboard Battery with Smart BMS",
            "DIY 21700 Battery Pack Builder Kit (with BMS)",
        ],
    },
    "helmets": {
        "label": "Helmets",
        "subcategory": "gear",
        "brands": ["Fox Racing", "Leatt", "Bell", "Troy Lee Designs", "Alpinestars", "Thor"],
        "products": [
            "Fox Racing Rampage Pro Carbon MIPS Full-Face Helmet",
            "Leatt MTB 4.0 Enduro Helmet Removable Chin",
            "Bell Super DH MIPS Full-Face / Half-Shell Helmet",
            "Troy Lee Designs SE5 Carbon MIPS Helmet",
            "Alpinestars Supertech M8 Motocross Helmet",
            "Thor Sector Adult Motocross Helmet",
        ],
    },
    "jerseys": {
        "label": "Jerseys & Tops",
        "subcategory": "gear",
        "brands": ["Fox Racing", "Leatt", "Thor", "Alpinestars", "FLY Racing"],
        "products": [
            "Fox Racing 360 Vented Motocross Jersey",
            "Leatt MTB Trail 3.0 Long-Sleeve Jersey",
            "Thor Sector Racing Moisture-Wicking Jersey",
            "Alpinestars Techstar Phantom MX Jersey",
            "FLY Racing F-16 Lightweight Race Jersey",
        ],
    },
    "pants": {
        "label": "Riding Pants",
        "subcategory": "gear",
        "brands": ["Fox Racing", "Leatt", "Thor", "Alpinestars", "FLY Racing"],
        "products": [
            "Fox Racing 360 Vented Motocross Pants",
            "Leatt MTB Trail 4.0 Stretch Pants",
            "Thor Pulse Air Ventilated Riding Pants",
            "Alpinestars Techstar Phantom MX Pants",
            "FLY Racing Kinetic K121 Riding Pants",
        ],
    },
    "gloves": {
        "label": "Gloves",
        "subcategory": "gear",
        "brands": ["Fox Racing", "Leatt", "Alpinestars", "Thor", "100%"],
        "products": [
            "Fox Racing Bomber LT D3O Touchscreen Gloves",
            "Leatt MTB 4.0 Lite Full-Finger Gloves",
            "Alpinestars Aero R3 Race Gloves",
            "100% Brisker Cold-Weather Insulated Gloves",
            "Thor Spectrum Mid-Weight Racing Gloves",
        ],
    },
    "protection": {
        "label": "Protection & Armor",
        "subcategory": "gear",
        "brands": ["Leatt", "Fox Racing", "Alpinestars", "POC", "G-Form"],
        "products": [
            "Leatt 4.5 Chest Protector with Removable Pads",
            "Fox Racing Titan Sport Roost Deflector",
            "Alpinestars Bionic Tech Body Armor Jacket",
            "POC VPD System Knee Guards CE Level 2",
            "Leatt Neck Brace GPX 5.5 Carbon",
            "G-Form Pro-X3 Elbow Pads",
        ],
    },
    "spare_parts": {
        "label": "Spare Parts & Upgrades",
        "subcategory": "parts",
        "brands": ["ASI", "Magura", "DNM", "RST", "Hope"],
        "products": [
            "ASI BAC4000 72V 150A Sine-Wave Controller",
            "Magura MT7 Pro 4-Piston Hydraulic Brake Kit",
            "DNM USD-8 Inverted Front Fork Suspension",
            "RST Volo Adjustable Rear Shock Absorber",
            "Sprocket + Chain Kit Heavy-Duty (Sur-Ron / Talaria)",
            "ENVE Handlebar 35mm Carbon (Riser)",
            "LED Headlight Kit 60V/72V Waterproof IP67",
            "Digital Color Speedometer Display (M5 / Bafang)",
            "Throttle Grip Assembly with 3-Speed Switch",
            "Hope V4 Floating Brake Rotor 203mm",
        ],
    },
    "merch_kilovoltz": {
        "label": "KiloVoltz Merchandise",
        "subcategory": "merch",
        "brands": ["KiloVoltz"],
        "products": [
            "KiloVoltz Logo Heavyweight Cotton Hoodie",
            "KiloVoltz Limited Race Jersey Cyberpunk Print",
            "KiloVoltz Embroidered Snapback Cap",
            "KiloVoltz Holographic Sticker Pack (12)",
            "KiloVoltz Organic Cotton T-Shirt",
        ],
    },
    "merch_rmr": {
        "label": "RMR Merchandise",
        "subcategory": "merch",
        "brands": ["RMR"],
        "products": [
            "RMR 'Riders Made Riches' Cyberpunk Hoodie",
            "RMR Neon Glow Race Jersey Edition",
            "RMR Neon Embroidered Snapback Hat",
            "RMR Holographic Crypto Rider Sticker Pack",
            "RMR 'Ride to Earn' Graphic T-Shirt",
        ],
    },
}


async def generate_products_for_category(category_key, category_data):
    """Use GPT to generate realistic product listings for a category."""
    pmin, pmax = PRICE_RANGES.get(category_key, (50, 500))
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"dropship-{category_key}-{uuid.uuid4().hex[:8]}",
        system_message=(
            "You are a senior e-commerce copywriter for an LEV (Light Electric Vehicle) marketplace called RMR. "
            "Generate realistic, accurate product listings with brand-correct specs and MAP-aligned pricing. "
            "Return ONLY a valid JSON array, no markdown, no commentary. Pricing must reflect real US retail."
        ),
    )

    products_prompt = (
        f'Generate {len(category_data["products"])} realistic product listings for "{category_data["label"]}".\n'
        f'Each price must be USD between ${pmin} and ${pmax} and aligned to typical US street price for that brand and tier.\n'
        f'Brands to use (pick the most appropriate for each): {", ".join(category_data["brands"])}\n\n'
        f'Product types (use these as anchors, you may keep these exact names):\n'
        + "\n".join(f"- {p}" for p in category_data["products"])
        + (
            '\n\nReturn a JSON array where each object has fields exactly:\n'
            '  "name": full product name with brand,\n'
            '  "description": 2-3 sentence accurate description with concrete technical details,\n'
            '  "brand": brand string (one of the brands above),\n'
            '  "specs": object with concrete technical specs (voltage, wattage, weight, range, top speed, material, size, etc. — use brand-correct values),\n'
            '  "retail_price": USD retail price (integer or 1-decimal float) within the range,\n'
            '  "wholesale_price": realistic wholesale price (about 55-65% of retail),\n'
            '  "weight_kg": shipping weight float,\n'
            '  "stock": realistic stock between 3 and 80\n'
            '\nReturn ONLY the JSON array.'
        )
    )

    msg = UserMessage(text=products_prompt)
    response = await chat.send_message(msg)

    text = response.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            s = text.index("[")
            e = text.rindex("]") + 1
            return json.loads(text[s:e])
        except Exception:
            print(f"  ! Could not extract JSON from response for {category_key}")
            return []


async def seed_marketplace(replace: bool = True):
    """Generate and seed all marketplace products."""
    print("=== RMR Dropshipping Agent v2 ===")
    print(f"Categories to process: {len(PRODUCT_CATEGORIES)}")

    if replace:
        deleted = await db.items.delete_many({"source": "dropship_agent"})
        print(f"Cleared {deleted.deleted_count} existing dropship items")

    all_items = []

    for cat_key, cat_data in PRODUCT_CATEGORIES.items():
        print(f"\n[{cat_key}] Generating {len(cat_data['products'])} products...")
        try:
            products = await generate_products_for_category(cat_key, cat_data)
            pmin, pmax = PRICE_RANGES.get(cat_key, (50, 500))
            for product in products:
                # Sanity-clamp pricing in case GPT goes out of range
                retail = float(product.get("retail_price", (pmin + pmax) / 2))
                retail = max(pmin, min(retail, pmax))
                wholesale = float(product.get("wholesale_price", retail * 0.6))
                name = product.get("name", "Unknown Product")
                stock = int(product.get("stock", random.randint(5, 60)))
                stock = max(1, min(stock, 100))

                image_url = pick_image(cat_key, seed=name)

                item = {
                    "item_id": f"item_{uuid.uuid4().hex[:12]}",
                    "name": name,
                    "description": product.get("description", ""),
                    "category": cat_data["subcategory"],
                    "subcategory": cat_key,
                    "brand": product.get("brand", cat_data["brands"][0]),
                    "price_usd": round(retail, 2),
                    "price_cad": round(retail * 1.36, 2),
                    "price_rmr": round(retail * 2.0, 0),  # 1 USD ≈ 2 RMR
                    "price_sol": round(retail * 2.0 / 1000.0, 4),  # 1 SOL = 1000 RMR
                    "wholesale_price": round(wholesale, 2),
                    "specs": product.get("specs", {}),
                    "weight_kg": float(product.get("weight_kg", 1.0)),
                    "stock": stock,
                    "image_url": image_url,
                    "source": "dropship_agent",
                    "is_available": True,
                    "is_featured": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                all_items.append(item)
            print(f"  Generated {len(products)} products")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Feature ~10 items across categories
    featured = random.sample(range(len(all_items)), k=min(10, len(all_items)))
    for i in featured:
        all_items[i]["is_featured"] = True

    print(f"\nInserting {len(all_items)} products into database...")
    if all_items:
        await db.items.insert_many(all_items)
        print(f"Successfully seeded {len(all_items)} products!")

    cats = {}
    for it in all_items:
        sc = it["subcategory"]
        cats[sc] = cats.get(sc, 0) + 1
    print("\n=== Summary ===")
    for sc, count in sorted(cats.items()):
        print(f"  {sc}: {count} products")
    return len(all_items)


if __name__ == "__main__":
    total = asyncio.run(seed_marketplace())
    print(f"\nDone! Total products: {total}")
