"""
Interactive Game Session Manager
Handles stateful games: Blackjack (hit/stand/double/split), Mines (tile reveal/cashout),
Poker (hold/draw), Hi-Lo (guess chain), Crash (cashout timing)
"""
import math
import random
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from provably_fair import (
    generate_server_seed, generate_client_seed,
    provably_fair_hash, hash_to_int, hash_to_float, create_shuffled_deck
)
from games import (
    card_str, card_rank_value, hand_total_bj, card_value_bj,
    baccarat_card_val, baccarat_hand_val, evaluate_poker, GAME_INFO
)

router = APIRouter(prefix="/api/sessions", tags=["game_sessions"])


# ==================== SCHEMAS ====================
class StartSessionBody(BaseModel):
    bet_amount: float = Field(gt=0)
    params: dict = {}

class ActionBody(BaseModel):
    action: str
    params: dict = {}


# ==================== HELPERS ====================
def card_display(card):
    return {"rank": card["rank"], "suit": card["suit"], "display": card_str(card)}


async def get_user_from_request(request: Request, db):
    import jwt, os
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, os.environ.get("JWT_SECRET"), algorithms=["HS256"])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Auth failed")


# ==================== BLACKJACK SESSION ====================
class BlackjackEngine:
    @staticmethod
    def start(bet_amount, params, hash_hex):
        deck = create_shuffled_deck(hash_hex)
        player = [deck.pop(), deck.pop()]
        dealer = [deck.pop(), deck.pop()]
        pv = hand_total_bj(player)
        dv = hand_total_bj(dealer)

        # Check for natural blackjack
        if pv == 21:
            if dv == 21:
                return {
                    "phase": "complete", "deck_index": len(deck),
                    "player_hands": [[card_display(c) for c in player]],
                    "dealer_hand": [card_display(c) for c in dealer],
                    "player_values": [pv], "dealer_value": dv,
                    "outcome": ["push"], "multiplier": 1.0,
                    "can_hit": False, "can_stand": False, "can_double": False, "can_split": False,
                    "active_hand": 0, "deck": [{"rank": c["rank"], "suit": c["suit"]} for c in deck],
                }
            return {
                "phase": "complete", "deck_index": len(deck),
                "player_hands": [[card_display(c) for c in player]],
                "dealer_hand": [card_display(c) for c in dealer],
                "player_values": [pv], "dealer_value": dv,
                "outcome": ["blackjack"], "multiplier": 2.5,
                "can_hit": False, "can_stand": False, "can_double": False, "can_split": False,
                "active_hand": 0, "deck": [{"rank": c["rank"], "suit": c["suit"]} for c in deck],
            }

        can_split = len(player) == 2 and card_value_bj(player[0]) == card_value_bj(player[1])
        can_double = len(player) == 2

        return {
            "phase": "player_turn", "deck_index": len(deck),
            "player_hands": [[card_display(c) for c in player]],
            "dealer_hand": [card_display(dealer[0]), {"rank": "?", "suit": "?", "display": "Hidden"}],
            "dealer_full": [card_display(c) for c in dealer],
            "player_values": [pv], "dealer_value": None,
            "outcome": None, "multiplier": 0,
            "can_hit": True, "can_stand": True,
            "can_double": can_double, "can_split": can_split,
            "active_hand": 0,
            "deck": [{"rank": c["rank"], "suit": c["suit"]} for c in deck],
            "split_bets": [bet_amount],
        }

    @staticmethod
    def action(state, action, params, bet_amount):
        deck_data = state.get("deck", [])
        deck = [{"rank": c["rank"], "suit": c["suit"]} for c in deck_data]
        di = 0
        active = state.get("active_hand", 0)
        player_hands = state.get("player_hands", [[]])
        split_bets = state.get("split_bets", [bet_amount])
        dealer_full = state.get("dealer_full", state.get("dealer_hand", []))

        def draw():
            nonlocal di
            if di < len(deck):
                c = deck[di]
                di += 1
                return c
            return {"rank": "2", "suit": "hearts"}

        def hand_val(hand):
            total = 0
            aces = 0
            for c in hand:
                r = c.get("rank", "2")
                if r in ["J", "Q", "K"]:
                    total += 10
                elif r == "A":
                    total += 11
                    aces += 1
                elif r == "?":
                    pass
                else:
                    total += int(r)
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        if action == "hit":
            card = draw()
            card["display"] = f"{card['rank']} of {card['suit']}"
            player_hands[active].append(card)
            pv = hand_val(player_hands[active])
            if pv > 21:
                # Bust - move to next hand or dealer
                if active + 1 < len(player_hands):
                    state["active_hand"] = active + 1
                    state["player_hands"] = player_hands
                    state["player_values"] = [hand_val(h) for h in player_hands]
                    state["can_double"] = len(player_hands[active + 1]) == 2
                    state["can_split"] = False
                    state["deck"] = deck[di:]
                    return state
                else:
                    return BlackjackEngine._resolve(state, player_hands, dealer_full, deck, di, split_bets, bet_amount)
            state["player_hands"] = player_hands
            state["player_values"] = [hand_val(h) for h in player_hands]
            state["can_double"] = False
            state["can_split"] = False
            state["deck"] = deck[di:]
            return state

        elif action == "stand":
            if active + 1 < len(player_hands):
                state["active_hand"] = active + 1
                state["can_double"] = len(player_hands[active + 1]) == 2
                state["can_split"] = False
                return state
            return BlackjackEngine._resolve(state, player_hands, dealer_full, deck, di, split_bets, bet_amount)

        elif action == "double":
            card = draw()
            card["display"] = f"{card['rank']} of {card['suit']}"
            player_hands[active].append(card)
            split_bets[active] = split_bets[active] * 2
            state["split_bets"] = split_bets
            if active + 1 < len(player_hands):
                state["active_hand"] = active + 1
                state["player_hands"] = player_hands
                state["player_values"] = [hand_val(h) for h in player_hands]
                state["deck"] = deck[di:]
                return state
            return BlackjackEngine._resolve(state, player_hands, dealer_full, deck, di, split_bets, bet_amount)

        elif action == "split":
            if len(player_hands[active]) == 2:
                c1 = player_hands[active][0]
                c2 = player_hands[active][1]
                new1 = draw()
                new1["display"] = f"{new1['rank']} of {new1['suit']}"
                new2 = draw()
                new2["display"] = f"{new2['rank']} of {new2['suit']}"
                player_hands[active] = [c1, new1]
                player_hands.insert(active + 1, [c2, new2])
                split_bets.insert(active + 1, bet_amount)
                state["player_hands"] = player_hands
                state["split_bets"] = split_bets
                state["player_values"] = [hand_val(h) for h in player_hands]
                state["can_split"] = False
                state["can_double"] = True
                state["deck"] = deck[di:]
                return state

        return state

    @staticmethod
    def _resolve(state, player_hands, dealer_full, deck, di, split_bets, original_bet):
        def hand_val(hand):
            total = 0
            aces = 0
            for c in hand:
                r = c.get("rank", "2")
                if r in ["J", "Q", "K"]:
                    total += 10
                elif r == "A":
                    total += 11
                    aces += 1
                elif r != "?":
                    total += int(r)
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        def draw():
            nonlocal di
            if di < len(deck):
                c = deck[di]
                di += 1
                c["display"] = f"{c['rank']} of {c['suit']}"
                return c
            return {"rank": "2", "suit": "hearts", "display": "2 of hearts"}

        # Dealer plays
        any_active = any(hand_val(h) <= 21 for h in player_hands)
        if any_active:
            while hand_val(dealer_full) < 17:
                dealer_full.append(draw())

        dv = hand_val(dealer_full)
        outcomes = []
        total_multiplier = 0

        for i, hand in enumerate(player_hands):
            pv = hand_val(hand)
            bet_ratio = split_bets[i] / original_bet if original_bet > 0 else 1
            if pv > 21:
                outcomes.append("bust")
            elif dv > 21:
                outcomes.append("win")
                total_multiplier += 2 * bet_ratio
            elif pv > dv:
                outcomes.append("win")
                total_multiplier += 2 * bet_ratio
            elif pv == dv:
                outcomes.append("push")
                total_multiplier += 1 * bet_ratio
            else:
                outcomes.append("lose")

        state["phase"] = "complete"
        state["player_hands"] = player_hands
        state["dealer_hand"] = dealer_full
        state["player_values"] = [hand_val(h) for h in player_hands]
        state["dealer_value"] = dv
        state["outcome"] = outcomes
        state["multiplier"] = round(total_multiplier, 2)
        state["can_hit"] = False
        state["can_stand"] = False
        state["can_double"] = False
        state["can_split"] = False
        state["deck"] = deck[di:]
        return state


# ==================== MINES SESSION ====================
class MinesEngine:
    @staticmethod
    def start(bet_amount, params, hash_hex):
        mc = int(params.get("mines_count", 3))
        mc = max(1, min(24, mc))
        positions = set()
        seed_int = int(hash_hex[:16], 16)
        rng = random.Random(seed_int)
        while len(positions) < mc:
            positions.add(rng.randint(0, 24))

        return {
            "phase": "playing", "mines_count": mc,
            "mine_positions": list(positions),
            "revealed": [], "grid_size": 25,
            "safe_tiles": 25 - mc, "current_multiplier": 1.0,
            "next_multiplier": round(0.97 * 25 / (25 - mc), 4),
        }

    @staticmethod
    def action(state, action, params, bet_amount):
        if action == "reveal":
            tile = int(params.get("tile", 0))
            if tile < 0 or tile >= 25:
                raise HTTPException(status_code=400, detail="Invalid tile")
            if tile in state["revealed"]:
                raise HTTPException(status_code=400, detail="Tile already revealed")

            mines = state["mine_positions"]
            revealed = state["revealed"]

            if tile in mines:
                state["phase"] = "complete"
                state["outcome"] = "bust"
                state["multiplier"] = 0
                state["hit_mine"] = tile
                return state

            revealed.append(tile)
            safe = state["safe_tiles"]
            r = len(revealed)
            prob = 1.0
            for i in range(r):
                prob *= (safe - i) / (25 - i)
            mult = round(0.97 / prob, 4) if prob > 0 else 0

            # Next multiplier
            next_prob = prob * (safe - r) / (25 - r) if (25 - r) > 0 and (safe - r) > 0 else 0
            next_mult = round(0.97 / next_prob, 4) if next_prob > 0 else 0

            state["revealed"] = revealed
            state["current_multiplier"] = mult
            state["next_multiplier"] = next_mult

            if r >= safe:
                state["phase"] = "complete"
                state["outcome"] = "max_win"
                state["multiplier"] = mult

            return state

        elif action == "cashout":
            if len(state["revealed"]) == 0:
                raise HTTPException(status_code=400, detail="Reveal at least one tile")
            state["phase"] = "complete"
            state["outcome"] = "cashout"
            state["multiplier"] = state["current_multiplier"]
            return state

        return state


# ==================== POKER SESSION (Video Poker - Jacks or Better) ====================
class PokerEngine:
    @staticmethod
    def start(bet_amount, params, hash_hex):
        deck = create_shuffled_deck(hash_hex)
        hand = [deck.pop() for _ in range(5)]
        return {
            "phase": "initial_deal",
            "hand": [card_display(c) for c in hand],
            "raw_hand": hand,
            "deck": [{"rank": c["rank"], "suit": c["suit"]} for c in deck],
            "held": [False, False, False, False, False],
        }

    @staticmethod
    def action(state, action, params, bet_amount):
        if action == "draw":
            held = params.get("held", [0, 1, 2, 3, 4])
            if not isinstance(held, list):
                held = []
            held_set = set(int(h) for h in held if 0 <= int(h) < 5)
            deck = state.get("deck", [])
            hand = state.get("raw_hand", [])
            di = 0

            new_hand = []
            for i in range(5):
                if i in held_set:
                    new_hand.append(hand[i])
                elif di < len(deck):
                    new_hand.append(deck[di])
                    di += 1
                else:
                    new_hand.append(hand[i])

            hand_name, mult = evaluate_poker(new_hand)
            state["phase"] = "complete"
            state["hand"] = [card_display(c) for c in new_hand]
            state["raw_hand"] = new_hand
            state["hand_rank"] = hand_name
            state["multiplier"] = mult
            state["outcome"] = "win" if mult > 0 else "lose"
            return state

        return state


# ==================== HI-LO SESSION ====================
class HiLoEngine:
    @staticmethod
    def start(bet_amount, params, hash_hex):
        deck = create_shuffled_deck(hash_hex)
        first = deck.pop()
        return {
            "phase": "playing",
            "current_card": card_display(first),
            "current_value": card_rank_value(first),
            "deck": [{"rank": c["rank"], "suit": c["suit"]} for c in deck],
            "deck_index": 0,
            "streak": 0, "current_multiplier": 1.0,
            "history": [card_display(first)],
        }

    @staticmethod
    def action(state, action, params, bet_amount):
        if action in ("higher", "lower"):
            deck = state.get("deck", [])
            di = state.get("deck_index", 0)
            if di >= len(deck):
                state["phase"] = "complete"
                state["outcome"] = "max_streak"
                state["multiplier"] = state["current_multiplier"]
                return state

            next_card = deck[di]
            next_card["display"] = f"{next_card['rank']} of {next_card['suit']}"
            nv = card_rank_value(next_card)
            cv = state["current_value"]

            correct = False
            if action == "higher" and nv >= cv:
                correct = True
            elif action == "lower" and nv <= cv:
                correct = True

            if correct:
                state["streak"] += 1
                state["current_multiplier"] = round(state["current_multiplier"] * 1.8, 4)
                state["current_card"] = card_display(next_card) if "display" in next_card else next_card
                state["current_value"] = nv
                state["deck_index"] = di + 1
                state["history"].append(next_card)
            else:
                state["phase"] = "complete"
                state["outcome"] = "wrong"
                state["multiplier"] = 0
                state["last_card"] = next_card
                state["history"].append(next_card)

            return state

        elif action == "cashout":
            if state["streak"] == 0:
                raise HTTPException(status_code=400, detail="Make at least one guess")
            state["phase"] = "complete"
            state["outcome"] = "cashout"
            state["multiplier"] = state["current_multiplier"]
            return state

        return state


# ==================== CRASH SESSION ====================
class CrashEngine:
    @staticmethod
    def start(bet_amount, params, hash_hex):
        h = int(hash_hex[:13], 16)
        e = 2**52
        crash_point = max(1.0, round((e / (h + 1)) * 0.97, 2))
        crash_point = min(crash_point, 1000.0)
        return {
            "phase": "running",
            "crash_point": crash_point,
            "current_multiplier": 1.0,
            "auto_cashout": float(params.get("auto_cashout", 0)),
        }

    @staticmethod
    def action(state, action, params, bet_amount):
        if action == "cashout":
            cashout_at = float(params.get("multiplier", state.get("current_multiplier", 1.0)))
            if cashout_at <= state["crash_point"]:
                state["phase"] = "complete"
                state["outcome"] = "cashout"
                state["multiplier"] = cashout_at
            else:
                state["phase"] = "complete"
                state["outcome"] = "crashed"
                state["multiplier"] = 0
            return state
        return state


# ==================== SESSION ENGINE MAP ====================
SESSION_ENGINES = {
    "blackjack": BlackjackEngine,
    "mines": MinesEngine,
    "poker": PokerEngine,
    "video_poker": PokerEngine,
    "hilo": HiLoEngine,
    "crash": CrashEngine,
}


# ==================== ROUTES ====================
def create_session_routes(db):

    async def get_user(request: Request):
        return await get_user_from_request(request, db)

    @router.post("/{game_name}/start")
    async def start_session(game_name: str, body: StartSessionBody, request: Request):
        user = await get_user(request)
        if game_name not in SESSION_ENGINES:
            raise HTTPException(status_code=404, detail=f"Game '{game_name}' does not support sessions. Use /api/games/{game_name}/play for instant play.")

        config = await db.game_configs.find_one({"game_id": game_name})
        if config and not config.get("enabled", True):
            raise HTTPException(status_code=400, detail="Game is currently disabled")

        min_bet = config.get("min_bet", 1) if config else 1
        max_bet = config.get("max_bet", 100000) if config else 100000
        if body.bet_amount < min_bet:
            raise HTTPException(status_code=400, detail=f"Minimum bet is ${min_bet}")
        if body.bet_amount > max_bet:
            raise HTTPException(status_code=400, detail=f"Maximum bet is ${max_bet}")

        # Check existing active session
        existing = await db.game_sessions.find_one({"user_id": user["_id"], "game": game_name, "status": "active"})
        if existing:
            raise HTTPException(status_code=400, detail="You already have an active session for this game")

        u = await db.users.find_one({"_id": ObjectId(user["_id"])})
        if u["balance"] < body.bet_amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Deduct bet
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": -body.bet_amount}})

        server_seed = generate_server_seed()
        client_seed = generate_client_seed()
        nonce = random.randint(1, 1000000)
        hash_hex = provably_fair_hash(server_seed, client_seed, nonce)

        engine = SESSION_ENGINES[game_name]
        initial_state = engine.start(body.bet_amount, body.params, hash_hex)

        # Check if game auto-completed (e.g., blackjack natural)
        is_complete = initial_state.get("phase") == "complete"

        session_doc = {
            "user_id": user["_id"],
            "game": game_name,
            "bet_amount": body.bet_amount,
            "status": "settled" if is_complete else "active",
            "state": initial_state,
            "server_seed": server_seed,
            "client_seed": client_seed,
            "nonce": nonce,
            "hash": hash_hex,
            "actions": [],
            "created_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc) if is_complete else None,
        }
        result = await db.game_sessions.insert_one(session_doc)
        session_id = str(result.inserted_id)

        # If auto-completed, settle now
        if is_complete:
            mult = initial_state.get("multiplier", 0)
            win_amount = round(body.bet_amount * mult, 2)
            await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": win_amount}})
            await _record_bet(db, user["_id"], game_name, body.bet_amount, win_amount, mult, initial_state, server_seed, client_seed, nonce, hash_hex)

        # Clean state for response (hide mines, dealer hole card, etc.)
        response_state = _clean_state(game_name, initial_state)
        u_after = await db.users.find_one({"_id": ObjectId(user["_id"])})

        return {
            "session_id": session_id,
            "game": game_name,
            "bet_amount": body.bet_amount,
            "status": "settled" if is_complete else "active",
            "state": response_state,
            "balance": round(u_after["balance"], 2),
        }

    @router.post("/{game_name}/{session_id}/action")
    async def session_action(game_name: str, session_id: str, body: ActionBody, request: Request):
        user = await get_user(request)
        try:
            session = await db.game_sessions.find_one({"_id": ObjectId(session_id)})
        except Exception:
            raise HTTPException(status_code=404, detail="Session not found")
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session["user_id"] != user["_id"]:
            raise HTTPException(status_code=403, detail="Not your session")
        if session["status"] != "active":
            raise HTTPException(status_code=400, detail="Session is not active")
        if session["game"] != game_name:
            raise HTTPException(status_code=400, detail="Game mismatch")

        engine = SESSION_ENGINES.get(game_name)
        if not engine:
            raise HTTPException(status_code=400, detail="Invalid game")

        state = session["state"]
        bet_amount = session["bet_amount"]

        # Handle double-down extra bet
        extra_bet = 0
        if game_name == "blackjack" and body.action == "double":
            u = await db.users.find_one({"_id": ObjectId(user["_id"])})
            if u["balance"] < bet_amount:
                raise HTTPException(status_code=400, detail="Insufficient balance to double")
            extra_bet = bet_amount
            await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": -extra_bet}})

        if game_name == "blackjack" and body.action == "split":
            u = await db.users.find_one({"_id": ObjectId(user["_id"])})
            if u["balance"] < bet_amount:
                raise HTTPException(status_code=400, detail="Insufficient balance to split")
            extra_bet = bet_amount
            await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": -extra_bet}})

        new_state = engine.action(state, body.action, body.params, bet_amount)
        is_complete = new_state.get("phase") == "complete"

        action_log = {"action": body.action, "params": body.params, "timestamp": datetime.now(timezone.utc).isoformat()}
        update = {"$set": {"state": new_state}, "$push": {"actions": action_log}}

        total_bet = bet_amount
        if game_name == "blackjack":
            split_bets = new_state.get("split_bets", [bet_amount])
            total_bet = sum(split_bets)

        if is_complete:
            mult = new_state.get("multiplier", 0)
            win_amount = round(total_bet * mult, 2)
            await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$inc": {"balance": win_amount}})
            update["$set"]["status"] = "settled"
            update["$set"]["completed_at"] = datetime.now(timezone.utc)
            server_seed = session.get("server_seed", "")
            client_seed = session.get("client_seed", "")
            nonce = session.get("nonce", 0)
            hash_hex = session.get("hash", "")
            await _record_bet(db, user["_id"], game_name, total_bet, win_amount, mult, new_state, server_seed, client_seed, nonce, hash_hex)

        await db.game_sessions.update_one({"_id": ObjectId(session_id)}, update)

        response_state = _clean_state(game_name, new_state)
        u_after = await db.users.find_one({"_id": ObjectId(user["_id"])})

        return {
            "session_id": session_id,
            "game": game_name,
            "status": "settled" if is_complete else "active",
            "state": response_state,
            "balance": round(u_after["balance"], 2),
            "bet_amount": total_bet,
            "win_amount": round(total_bet * new_state.get("multiplier", 0), 2) if is_complete else None,
        }

    @router.get("/{game_name}/active")
    async def get_active_session(game_name: str, request: Request):
        user = await get_user(request)
        session = await db.game_sessions.find_one({"user_id": user["_id"], "game": game_name, "status": "active"})
        if not session:
            return {"session": None}
        response_state = _clean_state(game_name, session["state"])
        return {
            "session": {
                "session_id": str(session["_id"]),
                "game": game_name,
                "bet_amount": session["bet_amount"],
                "state": response_state,
                "created_at": session["created_at"].isoformat() if isinstance(session["created_at"], datetime) else str(session["created_at"]),
            }
        }

    @router.get("/history")
    async def session_history(request: Request, page: int = 1, limit: int = 20):
        user = await get_user(request)
        query = {"user_id": user["_id"]}
        total = await db.game_sessions.count_documents(query)
        sessions = await db.game_sessions.find(query, {"state.deck": 0, "state.mine_positions": 0, "state.raw_hand": 0}).sort("created_at", -1).skip((page - 1) * limit).limit(limit).to_list(limit)
        result = []
        for s in sessions:
            result.append({
                "session_id": str(s["_id"]),
                "game": s["game"],
                "bet_amount": s["bet_amount"],
                "status": s["status"],
                "multiplier": s.get("state", {}).get("multiplier"),
                "outcome": s.get("state", {}).get("outcome"),
                "actions_count": len(s.get("actions", [])),
                "created_at": s["created_at"].isoformat() if isinstance(s["created_at"], datetime) else str(s["created_at"]),
            })
        return {"sessions": result, "total": total, "page": page}

    return router


def _clean_state(game_name, state):
    """Remove sensitive data from state before sending to client"""
    clean = {k: v for k, v in state.items() if k not in ("deck", "mine_positions", "dealer_full", "raw_hand", "deck_index")}
    if game_name == "mines" and state.get("phase") != "complete":
        clean.pop("mine_positions", None)
    if game_name == "crash" and state.get("phase") != "complete":
        clean.pop("crash_point", None)
    return clean


async def _record_bet(db, user_id, game, bet_amount, win_amount, multiplier, state, server_seed, client_seed, nonce, hash_hex):
    await db.bets.insert_one({
        "user_id": user_id, "game": game, "bet_amount": bet_amount,
        "win_amount": win_amount, "multiplier": multiplier,
        "result": {k: v for k, v in state.items() if k not in ("deck", "raw_hand", "deck_index")},
        "server_seed": server_seed, "client_seed": client_seed,
        "nonce": nonce, "hash": hash_hex, "status": "settled",
        "session_type": True, "created_at": datetime.now(timezone.utc),
    })
    net = win_amount - bet_amount
    u = await db.users.find_one({"_id": ObjectId(user_id)})
    await db.transactions.insert_one({
        "user_id": user_id, "type": "win" if net > 0 else "bet",
        "amount": net, "balance_after": round(u["balance"], 2),
        "description": f"{'Won' if net > 0 else 'Lost'} ${abs(net):.2f} on {game} (session)",
        "game": game, "created_at": datetime.now(timezone.utc),
    })
