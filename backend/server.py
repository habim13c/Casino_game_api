from dotenv import load_dotenv
load_dotenv()

import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import bcrypt
import jwt

from games import play_game, GAME_INFO, GAME_MAP

# ==================== CONFIG ====================
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@casino.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

# ==================== DB ====================
mongo_client = AsyncIOMotorClient(MONGO_URL)
db = mongo_client[DB_NAME]

# ==================== AUTH HELPERS ====================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {"sub": user_id, "email": email, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=24), "type": "access"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.get("status") == "banned":
            raise HTTPException(status_code=403, detail="Account banned")
        if user.get("status") == "frozen":
            raise HTTPException(status_code=403, detail="Account frozen")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

async def require_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_super_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return user

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

def user_response(user: dict) -> dict:
    return {
        "id": str(user["_id"]) if isinstance(user["_id"], ObjectId) else user["_id"],
        "email": user["email"],
        "name": user.get("name", ""),
        "display_name": user.get("display_name", ""),
        "role": user.get("role", "player"),
        "balance": user.get("balance", 0),
        "bonus_balance": user.get("bonus_balance", 0),
        "vip_tier": user.get("vip_tier", 0),
        "loyalty_points": user.get("loyalty_points", 0),
        "status": user.get("status", "active"),
        "avatar": user.get("avatar", ""),
        "created_at": user.get("created_at", "").isoformat() if isinstance(user.get("created_at"), datetime) else str(user.get("created_at", "")),
    }

# ==================== SCHEMAS ====================
class RegisterBody(BaseModel):
    email: str
    password: str
    name: str = ""

class LoginBody(BaseModel):
    email: str
    password: str

class DepositBody(BaseModel):
    amount: float = Field(gt=0)

class WithdrawBody(BaseModel):
    amount: float = Field(gt=0)

class GamePlayBody(BaseModel):
    bet_amount: float = Field(gt=0)
    params: dict = {}

class AdminBalanceBody(BaseModel):
    amount: float
    reason: str

class AdminStatusBody(BaseModel):
    status: str
    reason: str

class AdminGameConfigBody(BaseModel):
    enabled: Optional[bool] = None
    house_edge: Optional[float] = None
    min_bet: Optional[float] = None
    max_bet: Optional[float] = None

class AdminBonusBody(BaseModel):
    amount: float = Field(gt=0)
    wagering_req: float = 1.0
    reason: str = ""

# ==================== STARTUP ====================
async def seed_admin():
    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        await db.users.insert_one({
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "name": "Admin",
            "display_name": "Admin",
            "role": "super_admin",
            "balance": 0,
            "bonus_balance": 0,
            "vip_tier": 0,
            "loyalty_points": 0,
            "status": "active",
            "avatar": "",
            "created_at": datetime.now(timezone.utc),
        })
    elif not verify_password(ADMIN_PASSWORD, existing["password_hash"]):
        await db.users.update_one({"email": ADMIN_EMAIL}, {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}})

async def seed_game_configs():
    for game_id, info in GAME_INFO.items():
        existing = await db.game_configs.find_one({"game_id": game_id})
        if not existing:
            await db.game_configs.insert_one({
                "game_id": game_id,
                "name": info["name"],
                "category": info["category"],
                "description": info["description"],
                "enabled": True,
                "house_edge": info["house_edge"],
                "min_bet": info["min_bet"],
                "max_bet": info["max_bet"],
                "created_at": datetime.now(timezone.utc),
            })

async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.bets.create_index("user_id")
    await db.bets.create_index("created_at")
    await db.transactions.create_index("user_id")
    await db.transactions.create_index("created_at")
    await db.game_configs.create_index("game_id", unique=True)
    await db.admin_actions.create_index("created_at")

async def write_test_credentials():
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write("## Admin Account\n")
        f.write(f"- Email: {ADMIN_EMAIL}\n")
        f.write(f"- Password: {ADMIN_PASSWORD}\n")
        f.write("- Role: super_admin\n\n")
        f.write("## Test User\n")
        f.write("- Register at POST /api/auth/register\n")
        f.write("- Any email/password combo\n\n")
        f.write("## Auth Endpoints\n")
        f.write("- POST /api/auth/register\n")
        f.write("- POST /api/auth/login\n")
        f.write("- POST /api/auth/logout\n")
        f.write("- GET /api/auth/me\n")
        f.write("- POST /api/auth/refresh\n")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    await seed_admin()
    await seed_game_configs()
    await write_test_credentials()
    print("Casino backend started successfully")
    yield
    mongo_client.close()

# ==================== APP ====================
app = FastAPI(title="Casino API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "https://cafd1537-671b-41f5-a582-2c457f3b80d3.preview.emergentagent.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HEALTH ====================
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ==================== AUTH ENDPOINTS ====================
@app.post("/api/auth/register")
async def register(body: RegisterBody, response: Response):
    email = body.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user_doc = {
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name or email.split("@")[0],
        "display_name": body.name or email.split("@")[0],
        "role": "player",
        "balance": 1000.0,
        "bonus_balance": 0,
        "vip_tier": 0,
        "loyalty_points": 0,
        "status": "active",
        "avatar": "",
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    await db.transactions.insert_one({
        "user_id": str(result.inserted_id),
        "type": "bonus",
        "amount": 1000.0,
        "balance_after": 1000.0,
        "description": "Welcome bonus",
        "created_at": datetime.now(timezone.utc),
    })
    access = create_access_token(str(result.inserted_id), email, "player")
    refresh = create_refresh_token(str(result.inserted_id))
    set_auth_cookies(response, access, refresh)
    resp = user_response(user_doc)
    resp["token"] = access
    return resp

@app.post("/api/auth/login")
async def login(body: LoginBody, response: Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("status") == "banned":
        raise HTTPException(status_code=403, detail="Account banned")
    access = create_access_token(str(user["_id"]), email, user.get("role", "player"))
    refresh = create_refresh_token(str(user["_id"]))
    set_auth_cookies(response, access, refresh)
    resp = user_response(user)
    resp["token"] = access
    return resp

@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}

@app.get("/api/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user_response(await db.users.find_one({"_id": ObjectId(user["_id"])}))

@app.post("/api/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        access = create_access_token(str(user["_id"]), user["email"], user.get("role", "player"))
        response.set_cookie(key="access_token", value=access, httponly=True, secure=False, samesite="lax", max_age=86400, path="/")
        return {"message": "Token refreshed"}
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ==================== USER/WALLET ENDPOINTS ====================
@app.get("/api/user/balance")
async def get_balance(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(user["_id"])})
    return {"balance": u["balance"], "bonus_balance": u.get("bonus_balance", 0)}

@app.post("/api/user/deposit")
async def deposit(body: DepositBody, user: dict = Depends(get_current_user)):
    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user["_id"])},
        {"$inc": {"balance": body.amount}},
        return_document=True
    )
    await db.transactions.insert_one({
        "user_id": user["_id"],
        "type": "deposit",
        "amount": body.amount,
        "balance_after": result["balance"],
        "description": f"Deposit of ${body.amount:.2f}",
        "created_at": datetime.now(timezone.utc),
    })
    return {"balance": result["balance"], "message": f"Deposited ${body.amount:.2f}"}

@app.post("/api/user/withdraw")
async def withdraw(body: WithdrawBody, user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(user["_id"])})
    if u["balance"] < body.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    result = await db.users.find_one_and_update(
        {"_id": ObjectId(user["_id"]), "balance": {"$gte": body.amount}},
        {"$inc": {"balance": -body.amount}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    await db.transactions.insert_one({
        "user_id": user["_id"],
        "type": "withdrawal",
        "amount": -body.amount,
        "balance_after": result["balance"],
        "description": f"Withdrawal of ${body.amount:.2f}",
        "created_at": datetime.now(timezone.utc),
    })
    return {"balance": result["balance"], "message": f"Withdrew ${body.amount:.2f}"}

@app.get("/api/user/transactions")
async def get_transactions(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    type: Optional[str] = None
):
    query = {"user_id": user["_id"]}
    if type:
        query["type"] = type
    total = await db.transactions.count_documents(query)
    txns = await db.transactions.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for t in txns:
        if isinstance(t.get("created_at"), datetime):
            t["created_at"] = t["created_at"].isoformat()
    return {"transactions": txns, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/user/bets")
async def get_user_bets(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    game: Optional[str] = None
):
    query = {"user_id": user["_id"]}
    if game:
        query["game"] = game
    total = await db.bets.count_documents(query)
    bets = await db.bets.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for b in bets:
        if isinstance(b.get("created_at"), datetime):
            b["created_at"] = b["created_at"].isoformat()
    return {"bets": bets, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/user/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    u = await db.users.find_one({"_id": ObjectId(user["_id"])})
    total_bets = await db.bets.count_documents({"user_id": user["_id"]})
    total_wagered = 0
    total_won = 0
    pipeline = [
        {"$match": {"user_id": user["_id"]}},
        {"$group": {"_id": None, "wagered": {"$sum": "$bet_amount"}, "won": {"$sum": "$win_amount"}}}
    ]
    agg = await db.bets.aggregate(pipeline).to_list(1)
    if agg:
        total_wagered = round(agg[0]["wagered"], 2)
        total_won = round(agg[0]["won"], 2)
    resp = user_response(u)
    resp["stats"] = {"total_bets": total_bets, "total_wagered": total_wagered, "total_won": total_won, "net_profit": round(total_won - total_wagered, 2)}
    return resp

# ==================== GAME ENDPOINTS ====================
@app.get("/api/games")
async def list_games():
    configs = await db.game_configs.find({}, {"_id": 0}).to_list(100)
    return {"games": configs}

@app.get("/api/games/{game_name}")
async def get_game_info(game_name: str):
    config = await db.game_configs.find_one({"game_id": game_name}, {"_id": 0})
    if not config:
        raise HTTPException(status_code=404, detail="Game not found")
    return config

@app.post("/api/games/{game_name}/play")
async def play_game_endpoint(game_name: str, body: GamePlayBody, user: dict = Depends(get_current_user)):
    if game_name not in GAME_MAP:
        raise HTTPException(status_code=404, detail="Game not found")
    config = await db.game_configs.find_one({"game_id": game_name})
    if config and not config.get("enabled", True):
        raise HTTPException(status_code=400, detail="Game is currently disabled")
    min_bet = config.get("min_bet", 1) if config else 1
    max_bet = config.get("max_bet", 100000) if config else 100000
    if body.bet_amount < min_bet:
        raise HTTPException(status_code=400, detail=f"Minimum bet is ${min_bet}")
    if body.bet_amount > max_bet:
        raise HTTPException(status_code=400, detail=f"Maximum bet is ${max_bet}")
    u = await db.users.find_one({"_id": ObjectId(user["_id"])})
    if u["balance"] < body.bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    game_result = play_game(game_name, body.bet_amount, body.params)
    if not game_result:
        raise HTTPException(status_code=500, detail="Game engine error")
    win_amount = game_result["win_amount"]
    net = win_amount - body.bet_amount
    new_balance = u["balance"] + net
    await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"balance": round(new_balance, 2)}})
    loyalty_earned = int(body.bet_amount / 10)
    if loyalty_earned > 0:
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"loyalty_points": loyalty_earned}})
    bet_doc = {
        "user_id": user["_id"],
        "game": game_name,
        "bet_amount": body.bet_amount,
        "win_amount": win_amount,
        "multiplier": game_result.get("multiplier", 0),
        "result": game_result.get("result", {}),
        "server_seed": game_result.get("server_seed", ""),
        "client_seed": game_result.get("client_seed", ""),
        "nonce": game_result.get("nonce", 0),
        "hash": game_result.get("hash", ""),
        "status": "settled",
        "created_at": datetime.now(timezone.utc),
    }
    await db.bets.insert_one(bet_doc)
    tx_type = "win" if net > 0 else "bet"
    await db.transactions.insert_one({
        "user_id": user["_id"],
        "type": tx_type,
        "amount": net,
        "balance_after": round(new_balance, 2),
        "description": f"{'Won' if net > 0 else 'Lost'} ${abs(net):.2f} on {GAME_INFO.get(game_name, {}).get('name', game_name)}",
        "game": game_name,
        "created_at": datetime.now(timezone.utc),
    })
    return {
        "balance": round(new_balance, 2),
        "win_amount": win_amount,
        "multiplier": game_result.get("multiplier", 0),
        "result": game_result.get("result", {}),
        "game": game_name,
        "bet_amount": body.bet_amount,
        "provably_fair": {
            "server_seed": game_result.get("server_seed", ""),
            "client_seed": game_result.get("client_seed", ""),
            "nonce": game_result.get("nonce", 0),
            "hash": game_result.get("hash", ""),
        }
    }

# ==================== ADMIN ENDPOINTS ====================
@app.get("/api/admin/dashboard")
async def admin_dashboard(admin: dict = Depends(require_admin)):
    total_users = await db.users.count_documents({"role": "player"})
    active_users = await db.users.count_documents({"role": "player", "status": "active"})
    total_bets = await db.bets.count_documents({})
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    bets_today = await db.bets.count_documents({"created_at": {"$gte": today}})
    revenue_pipeline = [
        {"$group": {"_id": None, "total_wagered": {"$sum": "$bet_amount"}, "total_paid": {"$sum": "$win_amount"}}}
    ]
    rev = await db.bets.aggregate(revenue_pipeline).to_list(1)
    total_wagered = round(rev[0]["total_wagered"], 2) if rev else 0
    total_paid = round(rev[0]["total_paid"], 2) if rev else 0
    ggr = round(total_wagered - total_paid, 2)
    today_pipeline = [
        {"$match": {"created_at": {"$gte": today}}},
        {"$group": {"_id": None, "wagered": {"$sum": "$bet_amount"}, "paid": {"$sum": "$win_amount"}}}
    ]
    today_rev = await db.bets.aggregate(today_pipeline).to_list(1)
    today_wagered = round(today_rev[0]["wagered"], 2) if today_rev else 0
    today_paid = round(today_rev[0]["paid"], 2) if today_rev else 0
    today_ggr = round(today_wagered - today_paid, 2)
    game_pipeline = [
        {"$group": {"_id": "$game", "count": {"$sum": 1}, "wagered": {"$sum": "$bet_amount"}, "paid": {"$sum": "$win_amount"}}}
    ]
    game_stats = await db.bets.aggregate(game_pipeline).to_list(100)
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_bets": total_bets,
        "bets_today": bets_today,
        "total_wagered": total_wagered,
        "total_paid": total_paid,
        "ggr": ggr,
        "today_wagered": today_wagered,
        "today_paid": today_paid,
        "today_ggr": today_ggr,
        "game_stats": [{**g, "ggr": round(g["wagered"] - g["paid"], 2)} for g in game_stats],
    }

@app.get("/api/admin/users")
async def admin_list_users(
    admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    role: Optional[str] = None
):
    query = {}
    if search:
        query["$or"] = [{"email": {"$regex": search, "$options": "i"}}, {"name": {"$regex": search, "$options": "i"}}]
    if status:
        query["status"] = status
    if role:
        query["role"] = role
    total = await db.users.count_documents(query)
    users = await db.users.find(query, {"password_hash": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    return {"users": [user_response(u) for u in users], "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/admin/users/{user_id}")
async def admin_get_user(user_id: str, admin: dict = Depends(require_admin)):
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    total_bets = await db.bets.count_documents({"user_id": user_id})
    pipeline = [{"$match": {"user_id": user_id}}, {"$group": {"_id": None, "wagered": {"$sum": "$bet_amount"}, "won": {"$sum": "$win_amount"}}}]
    agg = await db.bets.aggregate(pipeline).to_list(1)
    resp = user_response(u)
    resp["stats"] = {"total_bets": total_bets, "total_wagered": round(agg[0]["wagered"], 2) if agg else 0, "total_won": round(agg[0]["won"], 2) if agg else 0}
    return resp

@app.patch("/api/admin/users/{user_id}/balance")
async def admin_adjust_balance(user_id: str, body: AdminBalanceBody, admin: dict = Depends(require_admin)):
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    new_bal = round(u["balance"] + body.amount, 2)
    if new_bal < 0:
        raise HTTPException(status_code=400, detail="Balance cannot go negative")
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"balance": new_bal}})
    await db.transactions.insert_one({
        "user_id": user_id, "type": "admin_adjustment", "amount": body.amount,
        "balance_after": new_bal, "description": f"Admin adjustment: {body.reason}",
        "admin_id": admin["_id"], "created_at": datetime.now(timezone.utc),
    })
    await db.admin_actions.insert_one({
        "admin_id": admin["_id"], "action_type": "balance_adjustment",
        "target_type": "user", "target_id": user_id,
        "before_state": {"balance": u["balance"]}, "after_state": {"balance": new_bal},
        "reason": body.reason, "created_at": datetime.now(timezone.utc),
    })
    return {"balance": new_bal, "message": "Balance adjusted"}

@app.patch("/api/admin/users/{user_id}/status")
async def admin_update_status(user_id: str, body: AdminStatusBody, admin: dict = Depends(require_admin)):
    if body.status not in ["active", "frozen", "banned"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    old_status = u.get("status", "active")
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": body.status}})
    await db.admin_actions.insert_one({
        "admin_id": admin["_id"], "action_type": "status_change",
        "target_type": "user", "target_id": user_id,
        "before_state": {"status": old_status}, "after_state": {"status": body.status},
        "reason": body.reason, "created_at": datetime.now(timezone.utc),
    })
    return {"status": body.status, "message": f"User status updated to {body.status}"}

@app.get("/api/admin/users/{user_id}/bets")
async def admin_user_bets(user_id: str, admin: dict = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    total = await db.bets.count_documents({"user_id": user_id})
    bets = await db.bets.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for b in bets:
        if isinstance(b.get("created_at"), datetime):
            b["created_at"] = b["created_at"].isoformat()
    return {"bets": bets, "total": total, "page": page}

@app.get("/api/admin/users/{user_id}/transactions")
async def admin_user_transactions(user_id: str, admin: dict = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    total = await db.transactions.count_documents({"user_id": user_id})
    txns = await db.transactions.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for t in txns:
        if isinstance(t.get("created_at"), datetime):
            t["created_at"] = t["created_at"].isoformat()
    return {"transactions": txns, "total": total, "page": page}

@app.post("/api/admin/users/{user_id}/bonus")
async def admin_issue_bonus(user_id: str, body: AdminBonusBody, admin: dict = Depends(require_admin)):
    try:
        u = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    new_bonus = round(u.get("bonus_balance", 0) + body.amount, 2)
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"bonus_balance": new_bonus}})
    await db.transactions.insert_one({
        "user_id": user_id, "type": "bonus", "amount": body.amount,
        "balance_after": u["balance"], "description": f"Bonus: {body.reason}",
        "admin_id": admin["_id"], "created_at": datetime.now(timezone.utc),
    })
    return {"bonus_balance": new_bonus, "message": "Bonus issued"}

@app.get("/api/admin/games/config")
async def admin_game_configs(admin: dict = Depends(require_admin)):
    configs = await db.game_configs.find({}, {"_id": 0}).to_list(100)
    return {"configs": configs}

@app.patch("/api/admin/games/{game_id}/config")
async def admin_update_game_config(game_id: str, body: AdminGameConfigBody, admin: dict = Depends(require_admin)):
    config = await db.game_configs.find_one({"game_id": game_id})
    if not config:
        raise HTTPException(status_code=404, detail="Game not found")
    updates = {}
    if body.enabled is not None:
        updates["enabled"] = body.enabled
    if body.house_edge is not None:
        updates["house_edge"] = body.house_edge
    if body.min_bet is not None:
        updates["min_bet"] = body.min_bet
    if body.max_bet is not None:
        updates["max_bet"] = body.max_bet
    if updates:
        await db.game_configs.update_one({"game_id": game_id}, {"$set": updates})
        await db.admin_actions.insert_one({
            "admin_id": admin["_id"], "action_type": "game_config_update",
            "target_type": "game", "target_id": game_id,
            "before_state": {k: config.get(k) for k in updates},
            "after_state": updates,
            "reason": "Game config updated", "created_at": datetime.now(timezone.utc),
        })
    return {"message": "Game config updated", "updates": updates}

@app.get("/api/admin/bets")
async def admin_all_bets(
    admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    game: Optional[str] = None
):
    query = {}
    if game:
        query["game"] = game
    total = await db.bets.count_documents(query)
    bets = await db.bets.find(query, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for b in bets:
        if isinstance(b.get("created_at"), datetime):
            b["created_at"] = b["created_at"].isoformat()
    return {"bets": bets, "total": total, "page": page, "pages": (total + limit - 1) // limit}

@app.get("/api/admin/reports/pnl")
async def admin_pnl_report(admin: dict = Depends(require_admin), days: int = Query(30, ge=1, le=365)):
    start = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": start}}},
        {"$group": {
            "_id": "$game",
            "total_bets": {"$sum": 1},
            "total_wagered": {"$sum": "$bet_amount"},
            "total_paid": {"$sum": "$win_amount"},
        }}
    ]
    results = await db.bets.aggregate(pipeline).to_list(100)
    total_wagered = sum(r["total_wagered"] for r in results)
    total_paid = sum(r["total_paid"] for r in results)
    ggr = total_wagered - total_paid
    return {
        "period_days": days,
        "total_wagered": round(total_wagered, 2),
        "total_paid": round(total_paid, 2),
        "ggr": round(ggr, 2),
        "ngr": round(ggr * 0.85, 2),
        "hold_pct": round((ggr / total_wagered * 100) if total_wagered > 0 else 0, 2),
        "by_game": [{"game": r["_id"], "bets": r["total_bets"], "wagered": round(r["total_wagered"], 2), "paid": round(r["total_paid"], 2), "ggr": round(r["total_wagered"] - r["total_paid"], 2)} for r in results]
    }

@app.get("/api/admin/audit")
async def admin_audit_log(admin: dict = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100)):
    total = await db.admin_actions.count_documents({})
    actions = await db.admin_actions.find({}, {"_id": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
    for a in actions:
        if isinstance(a.get("created_at"), datetime):
            a["created_at"] = a["created_at"].isoformat()
    return {"actions": actions, "total": total, "page": page}

@app.get("/api/admin/withdrawals/pending")
async def admin_pending_withdrawals(admin: dict = Depends(require_admin)):
    withdrawals = await db.withdrawal_queue.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    for w in withdrawals:
        if isinstance(w.get("created_at"), datetime):
            w["created_at"] = w["created_at"].isoformat()
    return {"withdrawals": withdrawals}
