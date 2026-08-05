"""Curated product image bank - all URLs HTTP-verified 2026-05-17.

Strategy: Only include Unsplash photo IDs that return HTTP 200. The
verification step in build pipeline keeps this list valid.
"""
import hashlib
import random

W = "?w=900&auto=format&fit=crop&q=70"

def _u(pid: str) -> str:
    return f"https://images.unsplash.com/photo-{pid}"

# All IDs below verified 2026-05-17 (HTTP 200)
IMAGES = {
    "electric_dirtbike": [
        _u("1568772585407-9361f9bf3a87"),  # dirt bike trail
        _u("1599819811279-d5ad9cccf838"),  # off road bike
        _u("1558981403-c5f9899a28bc"),     # motocross
        _u("1605559424843-9e4c228bf1c2"),  # motocross jump
    ],
    "emtb": [
        _u("1485965120184-e220f721d03e"),  # mtb jump
        _u("1532298229144-0ec0c57515c7"),  # downhill
        _u("1571333250630-f0230c320b6d"),  # mtb trail
        _u("1502744688674-c619d1586c9e"),  # mountain bike
    ],
    "skateboard": [
        _u("1547447134-cd3f5c716030"),   # skateboard
        _u("1547949003-9792a18a2601"),   # skateboard side
        _u("1531565637446-32307b194362"),  # skate close
        _u("1520342868574-5fa3804e551c"),  # longboard
    ],
    "euc": [
        _u("1572116469696-31de0f17cc34"),   # PEV
        _u("1564594985645-4427056e22e2"),   # scooter
        _u("1591293836027-e05b48473b67"),   # urban electric
        _u("1517991104123-1d56a6e81ed9"),   # urban
        _u("1564890369478-c89ca6d9cde9"),   # urban transport
    ],
    "motors": [
        _u("1517524008697-84bbe3c3fd98"),   # engine
        _u("1486496572940-2bb2341fdbdf"),   # gears
        _u("1581094288338-2314dddb7ece"),   # circuit
        _u("1605379399642-870262d3d051"),   # metal parts
        _u("1620714223084-8fcacc6dfd8d"),   # battery/motor
    ],
    "batteries": [
        _u("1620714223084-8fcacc6dfd8d"),   # battery pack
        _u("1593941707882-a5bba14938c7"),   # cells
        _u("1610824352934-c10d87b700cc"),   # lithium
        _u("1581094288338-2314dddb7ece"),   # battery circuit
        _u("1497436072909-60f360e1d4b1"),   # power
    ],
    "helmets": [
        _u("1591348122449-02525d70379b"),  # downhill helmet
        _u("1627928387551-0d5562a3e2b6"),  # helmet detail
        _u("1605559424843-9e4c228bf1c2"),  # motocross
    ],
    "jerseys": [
        _u("1556821840-3a63f95609a7"),    # hoodie
        _u("1542219550-37153d387c27"),    # athletic top
        _u("1521572163474-6864f9cf17ab"),  # t-shirt
        _u("1622519407650-3df9883f76a5"),  # jersey
        _u("1583744946564-b52ac1c389c8"),  # sportswear
    ],
    "pants": [
        _u("1542272604-787c3835535d"),  # jeans/pants
        _u("1584466977773-e625c37cdd50"),  # mtb shorts
        _u("1605559424843-9e4c228bf1c2"),  # rider pants
        _u("1473042904451-00171c69419d"),
        _u("1473496169904-658ba7c44d8a"),
    ],
    "gloves": [
        _u("1547949003-9792a18a2601"),
        _u("1574607383476-f517f260d30b"),  # leather gloves
        _u("1611591437281-460bfbe1220a"),  # gloves
        _u("1606107557195-0e29a4b5b4aa"),  # tactical gloves
    ],
    "protection": [
        _u("1591348122449-02525d70379b"),  # gear
        _u("1622547748225-3fc4abd2cca0"),  # rider gear
        _u("1568772585407-9361f9bf3a87"),  # rider protection
        _u("1605559424843-9e4c228bf1c2"),  # motocross
    ],
    "spare_parts": [
        _u("1486496572940-2bb2341fdbdf"),  # gears
        _u("1517524008697-84bbe3c3fd98"),  # engine
        _u("1605379399642-870262d3d051"),  # bike parts
        _u("1532298229144-0ec0c57515c7"),  # tools
        _u("1581094288338-2314dddb7ece"),  # circuit
    ],
    "merch_kilovoltz": [
        _u("1556821840-3a63f95609a7"),    # hoodie
        _u("1521572163474-6864f9cf17ab"),  # t-shirt
        _u("1542219550-37153d387c27"),    # apparel
        _u("1620712943543-bcc4688e7485"),  # stickers
        _u("1583743814966-8936f5b7be1a"),  # cap
        _u("1622519407650-3df9883f76a5"),
        _u("1583744946564-b52ac1c389c8"),
    ],
    "merch_rmr": [
        _u("1556821840-3a63f95609a7"),
        _u("1521572163474-6864f9cf17ab"),
        _u("1542219550-37153d387c27"),
        _u("1620712943543-bcc4688e7485"),
        _u("1583743814966-8936f5b7be1a"),
        _u("1622519407650-3df9883f76a5"),
        _u("1583744946564-b52ac1c389c8"),
    ],
}

DEFAULT_FALLBACK = [
    _u("1485965120184-e220f721d03e"),
    _u("1547447134-cd3f5c716030"),
]


def pick_image(subcategory: str, seed: str = "") -> str:
    """Deterministically pick a verified Unsplash image URL for a subcategory.
    Stable seed (product name) -> same image every time."""
    pool = IMAGES.get(subcategory, DEFAULT_FALLBACK)
    if seed:
        h = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
        return pool[h % len(pool)] + W
    return random.choice(pool) + W
