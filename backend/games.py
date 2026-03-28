import math
import random
from provably_fair import (
    generate_server_seed, generate_client_seed,
    provably_fair_hash, hash_to_float, hash_to_int,
    get_multiple_results, create_shuffled_deck
)

HOUSE_EDGE = 0.03

# ==================== CARD HELPERS ====================
def card_value_bj(card):
    r = card['rank']
    if r in ['J', 'Q', 'K']:
        return 10
    if r == 'A':
        return 11
    return int(r)

def hand_total_bj(hand):
    total = sum(card_value_bj(c) for c in hand)
    aces = sum(1 for c in hand if c['rank'] == 'A')
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total

def card_rank_value(card):
    order = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}
    return order.get(card['rank'], 0)

def card_str(card):
    return f"{card['rank']} of {card['suit']}"

# ==================== 1. SLOTS ====================
SLOT_SYMBOLS = ['cherry', 'lemon', 'orange', 'bell', 'diamond', 'seven', 'bar', 'star']
SLOT_PAY = {'seven': {3:50,2:5}, 'diamond': {3:25,2:3}, 'bar': {3:15,2:2}, 'star': {3:10,2:2}, 'bell': {3:8,2:1.5}, 'orange': {3:5,2:1}, 'lemon': {3:3,2:0.5}, 'cherry': {3:2,2:0.5}}

def play_slots(bet_amount, params, hash_hex):
    reels = [SLOT_SYMBOLS[hash_to_int(hash_hex, 0, len(SLOT_SYMBOLS), i)] for i in range(3)]
    mult = 0
    if reels[0] == reels[1] == reels[2]:
        mult = SLOT_PAY.get(reels[0], {}).get(3, 2)
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        m = reels[0] if reels[0] == reels[1] else reels[1]
        mult = SLOT_PAY.get(m, {}).get(2, 0.5)
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'reels': reels, 'is_win': mult > 0}}

# ==================== 2. BLACKJACK ====================
def play_blackjack(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]
    while hand_total_bj(player) < 17:
        player.append(deck.pop())
    pv = hand_total_bj(player)
    if pv <= 21:
        while hand_total_bj(dealer) < 17:
            dealer.append(deck.pop())
    dv = hand_total_bj(dealer)
    mult, outcome = 0, 'lose'
    if pv > 21:
        outcome, mult = 'bust', 0
    elif len(player) == 2 and pv == 21:
        if len(dealer) == 2 and dv == 21:
            outcome, mult = 'push', 1
        else:
            outcome, mult = 'blackjack', 2.5
    elif dv > 21:
        outcome, mult = 'win', 2
    elif pv > dv:
        outcome, mult = 'win', 2
    elif pv == dv:
        outcome, mult = 'push', 1
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'player_hand': [card_str(c) for c in player], 'dealer_hand': [card_str(c) for c in dealer], 'player_value': pv, 'dealer_value': dv, 'outcome': outcome}}

# ==================== 3. ROULETTE ====================
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def play_roulette(bet_amount, params, hash_hex):
    number = hash_to_int(hash_hex, 0, 37, 0)
    bt = params.get('bet_type', 'color')
    val = params.get('value', 'red')
    mult = 0
    if bt == 'straight' and int(val) == number: mult = 35
    elif bt == 'color':
        if (val == 'red' and number in RED) or (val == 'black' and number in BLACK): mult = 2
    elif bt == 'parity':
        if (val == 'even' and number > 0 and number % 2 == 0) or (val == 'odd' and number % 2 == 1): mult = 2
    elif bt == 'dozen':
        if val == '1st' and 1 <= number <= 12: mult = 3
        elif val == '2nd' and 13 <= number <= 24: mult = 3
        elif val == '3rd' and 25 <= number <= 36: mult = 3
    elif bt == 'half':
        if (val == '1-18' and 1 <= number <= 18) or (val == '19-36' and 19 <= number <= 36): mult = 2
    color = 'red' if number in RED else ('black' if number in BLACK else 'green')
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'number': number, 'color': color, 'bet_type': bt, 'bet_value': val, 'is_win': mult > 0}}

# ==================== 4. CRASH ====================
def play_crash(bet_amount, params, hash_hex):
    h = int(hash_hex[:13], 16)
    e = 2**52
    crash_point = max(1.0, round((e / (h + 1)) * (1 - HOUSE_EDGE), 2))
    crash_point = min(crash_point, 1000.0)
    ac = float(params.get('auto_cashout', 2.0))
    cashed = ac <= crash_point
    mult = ac if cashed else 0
    return {'win_amount': round(bet_amount * mult, 2) if cashed else 0, 'multiplier': mult, 'result': {'crash_point': crash_point, 'auto_cashout': ac, 'cashed_out': cashed}}

# ==================== 5. MINES ====================
def play_mines(bet_amount, params, hash_hex):
    mc = int(params.get('mines_count', 3))
    tr = int(params.get('tiles_revealed', 5))
    mc = max(1, min(24, mc))
    tr = max(1, min(24, tr))
    positions = set()
    results = get_multiple_results(hash_hex, mc * 3, 25)
    for r in results:
        if len(positions) >= mc: break
        positions.add(r % 25)
    while len(positions) < mc:
        for i in range(25):
            if i not in positions:
                positions.add(i)
                if len(positions) >= mc: break
    safe = 25 - mc
    if tr > safe:
        return {'win_amount': 0, 'multiplier': 0, 'result': {'mines_count': mc, 'tiles_revealed': tr, 'mine_positions': list(positions), 'survived': False}}
    prob = 1.0
    for i in range(tr):
        prob *= (safe - i) / (25 - i)
    mult = round((1 - HOUSE_EDGE) / prob, 2) if prob > 0 else 0
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'mines_count': mc, 'tiles_revealed': tr, 'mine_positions': list(positions), 'survived': True, 'potential_multiplier': mult}}

# ==================== 6. POKER (Video Poker - Jacks or Better) ====================
def evaluate_poker(hand):
    ranks = sorted([card_rank_value(c) for c in hand], reverse=True)
    suits = [c['suit'] for c in hand]
    is_flush = len(set(suits)) == 1
    is_straight = (ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5) or ranks == [14,5,4,3,2]
    counts = {}
    for r in ranks:
        counts[r] = counts.get(r, 0) + 1
    freq = sorted(counts.values(), reverse=True)
    if is_flush and is_straight and ranks[0] == 14 and ranks[1] == 13: return 'royal_flush', 250
    if is_flush and is_straight: return 'straight_flush', 50
    if freq == [4,1]: return 'four_of_a_kind', 25
    if freq == [3,2]: return 'full_house', 9
    if is_flush: return 'flush', 6
    if is_straight: return 'straight', 4
    if freq == [3,1,1]: return 'three_of_a_kind', 3
    if freq == [2,2,1]: return 'two_pair', 2
    if freq == [2,1,1,1]:
        pair_rank = [r for r,c in counts.items() if c == 2][0]
        if pair_rank >= 11: return 'jacks_or_better', 1
    return 'high_card', 0

def play_poker(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    hand = [deck.pop() for _ in range(5)]
    hand_name, mult = evaluate_poker(hand)
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'hand': [card_str(c) for c in hand], 'hand_rank': hand_name, 'is_win': mult > 0}}

# ==================== 7. CRAPS ====================
def play_craps(bet_amount, params, hash_hex):
    d1 = hash_to_int(hash_hex, 1, 7, 0)
    d2 = hash_to_int(hash_hex, 1, 7, 1)
    total = d1 + d2
    bt = params.get('bet_type', 'pass')
    mult = 0
    if bt == 'pass':
        if total in [7, 11]: mult = 2
        elif total in [2, 3, 12]: mult = 0
        else: mult = 2 if hash_to_float(hash_hex, 2) > 0.5 else 0
    elif bt == 'dont_pass':
        if total in [2, 3]: mult = 2
        elif total == 12: mult = 1
        elif total in [7, 11]: mult = 0
        else: mult = 0 if hash_to_float(hash_hex, 2) > 0.5 else 2
    elif bt == 'field':
        if total in [2, 12]: mult = 3
        elif total in [3, 4, 9, 10, 11]: mult = 2
    elif bt == 'any_seven':
        if total == 7: mult = 5
    elif bt == 'hardways':
        if d1 == d2 and total == int(params.get('value', 8)): mult = 10
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'dice': [d1, d2], 'total': total, 'bet_type': bt, 'is_win': mult > 0}}

# ==================== 8. SIC BO ====================
def play_sicbo(bet_amount, params, hash_hex):
    d1 = hash_to_int(hash_hex, 1, 7, 0)
    d2 = hash_to_int(hash_hex, 1, 7, 1)
    d3 = hash_to_int(hash_hex, 1, 7, 2)
    total = d1 + d2 + d3
    bt = params.get('bet_type', 'big')
    val = params.get('value', None)
    mult = 0
    is_triple = d1 == d2 == d3
    if bt == 'big' and 11 <= total <= 17 and not is_triple: mult = 2
    elif bt == 'small' and 4 <= total <= 10 and not is_triple: mult = 2
    elif bt == 'triple' and is_triple:
        if val and d1 == int(val): mult = 180
        else: mult = 30
    elif bt == 'total' and val and total == int(val):
        total_pays = {4:62,5:31,6:18,7:12,8:8,9:7,10:6,11:6,12:7,13:8,14:12,15:18,16:31,17:62}
        mult = total_pays.get(total, 0)
    elif bt == 'double' and val:
        v = int(val)
        if [d1,d2,d3].count(v) >= 2: mult = 11
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'dice': [d1, d2, d3], 'total': total, 'is_triple': is_triple, 'bet_type': bt, 'is_win': mult > 0}}

# ==================== 9. BACCARAT ====================
def baccarat_card_val(card):
    r = card['rank']
    if r in ['10', 'J', 'Q', 'K']: return 0
    if r == 'A': return 1
    return int(r)

def baccarat_hand_val(hand):
    return sum(baccarat_card_val(c) for c in hand) % 10

def play_baccarat(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    player = [deck.pop(), deck.pop()]
    banker = [deck.pop(), deck.pop()]
    pv = baccarat_hand_val(player)
    bv = baccarat_hand_val(banker)
    if pv <= 5: player.append(deck.pop())
    pv = baccarat_hand_val(player)
    p3 = baccarat_card_val(player[2]) if len(player) == 3 else -1
    draw_banker = False
    if bv <= 2: draw_banker = True
    elif bv == 3 and p3 != 8: draw_banker = True
    elif bv == 4 and p3 in [2,3,4,5,6,7]: draw_banker = True
    elif bv == 5 and p3 in [4,5,6,7]: draw_banker = True
    elif bv == 6 and p3 in [6,7]: draw_banker = True
    if draw_banker and len(player) == 3: banker.append(deck.pop())
    bv = baccarat_hand_val(banker)
    pv = baccarat_hand_val(player)
    bet_on = params.get('bet_on', 'player')
    mult = 0
    if pv > bv:
        winner = 'player'
        if bet_on == 'player': mult = 2
    elif bv > pv:
        winner = 'banker'
        if bet_on == 'banker': mult = 1.95
    else:
        winner = 'tie'
        if bet_on == 'tie': mult = 9
        elif bet_on in ['player', 'banker']: mult = 1
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'player_hand': [card_str(c) for c in player], 'banker_hand': [card_str(c) for c in banker], 'player_value': pv, 'banker_value': bv, 'winner': winner, 'bet_on': bet_on, 'is_win': mult > 1}}

# ==================== 10. WHEEL OF FORTUNE ====================
WHEEL_SEGMENTS = [
    {'label': '1x', 'mult': 1, 'weight': 24},
    {'label': '2x', 'mult': 2, 'weight': 15},
    {'label': '5x', 'mult': 5, 'weight': 7},
    {'label': '10x', 'mult': 10, 'weight': 4},
    {'label': '20x', 'mult': 20, 'weight': 2},
    {'label': '40x', 'mult': 40, 'weight': 1},
    {'label': '0x', 'mult': 0, 'weight': 1},
]
WHEEL_TOTAL_WEIGHT = sum(s['weight'] for s in WHEEL_SEGMENTS)

def play_wheel(bet_amount, params, hash_hex):
    val = hash_to_int(hash_hex, 0, WHEEL_TOTAL_WEIGHT, 0)
    cum = 0
    segment = WHEEL_SEGMENTS[0]
    for s in WHEEL_SEGMENTS:
        cum += s['weight']
        if val < cum:
            segment = s
            break
    mult = segment['mult']
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'segment': segment['label'], 'all_segments': [s['label'] for s in WHEEL_SEGMENTS], 'is_win': mult > 0}}

# ==================== 11. DRAGON TIGER ====================
def play_dragon_tiger(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    dragon = deck.pop()
    tiger = deck.pop()
    dv = card_rank_value(dragon)
    tv = card_rank_value(tiger)
    bet_on = params.get('bet_on', 'dragon')
    mult = 0
    if dv > tv:
        winner = 'dragon'
        if bet_on == 'dragon': mult = 2
    elif tv > dv:
        winner = 'tiger'
        if bet_on == 'tiger': mult = 2
    else:
        winner = 'tie'
        if bet_on == 'tie': mult = 11
        else: mult = 0.5
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'dragon': card_str(dragon), 'tiger': card_str(tiger), 'dragon_value': dv, 'tiger_value': tv, 'winner': winner, 'is_win': mult >= 2}}

# ==================== 12. VIDEO POKER ====================
def play_video_poker(bet_amount, params, hash_hex):
    return play_poker(bet_amount, params, hash_hex)

# ==================== 13. HI-LO ====================
def play_hilo(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    first = deck.pop()
    second = deck.pop()
    fv = card_rank_value(first)
    sv = card_rank_value(second)
    guess = params.get('guess', 'higher')
    mult = 0
    if guess == 'higher' and sv > fv: mult = 2
    elif guess == 'lower' and sv < fv: mult = 2
    elif sv == fv: mult = 3
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'first_card': card_str(first), 'second_card': card_str(second), 'first_value': fv, 'second_value': sv, 'guess': guess, 'is_win': mult > 0}}

# ==================== 14. PLINKO ====================
PLINKO_MULTS = {
    'low': [1.5, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.5],
    'medium': [3.0, 1.5, 1.2, 0.8, 0.3, 0.8, 1.2, 1.5, 3.0],
    'high': [10.0, 3.0, 1.5, 0.5, 0.1, 0.5, 1.5, 3.0, 10.0],
}

def play_plinko(bet_amount, params, hash_hex):
    risk = params.get('risk', 'medium')
    mults = PLINKO_MULTS.get(risk, PLINKO_MULTS['medium'])
    rows = 8
    pos = len(mults) // 2
    path = [pos]
    for i in range(rows):
        direction = 1 if hash_to_float(hash_hex, i) > 0.5 else -1
        pos = max(0, min(len(mults) - 1, pos + direction))
        path.append(pos)
    mult = mults[pos]
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'path': path, 'final_position': pos, 'risk': risk, 'multipliers': mults, 'is_win': mult > 0}}

# ==================== 15. LOTTERY ====================
def play_lottery(bet_amount, params, hash_hex):
    picked = params.get('numbers', [7, 14, 21, 28, 35, 42])
    if not picked or len(picked) < 1:
        picked = [7, 14, 21, 28, 35, 42]
    picked = [int(n) for n in picked[:6]]
    drawn = sorted(set(get_multiple_results(hash_hex, 10, 49)))[:6]
    drawn = [d + 1 for d in drawn]
    matches = len(set(picked) & set(drawn))
    payouts = {0: 0, 1: 0, 2: 0.5, 3: 3, 4: 20, 5: 500, 6: 10000}
    mult = payouts.get(matches, 0)
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'picked': picked, 'drawn': drawn, 'matches': matches, 'is_win': mult > 0}}

# ==================== 16. TEEN PATTI ====================
def teen_patti_rank(hand):
    ranks = sorted([card_rank_value(c) for c in hand], reverse=True)
    suits = [c['suit'] for c in hand]
    is_flush = len(set(suits)) == 1
    is_seq = ranks[0] - ranks[2] == 2 and len(set(ranks)) == 3
    is_trail = ranks[0] == ranks[1] == ranks[2]
    if is_trail: return 6, ranks
    if is_flush and is_seq: return 5, ranks
    if is_seq: return 4, ranks
    if is_flush: return 3, ranks
    if ranks[0] == ranks[1] or ranks[1] == ranks[2]: return 2, ranks
    return 1, ranks

def play_teen_patti(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    player = [deck.pop() for _ in range(3)]
    dealer = [deck.pop() for _ in range(3)]
    pr, pranks = teen_patti_rank(player)
    dr, dranks = teen_patti_rank(dealer)
    rank_names = {6:'Trail',5:'Pure Sequence',4:'Sequence',3:'Flush',2:'Pair',1:'High Card'}
    if pr > dr or (pr == dr and pranks > dranks):
        winner, mult = 'player', 2
    elif pr == dr and pranks == dranks:
        winner, mult = 'tie', 1
    else:
        winner, mult = 'dealer', 0
    bet_on = params.get('bet_on', 'player')
    if bet_on == 'player' and winner != 'player': mult = 0
    elif bet_on == 'dealer' and winner != 'dealer': mult = 0
    elif bet_on == 'tie' and winner == 'tie': mult = 5
    elif bet_on == 'tie': mult = 0
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'player_hand': [card_str(c) for c in player], 'dealer_hand': [card_str(c) for c in dealer], 'player_rank': rank_names.get(pr,''), 'dealer_rank': rank_names.get(dr,''), 'winner': winner, 'is_win': mult > 0}}

# ==================== 17. ANDAR BAHAR ====================
def play_andar_bahar(bet_amount, params, hash_hex):
    deck = create_shuffled_deck(hash_hex)
    joker = deck.pop()
    joker_rank = card_rank_value(joker)
    bet_on = params.get('bet_on', 'andar')
    andar_cards, bahar_cards = [], []
    winner = None
    for i in range(50):
        card = deck.pop()
        if i % 2 == 0:
            andar_cards.append(card)
            if card_rank_value(card) == joker_rank:
                winner = 'andar'
                break
        else:
            bahar_cards.append(card)
            if card_rank_value(card) == joker_rank:
                winner = 'bahar'
                break
    if not winner:
        winner = 'andar'
    mult = 0
    if bet_on == winner:
        mult = 1.9 if winner == 'andar' else 2.0
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'joker': card_str(joker), 'andar_count': len(andar_cards), 'bahar_count': len(bahar_cards), 'winner': winner, 'bet_on': bet_on, 'is_win': mult > 0}}

# ==================== 18. KENO ====================
def play_keno(bet_amount, params, hash_hex):
    picked = params.get('numbers', list(range(1, 11)))
    picked = [int(n) for n in picked[:10]]
    spots = len(picked)
    drawn_raw = get_multiple_results(hash_hex, 30, 80)
    drawn = sorted(list(set([d + 1 for d in drawn_raw]))[:20])
    matches = len(set(picked) & set(drawn))
    keno_pay = {
        1: {1: 3},
        2: {2: 9},
        3: {2: 2, 3: 25},
        4: {2: 1, 3: 5, 4: 75},
        5: {3: 3, 4: 15, 5: 250},
        6: {3: 2, 4: 8, 5: 50, 6: 1000},
        7: {3: 1, 4: 4, 5: 20, 6: 200, 7: 5000},
        8: {4: 3, 5: 10, 6: 75, 7: 1000, 8: 10000},
        9: {4: 2, 5: 6, 6: 40, 7: 300, 8: 5000, 9: 25000},
        10: {5: 4, 6: 20, 7: 100, 8: 2000, 9: 10000, 10: 100000},
    }
    mult = keno_pay.get(spots, {}).get(matches, 0)
    return {'win_amount': round(bet_amount * mult, 2), 'multiplier': mult, 'result': {'picked': picked, 'drawn': drawn, 'matches': matches, 'spots': spots, 'is_win': mult > 0}}


# ==================== GAME DISPATCHER ====================
GAME_MAP = {
    'slots': play_slots,
    'blackjack': play_blackjack,
    'roulette': play_roulette,
    'crash': play_crash,
    'mines': play_mines,
    'poker': play_poker,
    'craps': play_craps,
    'sicbo': play_sicbo,
    'baccarat': play_baccarat,
    'wheel': play_wheel,
    'dragon_tiger': play_dragon_tiger,
    'video_poker': play_video_poker,
    'hilo': play_hilo,
    'plinko': play_plinko,
    'lottery': play_lottery,
    'teen_patti': play_teen_patti,
    'andar_bahar': play_andar_bahar,
    'keno': play_keno,
}

GAME_INFO = {
    'slots': {'name': 'Slots', 'category': 'slots', 'house_edge': 3.0, 'min_bet': 1, 'max_bet': 10000, 'description': 'Classic 3-reel slot machine'},
    'blackjack': {'name': 'Blackjack', 'category': 'cards', 'house_edge': 2.0, 'min_bet': 5, 'max_bet': 50000, 'description': 'Beat the dealer to 21'},
    'roulette': {'name': 'Roulette', 'category': 'table', 'house_edge': 2.7, 'min_bet': 1, 'max_bet': 25000, 'description': 'European roulette'},
    'crash': {'name': 'Crash', 'category': 'instant', 'house_edge': 3.0, 'min_bet': 1, 'max_bet': 100000, 'description': 'Cash out before it crashes'},
    'mines': {'name': 'Mines', 'category': 'instant', 'house_edge': 3.0, 'min_bet': 1, 'max_bet': 10000, 'description': 'Reveal tiles, avoid mines'},
    'poker': {'name': 'Poker', 'category': 'cards', 'house_edge': 3.5, 'min_bet': 5, 'max_bet': 25000, 'description': 'Video poker - Jacks or Better'},
    'craps': {'name': 'Craps', 'category': 'dice', 'house_edge': 1.4, 'min_bet': 5, 'max_bet': 25000, 'description': 'Classic dice game'},
    'sicbo': {'name': 'Sic Bo', 'category': 'dice', 'house_edge': 2.8, 'min_bet': 1, 'max_bet': 10000, 'description': 'Three dice betting'},
    'baccarat': {'name': 'Baccarat', 'category': 'cards', 'house_edge': 1.2, 'min_bet': 10, 'max_bet': 100000, 'description': 'Player vs Banker'},
    'wheel': {'name': 'Wheel of Fortune', 'category': 'instant', 'house_edge': 5.0, 'min_bet': 1, 'max_bet': 5000, 'description': 'Spin the wheel'},
    'dragon_tiger': {'name': 'Dragon Tiger', 'category': 'cards', 'house_edge': 3.7, 'min_bet': 5, 'max_bet': 25000, 'description': 'Simple card comparison'},
    'video_poker': {'name': 'Video Poker', 'category': 'cards', 'house_edge': 3.5, 'min_bet': 1, 'max_bet': 10000, 'description': 'Draw poker machine'},
    'hilo': {'name': 'Hi-Lo', 'category': 'cards', 'house_edge': 2.5, 'min_bet': 1, 'max_bet': 10000, 'description': 'Higher or lower card game'},
    'plinko': {'name': 'Plinko', 'category': 'instant', 'house_edge': 3.0, 'min_bet': 1, 'max_bet': 10000, 'description': 'Drop the ball'},
    'lottery': {'name': 'Lottery', 'category': 'instant', 'house_edge': 15.0, 'min_bet': 1, 'max_bet': 100, 'description': 'Pick your lucky numbers'},
    'teen_patti': {'name': 'Teen Patti', 'category': 'cards', 'house_edge': 3.0, 'min_bet': 5, 'max_bet': 25000, 'description': 'Indian 3-card poker'},
    'andar_bahar': {'name': 'Andar Bahar', 'category': 'cards', 'house_edge': 2.5, 'min_bet': 5, 'max_bet': 25000, 'description': 'Classic Indian card game'},
    'keno': {'name': 'Keno', 'category': 'instant', 'house_edge': 10.0, 'min_bet': 1, 'max_bet': 100, 'description': 'Pick numbers and win'},
}

def play_game(game_name, bet_amount, params=None):
    if params is None:
        params = {}
    if game_name not in GAME_MAP:
        return None
    server_seed = generate_server_seed()
    client_seed = generate_client_seed()
    nonce = random.randint(1, 1000000)
    hash_hex = provably_fair_hash(server_seed, client_seed, nonce)
    result = GAME_MAP[game_name](bet_amount, params, hash_hex)
    result['server_seed'] = server_seed
    result['client_seed'] = client_seed
    result['nonce'] = nonce
    result['hash'] = hash_hex
    result['game'] = game_name
    return result
