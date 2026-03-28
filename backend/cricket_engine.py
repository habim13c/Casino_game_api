"""
Cricket Live Betting Engine
Full simulation engine, ball-by-ball processing, 19 betting markets,
auto-settlement, live odds calculation
"""
import random
import math
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List

router = APIRouter(prefix="/api/cricket", tags=["cricket"])

# ==================== MATCH FORMATS ====================
FORMATS = {
    "T20": {"overs": 20, "innings": 2},
    "ODI": {"overs": 50, "innings": 2},
    "TEST": {"overs": 90, "innings": 4},
    "T10": {"overs": 10, "innings": 2},
}

TEAMS = [
    {"name": "India", "code": "IND", "strength": 90},
    {"name": "Australia", "code": "AUS", "strength": 88},
    {"name": "England", "code": "ENG", "strength": 85},
    {"name": "New Zealand", "code": "NZ", "strength": 83},
    {"name": "South Africa", "code": "SA", "strength": 82},
    {"name": "Pakistan", "code": "PAK", "strength": 80},
    {"name": "Sri Lanka", "code": "SL", "strength": 75},
    {"name": "West Indies", "code": "WI", "strength": 73},
    {"name": "Bangladesh", "code": "BAN", "strength": 70},
    {"name": "Afghanistan", "code": "AFG", "strength": 68},
]

PLAYER_NAMES = {
    "IND": ["Sharma", "Kohli", "Gill", "Iyer", "Pant", "Jadeja", "Ashwin", "Bumrah", "Siraj", "Kuldeep", "Rahul"],
    "AUS": ["Warner", "Smith", "Labuschagne", "Head", "Green", "Carey", "Cummins", "Starc", "Hazlewood", "Lyon", "Maxwell"],
    "ENG": ["Root", "Brook", "Crawley", "Duckett", "Stokes", "Bairstow", "Anderson", "Broad", "Archer", "Rashid", "Buttler"],
    "NZ": ["Williamson", "Conway", "Latham", "Mitchell", "Blundell", "Southee", "Boult", "Henry", "Jamieson", "Santner", "Phillips"],
    "SA": ["Bavuma", "Markram", "Van der Dussen", "De Kock", "Rabada", "Nortje", "Jansen", "Ngidi", "Shamsi", "Miller", "Klaasen"],
    "PAK": ["Babar", "Rizwan", "Fakhar", "Imam", "Shaheen", "Naseem", "Rauf", "Wasim", "Shadab", "Iftikhar", "Salman"],
}

VENUES = ["MCG, Melbourne", "Lords, London", "Wankhede, Mumbai", "SCG, Sydney",
          "Eden Gardens, Kolkata", "Oval, London", "Galle Fort, Galle",
          "Dubai International", "Newlands, Cape Town", "Basin Reserve, Wellington"]

# ==================== SIMULATION ENGINE ====================
class CricketSimulator:
    @staticmethod
    def generate_delivery():
        """Simulate a single delivery"""
        rand = random.random()
        if rand < 0.01:
            return {"type": "wicket", "runs": 0, "method": random.choice(["bowled", "caught", "lbw", "run_out", "stumped"])}
        elif rand < 0.03:
            return {"type": "extra", "runs": random.choice([1, 2, 5]), "extra_type": random.choice(["wide", "no_ball"])}
        elif rand < 0.08:
            return {"type": "boundary", "runs": 4}
        elif rand < 0.12:
            return {"type": "six", "runs": 6}
        elif rand < 0.45:
            return {"type": "runs", "runs": 1}
        elif rand < 0.55:
            return {"type": "runs", "runs": 2}
        elif rand < 0.60:
            return {"type": "runs", "runs": 3}
        else:
            return {"type": "dot", "runs": 0}

    @staticmethod
    def simulate_over(team_strength=80):
        """Simulate a complete over"""
        deliveries = []
        balls = 0
        runs = 0
        wickets = 0
        while balls < 6:
            delivery = CricketSimulator.generate_delivery()
            if delivery["type"] == "extra":
                runs += delivery["runs"]
                deliveries.append(delivery)
                continue
            runs += delivery["runs"]
            if delivery["type"] == "wicket":
                wickets += 1
            balls += 1
            deliveries.append(delivery)
        return {"deliveries": deliveries, "runs": runs, "wickets": wickets}

    @staticmethod
    def simulate_innings(team_code, overs_limit, target=None, team_strength=80):
        """Simulate a complete innings"""
        players = PLAYER_NAMES.get(team_code, ["Player " + str(i) for i in range(1, 12)])
        scorecard = {
            "batting": [],
            "bowling": [],
            "total_runs": 0,
            "total_wickets": 0,
            "total_overs": 0,
            "extras": 0,
            "fours": 0,
            "sixes": 0,
            "run_rate": 0,
            "balls": [],
        }
        batsman_idx = 0
        bowler_idx = 0
        batsman_scores = {p: 0 for p in players[:11]}
        current_batsmen = [players[0], players[1]]

        for over_num in range(overs_limit):
            if scorecard["total_wickets"] >= 10:
                break
            if target and scorecard["total_runs"] >= target:
                break

            over_result = CricketSimulator.simulate_over(team_strength)
            for d in over_result["deliveries"]:
                ball_data = {
                    "over": over_num, "ball": len(scorecard["balls"]) % 6 + 1,
                    "batsman": current_batsmen[0],
                    "bowler": f"Bowler {over_num % 5 + 1}",
                    "runs": d["runs"], "type": d["type"],
                }
                if d["type"] == "wicket":
                    ball_data["method"] = d.get("method", "bowled")
                    scorecard["total_wickets"] += 1
                    scorecard["batting"].append({
                        "name": current_batsmen[0],
                        "runs": batsman_scores.get(current_batsmen[0], 0),
                        "dismissal": d.get("method", "bowled"),
                    })
                    batsman_idx += 1
                    if batsman_idx + 1 < len(players):
                        current_batsmen[0] = players[batsman_idx + 1]
                        batsman_scores[current_batsmen[0]] = 0
                elif d["type"] == "boundary":
                    scorecard["fours"] += 1
                    batsman_scores[current_batsmen[0]] = batsman_scores.get(current_batsmen[0], 0) + d["runs"]
                elif d["type"] == "six":
                    scorecard["sixes"] += 1
                    batsman_scores[current_batsmen[0]] = batsman_scores.get(current_batsmen[0], 0) + d["runs"]
                elif d["type"] == "extra":
                    scorecard["extras"] += d["runs"]
                else:
                    batsman_scores[current_batsmen[0]] = batsman_scores.get(current_batsmen[0], 0) + d["runs"]
                    if d["runs"] % 2 == 1:
                        current_batsmen[0], current_batsmen[1] = current_batsmen[1], current_batsmen[0]

                scorecard["total_runs"] += d["runs"]
                scorecard["balls"].append(ball_data)

            scorecard["total_overs"] = over_num + 1
            if target and scorecard["total_runs"] >= target:
                break

        scorecard["run_rate"] = round(scorecard["total_runs"] / max(scorecard["total_overs"], 1), 2)
        # Add not-out batsmen
        for b in current_batsmen:
            if b in batsman_scores:
                scorecard["batting"].append({"name": b, "runs": batsman_scores[b], "dismissal": "not out"})

        return scorecard

    @staticmethod
    def simulate_match(team1_code, team2_code, format_type="T20"):
        """Simulate a complete match"""
        fmt = FORMATS.get(format_type, FORMATS["T20"])
        team1 = next((t for t in TEAMS if t["code"] == team1_code), {"name": team1_code, "strength": 75})
        team2 = next((t for t in TEAMS if t["code"] == team2_code), {"name": team2_code, "strength": 75})

        toss_winner = random.choice([team1_code, team2_code])
        toss_decision = random.choice(["bat", "bowl"])
        bat_first = team1_code if (toss_winner == team1_code and toss_decision == "bat") or (toss_winner == team2_code and toss_decision == "bowl") else team2_code
        bowl_first = team2_code if bat_first == team1_code else team1_code

        innings1 = CricketSimulator.simulate_innings(bat_first, fmt["overs"], team_strength=team1["strength"] if bat_first == team1_code else team2["strength"])
        target = innings1["total_runs"] + 1
        innings2 = CricketSimulator.simulate_innings(bowl_first, fmt["overs"], target=target, team_strength=team2["strength"] if bowl_first == team2_code else team1["strength"])

        if innings2["total_runs"] >= target:
            winner = bowl_first
            result = f"{next(t['name'] for t in TEAMS if t['code'] == bowl_first)} won by {10 - innings2['total_wickets']} wickets"
        else:
            winner = bat_first
            margin = innings1["total_runs"] - innings2["total_runs"]
            result = f"{next(t['name'] for t in TEAMS if t['code'] == bat_first)} won by {margin} runs"

        return {
            "toss": {"winner": toss_winner, "decision": toss_decision},
            "bat_first": bat_first, "bowl_first": bowl_first,
            "innings": [innings1, innings2],
            "winner": winner, "result": result,
            "man_of_match": random.choice(innings1["batting"][:3] + innings2["batting"][:3])["name"] if innings1["batting"] and innings2["batting"] else "Unknown",
        }


# ==================== CRICKET MARKETS ====================
def generate_cricket_markets(match, team1, team2):
    t1_strength = next((t["strength"] for t in TEAMS if t["code"] == team1), 75)
    t2_strength = next((t["strength"] for t in TEAMS if t["code"] == team2), 75)
    total = t1_strength + t2_strength
    t1_prob = t1_strength / total
    t2_prob = t2_strength / total
    margin = 1.05
    t1_name = next((t["name"] for t in TEAMS if t["code"] == team1), team1)
    t2_name = next((t["name"] for t in TEAMS if t["code"] == team2), team2)

    markets = [
        {"market_type": "match_winner", "name": "Match Winner", "status": "open",
         "selections": [
             {"name": t1_name, "key": "team1", "odds": round(margin / t1_prob, 2)},
             {"name": t2_name, "key": "team2", "odds": round(margin / t2_prob, 2)},
         ]},
        {"market_type": "total_runs", "name": "Total Runs Over/Under", "status": "open", "line": 300,
         "selections": [
             {"name": "Over 300", "key": "over", "odds": 1.90},
             {"name": "Under 300", "key": "under", "odds": 1.95},
         ]},
        {"market_type": "first_over_runs", "name": "1st Over Runs", "status": "open",
         "selections": [
             {"name": "Over 6.5", "key": "over", "odds": 1.85},
             {"name": "Under 6.5", "key": "under", "odds": 2.00},
         ]},
        {"market_type": "powerplay_score", "name": "Powerplay Score", "status": "open",
         "selections": [
             {"name": "Over 45.5", "key": "over", "odds": 1.90},
             {"name": "Under 45.5", "key": "under", "odds": 1.90},
         ]},
        {"market_type": "toss_winner", "name": "Toss Winner", "status": "open",
         "selections": [
             {"name": t1_name, "key": "team1", "odds": 2.00},
             {"name": t2_name, "key": "team2", "odds": 2.00},
         ]},
        {"market_type": "top_batsman", "name": "Top Batsman", "status": "open",
         "selections": [{"name": p, "key": p.lower().replace(" ", "_"), "odds": round(random.uniform(3.0, 12.0), 2)} for p in (PLAYER_NAMES.get(team1, [])[:3] + PLAYER_NAMES.get(team2, [])[:3])]},
        {"market_type": "man_of_match", "name": "Man of the Match", "status": "open",
         "selections": [{"name": p, "key": p.lower().replace(" ", "_"), "odds": round(random.uniform(5.0, 15.0), 2)} for p in (PLAYER_NAMES.get(team1, [])[:3] + PLAYER_NAMES.get(team2, [])[:3])]},
        {"market_type": "fifty_scored", "name": "50 Scored (Yes/No)", "status": "open",
         "selections": [{"name": "Yes", "key": "yes", "odds": 1.40}, {"name": "No", "key": "no", "odds": 3.00}]},
        {"market_type": "hundred_scored", "name": "100 Scored (Yes/No)", "status": "open",
         "selections": [{"name": "Yes", "key": "yes", "odds": 3.50}, {"name": "No", "key": "no", "odds": 1.30}]},
        {"market_type": "team_total_innings", "name": f"{t1_name} Total (1st Innings)", "status": "open",
         "selections": [{"name": "Over 160.5", "key": "over", "odds": 1.90}, {"name": "Under 160.5", "key": "under", "odds": 1.90}]},
        {"market_type": "next_boundary", "name": "Next Boundary Type", "status": "open",
         "selections": [{"name": "Four", "key": "four", "odds": 1.70}, {"name": "Six", "key": "six", "odds": 2.30}]},
        {"market_type": "top_bowler", "name": "Top Bowler", "status": "open",
         "selections": [{"name": p, "key": p.lower().replace(" ", "_"), "odds": round(random.uniform(3.0, 8.0), 2)} for p in (PLAYER_NAMES.get(team1, [])[7:10] + PLAYER_NAMES.get(team2, [])[7:10])]},
        {"market_type": "wides_total", "name": "Total Wides Over/Under", "status": "open",
         "selections": [{"name": "Over 8.5", "key": "over", "odds": 1.90}, {"name": "Under 8.5", "key": "under", "odds": 1.90}]},
        {"market_type": "run_rate", "name": "Run Rate Over/Under", "status": "open",
         "selections": [{"name": "Over 8.0", "key": "over", "odds": 1.85}, {"name": "Under 8.0", "key": "under", "odds": 2.00}]},
        {"market_type": "series_winner", "name": "Series Winner", "status": "open",
         "selections": [
             {"name": t1_name, "key": "team1", "odds": round(margin / t1_prob, 2)},
             {"name": t2_name, "key": "team2", "odds": round(margin / t2_prob, 2)},
             {"name": "Draw", "key": "draw", "odds": 5.00},
         ]},
        {"market_type": "next_wicket_method", "name": "Next Wicket Method", "status": "open",
         "selections": [
             {"name": "Bowled", "key": "bowled", "odds": 3.50},
             {"name": "Caught", "key": "caught", "odds": 1.80},
             {"name": "LBW", "key": "lbw", "odds": 4.00},
             {"name": "Run Out", "key": "run_out", "odds": 8.00},
             {"name": "Stumped", "key": "stumped", "odds": 12.00},
         ]},
        {"market_type": "fall_of_next_wicket", "name": "Fall of Next Wicket", "status": "open",
         "selections": [{"name": "Over 25.5", "key": "over", "odds": 1.90}, {"name": "Under 25.5", "key": "under", "odds": 1.90}]},
        {"market_type": "player_performance", "name": "Player Performance Props", "status": "open",
         "selections": [
             {"name": f"{PLAYER_NAMES.get(team1, ['Player'])[0]} 30+ runs", "key": "t1_bat_30", "odds": 2.20},
             {"name": f"{PLAYER_NAMES.get(team2, ['Player'])[0]} 30+ runs", "key": "t2_bat_30", "odds": 2.40},
         ]},
        {"market_type": "tournament_outright", "name": "Tournament Outright Winner", "status": "open",
         "selections": [{"name": t["name"], "key": t["code"].lower(), "odds": round(random.uniform(4.0, 20.0), 2)} for t in TEAMS[:6]]},
    ]
    for i, m in enumerate(markets):
        m["market_id"] = f"cricket_mkt_{i}"
    return markets


# ==================== SEED MATCHES ====================
async def seed_cricket_matches(db):
    count = await db.cricket_matches.count_documents({})
    if count > 0:
        return

    matches = []
    series_list = [
        {"name": "ICC World Cup 2026", "format": "ODI"},
        {"name": "IPL 2026", "format": "T20"},
        {"name": "The Ashes 2026", "format": "TEST"},
        {"name": "T20 World Cup 2026", "format": "T20"},
    ]
    for series in series_list:
        series_doc = {
            "name": series["name"],
            "format": series["format"],
            "status": "ongoing",
            "created_at": datetime.now(timezone.utc),
        }
        sr = await db.cricket_series.insert_one(series_doc)
        series_id = str(sr.inserted_id)

        team_pairs = random.sample(TEAMS, min(6, len(TEAMS)))
        for i in range(0, len(team_pairs) - 1, 2):
            t1 = team_pairs[i]
            t2 = team_pairs[i + 1]
            is_live = random.random() < 0.3
            start_offset = random.randint(-2, 48)
            start_time = datetime.now(timezone.utc) + timedelta(hours=start_offset)

            match_data = {
                "series_id": series_id,
                "series_name": series["name"],
                "format": series["format"],
                "team1": {"name": t1["name"], "code": t1["code"]},
                "team2": {"name": t2["name"], "code": t2["code"]},
                "venue": random.choice(VENUES),
                "start_time": start_time,
                "status": "live" if is_live else ("upcoming" if start_offset > 0 else "completed"),
                "toss": None,
                "score": None,
                "current_innings": None,
                "markets": generate_cricket_markets(None, t1["code"], t2["code"]),
                "created_at": datetime.now(timezone.utc),
            }

            if is_live:
                # Generate partial score
                batting_team = random.choice([t1["code"], t2["code"]])
                overs = random.randint(3, int(FORMATS[series["format"]]["overs"] * 0.7))
                runs = random.randint(int(overs * 5), int(overs * 10))
                wickets = random.randint(0, min(6, overs // 3))
                match_data["score"] = {
                    "innings": [{"team": batting_team, "runs": runs, "wickets": wickets, "overs": overs}],
                }
                match_data["current_innings"] = 1
                match_data["toss"] = {"winner": batting_team, "decision": "bat"}

            if match_data["status"] == "completed":
                sim = CricketSimulator.simulate_match(t1["code"], t2["code"], series["format"])
                match_data["score"] = {
                    "innings": [
                        {"team": sim["bat_first"], "runs": sim["innings"][0]["total_runs"], "wickets": sim["innings"][0]["total_wickets"], "overs": sim["innings"][0]["total_overs"]},
                        {"team": sim["bowl_first"], "runs": sim["innings"][1]["total_runs"], "wickets": sim["innings"][1]["total_wickets"], "overs": sim["innings"][1]["total_overs"]},
                    ],
                }
                match_data["result"] = sim["result"]
                match_data["winner"] = sim["winner"]
                match_data["toss"] = sim["toss"]

            matches.append(match_data)

    if matches:
        await db.cricket_matches.insert_many(matches)
    await db.cricket_matches.create_index("status")
    await db.cricket_matches.create_index("series_id")


# ==================== ROUTES ====================
def create_cricket_routes(db):

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

    @router.get("/matches")
    async def list_matches(status: Optional[str] = None, format: Optional[str] = None, page: int = 1, limit: int = 20):
        query = {}
        if status: query["status"] = status
        if format: query["format"] = format
        total = await db.cricket_matches.count_documents(query)
        matches = await db.cricket_matches.find(query).sort("start_time", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
        result = []
        for m in matches:
            result.append({
                "match_id": str(m["_id"]),
                "series_name": m.get("series_name", ""),
                "format": m.get("format"),
                "team1": m.get("team1"), "team2": m.get("team2"),
                "venue": m.get("venue"),
                "start_time": m["start_time"].isoformat() if isinstance(m.get("start_time"), datetime) else str(m.get("start_time", "")),
                "status": m.get("status"),
                "score": m.get("score"),
                "result": m.get("result"),
                "markets_count": len(m.get("markets", [])),
            })
        return {"matches": result, "total": total, "page": page}

    @router.get("/matches/{match_id}")
    async def get_match(match_id: str):
        try: match = await db.cricket_matches.find_one({"_id": ObjectId(match_id)})
        except: raise HTTPException(status_code=404, detail="Match not found")
        if not match: raise HTTPException(status_code=404, detail="Match not found")
        match["_id"] = str(match["_id"])
        if isinstance(match.get("start_time"), datetime):
            match["start_time"] = match["start_time"].isoformat()
        if isinstance(match.get("created_at"), datetime):
            match["created_at"] = match["created_at"].isoformat()
        return {"match": match}

    @router.get("/matches/{match_id}/markets")
    async def get_match_markets(match_id: str):
        try: match = await db.cricket_matches.find_one({"_id": ObjectId(match_id)})
        except: raise HTTPException(status_code=404, detail="Match not found")
        if not match: raise HTTPException(status_code=404, detail="Match not found")
        return {"markets": match.get("markets", []), "match_status": match.get("status")}

    @router.post("/matches/{match_id}/bet")
    async def place_cricket_bet(match_id: str, request: Request):
        user = await get_user(request)
        body = await request.json()
        market_id = body.get("market_id")
        selection = body.get("selection")
        stake = float(body.get("stake", 0))

        if stake <= 0: raise HTTPException(status_code=400, detail="Invalid stake")

        try: match = await db.cricket_matches.find_one({"_id": ObjectId(match_id)})
        except: raise HTTPException(status_code=404, detail="Match not found")
        if not match: raise HTTPException(status_code=404, detail="Match not found")

        market = None
        for m in match.get("markets", []):
            if m.get("market_id") == market_id:
                market = m
                break
        if not market: raise HTTPException(status_code=404, detail="Market not found")
        if market.get("status") != "open": raise HTTPException(status_code=400, detail=f"Market is {market.get('status')}")

        sel_data = None
        for s in market.get("selections", []):
            if s.get("key") == selection:
                sel_data = s
                break
        if not sel_data: raise HTTPException(status_code=400, detail="Selection not found")

        u = await db.users.find_one({"_id": ObjectId(user["_id"])})
        if u["balance"] < stake: raise HTTPException(status_code=400, detail="Insufficient balance")

        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": -stake}})

        bet_doc = {
            "user_id": user["_id"],
            "match_id": match_id,
            "market_id": market_id,
            "market_name": market.get("name", ""),
            "selection": selection,
            "selection_name": sel_data["name"],
            "odds": sel_data["odds"],
            "stake": stake,
            "potential_win": round(stake * sel_data["odds"], 2),
            "status": "open",
            "created_at": datetime.now(timezone.utc),
        }
        result = await db.cricket_bets.insert_one(bet_doc)

        await db.transactions.insert_one({
            "user_id": user["_id"], "type": "cricket_bet",
            "amount": -stake, "balance_after": round(u["balance"] - stake, 2),
            "description": f"Cricket bet: {market.get('name')} - {sel_data['name']}",
            "created_at": datetime.now(timezone.utc),
        })

        u_after = await db.users.find_one({"_id": ObjectId(user["_id"])})
        return {
            "bet_id": str(result.inserted_id),
            "market": market.get("name"),
            "selection": sel_data["name"],
            "odds": sel_data["odds"],
            "stake": stake,
            "potential_win": round(stake * sel_data["odds"], 2),
            "balance": round(u_after["balance"], 2),
        }

    @router.get("/my-bets")
    async def my_cricket_bets(request: Request, page: int = 1, limit: int = 20):
        user = await get_user(request)
        total = await db.cricket_bets.count_documents({"user_id": user["_id"]})
        bets = await db.cricket_bets.find({"user_id": user["_id"]}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
        result = []
        for b in bets:
            result.append({
                "bet_id": str(b["_id"]),
                "match_id": b.get("match_id"),
                "market_name": b.get("market_name"),
                "selection_name": b.get("selection_name"),
                "odds": b.get("odds"), "stake": b.get("stake"),
                "potential_win": b.get("potential_win"),
                "status": b.get("status"),
                "win_amount": b.get("win_amount"),
                "created_at": b["created_at"].isoformat() if isinstance(b.get("created_at"), datetime) else str(b.get("created_at", "")),
            })
        return {"bets": result, "total": total, "page": page}

    @router.get("/series")
    async def list_series():
        series = await db.cricket_series.find({}).sort("created_at", -1).to_list(50)
        result = []
        for s in series:
            match_count = await db.cricket_matches.count_documents({"series_id": str(s["_id"])})
            result.append({
                "series_id": str(s["_id"]),
                "name": s.get("name"), "format": s.get("format"),
                "status": s.get("status"), "matches": match_count,
            })
        return {"series": result}

    @router.get("/live")
    async def live_matches():
        matches = await db.cricket_matches.find({"status": "live"}).to_list(20)
        result = []
        for m in matches:
            result.append({
                "match_id": str(m["_id"]),
                "team1": m.get("team1"), "team2": m.get("team2"),
                "format": m.get("format"), "venue": m.get("venue"),
                "score": m.get("score"),
                "markets_count": len([mk for mk in m.get("markets", []) if mk.get("status") == "open"]),
            })
        return {"live_matches": result}

    @router.post("/simulate/{match_id}")
    async def simulate_match(match_id: str, request: Request):
        user = await get_user(request)
        if user.get("role") not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Admin only")
        try: match = await db.cricket_matches.find_one({"_id": ObjectId(match_id)})
        except: raise HTTPException(status_code=404, detail="Match not found")
        if not match: raise HTTPException(status_code=404, detail="Match not found")

        t1 = match["team1"]["code"]
        t2 = match["team2"]["code"]
        sim = CricketSimulator.simulate_match(t1, t2, match.get("format", "T20"))

        score = {
            "innings": [
                {"team": sim["bat_first"], "runs": sim["innings"][0]["total_runs"], "wickets": sim["innings"][0]["total_wickets"], "overs": sim["innings"][0]["total_overs"]},
                {"team": sim["bowl_first"], "runs": sim["innings"][1]["total_runs"], "wickets": sim["innings"][1]["total_wickets"], "overs": sim["innings"][1]["total_overs"]},
            ],
        }

        await db.cricket_matches.update_one({"_id": ObjectId(match_id)}, {"$set": {
            "status": "completed", "score": score, "result": sim["result"],
            "winner": sim["winner"], "toss": sim["toss"],
            "simulation": sim,
        }})

        # Auto-settle match_winner bets
        markets = match.get("markets", [])
        for m in markets:
            if m.get("market_type") == "match_winner":
                winning = "team1" if sim["winner"] == t1 else "team2"
                m["status"] = "settled"
                m["winning_selection"] = winning
                open_bets = await db.cricket_bets.find({"match_id": match_id, "market_id": m["market_id"], "status": "open"}).to_list(10000)
                for bet in open_bets:
                    won = bet["selection"] == winning
                    win_amount = round(bet["stake"] * bet["odds"], 2) if won else 0
                    await db.cricket_bets.update_one({"_id": bet["_id"]}, {"$set": {"status": "won" if won else "lost", "win_amount": win_amount, "settled_at": datetime.now(timezone.utc)}})
                    if win_amount > 0:
                        await db.users.update_one({"_id": ObjectId(bet["user_id"])}, {"$inc": {"balance": win_amount}})

        await db.cricket_matches.update_one({"_id": ObjectId(match_id)}, {"$set": {"markets": markets}})

        return {"message": "Match simulated", "result": sim["result"], "winner": sim["winner"], "score": score}

    @router.get("/stats/teams")
    async def team_stats():
        return {"teams": TEAMS}

    @router.get("/stats/players/{team_code}")
    async def team_players(team_code: str):
        players = PLAYER_NAMES.get(team_code.upper(), [])
        return {"team_code": team_code, "players": [{"name": p, "role": "batsman" if i < 6 else "bowler"} for i, p in enumerate(players)]}

    return router
