from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, File, UploadFile, Query, Header
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import math
import random
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Object Storage Configuration
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "rmr-app"
storage_key = None

def init_storage():
    """Initialize object storage - call once at startup."""
    global storage_key
    if storage_key:
        return storage_key
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
        resp.raise_for_status()
        storage_key = resp.json()["storage_key"]
        return storage_key
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
        return None

def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload file to object storage."""
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str) -> tuple:
    """Download file from object storage."""
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not initialized")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Solana Configuration
SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.devnet.solana.com")

import solana_service

# Create the main app
app = FastAPI(title="RMR - Ride More Rewards API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============= Pydantic Models =============

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    picture: Optional[str] = None
    wallet_address: Optional[str] = None
    rmr_balance: float = 0.0
    total_distance: float = 0.0
    total_rides: int = 0
    vehicle_type: Optional[str] = "ebike"
    level: int = 1
    xp: int = 0
    created_at: Optional[datetime] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    vehicle_type: Optional[str] = None
    wallet_address: Optional[str] = None

class Ride(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ride_id: str
    user_id: str
    vehicle_type: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    distance: float = 0.0
    duration: int = 0
    status: str = "ongoing"
    gps_trace: Optional[List[Dict]] = None
    rmr_earned: float = 0.0
    validation_status: str = "pending"
    validation_flags: Optional[List[str]] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None

class RideStart(BaseModel):
    vehicle_type: Optional[str] = None

class RideUpdate(BaseModel):
    current_lat: float
    current_lng: float
    distance_delta: float

class RideFinish(BaseModel):
    total_distance: float
    gps_trace: Optional[List[Dict]] = None

class Airdrop(BaseModel):
    model_config = ConfigDict(extra="ignore")
    airdrop_id: str
    type: str = "rmr"
    latitude: float
    longitude: float
    radius: int = 50
    value: float = 0.0
    description: Optional[str] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None

class AirdropClaim(BaseModel):
    lat: float
    lng: float

class Challenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    challenge_id: str
    title: str
    description: str
    category: str
    type: str = "one_time"
    difficulty: str
    icon: Optional[str] = None
    requirement: float
    requirement_unit: str
    reward_rmr: float
    reward_xp: int = 0
    is_active: bool = True

class UserChallenge(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_challenge_id: str
    user_id: str
    challenge_id: str
    progress: float = 0.0
    status: str = "active"
    started_at: datetime
    completed_at: Optional[datetime] = None

class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")
    item_id: str
    name: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    price_rmr: float
    price_cad: Optional[float] = None
    stock: int = 0
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    specs: Optional[Dict] = None
    is_available: bool = True
    is_featured: bool = False

class Listing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    listing_id: str
    seller_id: str
    title: str
    description: Optional[str] = None
    category: str
    condition: str
    price_rmr: float
    price_cad: Optional[float] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    status: str = "active"
    created_at: datetime

class ListingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    condition: str
    price_rmr: float
    price_cad: Optional[float] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    transaction_id: str
    user_id: str
    type: str
    amount: float
    reference_id: Optional[str] = None
    status: str = "completed"
    created_at: datetime

# ============= Auth Helper =============

async def get_current_user(request: Request) -> User:
    """Get current authenticated user from session token."""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user_doc)


async def get_optional_user(request: Request) -> Optional[User]:
    """Like get_current_user but returns None instead of raising for unauthenticated."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


# ============= Auth Endpoints =============

async def upsert_user(email: str, name: str, picture: str) -> str:
    """Find or create user. Returns user_id."""
    name_parts = name.split(" ", 1) if name else ["", ""]
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        await db.users.update_one(
            {"user_id": existing["user_id"]},
            {"$set": {"name": name, "picture": picture, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return existing["user_id"]
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    await db.users.insert_one({
        "user_id": user_id, "email": email, "name": name,
        "first_name": first_name, "last_name": last_name, "picture": picture,
        "rmr_balance": 100.0, "total_distance": 0.0, "total_rides": 0,
        "vehicle_type": "ebike", "wallet_address": None, "level": 1, "xp": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return user_id


@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token after Google OAuth."""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent Auth to get user data
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client_http:
        auth_response = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        
        auth_data = auth_response.json()
    
    session_token = auth_data.get("session_token")
    email = auth_data.get("email")
    name = auth_data.get("name", "")
    picture = auth_data.get("picture")
    
    user_id = await upsert_user(email, name, picture)
    
    # Auto-promote first user to admin
    admin_count = await db.admins.count_documents({})
    if admin_count == 0:
        await db.admins.insert_one({
            "user_id": user_id,
            "promoted_by": "auto_first_login",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Auto-promoted first user {email} to admin")
    
    # Store session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    # Return token in body too for Bearer-token fallback in cross-domain scenarios
    user_doc["session_token"] = session_token
    return user_doc

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session."""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"success": True}

# ============= Rider Endpoints =============

@api_router.get("/rider/stats")
async def get_rider_stats(user: User = Depends(get_current_user)):
    """Get rider statistics."""
    # Calculate rank
    users_above = await db.users.count_documents({"rmr_balance": {"$gt": user.rmr_balance}})
    rank = users_above + 1
    
    # Calculate XP to next level
    xp_to_next = (user.level * 100) - user.xp
    
    return {
        "totalDistance": user.total_distance,
        "totalRides": user.total_rides,
        "rmrBalance": user.rmr_balance,
        "rank": rank,
        "level": user.level,
        "xp": user.xp,
        "xpToNextLevel": max(0, xp_to_next)
    }

@api_router.patch("/rider/profile")
async def update_profile(update: UserUpdate, user: User = Depends(get_current_user)):
    """Update rider profile."""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"user_id": user.user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return updated_user

@api_router.patch("/rider/vehicle")
async def update_vehicle(request: Request, user: User = Depends(get_current_user)):
    """Update rider vehicle type."""
    body = await request.json()
    vehicle_type = body.get("vehicleType")
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"vehicle_type": vehicle_type, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return updated_user

@api_router.get("/rider/leaderboard")
async def get_leaderboard():
    """Get top riders leaderboard."""
    leaders = await db.users.find(
        {},
        {"_id": 0, "user_id": 1, "first_name": 1, "last_name": 1, "username": 1, "rmr_balance": 1, "total_distance": 1, "total_rides": 1, "picture": 1}
    ).sort("rmr_balance", -1).limit(50).to_list(50)
    
    return leaders

@api_router.get("/rider/transactions")
async def get_transactions(user: User = Depends(get_current_user)):
    """Get user transactions."""
    transactions = await db.transactions.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(100).to_list(100)
    
    return transactions

# ============= Rides Endpoints =============

@api_router.post("/rides/start")
async def start_ride(ride_data: RideStart, user: User = Depends(get_current_user)):
    """Start a new ride."""
    # Check for ongoing rides
    ongoing = await db.rides.find_one({"user_id": user.user_id, "status": "ongoing"}, {"_id": 0})
    if ongoing:
        raise HTTPException(status_code=400, detail="You already have an ongoing ride")
    
    ride = {
        "ride_id": f"ride_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "vehicle_type": ride_data.vehicle_type or user.vehicle_type,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": None,
        "distance": 0.0,
        "duration": 0,
        "status": "ongoing",
        "gps_trace": [],
        "rmr_earned": 0.0,
        "validation_status": "pending",
        "validation_flags": [],
        "average_speed": None,
        "max_speed": None
    }
    
    await db.rides.insert_one(ride)
    ride.pop("_id", None)
    return ride

@api_router.get("/rides")
async def get_rides(user: User = Depends(get_current_user)):
    """Get user's rides."""
    rides = await db.rides.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("start_time", -1).limit(50).to_list(50)
    
    return rides

@api_router.get("/rides/current")
async def get_current_ride(user: User = Depends(get_current_user)):
    """Get current ongoing ride."""
    ride = await db.rides.find_one({"user_id": user.user_id, "status": "ongoing"}, {"_id": 0})
    return ride

@api_router.patch("/rides/{ride_id}/update")
async def update_ride(ride_id: str, update: RideUpdate, user: User = Depends(get_current_user)):
    """Update ride with GPS data."""
    ride = await db.rides.find_one({"ride_id": ride_id, "user_id": user.user_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride["status"] != "ongoing":
        raise HTTPException(status_code=400, detail="Ride is not ongoing")
    
    # Add GPS point
    gps_point = {
        "lat": update.current_lat,
        "lng": update.current_lng,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    new_distance = ride["distance"] + update.distance_delta
    
    await db.rides.update_one(
        {"ride_id": ride_id},
        {
            "$push": {"gps_trace": gps_point},
            "$set": {"distance": new_distance}
        }
    )
    
    updated_ride = await db.rides.find_one({"ride_id": ride_id}, {"_id": 0})
    return updated_ride


# ---- Ride finish helpers ----

VEHICLE_MULTIPLIERS = {
    "bicycle": 1.0, "ebike": 1.5, "skateboard": 1.0,
    "electric_skateboard": 1.5, "onewheel": 1.5, "euc": 1.5,
    "dirt_bike": 0.75, "electric_dirt_bike": 1.5,
}

def validate_ride_data(distance: float, avg_speed: float, duration: int) -> tuple:
    """Validate ride metrics. Returns (passed, flags)."""
    flags = []
    if distance < 0.1:
        flags.append("distance_too_short")
    if avg_speed > 100:
        flags.append("speed_unrealistic")
    if duration < 60:
        flags.append("duration_too_short")
    return len(flags) == 0, flags

def calculate_ride_earnings(distance: float, vehicle_type: str, validated: bool) -> tuple:
    """Calculate RMR reward for a ride. Returns (rmr_earned, multiplier)."""
    multiplier = VEHICLE_MULTIPLIERS.get(vehicle_type, 1.0)
    rmr_earned = round(distance * multiplier, 2) if validated else 0
    return rmr_earned, multiplier

def calculate_level_up(current_xp: int, current_level: int, xp_gained: int) -> tuple:
    """Process XP gain and level ups. Returns (new_level, new_xp)."""
    new_xp = current_xp + xp_gained
    new_level = current_level
    while new_xp >= new_level * 100:
        new_xp -= new_level * 100
        new_level += 1
    return new_level, new_xp


@api_router.post("/rides/{ride_id}/finish")
async def finish_ride(ride_id: str, finish_data: RideFinish, user: User = Depends(get_current_user)):
    """Finish a ride and calculate rewards."""
    ride = await db.rides.find_one({"ride_id": ride_id, "user_id": user.user_id}, {"_id": 0})
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")
    
    if ride["status"] != "ongoing":
        raise HTTPException(status_code=400, detail="Ride is not ongoing")
    
    start_time = datetime.fromisoformat(ride["start_time"].replace("Z", "+00:00"))
    end_time = datetime.now(timezone.utc)
    duration = int((end_time - start_time).total_seconds())
    
    # Validate ride
    distance = finish_data.total_distance
    avg_speed = (distance / (duration / 3600)) if duration > 0 else 0
    max_speed = avg_speed * 1.3
    
    validation_passed, validation_flags = validate_ride_data(distance, avg_speed, duration)
    base_rmr, vehicle_multiplier = calculate_ride_earnings(distance, ride.get("vehicle_type", "ebike"), validation_passed)

    # Apply subscription tier earn multiplier (Free 1x, Pro 1.25x, VIP 1.5x)
    tier = await get_user_tier(user.user_id)
    tier_mult = SUBSCRIPTION_TIERS[tier]["earn_multiplier"]
    rmr_earned = round(base_rmr * tier_mult, 2)
    multiplier = round(vehicle_multiplier * tier_mult, 3)
    
    # Update ride
    await db.rides.update_one(
        {"ride_id": ride_id},
        {"$set": {
            "end_time": end_time.isoformat(),
            "distance": distance,
            "duration": duration,
            "status": "completed" if validation_passed else "flagged",
            "gps_trace": finish_data.gps_trace or ride.get("gps_trace", []),
            "rmr_earned": rmr_earned,
            "validation_status": "passed" if validation_passed else "failed",
            "validation_flags": validation_flags,
            "average_speed": round(avg_speed, 2),
            "max_speed": round(max_speed, 2)
        }}
    )
    
    # Update user stats if validated
    if validation_passed:
        xp_earned = int(distance * 10)
        new_level, new_xp = calculate_level_up(user.xp, user.level, xp_earned)
        
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {
                "rmr_balance": rmr_earned,
                "total_distance": distance,
                "total_rides": 1
            }, "$set": {
                "level": new_level,
                "xp": new_xp
            }}
        )
        
        # Create transaction
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "ride_reward",
            "amount": rmr_earned,
            "reference_id": ride_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "ride": await db.rides.find_one({"ride_id": ride_id}, {"_id": 0}),
        "validation": {
            "passed": validation_passed,
            "flags": validation_flags,
            "computedDistance": distance,
            "averageSpeed": round(avg_speed, 2),
            "maxSpeed": round(max_speed, 2),
            "rewardMultiplier": multiplier
        },
        "rmrEarned": rmr_earned,
        "tierMultiplier": tier_mult,
        "tier": tier,
    }

# ============= Airdrops Endpoints =============

@api_router.get("/airdrops/nearby")
async def get_nearby_airdrops(lat: float = 0, lng: float = 0):
    """Get nearby airdrops."""
    airdrops = await db.airdrops.find(
        {"is_active": True},
        {"_id": 0}
    ).limit(50).to_list(50)
    
    # If no airdrops exist, create some demo ones
    if not airdrops:
        demo_airdrops = [
            {"airdrop_id": f"airdrop_{uuid.uuid4().hex[:8]}", "type": "rmr", "latitude": lat + random.uniform(-0.01, 0.01), "longitude": lng + random.uniform(-0.01, 0.01), "radius": 50, "value": 5.0, "description": "VOLTZ Token Airdrop", "is_active": True},
            {"airdrop_id": f"airdrop_{uuid.uuid4().hex[:8]}", "type": "rmr", "latitude": lat + random.uniform(-0.02, 0.02), "longitude": lng + random.uniform(-0.02, 0.02), "radius": 75, "value": 10.0, "description": "Big VOLTZ Drop!", "is_active": True},
            {"airdrop_id": f"airdrop_{uuid.uuid4().hex[:8]}", "type": "rmr", "latitude": lat + random.uniform(-0.015, 0.015), "longitude": lng + random.uniform(-0.015, 0.015), "radius": 30, "value": 2.5, "description": "Quick Grab", "is_active": True},
        ]
        await db.airdrops.insert_many(demo_airdrops)
        # re-fetch without _id to avoid serialization issue
        airdrops = await db.airdrops.find({"is_active": True}, {"_id": 0}).limit(50).to_list(50)
    
    return airdrops

@api_router.post("/airdrops/{airdrop_id}/claim")
async def claim_airdrop(airdrop_id: str, claim: AirdropClaim, user: User = Depends(get_current_user)):
    """Claim an airdrop."""
    airdrop = await db.airdrops.find_one({"airdrop_id": airdrop_id, "is_active": True}, {"_id": 0})
    if not airdrop:
        raise HTTPException(status_code=404, detail="Airdrop not found or already claimed")
    
    # Check if already claimed by user
    existing_claim = await db.claims.find_one({"airdrop_id": airdrop_id, "user_id": user.user_id})
    if existing_claim:
        raise HTTPException(status_code=400, detail="Already claimed this airdrop")
    
    # Check distance
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    dist = haversine(claim.lat, claim.lng, airdrop["latitude"], airdrop["longitude"])
    if dist > airdrop.get("radius", 50):
        raise HTTPException(status_code=400, detail="Too far from airdrop location")

    # Apply tier bonus (Free 1x, Pro 1.1x, VIP 1.25x)
    base_reward = airdrop.get("value", 0)
    sub_tier = await get_user_tier(user.user_id)
    AIRDROP_TIER_BONUS = {"free": 1.0, "pro": 1.1, "vip": 1.25}
    reward = round(base_reward * AIRDROP_TIER_BONUS.get(sub_tier, 1.0), 2)
    tier_bonus = reward - base_reward
    
    # Record claim
    await db.claims.insert_one({
        "claim_id": f"claim_{uuid.uuid4().hex[:12]}",
        "airdrop_id": airdrop_id,
        "user_id": user.user_id,
        "claimed_at": datetime.now(timezone.utc).isoformat(),
        "base_reward": base_reward,
        "tier_bonus": tier_bonus,
        "tier": sub_tier,
    })
    
    # Update user balance
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": reward}}
    )
    
    # Create transaction
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "airdrop_claim",
        "amount": reward,
        "reference_id": airdrop_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "reward": reward,
        "base_reward": base_reward,
        "tier_bonus": tier_bonus,
        "tier": sub_tier,
        "message": f"Claimed {reward} VOLTZ" + (f" (+{tier_bonus} {sub_tier.upper()} bonus)" if tier_bonus > 0 else "") + "!"
    }

# ============= Challenges Endpoints =============

@api_router.get("/challenges")
async def get_challenges():
    """Get all active challenges."""
    challenges = await db.challenges.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    # If no challenges, create demo ones
    if not challenges:
        demo_challenges = [
            {"challenge_id": "ch_distance_10", "title": "First Steps", "description": "Complete 10 km total distance", "category": "distance", "type": "one_time", "difficulty": "rookie", "icon": "bicycle", "requirement": 10, "requirement_unit": "km", "reward_rmr": 25, "reward_xp": 100, "is_active": True},
            {"challenge_id": "ch_distance_50", "title": "Road Warrior", "description": "Complete 50 km total distance", "category": "distance", "type": "one_time", "difficulty": "rider", "icon": "road", "requirement": 50, "requirement_unit": "km", "reward_rmr": 100, "reward_xp": 500, "is_active": True},
            {"challenge_id": "ch_rides_5", "title": "Getting Started", "description": "Complete 5 rides", "category": "streak", "type": "one_time", "difficulty": "rookie", "icon": "flag", "requirement": 5, "requirement_unit": "rides", "reward_rmr": 15, "reward_xp": 75, "is_active": True},
            {"challenge_id": "ch_airdrop_3", "title": "Treasure Hunter", "description": "Collect 3 airdrops", "category": "airdrop", "type": "one_time", "difficulty": "rookie", "icon": "gift", "requirement": 3, "requirement_unit": "airdrops", "reward_rmr": 20, "reward_xp": 50, "is_active": True},
            {"challenge_id": "ch_speed_30", "title": "Speed Demon", "description": "Reach 30 km/h average speed on a ride", "category": "speed", "type": "one_time", "difficulty": "rider", "icon": "zap", "requirement": 30, "requirement_unit": "km/h", "reward_rmr": 50, "reward_xp": 200, "is_active": True},
        ]
        await db.challenges.insert_many(demo_challenges)
        challenges = await db.challenges.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    return challenges

@api_router.get("/challenges/mine")
async def get_my_challenges(user: User = Depends(get_current_user)):
    """Get user's joined challenges with progress."""
    user_challenges = await db.user_challenges.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with challenge details
    result = []
    for uc in user_challenges:
        challenge = await db.challenges.find_one({"challenge_id": uc["challenge_id"]}, {"_id": 0})
        if challenge:
            result.append({**uc, "challenge": challenge})
    
    return result

@api_router.post("/challenges/{challenge_id}/join")
async def join_challenge(challenge_id: str, user: User = Depends(get_current_user)):
    """Join a challenge."""
    challenge = await db.challenges.find_one({"challenge_id": challenge_id, "is_active": True}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    existing = await db.user_challenges.find_one({"user_id": user.user_id, "challenge_id": challenge_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this challenge")
    
    user_challenge = {
        "user_challenge_id": f"uc_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "challenge_id": challenge_id,
        "progress": 0,
        "status": "active",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    await db.user_challenges.insert_one(user_challenge)
    user_challenge.pop("_id", None)
    return user_challenge

@api_router.post("/challenges/{challenge_id}/claim")
async def claim_challenge(challenge_id: str, user: User = Depends(get_current_user)):
    """Claim challenge reward."""
    user_challenge = await db.user_challenges.find_one(
        {"user_id": user.user_id, "challenge_id": challenge_id, "status": "completed"},
        {"_id": 0}
    )
    
    if not user_challenge:
        raise HTTPException(status_code=400, detail="Challenge not completed or already claimed")
    
    challenge = await db.challenges.find_one({"challenge_id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Update status to claimed
    await db.user_challenges.update_one(
        {"user_id": user.user_id, "challenge_id": challenge_id},
        {"$set": {"status": "claimed", "claimed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Award rewards (apply tier bonus to RMR)
    base_reward_rmr = challenge.get("reward_rmr", 0)
    reward_xp = challenge.get("reward_xp", 0)
    sub_tier = await get_user_tier(user.user_id)
    tier_mult = SUBSCRIPTION_TIERS[sub_tier]["earn_multiplier"]
    reward_rmr = round(base_reward_rmr * tier_mult, 2)
    
    new_xp = user.xp + reward_xp
    new_level = user.level
    while new_xp >= new_level * 100:
        new_xp -= new_level * 100
        new_level += 1
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": reward_rmr}, "$set": {"xp": new_xp, "level": new_level}}
    )
    
    # Create transaction
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "challenge_reward",
        "amount": reward_rmr,
        "reference_id": challenge_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "rewardRmr": reward_rmr,
        "message": f"Claimed {reward_rmr} RMR and {reward_xp} XP!"
    }

# ============= Marketplace Endpoints =============

@api_router.get("/marketplace/items")
async def get_marketplace_items(category: Optional[str] = None):
    """Get marketplace items."""
    query = {"is_available": True}
    if category:
        query["category"] = category
    
    items = await db.items.find(query, {"_id": 0}).to_list(100)
    
    # If no items, create demo ones
    if not items:
        demo_items = [
            {"item_id": "item_ebike_1", "name": "Urban Commuter eBike", "description": "Perfect city ebike with 60km range", "category": "bike", "subcategory": "ebike", "brand": "RMR Customs", "price_rmr": 2500, "price_cad": 2499.99, "stock": 5, "image_url": "https://images.unsplash.com/photo-1736413988047-8086b6592096?w=800", "is_available": True, "is_featured": True},
            {"item_id": "item_eskate_1", "name": "Boosted Board Pro", "description": "High-performance electric skateboard", "category": "bike", "subcategory": "eskate", "brand": "Evolve", "price_rmr": 1800, "price_cad": 1799.99, "stock": 3, "image_url": "https://images.unsplash.com/photo-1529153510182-75ced468f736?w=800", "is_available": True, "is_featured": True},
            {"item_id": "item_helmet_1", "name": "Pro Rider Helmet", "description": "Full-face protection with MIPS", "category": "gear", "subcategory": "helmet", "brand": "Fox Racing", "price_rmr": 350, "price_cad": 349.99, "stock": 15, "image_url": "https://images.unsplash.com/photo-1627928387551-0d5562a3e2b6?w=800", "is_available": True, "is_featured": False},
            {"item_id": "item_gloves_1", "name": "Riding Gloves", "description": "Breathable mesh with knuckle protection", "category": "gear", "subcategory": "gloves", "brand": "RMR Gear", "price_rmr": 75, "price_cad": 74.99, "stock": 25, "image_url": "https://images.pexels.com/photos/8927100/pexels-photo-8927100.jpeg?w=800", "is_available": True, "is_featured": False},
            {"item_id": "item_hoodie_1", "name": "RMR Logo Hoodie", "description": "Premium cotton blend hoodie", "category": "merch", "subcategory": "hoodie", "brand": "RMR", "price_rmr": 120, "price_cad": 89.99, "stock": 50, "image_url": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800", "is_available": True, "is_featured": True},
        ]
        await db.items.insert_many(demo_items)
        items = await db.items.find(query, {"_id": 0}).to_list(100)
    
    return items

@api_router.get("/marketplace/items/{item_id}")
async def get_marketplace_item(item_id: str):
    """Get single marketplace item."""
    item = await db.items.find_one({"item_id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@api_router.get("/marketplace/featured")
async def get_featured_items():
    """Get featured marketplace items."""
    items = await db.items.find({"is_available": True, "is_featured": True}, {"_id": 0}).limit(6).to_list(6)
    return items

# ============= Listings (P2P) Endpoints =============

@api_router.get("/listings")
async def get_listings(category: Optional[str] = None):
    """Get P2P listings."""
    query = {"status": "active"}
    if category:
        query["category"] = category
    
    listings = await db.listings.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return listings

@api_router.get("/listings/mine")
async def get_my_listings(user: User = Depends(get_current_user)):
    """Get user's listings."""
    listings = await db.listings.find({"seller_id": user.user_id}, {"_id": 0}).to_list(50)
    return listings

@api_router.post("/listings")
async def create_listing(listing: ListingCreate, user: User = Depends(get_current_user)):
    """Create a new listing."""
    new_listing = {
        "listing_id": f"listing_{uuid.uuid4().hex[:12]}",
        "seller_id": user.user_id,
        **listing.model_dump(),
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.listings.insert_one(new_listing)
    new_listing.pop("_id", None)
    return new_listing

@api_router.get("/listings/{listing_id}")
async def get_listing(listing_id: str):
    """Get single listing."""
    listing = await db.listings.find_one({"listing_id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@api_router.delete("/listings/{listing_id}")
async def delete_listing(listing_id: str, user: User = Depends(get_current_user)):
    """Delete a listing."""
    listing = await db.listings.find_one({"listing_id": listing_id, "seller_id": user.user_id})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    await db.listings.delete_one({"listing_id": listing_id})
    return {"success": True}

@api_router.post("/listings/{listing_id}/purchase")
async def purchase_listing(listing_id: str, user: User = Depends(get_current_user)):
    """Purchase a P2P listing."""
    listing = await db.listings.find_one({"listing_id": listing_id, "status": "active"}, {"_id": 0})
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found or sold")
    
    if listing["seller_id"] == user.user_id:
        raise HTTPException(status_code=400, detail="Cannot buy your own listing")
    
    if user.rmr_balance < listing["price_rmr"]:
        raise HTTPException(status_code=400, detail="Insufficient VOLTZ balance")
    
    # Calculate commission (5%)
    commission = listing["price_rmr"] * 0.05
    seller_earnings = listing["price_rmr"] - commission
    
    # Update buyer balance
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": -listing["price_rmr"]}}
    )
    
    # Update seller balance
    await db.users.update_one(
        {"user_id": listing["seller_id"]},
        {"$inc": {"rmr_balance": seller_earnings}}
    )
    
    # Update listing status
    await db.listings.update_one(
        {"listing_id": listing_id},
        {"$set": {"status": "sold", "buyer_id": user.user_id}}
    )
    
    # Create transactions
    await db.transactions.insert_many([
        {
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "listing_purchase",
            "amount": -listing["price_rmr"],
            "reference_id": listing_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": listing["seller_id"],
            "type": "listing_sale",
            "amount": seller_earnings,
            "reference_id": listing_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ])
    
    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    
    return {
        "success": True,
        "newBalance": updated_user["rmr_balance"],
        "commission": commission,
        "sellerEarnings": seller_earnings
    }

# ============= Wallet Endpoints =============

@api_router.post("/wallet/link")
async def link_wallet(request: Request, user: User = Depends(get_current_user)):
    """Link Solana wallet."""
    body = await request.json()
    wallet_address = body.get("walletAddress")
    
    if not wallet_address or len(wallet_address) < 32:
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"wallet_address": wallet_address}}
    )
    
    return {
        "success": True,
        "walletAddress": wallet_address,
        "mintingEnabled": True
    }

@api_router.get("/wallet/balance")
async def get_wallet_balance(user: User = Depends(get_current_user)):
    """Get wallet balance info."""
    # Get tracked on-chain balance from our database
    on_chain_balance = 0
    if user.wallet_address:
        wallet_doc = await db.wallet_balances.find_one(
            {"user_id": user.user_id, "wallet_address": user.wallet_address},
            {"_id": 0}
        )
        if wallet_doc:
            on_chain_balance = wallet_doc.get("on_chain_balance", 0)
    
    return {
        "inAppBalance": user.rmr_balance,
        "onChainBalance": on_chain_balance,
        "walletAddress": user.wallet_address,
        "mintingEnabled": user.wallet_address is not None,
        "cluster": "devnet"
    }

@api_router.get("/wallet/info")
async def get_wallet_info():
    """Get token info."""
    return {
        "mintAddress": "RMRTokenDevnetAddress",
        "decimals": 6,
        "cluster": "devnet",
        "mintingEnabled": True,
        "tokenSymbol": "VOLTZ"
    }

# ============= Stripe Payment Endpoints =============

# Payment packages (server-side defined - never accept amounts from frontend)
PAYMENT_PACKAGES = {
    "rmr_100": {"rmr": 100, "price_cad": 9.99, "name": "100 VOLTZ Tokens"},
    "rmr_500": {"rmr": 500, "price_cad": 39.99, "name": "500 VOLTZ Tokens"},
    "rmr_1000": {"rmr": 1000, "price_cad": 69.99, "name": "1000 VOLTZ Tokens"},
}

class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

@api_router.post("/payments/checkout")
async def create_checkout(request: Request, checkout_req: CheckoutRequest, user: User = Depends(get_current_user)):
    """Create Stripe checkout session for VOLTZ token purchase."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    if checkout_req.package_id not in PAYMENT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = PAYMENT_PACKAGES[checkout_req.package_id]
    
    # Build URLs from frontend origin
    success_url = f"{checkout_req.origin_url}/wallet?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_req.origin_url}/wallet"
    
    # Initialize Stripe
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(package["price_cad"]),
        currency="cad",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user.user_id,
            "package_id": checkout_req.package_id,
            "rmr_amount": str(package["rmr"])
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "transaction_id": f"pay_{uuid.uuid4().hex[:12]}",
        "session_id": session.session_id,
        "user_id": user.user_id,
        "package_id": checkout_req.package_id,
        "rmr_amount": package["rmr"],
        "amount_cad": package["price_cad"],
        "currency": "cad",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, user: User = Depends(get_current_user)):
    """Get payment status and fulfill if completed."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Check if already processed
    tx = await db.payment_transactions.find_one({"session_id": session_id, "user_id": user.user_id}, {"_id": 0})
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if tx["payment_status"] == "completed":
        return {"status": "completed", "payment_status": "paid", "rmr_credited": tx["rmr_amount"]}
    
    # Check with Stripe
    stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")
    status = await stripe_checkout.get_checkout_status(session_id)
    
    if status.payment_status == "paid" and tx["payment_status"] != "completed":
        # If this is a subscription intent, activate the subscription instead of crediting RMR
        if tx.get("type") == "subscription":
            tier = tx.get("tier", "pro")
            expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            sub_id = f"sub_{uuid.uuid4().hex[:12]}"
            await db.subscriptions.update_many({"user_id": user.user_id, "status": "active"}, {"$set": {"status": "superseded"}})
            sub_doc = {
                "subscription_id": sub_id,
                "user_id": user.user_id,
                "tier": tier,
                "status": "active",
                "payment_method": "stripe",
                "amount_cad": tx.get("amount_cad", 0),
                "stripe_session_id": session_id,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires,
                "auto_renew": False,
            }
            await db.subscriptions.insert_one(sub_doc)
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
            )
            await db.transactions.insert_one({
                "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
                "user_id": user.user_id,
                "type": "subscription",
                "amount": 0,
                "reference_id": sub_id,
                "status": "completed",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "meta": {"tier": tier, "method": "stripe", "amount_cad": tx.get("amount_cad", 0)},
            })
            return {"status": "completed", "payment_status": "paid", "subscription_tier": tier, "rmr_credited": 0}

        # Credit RMR to user (default purchase flow)
        rmr_amount = tx["rmr_amount"]
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {"rmr_balance": rmr_amount}}
        )
        
        # Update transaction
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Create transaction record
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "purchase",
            "amount": rmr_amount,
            "reference_id": session_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"status": "completed", "payment_status": "paid", "rmr_credited": rmr_amount}
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "rmr_credited": 0
    }

@api_router.get("/payments/packages")
async def get_payment_packages():
    """Get available RMR purchase packages."""
    return [
        {"id": k, **v} for k, v in PAYMENT_PACKAGES.items()
    ]

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    stripe_key = os.environ.get('STRIPE_API_KEY')
    if not stripe_key:
        return {"status": "not configured"}
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        stripe_checkout = StripeCheckout(api_key=stripe_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            tx = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            
            if tx and tx["payment_status"] != "completed":
                # Credit RMR
                await db.users.update_one(
                    {"user_id": tx["user_id"]},
                    {"$inc": {"rmr_balance": tx["rmr_amount"]}}
                )
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
                )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}

# ============= Admin Endpoints =============

async def get_admin_user(request: Request) -> User:
    """Get current admin user."""
    user = await get_current_user(request)
    # Check if user is admin
    admin_doc = await db.admins.find_one({"user_id": user.user_id})
    if not admin_doc:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

class AdminItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    price_rmr: float
    price_cad: Optional[float] = None
    stock: int = 0
    image_url: Optional[str] = None
    is_featured: bool = False

class AdminChallengeCreate(BaseModel):
    title: str
    description: str
    category: str
    difficulty: str
    requirement: float
    requirement_unit: str
    reward_rmr: float
    reward_xp: int = 0

class AdminAirdropCreate(BaseModel):
    latitude: float
    longitude: float
    value: float
    description: Optional[str] = None
    radius: int = 50

@api_router.post("/admin/items")
async def admin_create_item(item: AdminItemCreate, admin: User = Depends(get_admin_user)):
    """Admin: Create marketplace item."""
    new_item = {
        "item_id": f"item_{uuid.uuid4().hex[:12]}",
        **item.model_dump(),
        "is_available": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.items.insert_one(new_item)
    new_item.pop("_id", None)
    return new_item

@api_router.put("/admin/items/{item_id}")
async def admin_update_item(item_id: str, item: AdminItemCreate, admin: User = Depends(get_admin_user)):
    """Admin: Update marketplace item."""
    result = await db.items.update_one(
        {"item_id": item_id},
        {"$set": {**item.model_dump(), "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True}

@api_router.delete("/admin/items/{item_id}")
async def admin_delete_item(item_id: str, admin: User = Depends(get_admin_user)):
    """Admin: Delete marketplace item."""
    await db.items.delete_one({"item_id": item_id})
    return {"success": True}

@api_router.post("/admin/challenges")
async def admin_create_challenge(challenge: AdminChallengeCreate, admin: User = Depends(get_admin_user)):
    """Admin: Create challenge."""
    new_challenge = {
        "challenge_id": f"ch_{uuid.uuid4().hex[:12]}",
        **challenge.model_dump(),
        "type": "one_time",
        "icon": "target",
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.challenges.insert_one(new_challenge)
    new_challenge.pop("_id", None)
    return new_challenge

@api_router.delete("/admin/challenges/{challenge_id}")
async def admin_delete_challenge(challenge_id: str, admin: User = Depends(get_admin_user)):
    """Admin: Delete challenge."""
    await db.challenges.delete_one({"challenge_id": challenge_id})
    return {"success": True}

@api_router.post("/admin/airdrops")
async def admin_create_airdrop(airdrop: AdminAirdropCreate, admin: User = Depends(get_admin_user)):
    """Admin: Create airdrop."""
    new_airdrop = {
        "airdrop_id": f"airdrop_{uuid.uuid4().hex[:8]}",
        "type": "rmr",
        **airdrop.model_dump(),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.airdrops.insert_one(new_airdrop)
    new_airdrop.pop("_id", None)
    return new_airdrop

@api_router.delete("/admin/airdrops/{airdrop_id}")
async def admin_delete_airdrop(airdrop_id: str, admin: User = Depends(get_admin_user)):
    """Admin: Delete airdrop."""
    await db.airdrops.delete_one({"airdrop_id": airdrop_id})
    return {"success": True}

@api_router.get("/admin/stats")
async def admin_get_stats(admin: User = Depends(get_admin_user)):
    """Admin: Get platform stats using aggregation pipelines."""
    total_users = await db.users.count_documents({})
    total_rides = await db.rides.count_documents({})
    
    # Aggregate total distance from users
    distance_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$total_distance"}}}]
    distance_result = await db.users.aggregate(distance_pipeline).to_list(1)
    total_distance = distance_result[0]["total"] if distance_result else 0
    
    # Aggregate total VOLTZ distributed from transactions
    rmr_pipeline = [
        {"$match": {"type": {"$in": ["ride_reward", "airdrop_claim", "challenge_reward"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    rmr_result = await db.transactions.aggregate(rmr_pipeline).to_list(1)
    total_rmr_distributed = rmr_result[0]["total"] if rmr_result else 0
    
    return {
        "totalUsers": total_users,
        "totalRides": total_rides,
        "totalDistance": round(total_distance, 2),
        "totalRmrDistributed": round(total_rmr_distributed, 2)
    }

@api_router.post("/admin/make-admin/{user_id}")
async def admin_make_admin(user_id: str, admin: User = Depends(get_admin_user)):
    """Admin: Make another user an admin."""
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.admins.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"success": True}

@api_router.post("/admin/bootstrap")
async def bootstrap_admin(user: User = Depends(get_current_user)):
    """Bootstrap: Make the current user admin if no admins exist yet."""
    admin_count = await db.admins.count_documents({})
    if admin_count > 0:
        raise HTTPException(status_code=403, detail="Admin already exists. Use /admin/make-admin instead.")
    
    await db.admins.insert_one({
        "user_id": user.user_id,
        "promoted_by": "self_bootstrap",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    return {"success": True, "message": "You are now the first admin!"}

@api_router.get("/admin/check")
async def admin_check(user: User = Depends(get_current_user)):
    """Check if current user is admin."""
    admin_doc = await db.admins.find_one({"user_id": user.user_id})
    return {"isAdmin": admin_doc is not None}

@api_router.get("/admin/users")
async def admin_get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    admin: User = Depends(get_admin_user)
):
    """Admin: Get paginated user list."""
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.users.count_documents(query)
    skip = (page - 1) * limit
    
    users = []
    async for u in db.users.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        users.append(u)
    
    # Batch check admin status for all users at once (avoids N+1)
    if users:
        user_ids = [u["user_id"] for u in users]
        admin_docs = await db.admins.find({"user_id": {"$in": user_ids}}, {"user_id": 1}).to_list(None)
        admin_ids = {doc["user_id"] for doc in admin_docs}
        for u in users:
            u["is_admin"] = u["user_id"] in admin_ids
    
    return {"users": users, "total": total, "page": page, "limit": limit, "pages": math.ceil(total / limit) if total > 0 else 1}

@api_router.get("/admin/transactions")
async def admin_get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    type_filter: str = Query(""),
    admin: User = Depends(get_admin_user)
):
    """Admin: Get transaction audit log."""
    query = {}
    if type_filter:
        query["type"] = type_filter
    
    total = await db.transactions.count_documents(query)
    skip = (page - 1) * limit
    
    transactions = []
    async for tx in db.transactions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        transactions.append(tx)
    
    return {"transactions": transactions, "total": total, "page": page, "pages": math.ceil(total / limit) if total > 0 else 1}

@api_router.post("/admin/mint-rmr")
async def admin_mint_rmr(request: Request, admin: User = Depends(get_admin_user)):
    """Admin: Mint VOLTZ to a user or the treasury."""
    body = await request.json()
    target_user_id = body.get("user_id")
    amount = float(body.get("amount", 0))
    reason = body.get("reason", "admin_mint")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    if target_user_id:
        target = await db.users.find_one({"user_id": target_user_id})
        if not target:
            raise HTTPException(status_code=404, detail="User not found")
        
        await db.users.update_one({"user_id": target_user_id}, {"$inc": {"rmr_balance": amount}})
    
    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": target_user_id or "treasury",
        "type": "admin_mint",
        "amount": amount,
        "reference_id": reason,
        "admin_id": admin.user_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    updated = await db.users.find_one({"user_id": target_user_id}, {"_id": 0}) if target_user_id else None
    
    return {"success": True, "amount": amount, "new_balance": updated["rmr_balance"] if updated else None}

@api_router.post("/admin/burn-rmr")
async def admin_burn_rmr(request: Request, admin: User = Depends(get_admin_user)):
    """Admin: Burn/deduct RMR from a user."""
    body = await request.json()
    target_user_id = body.get("user_id")
    amount = float(body.get("amount", 0))
    reason = body.get("reason", "admin_burn")
    
    if not target_user_id or amount <= 0:
        raise HTTPException(status_code=400, detail="user_id and positive amount required")
    
    target = await db.users.find_one({"user_id": target_user_id})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one({"user_id": target_user_id}, {"$inc": {"rmr_balance": -amount}})
    
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": target_user_id,
        "type": "admin_burn",
        "amount": -amount,
        "reference_id": reason,
        "admin_id": admin.user_id,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    updated = await db.users.find_one({"user_id": target_user_id}, {"_id": 0})
    return {"success": True, "amount": amount, "new_balance": updated["rmr_balance"]}

@api_router.get("/admin/rmr-supply")
async def admin_rmr_supply(admin: User = Depends(get_admin_user)):
    """Admin: Get total RMR supply stats using aggregation pipelines."""
    # Total circulating supply
    supply_pipeline = [{"$group": {"_id": None, "total": {"$sum": "$rmr_balance"}}}]
    supply_result = await db.users.aggregate(supply_pipeline).to_list(1)
    total_supply = supply_result[0]["total"] if supply_result else 0
    
    # Total minted by admin
    minted_pipeline = [
        {"$match": {"type": "admin_mint"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    minted_result = await db.transactions.aggregate(minted_pipeline).to_list(1)
    total_minted = minted_result[0]["total"] if minted_result else 0
    
    # Total burned by admin
    burned_pipeline = [
        {"$match": {"type": "admin_burn"}},
        {"$group": {"_id": None, "total": {"$sum": {"$abs": "$amount"}}}}
    ]
    burned_result = await db.transactions.aggregate(burned_pipeline).to_list(1)
    total_burned = burned_result[0]["total"] if burned_result else 0
    
    # Total earned from rewards
    earned_pipeline = [
        {"$match": {"type": {"$in": ["ride_reward", "airdrop_claim", "challenge_reward"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    earned_result = await db.transactions.aggregate(earned_pipeline).to_list(1)
    total_earned = earned_result[0]["total"] if earned_result else 0
    
    return {
        "totalCirculating": round(total_supply, 2),
        "totalMinted": round(total_minted, 2),
        "totalBurned": round(total_burned, 2),
        "totalEarned": round(total_earned, 2),
    }

@api_router.post("/admin/run-dropship-agent")
async def admin_run_dropship_agent(admin: User = Depends(get_admin_user)):
    """Admin: Trigger the dropshipping agent to refresh marketplace."""
    import subprocess
    p = subprocess.Popen(
        ['python3', '/app/backend/dropship_agent.py'],
        stdout=open('/var/log/dropship_agent.log', 'w'),
        stderr=subprocess.STDOUT,
        cwd='/app/backend',
        start_new_session=True
    )
    return {"success": True, "message": "Dropshipping agent started", "pid": p.pid}

@api_router.get("/admin/dropship-status")
async def admin_dropship_status(admin: User = Depends(get_admin_user)):
    """Admin: Check dropship agent status."""
    try:
        product_count = await db.items.count_documents({"source": "dropship_agent"})
        return {"total_dropship_products": product_count, "status": "ready"}
    except Exception:
        return {"total_dropship_products": 0, "status": "unknown"}

@api_router.post("/admin/setup-solana")
async def admin_setup_solana(admin: User = Depends(get_admin_user)):
    """Admin: Run Solana devnet bootstrap (generate keypair, create RMR mint, airdrop SOL)."""
    import subprocess
    p = subprocess.Popen(
        ['python3', '/app/backend/setup_solana.py'],
        stdout=open('/var/log/solana_setup.log', 'w'),
        stderr=subprocess.STDOUT,
        cwd='/app/backend',
        start_new_session=True
    )
    return {"success": True, "message": "Solana setup started. Check /var/log/solana_setup.log for progress.", "pid": p.pid}

@api_router.get("/admin/solana-config")
async def admin_solana_config(admin: User = Depends(get_admin_user)):
    """Admin: Get current Solana configuration status."""
    return {
        "status": solana_service.get_status(),
        "has_private_key": bool(os.environ.get("SOLANA_PRIVATE_KEY")),
        "has_mint_address": bool(os.environ.get("RMR_MINT_ADDRESS")),
        "rpc_url": os.environ.get("SOLANA_RPC_URL", "https://api.devnet.solana.com"),
    }


@api_router.post("/admin/purge-poc-users")
async def admin_purge_poc(admin: User = Depends(get_admin_user)):
    """Admin: Remove all proof-of-concept seed users and their rides/sessions.
    Useful after switching from test users to real Google logins."""
    # Identify POC users by their seeded user_id prefix
    poc_query = {"user_id": {"$regex": "^poc_"}}
    poc_users = await db.users.find(poc_query, {"_id": 0, "user_id": 1}).to_list(None)
    uids = [u["user_id"] for u in poc_users]
    if not uids:
        return {"success": True, "removed": 0, "message": "No POC users found"}
    deleted_users = await db.users.delete_many({"user_id": {"$in": uids}})
    await db.user_sessions.delete_many({"user_id": {"$in": uids}})
    await db.rides.delete_many({"user_id": {"$in": uids}})
    await db.transactions.delete_many({"user_id": {"$in": uids}})
    await db.user_challenges.delete_many({"user_id": {"$in": uids}})
    await db.user_achievements.delete_many({"user_id": {"$in": uids}})
    await db.staking.delete_many({"user_id": {"$in": uids}})
    await db.claims.delete_many({"user_id": {"$in": uids}})
    await db.wallet_balances.delete_many({"user_id": {"$in": uids}})
    await db.admins.delete_many({"user_id": {"$in": uids}})
    await db.carbon_awards.delete_many({"winner_user_id": {"$in": uids}})
    return {"success": True, "removed": deleted_users.deleted_count, "user_ids": uids}

# ============= Image Upload Endpoints =============

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

@api_router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Upload an image for listings."""
    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, png, webp, gif")
    
    # Read file
    data = await file.read()
    
    # Validate size
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    # Generate path
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{user.user_id}/{file_id}.{ext}"
    
    try:
        result = put_object(path, data, file.content_type)
        
        # Store reference in DB
        file_record = {
            "file_id": file_id,
            "user_id": user.user_id,
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": result.get("size", len(data)),
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.files.insert_one(file_record)
        
        return {
            "success": True,
            "file_id": file_id,
            "path": result["path"],
            "url": f"/api/files/{file_id}"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@api_router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    authorization: str = Header(None),
    auth: str = Query(None)
):
    """Retrieve an uploaded file."""
    # Find file record
    record = await db.files.find_one({"file_id": file_id, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        data, content_type = get_object(record["storage_path"])
        return Response(
            content=data,
            media_type=record.get("content_type", content_type),
            headers={"Cache-Control": "public, max-age=86400"}
        )
    except Exception as e:
        logger.error(f"File retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")

# ============= Achievement NFTs =============

ACHIEVEMENT_DEFS = [
    {"id": "first_ride", "title": "First Ride", "description": "Complete your first ride", "icon": "bicycle", "category": "rides", "requirement": 1, "rarity": "common", "rmr_reward": 5},
    {"id": "10_rides", "title": "Road Warrior", "description": "Complete 10 rides", "icon": "fire", "category": "rides", "requirement": 10, "rarity": "uncommon", "rmr_reward": 25},
    {"id": "50_rides", "title": "Legendary Rider", "description": "Complete 50 rides", "icon": "trophy", "category": "rides", "requirement": 50, "rarity": "epic", "rmr_reward": 100},
    {"id": "10km", "title": "10K Explorer", "description": "Ride a total of 10 km", "icon": "map", "category": "distance", "requirement": 10, "rarity": "common", "rmr_reward": 10},
    {"id": "50km", "title": "50K Voyager", "description": "Ride a total of 50 km", "icon": "globe", "category": "distance", "requirement": 50, "rarity": "uncommon", "rmr_reward": 50},
    {"id": "100km", "title": "Century Rider", "description": "Ride a total of 100 km", "icon": "medal", "category": "distance", "requirement": 100, "rarity": "rare", "rmr_reward": 100},
    {"id": "500km", "title": "Unstoppable", "description": "Ride a total of 500 km", "icon": "lightning", "category": "distance", "requirement": 500, "rarity": "legendary", "rmr_reward": 500},
    {"id": "first_airdrop", "title": "Treasure Hunter", "description": "Claim your first airdrop", "icon": "gift", "category": "airdrops", "requirement": 1, "rarity": "common", "rmr_reward": 5},
    {"id": "first_challenge", "title": "Challenger", "description": "Complete your first challenge", "icon": "target", "category": "challenges", "requirement": 1, "rarity": "common", "rmr_reward": 10},
    {"id": "5_challenges", "title": "Quest Master", "description": "Complete 5 challenges", "icon": "crown", "category": "challenges", "requirement": 5, "rarity": "rare", "rmr_reward": 75},
    {"id": "first_purchase", "title": "Shopper", "description": "Make your first marketplace purchase", "icon": "cart", "category": "marketplace", "requirement": 1, "rarity": "common", "rmr_reward": 5},
    {"id": "wallet_linked", "title": "Web3 Native", "description": "Link a Solana wallet", "icon": "wallet", "category": "wallet", "requirement": 1, "rarity": "uncommon", "rmr_reward": 15},
    {"id": "level_5", "title": "Rising Star", "description": "Reach level 5", "icon": "star", "category": "level", "requirement": 5, "rarity": "uncommon", "rmr_reward": 25},
    {"id": "level_10", "title": "Elite Rider", "description": "Reach level 10", "icon": "diamond", "category": "level", "requirement": 10, "rarity": "epic", "rmr_reward": 100},
]

@api_router.get("/achievements")
async def get_achievements(user: User = Depends(get_current_user)):
    """Get all achievements and user's unlock status."""
    earned = await db.user_achievements.find({"user_id": user.user_id}, {"_id": 0}).to_list(None)
    earned_ids = {a["achievement_id"] for a in earned}

    # Calculate user progress
    total_rides = user.total_rides
    total_distance = user.total_distance
    airdrops_claimed = await db.transactions.count_documents({"user_id": user.user_id, "type": "airdrop_claim"})
    challenges_done = await db.transactions.count_documents({"user_id": user.user_id, "type": "challenge_reward"})
    purchases = await db.purchases.count_documents({"user_id": user.user_id})
    wallet_linked = 1 if user.wallet_address else 0

    progress_map = {
        "rides": total_rides,
        "distance": total_distance,
        "airdrops": airdrops_claimed,
        "challenges": challenges_done,
        "marketplace": purchases,
        "wallet": wallet_linked,
        "level": user.level,
    }

    results = []
    for a in ACHIEVEMENT_DEFS:
        current = progress_map.get(a["category"], 0)
        unlocked = a["id"] in earned_ids
        earned_data = next((e for e in earned if e["achievement_id"] == a["id"]), None)
        results.append({
            **a,
            "progress": min(current, a["requirement"]),
            "unlocked": unlocked,
            "claimed": earned_data.get("claimed", False) if earned_data else False,
            "unlocked_at": earned_data.get("unlocked_at") if earned_data else None,
            "nft_signature": earned_data.get("nft_signature") if earned_data else None,
        })
    return results

@api_router.post("/achievements/{achievement_id}/claim")
async def claim_achievement(achievement_id: str, user: User = Depends(get_current_user)):
    """Claim an unlocked achievement to receive RMR reward."""
    ach_def = next((a for a in ACHIEVEMENT_DEFS if a["id"] == achievement_id), None)
    if not ach_def:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # Check if already claimed
    existing = await db.user_achievements.find_one(
        {"user_id": user.user_id, "achievement_id": achievement_id}, {"_id": 0}
    )
    if existing and existing.get("claimed"):
        raise HTTPException(status_code=400, detail="Already claimed")

    # Check progress
    progress_map = {
        "rides": user.total_rides,
        "distance": user.total_distance,
        "airdrops": await db.transactions.count_documents({"user_id": user.user_id, "type": "airdrop_claim"}),
        "challenges": await db.transactions.count_documents({"user_id": user.user_id, "type": "challenge_reward"}),
        "marketplace": await db.purchases.count_documents({"user_id": user.user_id}),
        "wallet": 1 if user.wallet_address else 0,
        "level": user.level,
    }
    current = progress_map.get(ach_def["category"], 0)
    if current < ach_def["requirement"]:
        raise HTTPException(status_code=400, detail=f"Not yet unlocked. Progress: {current}/{ach_def['requirement']}")

    # Mint NFT (demo or live)
    nft_sig = None
    mode = "demo"
    if solana_service.is_real_mode() and user.wallet_address:
        result = solana_service.mint_tokens(user.wallet_address, 0)  # NFT placeholder
        nft_sig = result.get("signature")
        mode = "live"

    now = datetime.now(timezone.utc).isoformat()
    await db.user_achievements.update_one(
        {"user_id": user.user_id, "achievement_id": achievement_id},
        {"$set": {
            "user_id": user.user_id,
            "achievement_id": achievement_id,
            "unlocked_at": now,
            "claimed": True,
            "claimed_at": now,
            "nft_signature": nft_sig,
            "mode": mode,
            "rmr_reward": ach_def["rmr_reward"],
        }},
        upsert=True
    )

    # Credit RMR reward
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": ach_def["rmr_reward"]}}
    )
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "achievement_reward",
        "amount": ach_def["rmr_reward"],
        "reference_id": achievement_id,
        "status": "completed",
        "created_at": now,
    })

    updated = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return {
        "success": True,
        "achievement": ach_def["title"],
        "rarity": ach_def["rarity"],
        "rmr_earned": ach_def["rmr_reward"],
        "new_balance": updated["rmr_balance"],
        "nft_signature": nft_sig,
        "mode": mode,
    }

# ============= RMR Staking =============

STAKING_TIERS = {
    "7d": {"days": 7, "apy": 5.0, "label": "7 Days", "min_amount": 10},
    "30d": {"days": 30, "apy": 12.0, "label": "30 Days", "min_amount": 50},
    "90d": {"days": 90, "apy": 25.0, "label": "90 Days", "min_amount": 100},
}

class StakeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    tier: str = Field(..., description="7d, 30d, or 90d")

@api_router.get("/staking/tiers")
async def get_staking_tiers():
    """Get available staking tiers with APY rates."""
    return [{"id": k, **v} for k, v in STAKING_TIERS.items()]

@api_router.get("/staking/positions")
async def get_staking_positions(user: User = Depends(get_current_user)):
    """Get user's active and completed staking positions."""
    positions = await db.staking.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(None)

    now = datetime.now(timezone.utc)
    for pos in positions:
        unlock_at = datetime.fromisoformat(pos["unlock_at"])
        if unlock_at.tzinfo is None:
            unlock_at = unlock_at.replace(tzinfo=timezone.utc)
        pos["is_unlocked"] = now >= unlock_at
        elapsed = min((now - datetime.fromisoformat(pos["created_at"]).replace(tzinfo=timezone.utc)).days, pos["lock_days"])
        pos["earned_so_far"] = round(pos["amount"] * (pos["apy"] / 100) * (elapsed / 365), 2)

    return positions

@api_router.post("/staking/stake")
async def stake_rmr(req: StakeRequest, user: User = Depends(get_current_user)):
    """Stake VOLTZ tokens for bonus rewards. Higher APY tiers require Pro/VIP subscription."""
    tier = STAKING_TIERS.get(req.tier)
    if not tier:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Choose from: {', '.join(STAKING_TIERS.keys())}")

    if req.amount < tier["min_amount"]:
        raise HTTPException(status_code=400, detail=f"Minimum stake for {tier['label']} is {tier['min_amount']} VOLTZ")

    if req.amount > user.rmr_balance:
        raise HTTPException(status_code=400, detail="Insufficient VOLTZ balance")

    # Enforce subscription-tier APY cap
    sub_tier = await get_user_tier(user.user_id)
    apy_cap = SUBSCRIPTION_TIERS[sub_tier]["staking_apy_max"]
    if tier["apy"] > apy_cap:
        raise HTTPException(
            status_code=403,
            detail=f"This staking tier ({tier['apy']}% APY) requires a higher membership. Your {sub_tier.upper()} tier caps at {apy_cap}% APY. Upgrade at /subscription."
        )

    now = datetime.now(timezone.utc)
    unlock_at = now + timedelta(days=tier["days"])
    expected_reward = round(req.amount * (tier["apy"] / 100) * (tier["days"] / 365), 2)

    stake_id = f"stake_{uuid.uuid4().hex[:12]}"
    await db.staking.insert_one({
        "stake_id": stake_id,
        "user_id": user.user_id,
        "amount": req.amount,
        "tier": req.tier,
        "apy": tier["apy"],
        "lock_days": tier["days"],
        "expected_reward": expected_reward,
        "status": "active",
        "created_at": now.isoformat(),
        "unlock_at": unlock_at.isoformat(),
    })

    # Deduct staked amount from balance
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": -req.amount}}
    )
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "stake_lock",
        "amount": -req.amount,
        "reference_id": stake_id,
        "status": "completed",
        "created_at": now.isoformat(),
    })

    updated = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return {
        "success": True,
        "stake_id": stake_id,
        "amount": req.amount,
        "tier": tier["label"],
        "apy": tier["apy"],
        "expected_reward": expected_reward,
        "unlock_at": unlock_at.isoformat(),
        "new_balance": updated["rmr_balance"],
    }

@api_router.post("/staking/{stake_id}/unstake")
async def unstake_rmr(stake_id: str, user: User = Depends(get_current_user)):
    """Unstake VOLTZ tokens and collect rewards (if lock period is over)."""
    pos = await db.staking.find_one({"stake_id": stake_id, "user_id": user.user_id}, {"_id": 0})
    if not pos:
        raise HTTPException(status_code=404, detail="Staking position not found")

    if pos["status"] != "active":
        raise HTTPException(status_code=400, detail="Position already unstaked")

    now = datetime.now(timezone.utc)
    unlock_at = datetime.fromisoformat(pos["unlock_at"])
    if unlock_at.tzinfo is None:
        unlock_at = unlock_at.replace(tzinfo=timezone.utc)

    if now < unlock_at:
        # Early unstake — no rewards, 5% penalty
        penalty = round(pos["amount"] * 0.05, 2)
        return_amount = pos["amount"] - penalty
        reward = 0
        status = "early_unstaked"
    else:
        # Full reward — cap elapsed at lock period
        elapsed = min(
            (now - datetime.fromisoformat(pos["created_at"]).replace(tzinfo=timezone.utc)).days,
            pos["lock_days"]
        )
        reward = round(pos["amount"] * (pos["apy"] / 100) * (elapsed / 365), 2)
        return_amount = pos["amount"]
        penalty = 0
        status = "completed"

    await db.staking.update_one(
        {"stake_id": stake_id},
        {"$set": {"status": status, "actual_reward": reward, "penalty": penalty, "unstaked_at": now.isoformat()}}
    )

    total_credit = return_amount + reward
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": total_credit}}
    )
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "stake_unlock",
        "amount": total_credit,
        "reference_id": stake_id,
        "status": "completed",
        "created_at": now.isoformat(),
    })
    if penalty > 0:
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "stake_penalty",
            "amount": -penalty,
            "reference_id": stake_id,
            "status": "completed",
            "created_at": now.isoformat(),
        })
    if reward > 0:
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "stake_reward",
            "amount": reward,
            "reference_id": stake_id,
            "status": "completed",
            "created_at": now.isoformat(),
        })

    updated = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return {
        "success": True,
        "principal": pos["amount"],
        "reward": reward,
        "penalty": penalty,
        "total_returned": total_credit,
        "status": status,
        "new_balance": updated["rmr_balance"],
    }

# ============= Solana Token Endpoints =============

class MintRequest(BaseModel):
    amount: float = Field(..., description="Amount of VOLTZ to mint to wallet")

class TransferRequest(BaseModel):
    to_wallet: str = Field(..., description="Recipient Solana wallet address")
    amount: float = Field(..., description="Amount of VOLTZ to transfer")

@api_router.post("/solana/mint")
async def mint_rmr_tokens(mint_req: MintRequest, user: User = Depends(get_current_user)):
    """Mint VOLTZ tokens to user's linked Solana wallet."""
    if not user.wallet_address:
        raise HTTPException(status_code=400, detail="No wallet linked. Please link a Solana wallet first.")
    if mint_req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if mint_req.amount > user.rmr_balance:
        raise HTTPException(status_code=400, detail="Insufficient VOLTZ balance")

    # Call Solana service (real or demo)
    result = solana_service.mint_tokens(user.wallet_address, mint_req.amount)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Minting failed"))

    # Deduct from in-app balance
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": -mint_req.amount}}
    )

    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "type": "mint_to_wallet",
        "amount": -mint_req.amount,
        "reference_id": result["transaction_id"],
        "wallet_address": user.wallet_address,
        "signature": result.get("signature"),
        "status": "confirmed" if result.get("signature") else "pending",
        "minting_mode": result["mode"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Update on-chain balance tracking
    await db.wallet_balances.update_one(
        {"user_id": user.user_id, "wallet_address": user.wallet_address},
        {"$inc": {"on_chain_balance": mint_req.amount}},
        upsert=True
    )

    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    return {
        "success": True,
        "transaction_id": result["transaction_id"],
        "amount_minted": mint_req.amount,
        "wallet_address": user.wallet_address,
        "new_in_app_balance": updated_user["rmr_balance"],
        "minting_mode": result["mode"],
        "signature": result.get("signature"),
        "explorer_url": result.get("explorer") or f"https://explorer.solana.com/address/{user.wallet_address}?cluster=devnet",
        "message": f"{'Minted' if result['mode'] == 'live' else 'Queued'} {mint_req.amount} VOLTZ to your wallet",
    }

@api_router.post("/solana/transfer")
async def transfer_rmr_tokens(req: TransferRequest, user: User = Depends(get_current_user)):
    """Transfer VOLTZ tokens to another Solana wallet (P2P)."""
    if not user.wallet_address:
        raise HTTPException(status_code=400, detail="No wallet linked")
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if req.amount > user.rmr_balance:
        raise HTTPException(status_code=400, detail="Insufficient VOLTZ balance")
    if req.to_wallet == user.wallet_address:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    # For demo mode, handle in-app; for live, do on-chain
    mode = "live" if solana_service.is_real_mode() else "demo"
    tx_id = f"transfer_{uuid.uuid4().hex[:12]}"

    # Deduct sender balance
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$inc": {"rmr_balance": -req.amount}}
    )

    # Credit recipient if they exist in our system
    recipient = await db.users.find_one({"wallet_address": req.to_wallet}, {"_id": 0})
    if recipient:
        await db.users.update_one(
            {"user_id": recipient["user_id"]},
            {"$inc": {"rmr_balance": req.amount}}
        )

    # Record transactions
    await db.transactions.insert_one({
        "transaction_id": tx_id,
        "user_id": user.user_id,
        "type": "transfer_out",
        "amount": -req.amount,
        "reference_id": req.to_wallet,
        "status": "completed",
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    if recipient:
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": recipient["user_id"],
            "type": "transfer_in",
            "amount": req.amount,
            "reference_id": user.wallet_address,
            "status": "completed",
            "mode": mode,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})

    return {
        "success": True,
        "transaction_id": tx_id,
        "amount": req.amount,
        "from_wallet": user.wallet_address,
        "to_wallet": req.to_wallet,
        "new_balance": updated_user["rmr_balance"],
        "mode": mode,
        "recipient_found": recipient is not None,
    }

@api_router.get("/solana/balance/{wallet_address}")
async def get_onchain_balance(wallet_address: str):
    """Get on-chain VOLTZ token balance for any wallet."""
    result = solana_service.get_balance(wallet_address)
    return result

@api_router.get("/solana/status")
async def get_solana_status():
    """Check Solana connection and VOLTZ token status."""
    return solana_service.get_status()

# ============= Marketplace SOL Payment =============

class MarketplacePurchase(BaseModel):
    item_id: str
    payment_method: str = Field(..., description="rmr or sol")

@api_router.post("/marketplace/purchase")
async def purchase_marketplace_item(req: MarketplacePurchase, user: User = Depends(get_current_user)):
    """Purchase a marketplace item with RMR or SOL."""
    item = await db.items.find_one({"item_id": req.item_id, "is_available": True}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or unavailable")

    if req.payment_method == "rmr":
        price = item.get("price_rmr", 0)
        if price <= 0:
            raise HTTPException(status_code=400, detail="Item has no VOLTZ price")
        if user.rmr_balance < price:
            raise HTTPException(status_code=400, detail=f"Insufficient VOLTZ. Need {price}, have {user.rmr_balance:.2f}")

        await db.users.update_one({"user_id": user.user_id}, {"$inc": {"rmr_balance": -price}})
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "marketplace_purchase",
            "amount": -price,
            "reference_id": req.item_id,
            "payment_method": "rmr",
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    elif req.payment_method == "sol":
        price_sol = item.get("price_sol")
        if not price_sol:
            # Auto-convert: 1 SOL = ~1000 VOLTZ (configurable rate)
            sol_rate = float(os.environ.get("SOL_TO_RMR_RATE", "1000"))
            price_sol = round(item.get("price_rmr", 0) / sol_rate, 4)

        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "marketplace_purchase",
            "amount": -item.get("price_rmr", 0),
            "reference_id": req.item_id,
            "payment_method": "sol",
            "sol_amount": price_sol,
            "status": "pending_sol_confirmation",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Record purchase for SOL payment
        await db.purchases.insert_one({
            "purchase_id": f"pur_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "item_id": req.item_id,
            "item_name": item.get("name"),
            "price_rmr": item.get("price_rmr"),
            "price_sol": price_sol,
            "payment_method": "sol",
            "status": "pending_sol_confirmation",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Decrease stock for SOL payment too
        if item.get("stock", 0) > 0:
            await db.items.update_one({"item_id": req.item_id}, {"$inc": {"stock": -1}})

        return {
            "success": True,
            "payment_method": "sol",
            "sol_amount": price_sol,
            "item": item.get("name"),
            "status": "pending",
            "note": "Send SOL to the treasury wallet to complete purchase",
            "treasury_wallet": solana_service.RMR_TREASURY_ATA or "configure_treasury",
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method. Use 'rmr' or 'sol'")

    # Record purchase
    await db.purchases.insert_one({
        "purchase_id": f"pur_{uuid.uuid4().hex[:12]}",
        "user_id": user.user_id,
        "item_id": req.item_id,
        "item_name": item.get("name"),
        "price_rmr": item.get("price_rmr"),
        "payment_method": req.payment_method,
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Decrease stock
    if item.get("stock", 0) > 0:
        await db.items.update_one({"item_id": req.item_id}, {"$inc": {"stock": -1}})

    updated_user = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return {
        "success": True,
        "payment_method": "rmr",
        "item": item.get("name"),
        "price_paid": item.get("price_rmr"),
        "new_balance": updated_user["rmr_balance"],
    }

# ============= Carbon Footprint =============
# CO2 emissions in grams per kilometer for each vehicle type vs a typical gasoline car (170 g/km)
# Sources: IEA / EU EEA averages for life-cycle emissions

CAR_BASELINE_G_PER_KM = 170.0  # avg compact car

VEHICLE_CO2_G_PER_KM = {
    "bicycle": 0.0,
    "skateboard": 0.0,
    "ebike": 6.0,
    "electric_skateboard": 5.0,
    "onewheel": 5.0,
    "euc": 5.0,
    "dirt_bike": 250.0,           # gas-powered dirt bike (heavier emissions than car)
    "electric_dirt_bike": 12.0,
}

VEHICLE_LABELS = {
    "bicycle": "Bicycle",
    "skateboard": "Skateboard",
    "ebike": "E-Bike",
    "electric_skateboard": "E-Skateboard",
    "onewheel": "Onewheel",
    "euc": "Electric Unicycle",
    "dirt_bike": "Dirt Bike",
    "electric_dirt_bike": "Electric Dirt Bike",
}

def calc_co2_saved_kg(distance_km: float, vehicle_type: str) -> dict:
    """Calculate CO2 saved (kg) vs a typical car for a given distance & vehicle."""
    if distance_km <= 0:
        return {"saved_kg": 0.0, "emitted_kg": 0.0, "car_kg": 0.0}
    veh_g = VEHICLE_CO2_G_PER_KM.get(vehicle_type, 6.0)  # default to ebike
    car_g_total = CAR_BASELINE_G_PER_KM * distance_km
    veh_g_total = veh_g * distance_km
    saved_g = max(0.0, car_g_total - veh_g_total)
    return {
        "saved_kg": round(saved_g / 1000.0, 3),
        "emitted_kg": round(veh_g_total / 1000.0, 3),
        "car_kg": round(car_g_total / 1000.0, 3),
    }

def month_range_utc(year: Optional[int] = None, month: Optional[int] = None) -> tuple:
    """Return (start_iso, end_iso) for a given UTC month. Defaults to current month."""
    now = datetime.now(timezone.utc)
    y = year or now.year
    m = month or now.month
    start = datetime(y, m, 1, tzinfo=timezone.utc)
    if m == 12:
        end = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(y, m + 1, 1, tzinfo=timezone.utc)
    return start.isoformat(), end.isoformat(), y, m

async def aggregate_user_carbon(user_id: str, start_iso: Optional[str] = None, end_iso: Optional[str] = None) -> dict:
    """Aggregate CO2 saved per user across rides within an optional date range."""
    query: Dict[str, Any] = {"user_id": user_id, "status": "completed"}
    if start_iso and end_iso:
        query["end_time"] = {"$gte": start_iso, "$lt": end_iso}

    totals = {"distance_km": 0.0, "saved_kg": 0.0, "emitted_kg": 0.0, "car_kg": 0.0, "rides": 0}
    by_vehicle: Dict[str, dict] = {}

    async for r in db.rides.find(query, {"_id": 0}):
        distance = float(r.get("distance", 0) or 0)
        vt = r.get("vehicle_type") or "ebike"
        co2 = calc_co2_saved_kg(distance, vt)
        totals["distance_km"] += distance
        totals["saved_kg"] += co2["saved_kg"]
        totals["emitted_kg"] += co2["emitted_kg"]
        totals["car_kg"] += co2["car_kg"]
        totals["rides"] += 1
        if vt not in by_vehicle:
            by_vehicle[vt] = {
                "vehicle": vt,
                "label": VEHICLE_LABELS.get(vt, vt),
                "distance_km": 0.0, "saved_kg": 0.0, "rides": 0,
                "g_per_km": VEHICLE_CO2_G_PER_KM.get(vt, 6.0),
            }
        by_vehicle[vt]["distance_km"] += distance
        by_vehicle[vt]["saved_kg"] += co2["saved_kg"]
        by_vehicle[vt]["rides"] += 1

    # round
    for k in ("distance_km", "saved_kg", "emitted_kg", "car_kg"):
        totals[k] = round(totals[k], 3)
    for v in by_vehicle.values():
        v["distance_km"] = round(v["distance_km"], 3)
        v["saved_kg"] = round(v["saved_kg"], 3)

    # equivalent metrics
    saved_kg = totals["saved_kg"]
    totals["trees_equivalent"] = round(saved_kg / 21.77, 2)   # 1 mature tree absorbs ~21.77 kg CO2/yr
    totals["car_km_offset"] = round(saved_kg * 1000 / CAR_BASELINE_G_PER_KM, 2)
    totals["smartphone_charges"] = round(saved_kg * 1000 / 8.22, 1)  # 8.22 g CO2 per phone charge

    return {"totals": totals, "by_vehicle": list(by_vehicle.values())}


@api_router.get("/carbon/me")
async def carbon_me(user: User = Depends(get_current_user)):
    """Get the current user's lifetime + this-month CO2 savings."""
    lifetime = await aggregate_user_carbon(user.user_id)
    start_iso, end_iso, year, month = month_range_utc()
    monthly = await aggregate_user_carbon(user.user_id, start_iso, end_iso)

    # Find this user's rank in the monthly leaderboard
    pipeline = [
        {"$match": {"status": "completed", "end_time": {"$gte": start_iso, "$lt": end_iso}}},
        {"$group": {"_id": "$user_id", "total_distance": {"$sum": "$distance"}, "rides": {"$sum": 1}}},
    ]
    rows = await db.rides.aggregate(pipeline).to_list(None)

    # For monthly rank we need CO2 saved per user; recompute simply (we already group rides by user)
    # use distance + most-used vehicle for that user; safer: re-aggregate per user
    user_saved: Dict[str, float] = {}
    for row in rows:
        agg = await aggregate_user_carbon(row["_id"], start_iso, end_iso)
        user_saved[row["_id"]] = agg["totals"]["saved_kg"]

    ranked = sorted(user_saved.items(), key=lambda x: x[1], reverse=True)
    rank = next((i + 1 for i, (uid, _v) in enumerate(ranked) if uid == user.user_id), None)
    total_riders = len(ranked)

    return {
        "user_id": user.user_id,
        "lifetime": lifetime,
        "monthly": monthly,
        "month": {"year": year, "month": month, "label": datetime(year, month, 1).strftime("%B %Y")},
        "monthly_rank": rank,
        "monthly_total_riders": total_riders,
        "car_baseline_g_per_km": CAR_BASELINE_G_PER_KM,
        "vehicle_emissions_g_per_km": VEHICLE_CO2_G_PER_KM,
    }


@api_router.get("/carbon/leaderboard")
async def carbon_leaderboard(year: Optional[int] = None, month: Optional[int] = None, limit: int = 25):
    """Get the monthly carbon-saved leaderboard. Defaults to current UTC month."""
    start_iso, end_iso, y, m = month_range_utc(year, month)

    # Group rides by user
    pipeline = [
        {"$match": {"status": "completed", "end_time": {"$gte": start_iso, "$lt": end_iso}}},
        {"$group": {
            "_id": "$user_id",
            "total_distance": {"$sum": "$distance"},
            "rides": {"$sum": 1},
        }},
    ]
    rows = await db.rides.aggregate(pipeline).to_list(None)

    out = []
    for row in rows:
        agg = await aggregate_user_carbon(row["_id"], start_iso, end_iso)
        user_doc = await db.users.find_one(
            {"user_id": row["_id"]},
            {"_id": 0, "user_id": 1, "first_name": 1, "last_name": 1, "name": 1, "username": 1, "picture": 1, "vehicle_type": 1, "wallet_address": 1}
        )
        if not user_doc:
            continue
        out.append({
            **user_doc,
            "distance_km": agg["totals"]["distance_km"],
            "saved_kg": agg["totals"]["saved_kg"],
            "rides": agg["totals"]["rides"],
            "trees_equivalent": agg["totals"]["trees_equivalent"],
            "primary_vehicle": agg["by_vehicle"][0]["vehicle"] if agg["by_vehicle"] else (user_doc.get("vehicle_type") or "ebike"),
        })

    out.sort(key=lambda x: x["saved_kg"], reverse=True)
    out = out[:limit]

    # Get the awarded winner for the month (if any)
    award = await db.carbon_awards.find_one({"year": y, "month": m}, {"_id": 0})

    return {
        "month": {"year": y, "month": m, "label": datetime(y, m, 1).strftime("%B %Y")},
        "leaderboard": out,
        "awarded": award,
        "total_riders": len(rows),
    }


@api_router.get("/carbon/stats")
async def carbon_stats():
    """Get global community carbon stats (lifetime)."""
    total_saved = 0.0
    total_distance = 0.0
    rides_count = 0
    by_vehicle: Dict[str, dict] = {}

    async for r in db.rides.find({"status": "completed"}, {"_id": 0, "distance": 1, "vehicle_type": 1}):
        distance = float(r.get("distance", 0) or 0)
        vt = r.get("vehicle_type") or "ebike"
        co2 = calc_co2_saved_kg(distance, vt)
        total_saved += co2["saved_kg"]
        total_distance += distance
        rides_count += 1
        if vt not in by_vehicle:
            by_vehicle[vt] = {
                "vehicle": vt,
                "label": VEHICLE_LABELS.get(vt, vt),
                "distance_km": 0.0,
                "saved_kg": 0.0,
                "rides": 0,
            }
        by_vehicle[vt]["distance_km"] += distance
        by_vehicle[vt]["saved_kg"] += co2["saved_kg"]
        by_vehicle[vt]["rides"] += 1

    for v in by_vehicle.values():
        v["distance_km"] = round(v["distance_km"], 3)
        v["saved_kg"] = round(v["saved_kg"], 3)

    return {
        "total_saved_kg": round(total_saved, 3),
        "total_distance_km": round(total_distance, 3),
        "total_rides": rides_count,
        "trees_equivalent": round(total_saved / 21.77, 2),
        "car_km_offset": round(total_saved * 1000 / CAR_BASELINE_G_PER_KM, 2),
        "by_vehicle": list(by_vehicle.values()),
        "car_baseline_g_per_km": CAR_BASELINE_G_PER_KM,
    }


# Admin Carbon
class AwardCarbonRequest(BaseModel):
    year: Optional[int] = None
    month: Optional[int] = None
    reward_rmr: float = Field(default=500.0, gt=0)

@api_router.get("/admin/carbon/monthly")
async def admin_carbon_monthly(year: Optional[int] = None, month: Optional[int] = None, admin: User = Depends(get_admin_user)):
    """Admin: Get full monthly carbon stats (all riders + global)."""
    lb = await carbon_leaderboard(year=year, month=month, limit=1000)
    start_iso, end_iso, y, m = month_range_utc(year, month)

    total_saved = sum(r["saved_kg"] for r in lb["leaderboard"])
    total_distance = sum(r["distance_km"] for r in lb["leaderboard"])
    total_rides = sum(r["rides"] for r in lb["leaderboard"])

    return {
        "month": lb["month"],
        "leaderboard": lb["leaderboard"],
        "awarded": lb["awarded"],
        "totals": {
            "saved_kg": round(total_saved, 3),
            "distance_km": round(total_distance, 3),
            "rides": total_rides,
            "trees_equivalent": round(total_saved / 21.77, 2),
            "active_riders": len(lb["leaderboard"]),
        },
    }


@api_router.post("/admin/carbon/award-winner")
async def admin_carbon_award(req: AwardCarbonRequest, admin: User = Depends(get_admin_user)):
    """Admin: Award the top eco-rider for a given month with VOLTZ airdrop (on-chain if wallet linked)."""
    start_iso, end_iso, y, m = month_range_utc(req.year, req.month)

    # Check if already awarded for that month
    existing = await db.carbon_awards.find_one({"year": y, "month": m})
    if existing:
        raise HTTPException(status_code=400, detail=f"{datetime(y, m, 1).strftime('%B %Y')} winner already awarded.")

    # Compute leaderboard
    lb_res = await carbon_leaderboard(year=y, month=m, limit=5)
    leaders = lb_res["leaderboard"]
    if not leaders:
        raise HTTPException(status_code=400, detail="No eligible rides for this month")

    winner = leaders[0]
    winner_user = await db.users.find_one({"user_id": winner["user_id"]}, {"_id": 0})
    if not winner_user:
        raise HTTPException(status_code=404, detail="Winner user not found")

    # Credit in-app RMR balance
    await db.users.update_one(
        {"user_id": winner_user["user_id"]},
        {"$inc": {"rmr_balance": req.reward_rmr}}
    )

    # If wallet linked, try to mint on-chain via Solana service
    sol_signature = None
    sol_mode = "in_app_only"
    if winner_user.get("wallet_address"):
        try:
            mint_res = solana_service.mint_tokens(winner_user["wallet_address"], req.reward_rmr)
            if mint_res.get("success"):
                sol_signature = mint_res.get("signature")
                sol_mode = mint_res.get("mode", "demo")
                # Track on-chain balance
                await db.wallet_balances.update_one(
                    {"user_id": winner_user["user_id"], "wallet_address": winner_user["wallet_address"]},
                    {"$inc": {"on_chain_balance": req.reward_rmr}},
                    upsert=True
                )
        except Exception as e:
            logger.error(f"Carbon airdrop on-chain mint failed: {e}")

    award_doc = {
        "award_id": f"carbon_award_{uuid.uuid4().hex[:12]}",
        "year": y,
        "month": m,
        "month_label": datetime(y, m, 1).strftime("%B %Y"),
        "winner_user_id": winner_user["user_id"],
        "winner_email": winner_user.get("email"),
        "winner_name": winner_user.get("name") or (winner_user.get("first_name", "") + " " + winner_user.get("last_name", "")).strip(),
        "winner_wallet": winner_user.get("wallet_address"),
        "saved_kg": winner["saved_kg"],
        "distance_km": winner["distance_km"],
        "rides": winner["rides"],
        "reward_rmr": req.reward_rmr,
        "sol_mode": sol_mode,
        "sol_signature": sol_signature,
        "explorer_url": f"https://explorer.solana.com/tx/{sol_signature}?cluster=devnet" if sol_signature else None,
        "awarded_by": admin.user_id,
        "awarded_at": datetime.now(timezone.utc).isoformat(),
        "runners_up": leaders[1:3] if len(leaders) > 1 else [],
    }
    await db.carbon_awards.insert_one(award_doc)
    award_doc.pop("_id", None)

    # Record transaction
    await db.transactions.insert_one({
        "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
        "user_id": winner_user["user_id"],
        "type": "carbon_award",
        "amount": req.reward_rmr,
        "reference_id": award_doc["award_id"],
        "admin_id": admin.user_id,
        "status": "completed",
        "sol_signature": sol_signature,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    return {"success": True, "award": award_doc}


@api_router.get("/carbon/awards")
async def carbon_awards_history(limit: int = 12):
    """Get the history of monthly carbon-saved award winners."""
    awards = await db.carbon_awards.find({}, {"_id": 0}).sort("awarded_at", -1).limit(limit).to_list(limit)
    return awards


# ============= Subscription Tiers =============

SUBSCRIPTION_TIERS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price_cad": 0,
        "price_rmr": 0,
        "min_stake_rmr": 0,
        "earn_multiplier": 1.0,
        "staking_apy_max": 5,
        "vote_power": 0,
        "can_propose": False,
        "early_airdrops": False,
        "exclusive_marketplace": False,
        "features": [
            "GPS ride tracking",
            "Earn VOLTZ per km",
            "Marketplace access",
            "Achievements & quests",
        ],
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_cad": 9.99,
        "price_rmr": 500,
        "min_stake_rmr": 0,
        "earn_multiplier": 1.25,
        "staking_apy_max": 12,
        "vote_power": 1,
        "can_propose": False,
        "early_airdrops": True,
        "exclusive_marketplace": False,
        "features": [
            "1.25x VOLTZ earning multiplier",
            "30-day staking with 12% APY",
            "Early access to airdrops",
            "1 vote on governance proposals",
            "Pro badge",
        ],
    },
    "vip": {
        "id": "vip",
        "name": "VIP",
        "price_cad": 29.99,
        "price_rmr": 2000,
        "min_stake_rmr": 5000,
        "earn_multiplier": 1.5,
        "staking_apy_max": 25,
        "vote_power": 10,
        "can_propose": True,
        "early_airdrops": True,
        "exclusive_marketplace": True,
        "features": [
            "1.5x VOLTZ earning multiplier",
            "90-day staking with 25% APY",
            "Early access to all airdrops",
            "10 votes per proposal",
            "Create governance proposals",
            "Exclusive VIP marketplace items",
            "VIP badge",
        ],
    },
}


async def get_user_tier(user_id: str) -> str:
    """Return the user's current active subscription tier. Auto-downgrades expired ones.
    Also auto-promotes to VIP if they have >= 5000 VOLTZ staked (active stakes)."""
    sub = await db.subscriptions.find_one({"user_id": user_id, "status": "active"}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    if sub and sub.get("expires_at") and sub["expires_at"] < now:
        await db.subscriptions.update_one({"user_id": user_id, "status": "active"}, {"$set": {"status": "expired"}})
        sub = None

    # Stake-based VIP check
    active_stakes = await db.staking.find({"user_id": user_id, "status": "active"}, {"_id": 0, "amount": 1, "tier": 1}).to_list(None)
    total_staked = sum(s["amount"] for s in active_stakes)
    if total_staked >= SUBSCRIPTION_TIERS["vip"]["min_stake_rmr"]:
        return "vip"

    if sub:
        return sub.get("tier", "free")
    return "free"


async def voting_power(user_id: str) -> Dict[str, Any]:
    """Voting power = tier base + bonus from staked VOLTZ (1 per 1000 RMR, capped at 20)."""
    tier = await get_user_tier(user_id)
    base = SUBSCRIPTION_TIERS[tier]["vote_power"]
    stakes = await db.staking.find({"user_id": user_id, "status": "active"}, {"_id": 0, "amount": 1}).to_list(None)
    staked = sum(s["amount"] for s in stakes)
    bonus = min(20, int(staked / 1000))
    return {"tier": tier, "base": base, "bonus": bonus, "total": base + bonus, "staked": staked}


@api_router.get("/subscriptions/tiers")
async def list_tiers():
    """Public: list all subscription tiers."""
    return list(SUBSCRIPTION_TIERS.values())


@api_router.get("/subscriptions/me")
async def my_subscription(user: User = Depends(get_current_user)):
    """Current user's subscription state + voting power."""
    sub = await db.subscriptions.find_one({"user_id": user.user_id, "status": "active"}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    if sub and sub.get("expires_at") and sub["expires_at"] < now:
        await db.subscriptions.update_one({"user_id": user.user_id, "status": "active"}, {"$set": {"status": "expired"}})
        sub = None

    tier = await get_user_tier(user.user_id)
    vp = await voting_power(user.user_id)
    return {
        "tier": tier,
        "subscription": sub,
        "voting_power": vp,
        "tier_meta": SUBSCRIPTION_TIERS[tier],
    }


class SubscribeRequest(BaseModel):
    tier: str = Field(..., pattern="^(pro|vip)$")
    payment_method: str = Field(..., pattern="^(rmr|stripe)$")
    origin_url: Optional[str] = None


@api_router.post("/subscriptions/subscribe")
async def subscribe(req: SubscribeRequest, user: User = Depends(get_current_user)):
    """Subscribe to Pro or VIP. Pay in VOLTZ (instant) or Stripe (checkout URL)."""
    if req.tier not in ("pro", "vip"):
        raise HTTPException(400, "Invalid tier")
    tier_meta = SUBSCRIPTION_TIERS[req.tier]

    if req.payment_method == "rmr":
        cost = tier_meta["price_rmr"]
        if (user.rmr_balance or 0) < cost:
            raise HTTPException(400, f"Insufficient VOLTZ. Need {cost}, have {user.rmr_balance or 0}")
        # Deduct & create subscription
        await db.users.update_one({"user_id": user.user_id}, {"$inc": {"rmr_balance": -cost}})
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        # mark any existing active sub as superseded
        await db.subscriptions.update_many({"user_id": user.user_id, "status": "active"}, {"$set": {"status": "superseded"}})
        sub_doc = {
            "subscription_id": sub_id,
            "user_id": user.user_id,
            "tier": req.tier,
            "status": "active",
            "payment_method": "rmr",
            "amount_rmr": cost,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires,
            "auto_renew": False,
        }
        await db.subscriptions.insert_one(sub_doc)
        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": user.user_id,
            "type": "subscription",
            "amount": -cost,
            "reference_id": sub_id,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "meta": {"tier": req.tier, "method": "rmr"},
        })
        sub_doc.pop("_id", None)
        return {"success": True, "subscription": sub_doc, "method": "rmr"}

    # Stripe flow
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    stripe_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_key:
        raise HTTPException(503, "Stripe not configured")
    if not req.origin_url:
        raise HTTPException(400, "origin_url is required for Stripe payment")
    try:
        host_url = req.origin_url.rstrip("/")
        webhook_url = f"{host_url}/api/webhook/stripe"
        checkout = StripeCheckout(api_key=stripe_key, webhook_url=webhook_url)
        checkout_req = CheckoutSessionRequest(
            amount=float(tier_meta["price_cad"]),
            currency="cad",
            success_url=f"{host_url}/subscription?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{host_url}/subscription?cancelled=1",
            metadata={
                "type": "subscription",
                "tier": req.tier,
                "user_id": user.user_id,
            },
        )
        session = await checkout.create_checkout_session(checkout_req)
        # Persist intent in payment_transactions so /payments/status can find it
        await db.payment_transactions.insert_one({
            "session_id": session.session_id,
            "user_id": user.user_id,
            "type": "subscription",
            "tier": req.tier,
            "amount_cad": float(tier_meta["price_cad"]),
            "rmr_amount": 0,
            "payment_status": "pending",
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"success": True, "checkout_url": session.url, "session_id": session.session_id, "method": "stripe"}
    except Exception as e:
        raise HTTPException(500, f"Stripe error: {e}")


@api_router.post("/subscriptions/cancel")
async def cancel_subscription(user: User = Depends(get_current_user)):
    """Cancel auto-renewal on active subscription (keeps access until expires_at)."""
    res = await db.subscriptions.update_one(
        {"user_id": user.user_id, "status": "active"},
        {"$set": {"auto_renew": False, "cancelled_at": datetime.now(timezone.utc).isoformat()}}
    )
    if res.modified_count == 0:
        raise HTTPException(400, "No active subscription to cancel")
    return {"success": True}


# Hook subscription Stripe session into existing /payments/status endpoint
# We use a check at the end of /payments/status to handle subscription type intents.


# ============= Governance =============

PROPOSAL_TYPES = {
    "vehicle_add":      {"label": "Add Vehicle Type",      "needs_admin_exec": True},
    "vehicle_remove":   {"label": "Remove Vehicle Type",   "needs_admin_exec": True},
    "parameter_change": {"label": "Parameter Change",      "needs_admin_exec": True},
    "feature_request":  {"label": "Feature Request",       "needs_admin_exec": True},
    "treasury":         {"label": "Treasury Proposal",     "needs_admin_exec": True},
    "community":        {"label": "Community Initiative",  "needs_admin_exec": True},
}

DEFAULT_QUORUM = 10        # min total voting-power required for valid result
DEFAULT_THRESHOLD = 0.60   # 60% yes votes (of yes+no) required


class ProposalCreate(BaseModel):
    type: str
    title: str = Field(..., min_length=4, max_length=120)
    description: str = Field(..., min_length=10, max_length=2000)
    metadata: Optional[Dict[str, Any]] = None
    duration_days: int = Field(default=7, ge=1, le=30)


class VoteRequest(BaseModel):
    choice: str = Field(..., pattern="^(yes|no|abstain)$")


@api_router.get("/governance/config")
async def governance_config():
    """Public: list proposal types and rules."""
    return {
        "proposal_types": [{"id": k, **v} for k, v in PROPOSAL_TYPES.items()],
        "quorum": DEFAULT_QUORUM,
        "threshold": DEFAULT_THRESHOLD,
        "tiers": list(SUBSCRIPTION_TIERS.values()),
    }


@api_router.get("/governance/proposals")
async def list_proposals(status: Optional[str] = None, limit: int = 50, user: Optional[User] = Depends(get_optional_user)):
    """List proposals (optionally filter by status). Auto-finalizes any expired active ones."""
    # Auto-finalize stale active proposals
    now = datetime.now(timezone.utc).isoformat()
    stale = db.proposals.find({"status": "active", "voting_ends_at": {"$lt": now}}, {"_id": 0, "proposal_id": 1})
    async for s in stale:
        await _finalize_proposal(s["proposal_id"])

    q: Dict[str, Any] = {}
    if status:
        q["status"] = status
    rows = await db.proposals.find(q, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)

    # Attach the caller's vote if any
    if user:
        ids = [r["proposal_id"] for r in rows]
        votes = await db.votes.find({"user_id": user.user_id, "proposal_id": {"$in": ids}}, {"_id": 0}).to_list(None)
        vote_by_pid = {v["proposal_id"]: v for v in votes}
        for r in rows:
            r["my_vote"] = vote_by_pid.get(r["proposal_id"])
    return rows


@api_router.get("/governance/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, user: Optional[User] = Depends(get_optional_user)):
    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Proposal not found")

    # auto-finalize if past end
    now = datetime.now(timezone.utc).isoformat()
    if p["status"] == "active" and p.get("voting_ends_at") and p["voting_ends_at"] < now:
        await _finalize_proposal(proposal_id)
        p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})

    # Attach recent voters
    votes = await db.votes.find({"proposal_id": proposal_id}, {"_id": 0}).sort("voted_at", -1).limit(20).to_list(20)
    # enrich with display names
    uids = list({v["user_id"] for v in votes})
    users = {u["user_id"]: u async for u in db.users.find({"user_id": {"$in": uids}}, {"_id": 0, "user_id": 1, "first_name": 1, "last_name": 1, "name": 1, "picture": 1})}
    for v in votes:
        u = users.get(v["user_id"], {})
        v["voter_name"] = u.get("name") or f"{u.get('first_name','')} {u.get('last_name','')}".strip() or "Anon"
        v["voter_picture"] = u.get("picture")

    p["recent_votes"] = votes
    if user:
        my_vote = next((v for v in votes if v["user_id"] == user.user_id), None)
        if not my_vote:
            my_vote = await db.votes.find_one({"proposal_id": proposal_id, "user_id": user.user_id}, {"_id": 0})
        p["my_vote"] = my_vote
    return p


@api_router.post("/governance/proposals")
async def create_proposal(req: ProposalCreate, user: User = Depends(get_current_user)):
    """Create a proposal. VIP-only."""
    if req.type not in PROPOSAL_TYPES:
        raise HTTPException(400, "Invalid proposal type")
    tier = await get_user_tier(user.user_id)
    if not SUBSCRIPTION_TIERS[tier]["can_propose"]:
        raise HTTPException(403, "Only VIP members can create proposals. Upgrade your subscription.")

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=req.duration_days)
    proposal = {
        "proposal_id": f"prop_{uuid.uuid4().hex[:12]}",
        "type": req.type,
        "type_label": PROPOSAL_TYPES[req.type]["label"],
        "title": req.title,
        "description": req.description,
        "metadata": req.metadata or {},
        "created_by": user.user_id,
        "created_by_name": user.name or f"{user.first_name or ''} {user.last_name or ''}".strip() or "Anon",
        "created_at": now.isoformat(),
        "voting_starts_at": now.isoformat(),
        "voting_ends_at": end.isoformat(),
        "status": "active",
        "min_quorum": DEFAULT_QUORUM,
        "pass_threshold": DEFAULT_THRESHOLD,
        "vote_counts": {"yes": 0, "no": 0, "abstain": 0},
        "voting_power": {"yes": 0, "no": 0, "abstain": 0, "total": 0},
        "voter_count": 0,
        "executed_at": None,
        "executed_by": None,
        "execution_result": None,
    }
    await db.proposals.insert_one(proposal)
    proposal.pop("_id", None)
    return proposal


@api_router.post("/governance/proposals/{proposal_id}/vote")
async def cast_vote(proposal_id: str, req: VoteRequest, user: User = Depends(get_current_user)):
    """Cast a vote on an active proposal. One vote per user. Pro=1pw, VIP=10pw + stake bonus."""
    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Proposal not found")
    if p["status"] != "active":
        raise HTTPException(400, f"Voting is closed (status: {p['status']})")

    now = datetime.now(timezone.utc).isoformat()
    if p.get("voting_ends_at") and p["voting_ends_at"] < now:
        await _finalize_proposal(proposal_id)
        raise HTTPException(400, "Voting period ended")

    vp = await voting_power(user.user_id)
    if vp["total"] <= 0:
        raise HTTPException(403, "You need Pro or VIP to vote. Upgrade your subscription.")

    # Block re-voting (or allow update? for v1 we lock)
    existing = await db.votes.find_one({"proposal_id": proposal_id, "user_id": user.user_id})
    if existing:
        raise HTTPException(400, "You already voted on this proposal")

    vote = {
        "vote_id": f"vote_{uuid.uuid4().hex[:12]}",
        "proposal_id": proposal_id,
        "user_id": user.user_id,
        "choice": req.choice,
        "voting_power": vp["total"],
        "tier": vp["tier"],
        "voted_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.votes.insert_one(vote)

    inc = {
        f"vote_counts.{req.choice}": 1,
        f"voting_power.{req.choice}": vp["total"],
        "voting_power.total": vp["total"],
        "voter_count": 1,
    }
    await db.proposals.update_one({"proposal_id": proposal_id}, {"$inc": inc})

    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    vote.pop("_id", None)
    return {"success": True, "vote": vote, "proposal": p}


async def _finalize_proposal(proposal_id: str):
    """Compute pass/fail based on quorum and threshold. Idempotent."""
    p = await db.proposals.find_one({"proposal_id": proposal_id})
    if not p or p["status"] != "active":
        return
    vp = p.get("voting_power", {})
    yes = vp.get("yes", 0); no = vp.get("no", 0); total = vp.get("total", 0)
    decisive = yes + no
    if total < p.get("min_quorum", DEFAULT_QUORUM):
        new_status = "failed_quorum"
    elif decisive == 0:
        new_status = "failed_quorum"
    elif (yes / decisive) >= p.get("pass_threshold", DEFAULT_THRESHOLD):
        new_status = "passed"
    else:
        new_status = "failed"
    await db.proposals.update_one(
        {"proposal_id": proposal_id},
        {"$set": {"status": new_status, "finalized_at": datetime.now(timezone.utc).isoformat()}}
    )


@api_router.post("/admin/governance/proposals/{proposal_id}/execute")
async def execute_proposal(proposal_id: str, admin: User = Depends(get_admin_user)):
    """Admin executes a passed proposal. Runs the type-specific action."""
    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    if not p:
        raise HTTPException(404, "Proposal not found")
    if p["status"] != "passed":
        raise HTTPException(400, f"Cannot execute (status: {p['status']})")

    ptype = p["type"]
    metadata = p.get("metadata", {})
    result: Dict[str, Any] = {"action": ptype}

    if ptype == "vehicle_add":
        veh = (metadata.get("vehicle_id") or "").strip().lower().replace(" ", "_")
        label = metadata.get("label") or veh.replace("_", " ").title()
        g_per_km = float(metadata.get("g_per_km", 8))
        if not veh:
            raise HTTPException(400, "metadata.vehicle_id missing")
        # Persist to protocol_settings
        await db.protocol_settings.update_one(
            {"key": "vehicle_emissions"},
            {"$set": {f"value.{veh}": g_per_km, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        await db.protocol_settings.update_one(
            {"key": "vehicle_labels"},
            {"$set": {f"value.{veh}": label, "updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        # Update in-process tables so runtime picks it up immediately
        VEHICLE_CO2_G_PER_KM[veh] = g_per_km
        VEHICLE_LABELS[veh] = label
        result.update({"vehicle_id": veh, "label": label, "g_per_km": g_per_km})

    elif ptype == "vehicle_remove":
        veh = (metadata.get("vehicle_id") or "").strip().lower()
        if not veh:
            raise HTTPException(400, "metadata.vehicle_id missing")
        await db.protocol_settings.update_one(
            {"key": "vehicle_emissions"}, {"$unset": {f"value.{veh}": ""}}
        )
        await db.protocol_settings.update_one(
            {"key": "vehicle_labels"}, {"$unset": {f"value.{veh}": ""}}
        )
        VEHICLE_CO2_G_PER_KM.pop(veh, None)
        VEHICLE_LABELS.pop(veh, None)
        result.update({"vehicle_id": veh, "removed": True})

    elif ptype == "parameter_change":
        key = metadata.get("key")
        value = metadata.get("value")
        if not key:
            raise HTTPException(400, "metadata.key missing")
        await db.protocol_settings.update_one(
            {"key": key},
            {"$set": {"value": value, "updated_at": datetime.now(timezone.utc).isoformat(), "updated_by_proposal": proposal_id}},
            upsert=True
        )
        result.update({"key": key, "value": value})

    else:
        # feature_request / treasury / community → record intent only
        result.update({"note": "Logged for off-chain action"})

    await db.proposals.update_one(
        {"proposal_id": proposal_id},
        {"$set": {
            "status": "executed",
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "executed_by": admin.user_id,
            "execution_result": result,
        }}
    )
    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    return {"success": True, "proposal": p}


@api_router.post("/admin/governance/proposals/{proposal_id}/finalize")
async def admin_finalize(proposal_id: str, admin: User = Depends(get_admin_user)):
    """Admin can force-finalize a proposal."""
    await _finalize_proposal(proposal_id)
    p = await db.proposals.find_one({"proposal_id": proposal_id}, {"_id": 0})
    return {"success": True, "proposal": p}


@api_router.get("/governance/me")
async def my_governance(user: User = Depends(get_current_user)):
    """My voting power + recent votes."""
    vp = await voting_power(user.user_id)
    votes = await db.votes.find({"user_id": user.user_id}, {"_id": 0}).sort("voted_at", -1).limit(50).to_list(50)
    proposed = await db.proposals.find({"created_by": user.user_id}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"voting_power": vp, "recent_votes": votes, "proposed": proposed}


# ============= Health Check =============

@api_router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
    # Start the monthly carbon scheduler
    try:
        start_carbon_scheduler()
    except Exception as e:
        logger.error(f"Carbon scheduler failed to start: {e}")


# ============= Monthly Carbon Scheduler =============
_carbon_scheduler = None

def start_carbon_scheduler():
    """Start APScheduler to auto-award previous month's top eco-rider on the 1st of each month at 00:05 UTC."""
    global _carbon_scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed - skipping monthly carbon scheduler")
        return

    if _carbon_scheduler:
        return

    async def auto_award_previous_month():
        """Award the previous month's top eco-rider (idempotent)."""
        now = datetime.now(timezone.utc)
        if now.month == 1:
            prev_year, prev_month = now.year - 1, 12
        else:
            prev_year, prev_month = now.year, now.month - 1

        # idempotency
        existing = await db.carbon_awards.find_one({"year": prev_year, "month": prev_month})
        if existing:
            logger.info(f"Carbon scheduler: {prev_year}-{prev_month:02d} already awarded, skipping")
            return

        start_iso, end_iso, y, m = month_range_utc(prev_year, prev_month)
        # Find top rider
        pipeline = [
            {"$match": {"status": "completed", "end_time": {"$gte": start_iso, "$lt": end_iso}}},
            {"$group": {"_id": "$user_id", "total_distance": {"$sum": "$distance"}, "rides": {"$sum": 1}}},
        ]
        rows = await db.rides.aggregate(pipeline).to_list(None)
        if not rows:
            logger.info(f"Carbon scheduler: no rides for {prev_year}-{prev_month:02d}")
            return

        best_uid, best_kg = None, 0.0
        best_dist, best_rides = 0.0, 0
        for row in rows:
            agg = await aggregate_user_carbon(row["_id"], start_iso, end_iso)
            if agg["totals"]["saved_kg"] > best_kg:
                best_kg = agg["totals"]["saved_kg"]
                best_uid = row["_id"]
                best_dist = agg["totals"]["distance_km"]
                best_rides = agg["totals"]["rides"]

        if not best_uid:
            return

        winner = await db.users.find_one({"user_id": best_uid}, {"_id": 0})
        if not winner:
            return

        reward = 500.0
        await db.users.update_one({"user_id": best_uid}, {"$inc": {"rmr_balance": reward}})

        sol_signature, sol_mode = None, "in_app_only"
        if winner.get("wallet_address"):
            try:
                res = solana_service.mint_tokens(winner["wallet_address"], reward)
                if res.get("success"):
                    sol_signature = res.get("signature")
                    sol_mode = res.get("mode", "demo")
                    await db.wallet_balances.update_one(
                        {"user_id": best_uid, "wallet_address": winner["wallet_address"]},
                        {"$inc": {"on_chain_balance": reward}},
                        upsert=True,
                    )
            except Exception as e:
                logger.error(f"Auto-award on-chain mint failed: {e}")

        await db.carbon_awards.insert_one({
            "award_id": f"carbon_award_{uuid.uuid4().hex[:12]}",
            "year": y, "month": m,
            "month_label": datetime(y, m, 1).strftime("%B %Y"),
            "winner_user_id": best_uid,
            "winner_email": winner.get("email"),
            "winner_name": winner.get("name") or f"{winner.get('first_name','')} {winner.get('last_name','')}".strip(),
            "winner_wallet": winner.get("wallet_address"),
            "saved_kg": round(best_kg, 3),
            "distance_km": round(best_dist, 3),
            "rides": best_rides,
            "reward_rmr": reward,
            "sol_mode": sol_mode,
            "sol_signature": sol_signature,
            "explorer_url": f"https://explorer.solana.com/tx/{sol_signature}?cluster=devnet" if sol_signature else None,
            "awarded_by": "auto_scheduler",
            "awarded_at": datetime.now(timezone.utc).isoformat(),
        })

        await db.transactions.insert_one({
            "transaction_id": f"tx_{uuid.uuid4().hex[:12]}",
            "user_id": best_uid,
            "type": "carbon_award",
            "amount": reward,
            "reference_id": f"auto_{y}_{m:02d}",
            "status": "completed",
            "sol_signature": sol_signature,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Carbon scheduler: awarded {winner.get('email')} {reward} RMR for {y}-{m:02d}")

    sched = AsyncIOScheduler(timezone="UTC")
    # 1st of each month at 00:05 UTC
    sched.add_job(auto_award_previous_month, CronTrigger(day=1, hour=0, minute=5), id="carbon_monthly", replace_existing=True)
    sched.start()
    _carbon_scheduler = sched
    logger.info("Carbon monthly auto-award scheduler started (runs 1st of every month at 00:05 UTC)")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
