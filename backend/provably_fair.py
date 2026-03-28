import hashlib
import secrets


def generate_server_seed():
    return secrets.token_hex(32)


def generate_client_seed():
    return secrets.token_hex(16)


def provably_fair_hash(server_seed, client_seed, nonce):
    message = f"{server_seed}:{client_seed}:{nonce}"
    return hashlib.sha256(message.encode()).hexdigest()


def hash_to_float(hash_hex, offset=0):
    hex_portion = hash_hex[offset * 8:(offset + 1) * 8]
    return int(hex_portion, 16) / 0xFFFFFFFF


def hash_to_int(hash_hex, min_val, max_val, offset=0):
    f = hash_to_float(hash_hex, offset)
    return min_val + int(f * (max_val - min_val))


def get_multiple_results(hash_hex, count, max_val):
    results = []
    current_hash = hash_hex
    for i in range(count):
        offset = i % 8
        if i > 0 and offset == 0:
            current_hash = hashlib.sha256(current_hash.encode()).hexdigest()
        results.append(hash_to_int(current_hash, 0, max_val, offset))
    return results


def verify_hash(server_seed, client_seed, nonce, expected_hash):
    return provably_fair_hash(server_seed, client_seed, nonce) == expected_hash


def create_shuffled_deck(hash_hex):
    import random
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [{'rank': r, 'suit': s} for s in suits for r in ranks]
    seed_int = int(hash_hex[:16], 16)
    rng = random.Random(seed_int)
    rng.shuffle(deck)
    return deck
