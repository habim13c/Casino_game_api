"""
Sportsbook Betting Engine
Supports: Pre-match, Live, Parlay, Cash Out, Over/Under, Handicap, Futures, System Bets
Odds formats: Decimal, Fractional, American
"""
import random
import math
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/betting", tags=["betting"])


# ==================== ODDS CONVERSION ====================
def decimal_to_fractional(decimal_odds):
    if decimal_odds <= 1:
        return "0/1"
    num = decimal_odds - 1
    # Simplify fraction
    from fractions import Fraction
    f = Fraction(num).limit_denominator(100)
    return f"{f.numerator}/{f.denominator}"

def decimal_to_american(decimal_odds):
    if decimal_odds >= 2.0:
        return f"+{int((decimal_odds - 1) * 100)}"
    elif decimal_odds > 1.0:
        return f"-{int(100 / (decimal_odds - 1))}"
    return "-100"

def convert_odds(decimal_odds):
    return {
        "decimal": round(decimal_odds, 2),
        "fractional": decimal_to_fractional(decimal_odds),
        "american": decimal_to_american(decimal_odds),
    }


# ==================== SCHEMAS ====================
class CreateEventBody(BaseModel):
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: str
    markets: list = []

class PlaceBetBody(BaseModel):
    selections: list  # [{event_id, market_id, selection, odds}]
    stake: float = Field(gt=0)
    bet_type: str = "single"  # single, parlay, system

class CashOutBody(BaseModel):
    bet_id: str

class SettleMarketBody(BaseModel):
    event_id: str
    market_id: str
    result: str
    winning_selection: str


# ==================== MARKET GENERATORS ====================
SPORTS = ["football", "basketball", "tennis", "cricket", "esports", "mma", "baseball"]

def generate_match_winner_market(home, away):
    # Generate odds with margin (~5%)
    home_prob = random.uniform(0.25, 0.65)
    draw_prob = random.uniform(0.1, 0.3) if random.random() > 0.3 else 0
    away_prob = 1 - home_prob - draw_prob
    margin = 1.05
    selections = [
        {"name": home, "key": "home", "odds": round(margin / home_prob, 2), "probability": round(home_prob, 4)},
        {"name": away, "key": "away", "odds": round(margin / away_prob, 2), "probability": round(away_prob, 4)},
    ]
    if draw_prob > 0:
        selections.append({"name": "Draw", "key": "draw", "odds": round(margin / draw_prob, 2), "probability": round(draw_prob, 4)})
    return {
        "market_type": "match_winner",
        "name": "Match Winner",
        "selections": selections,
        "status": "open",
    }

def generate_over_under_market(total_line=None):
    if total_line is None:
        total_line = round(random.uniform(1.5, 5.5) * 2) / 2
    margin = 1.05
    over_prob = random.uniform(0.4, 0.6)
    under_prob = 1 - over_prob
    return {
        "market_type": "over_under",
        "name": f"Over/Under {total_line}",
        "line": total_line,
        "selections": [
            {"name": f"Over {total_line}", "key": "over", "odds": round(margin / over_prob, 2)},
            {"name": f"Under {total_line}", "key": "under", "odds": round(margin / under_prob, 2)},
        ],
        "status": "open",
    }

def generate_handicap_market(home, away, line=None):
    if line is None:
        line = round(random.uniform(-2.5, 2.5) * 2) / 2
    margin = 1.05
    home_prob = random.uniform(0.4, 0.6)
    return {
        "market_type": "handicap",
        "name": f"Handicap ({'+' if line > 0 else ''}{line})",
        "line": line,
        "selections": [
            {"name": f"{home} {'+' if line > 0 else ''}{line}", "key": "home", "odds": round(margin / home_prob, 2)},
            {"name": f"{away} {'+' if -line > 0 else ''}{-line}", "key": "away", "odds": round(margin / (1 - home_prob), 2)},
        ],
        "status": "open",
    }

def generate_prop_market(description, options):
    margin = 1.05
    n = len(options)
    probs = [random.uniform(0.1, 0.9) for _ in range(n)]
    total = sum(probs)
    probs = [p / total for p in probs]
    return {
        "market_type": "prop",
        "name": description,
        "selections": [{"name": opt, "key": opt.lower().replace(" ", "_"), "odds": round(margin / p, 2)} for opt, p in zip(options, probs)],
        "status": "open",
    }

def generate_markets_for_event(home, away, sport):
    markets = [generate_match_winner_market(home, away), generate_over_under_market()]
    if sport in ["football", "basketball", "baseball"]:
        markets.append(generate_handicap_market(home, away))
        markets.append(generate_over_under_market(round(random.uniform(0.5, 3.5) * 2) / 2))
    if sport == "football":
        markets.append(generate_prop_market("Both Teams to Score", ["Yes", "No"]))
        markets.append(generate_prop_market("First Goal Scorer", [f"{home} Player", f"{away} Player"]))
    if sport == "tennis":
        markets.append(generate_prop_market("Total Sets", ["2 Sets", "3 Sets"]))
    markets.append(generate_prop_market("Correct Score", ["1-0", "2-1", "0-0", "2-0", "1-1", "Other"]))
    for i, m in enumerate(markets):
        m["market_id"] = f"mkt_{i}"
    return markets


# ==================== SAMPLE EVENTS GENERATOR ====================
TEAMS = {
    "football": [("Manchester City", "Liverpool"), ("Real Madrid", "Barcelona"), ("Bayern Munich", "Dortmund"), ("PSG", "Marseille"), ("Juventus", "AC Milan"), ("Arsenal", "Chelsea")],
    "basketball": [("Lakers", "Celtics"), ("Warriors", "Nets"), ("Bucks", "76ers"), ("Nuggets", "Heat")],
    "tennis": [("Djokovic", "Nadal"), ("Alcaraz", "Sinner"), ("Medvedev", "Zverev")],
    "cricket": [("India", "Australia"), ("England", "New Zealand"), ("Pakistan", "South Africa")],
    "esports": [("T1", "Gen.G"), ("Cloud9", "FaZe"), ("Fnatic", "G2")],
    "mma": [("Fighter A", "Fighter B"), ("Champion", "Challenger")],
}

LEAGUES = {
    "football": ["Premier League", "La Liga", "Bundesliga", "Ligue 1", "Serie A"],
    "basketball": ["NBA", "EuroLeague"],
    "tennis": ["ATP Tour", "Grand Slam"],
    "cricket": ["ICC World Cup", "IPL", "The Ashes"],
    "esports": ["LCK", "Valorant Champions"],
    "mma": ["UFC", "Bellator"],
}

async def seed_events(db):
    count = await db.betting_events.count_documents({})
    if count > 0:
        return

    events = []
    for sport, team_pairs in TEAMS.items():
        leagues = LEAGUES.get(sport, ["League"])
        for home, away in team_pairs:
            league = random.choice(leagues)
            start_offset = random.randint(1, 72)
            start_time = datetime.now(timezone.utc) + timedelta(hours=start_offset)
            markets = generate_markets_for_event(home, away, sport)
            is_live = random.random() < 0.3
            event = {
                "sport": sport,
                "league": league,
                "home_team": home,
                "away_team": away,
                "start_time": start_time,
                "status": "live" if is_live else "upcoming",
                "markets": markets,
                "score": {"home": random.randint(0, 3), "away": random.randint(0, 2)} if is_live else None,
                "minute": random.randint(1, 90) if is_live and sport == "football" else None,
                "created_at": datetime.now(timezone.utc),
            }
            events.append(event)

    if events:
        await db.betting_events.insert_many(events)
    await db.betting_events.create_index("sport")
    await db.betting_events.create_index("status")
    await db.betting_events.create_index("start_time")


# ==================== PARLAY CALCULATOR ====================
def calculate_parlay_odds(selections):
    combined = 1.0
    for sel in selections:
        combined *= sel.get("odds", 1.0)
    return round(combined, 2)

def calculate_system_bet_combinations(selections, min_combo):
    from itertools import combinations
    combos = list(combinations(range(len(selections)), min_combo))
    return combos


# ==================== ROUTES ====================
def create_betting_routes(db):

    async def get_user(request: Request):
        import jwt, os
        token = request.cookies.get("access_token")
        if not token:
            auth = request.headers.get("Authorization", "")
            if auth.startswith("Bearer "): token = auth[7:]
        if not token: raise HTTPException(status_code=401, detail="Not authenticated")
        try:
            payload = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
            user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
            if not user: raise HTTPException(status_code=401, detail="User not found")
            user["_id"] = str(user["_id"])
            return user
        except: raise HTTPException(status_code=401, detail="Auth failed")

    @router.get("/events")
    async def list_events(sport: Optional[str] = None, status: Optional[str] = None, page: int = 1, limit: int = 20):
        query = {}
        if sport: query["sport"] = sport
        if status: query["status"] = status
        total = await db.betting_events.count_documents(query)
        events = await db.betting_events.find(query).sort("start_time", 1).skip((page - 1) * limit).limit(limit).to_list(limit)
        result = []
        for e in events:
            result.append({
                "event_id": str(e["_id"]),
                "sport": e["sport"], "league": e.get("league", ""),
                "home_team": e["home_team"], "away_team": e["away_team"],
                "start_time": e["start_time"].isoformat() if isinstance(e["start_time"], datetime) else str(e["start_time"]),
                "status": e.get("status", "upcoming"),
                "score": e.get("score"),
                "minute": e.get("minute"),
                "markets_count": len(e.get("markets", [])),
            })
        return {"events": result, "total": total, "page": page, "sports": SPORTS}

    @router.get("/events/{event_id}")
    async def get_event(event_id: str):
        try: event = await db.betting_events.find_one({"_id": ObjectId(event_id)})
        except: raise HTTPException(status_code=404, detail="Event not found")
        if not event: raise HTTPException(status_code=404, detail="Event not found")
        markets = event.get("markets", [])
        for m in markets:
            for s in m.get("selections", []):
                s["odds_display"] = convert_odds(s["odds"])
        return {
            "event_id": str(event["_id"]),
            "sport": event["sport"], "league": event.get("league", ""),
            "home_team": event["home_team"], "away_team": event["away_team"],
            "start_time": event["start_time"].isoformat() if isinstance(event["start_time"], datetime) else str(event["start_time"]),
            "status": event.get("status", "upcoming"),
            "score": event.get("score"), "minute": event.get("minute"),
            "markets": markets,
        }

    @router.post("/place")
    async def place_bet(body: PlaceBetBody, request: Request):
        user = await get_user(request)
        if not body.selections:
            raise HTTPException(status_code=400, detail="No selections")
        if body.stake <= 0:
            raise HTTPException(status_code=400, detail="Invalid stake")

        u = await db.users.find_one({"_id": ObjectId(user["_id"])})
        total_stake = body.stake
        if body.bet_type == "system":
            # System bets have multiple combinations
            total_stake = body.stake * len(body.selections)
        if u["balance"] < total_stake:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Validate selections
        validated = []
        for sel in body.selections:
            try:
                event = await db.betting_events.find_one({"_id": ObjectId(sel["event_id"])})
            except:
                raise HTTPException(status_code=400, detail=f"Event not found: {sel.get('event_id')}")
            if not event:
                raise HTTPException(status_code=400, detail=f"Event not found")
            market = None
            for m in event.get("markets", []):
                if m.get("market_id") == sel.get("market_id"):
                    market = m
                    break
            if not market:
                raise HTTPException(status_code=400, detail=f"Market not found: {sel.get('market_id')}")
            if market.get("status") != "open":
                raise HTTPException(status_code=400, detail=f"Market is {market.get('status')}")
            selection_data = None
            for s in market.get("selections", []):
                if s.get("key") == sel.get("selection"):
                    selection_data = s
                    break
            if not selection_data:
                raise HTTPException(status_code=400, detail=f"Selection not found: {sel.get('selection')}")
            validated.append({
                "event_id": sel["event_id"],
                "event_name": f"{event['home_team']} vs {event['away_team']}",
                "market_id": sel["market_id"],
                "market_name": market.get("name", ""),
                "selection": sel["selection"],
                "selection_name": selection_data["name"],
                "odds": selection_data["odds"],
                "sport": event["sport"],
            })

        # Calculate potential winnings
        if body.bet_type == "single":
            if len(validated) != 1:
                raise HTTPException(status_code=400, detail="Single bet requires exactly one selection")
            potential_win = round(body.stake * validated[0]["odds"], 2)
        elif body.bet_type == "parlay":
            combined_odds = calculate_parlay_odds(validated)
            potential_win = round(body.stake * combined_odds, 2)
        elif body.bet_type == "system":
            min_combo = max(2, len(validated) - 1)
            combos = calculate_system_bet_combinations(validated, min_combo)
            potential_win = 0
            for combo in combos:
                combo_odds = 1.0
                for idx in combo:
                    combo_odds *= validated[idx]["odds"]
                potential_win += body.stake * combo_odds
            potential_win = round(potential_win, 2)
        else:
            potential_win = round(body.stake * validated[0]["odds"], 2)

        # Max win limit
        max_win = 100000
        if potential_win > max_win:
            raise HTTPException(status_code=400, detail=f"Potential win exceeds max limit (${max_win})")

        # Deduct stake
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": -total_stake}})

        bet_doc = {
            "user_id": user["_id"],
            "bet_type": body.bet_type,
            "selections": validated,
            "stake": body.stake,
            "total_stake": total_stake,
            "potential_win": potential_win,
            "odds": calculate_parlay_odds(validated) if body.bet_type == "parlay" else validated[0]["odds"],
            "status": "open",
            "cash_out_available": True,
            "created_at": datetime.now(timezone.utc),
        }
        result = await db.sport_bets.insert_one(bet_doc)

        await db.transactions.insert_one({
            "user_id": user["_id"], "type": "sport_bet",
            "amount": -total_stake, "balance_after": round(u["balance"] - total_stake, 2),
            "description": f"Sport bet: {body.bet_type} - ${body.stake}",
            "created_at": datetime.now(timezone.utc),
        })

        u_after = await db.users.find_one({"_id": ObjectId(user["_id"])})
        return {
            "bet_id": str(result.inserted_id),
            "bet_type": body.bet_type,
            "selections": validated,
            "stake": body.stake,
            "potential_win": potential_win,
            "status": "open",
            "balance": round(u_after["balance"], 2),
        }

    @router.post("/cashout")
    async def cash_out(body: CashOutBody, request: Request):
        user = await get_user(request)
        try: bet = await db.sport_bets.find_one({"_id": ObjectId(body.bet_id)})
        except: raise HTTPException(status_code=404, detail="Bet not found")
        if not bet: raise HTTPException(status_code=404, detail="Bet not found")
        if bet["user_id"] != user["_id"]: raise HTTPException(status_code=403, detail="Not your bet")
        if bet["status"] != "open": raise HTTPException(status_code=400, detail="Bet cannot be cashed out")
        if not bet.get("cash_out_available"): raise HTTPException(status_code=400, detail="Cash out not available")

        # Cash out value = stake * (partial odds factor)
        cash_out_value = round(bet["stake"] * random.uniform(0.6, 1.4), 2)
        cash_out_value = max(round(bet["stake"] * 0.1, 2), cash_out_value)

        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": cash_out_value}})
        await db.sport_bets.update_one({"_id": ObjectId(body.bet_id)}, {"$set": {"status": "cashed_out", "cash_out_value": cash_out_value, "settled_at": datetime.now(timezone.utc)}})
        await db.transactions.insert_one({
            "user_id": user["_id"], "type": "cashout",
            "amount": cash_out_value, "description": f"Cash out: ${cash_out_value}",
            "created_at": datetime.now(timezone.utc),
        })
        u_after = await db.users.find_one({"_id": ObjectId(user["_id"])})
        return {"bet_id": body.bet_id, "cash_out_value": cash_out_value, "status": "cashed_out", "balance": round(u_after["balance"], 2)}

    @router.get("/my-bets")
    async def my_bets(request: Request, status: Optional[str] = None, page: int = 1, limit: int = 20):
        user = await get_user(request)
        query = {"user_id": user["_id"]}
        if status: query["status"] = status
        total = await db.sport_bets.count_documents(query)
        bets = await db.sport_bets.find(query).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
        result = []
        for b in bets:
            result.append({
                "bet_id": str(b["_id"]),
                "bet_type": b.get("bet_type"),
                "selections": b.get("selections", []),
                "stake": b.get("stake"), "total_stake": b.get("total_stake"),
                "potential_win": b.get("potential_win"),
                "odds": b.get("odds"),
                "status": b.get("status"),
                "cash_out_available": b.get("cash_out_available", False),
                "win_amount": b.get("win_amount"),
                "created_at": b["created_at"].isoformat() if isinstance(b.get("created_at"), datetime) else str(b.get("created_at", "")),
            })
        return {"bets": result, "total": total, "page": page}

    @router.get("/sports")
    async def list_sports():
        pipeline = [{"$group": {"_id": "$sport", "count": {"$sum": 1}}}]
        sports = await db.betting_events.aggregate(pipeline).to_list(20)
        return {"sports": [{"sport": s["_id"], "events": s["count"]} for s in sports]}

    @router.get("/live")
    async def live_events():
        events = await db.betting_events.find({"status": "live"}).to_list(50)
        result = []
        for e in events:
            result.append({
                "event_id": str(e["_id"]),
                "sport": e["sport"], "league": e.get("league", ""),
                "home_team": e["home_team"], "away_team": e["away_team"],
                "score": e.get("score"), "minute": e.get("minute"),
                "markets_count": len(e.get("markets", [])),
            })
        return {"live_events": result}

    # Admin: Settle market
    @router.post("/admin/settle")
    async def admin_settle_market(body: SettleMarketBody, request: Request):
        user = await get_user(request)
        if user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin only")
        try:
            event = await db.betting_events.find_one({"_id": ObjectId(body.event_id)})
        except:
            raise HTTPException(status_code=404, detail="Event not found")
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Update market status
        markets = event.get("markets", [])
        for m in markets:
            if m.get("market_id") == body.market_id:
                m["status"] = "settled"
                m["result"] = body.result
                m["winning_selection"] = body.winning_selection
                break

        await db.betting_events.update_one({"_id": ObjectId(body.event_id)}, {"$set": {"markets": markets}})

        # Settle all open bets with this market
        open_bets = await db.sport_bets.find({"status": "open"}).to_list(10000)
        settled_count = 0
        for bet in open_bets:
            for sel in bet.get("selections", []):
                if sel["event_id"] == body.event_id and sel["market_id"] == body.market_id:
                    won = sel["selection"] == body.winning_selection
                    if bet["bet_type"] == "single":
                        win_amount = round(bet["stake"] * sel["odds"], 2) if won else 0
                        new_status = "won" if won else "lost"
                        await db.sport_bets.update_one({"_id": bet["_id"]}, {"$set": {"status": new_status, "win_amount": win_amount, "settled_at": datetime.now(timezone.utc)}})
                        if win_amount > 0:
                            await db.users.update_one({"_id": ObjectId(bet["user_id"])}, {"$inc": {"balance": win_amount}})
                            await db.transactions.insert_one({
                                "user_id": bet["user_id"], "type": "sport_win",
                                "amount": win_amount, "description": f"Sport bet won: ${win_amount}",
                                "created_at": datetime.now(timezone.utc),
                            })
                        settled_count += 1

        return {"message": f"Market settled. {settled_count} bets processed.", "winning_selection": body.winning_selection}

    return router
